"""Celery tasks for executing graphs."""

import os
import json
import asyncio
import logging
import contextvars
from datetime import datetime
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque

from agate_core import RunContext, GraphSpec, NodeConfig, get as get_node
from agate_db import get_session, Run, ProcessedItem, Project, get_all_project_api_keys

# Import nodes to register them
import agate_nodes  # noqa: F401

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "agate",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Number of queues for round-robin distribution
NUM_QUEUES = int(os.getenv("CELERY_NUM_QUEUES", "4"))

# Task timeout configuration (in seconds)
# Soft limit: raises SoftTimeLimitExceeded (can be caught for cleanup)
# Hard limit: raises TimeLimitExceeded (kills process, no cleanup)
# Increased defaults to accommodate longer flows; can be overridden via env.
TASK_SOFT_TIME_LIMIT = int(os.getenv("TASK_SOFT_TIME_LIMIT", "3600"))  # 60 minutes default
TASK_HARD_TIME_LIMIT = int(os.getenv("TASK_HARD_TIME_LIMIT", "4200"))  # 70 minutes default

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Fair distribution: only prefetch 1 task per worker process
    # This prevents workers from hoarding tasks and ensures better load balancing
    worker_prefetch_multiplier=1,
    # Acknowledge tasks after completion, not before
    # This ensures tasks are retried if worker crashes mid-execution
    task_acks_late=True,
    # Default queue fallback (workers will consume from all queues specified via -Q flag)
    task_default_queue='queue-0',
)

current_node_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_node_id", default=None
)


class NodeLogHandler(logging.Handler):
    """Capture logs emitted by nodes and group them by node ID."""

    def __init__(self, node_logs: Dict[str, List[str]]):
        super().__init__(level=logging.INFO)
        self.node_logs = node_logs
        self.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            node_id = current_node_id.get()
            if not node_id:
                return
            message = self.format(record)
            self.node_logs.setdefault(node_id, []).append(message)
        except Exception:
            # Never allow logging failures to bubble up
            return


def topological_sort(nodes: List[NodeConfig], edges: list) -> List[NodeConfig]:
    """
    Sort nodes in topological order based on edges.
    
    Args:
        nodes: List of node configurations
        edges: List of edges (dicts with 'source' and 'target')
        
    Returns:
        List of nodes in execution order
    """
    # Build adjacency list and in-degree count
    node_map = {node.id: node for node in nodes}
    adjacency = defaultdict(list)
    in_degree = {node.id: 0 for node in nodes}
    
    for edge in edges:
        source = edge.source if hasattr(edge, 'source') else edge['source']
        target = edge.target if hasattr(edge, 'target') else edge['target']
        adjacency[source].append(target)
        in_degree[target] += 1
    
    # Find nodes with no incoming edges
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    sorted_nodes = []
    
    while queue:
        node_id = queue.popleft()
        sorted_nodes.append(node_map[node_id])
        
        # Reduce in-degree for dependent nodes
        for neighbor in adjacency[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check for cycles
    if len(sorted_nodes) != len(nodes):
        raise ValueError("Graph contains a cycle")
    
    return sorted_nodes


def build_execution_levels(nodes: List[NodeConfig], edges: list) -> List[List[str]]:
    """
    Group nodes into execution levels for parallel execution.
    Nodes at the same level can run in parallel.
    
    Args:
        nodes: List of node configurations
        edges: List of edges
        
    Returns:
        List of levels, where each level is a list of node IDs
    """
    # Calculate depth of each node
    node_map = {node.id: node for node in nodes}
    depths = {}
    
    # Get topological order first
    sorted_nodes = topological_sort(nodes, edges)
    
    # Calculate depth for each node
    for node in sorted_nodes:
        max_input_depth = -1
        for edge in edges:
            source = edge.source if hasattr(edge, 'source') else edge['source']
            target = edge.target if hasattr(edge, 'target') else edge['target']
            if target == node.id and source in depths:
                max_input_depth = max(max_input_depth, depths[source])
        depths[node.id] = max_input_depth + 1
    
    # Group by depth
    levels_dict = defaultdict(list)
    for node_id, depth in depths.items():
        levels_dict[depth].append(node_id)
    
    # Return as ordered list of levels
    return [levels_dict[i] for i in sorted(levels_dict.keys())]


async def execute_node_async(node_config: NodeConfig, inputs: Dict[str, Any], ctx: RunContext) -> Any:
    """
    Execute a single node asynchronously.
    
    Args:
        node_config: Node configuration
        inputs: Input data for the node
        ctx: Runtime context
        
    Returns:
        Validated output from the node
    """
    token = current_node_id.set(node_config.id)
    try:
        NodeClass = get_node(node_config.type)
        validated_input = NodeClass.Input.model_validate(inputs)
        params = NodeClass.Params.model_validate(node_config.params)
        node_instance = NodeClass()
        output = await node_instance.run(validated_input, params, ctx)
        return NodeClass.Output.model_validate(output)
    finally:
        current_node_id.reset(token)


async def execute_level_async(level_configs: List[NodeConfig], level_inputs: Dict[str, Dict[str, Any]], ctx: RunContext) -> List[Any]:
    """
    Execute all nodes at a level in parallel.
    
    Args:
        level_configs: List of node configurations for this level
        level_inputs: Dict mapping node_id to input data
        ctx: Runtime context
        
    Returns:
        List of outputs from all nodes
    """
    tasks = [
        execute_node_async(config, level_inputs[config.id], ctx)
        for config in level_configs
    ]
    return await asyncio.gather(*tasks)


def execute_level_with_timeout(
    level_configs: List[NodeConfig], 
    level_inputs: Dict[str, Dict[str, Any]], 
    ctx: RunContext,
    timeout_seconds: float = 1500.0  # 25 minutes, less than soft limit (30 min)
) -> List[Any]:
    """
    Execute level with timeout to allow Celery signals to interrupt.
    
    Wraps asyncio.run() with asyncio.wait_for() so that Celery's timeout
    signals can properly interrupt long-running async operations.
    
    Args:
        level_configs: List of node configurations for this level
        level_inputs: Dict mapping node_id to input data
        ctx: Runtime context
        timeout_seconds: Maximum time to wait for level execution (default: 1500s / 25 minutes)
        
    Returns:
        List of outputs from all nodes
        
    Raises:
        TimeoutError: If execution exceeds timeout_seconds
    """
    try:
        return asyncio.run(
            asyncio.wait_for(
                execute_level_async(level_configs, level_inputs, ctx),
                timeout=timeout_seconds
            )
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Level execution exceeded {timeout_seconds}s timeout")


def map_node_inputs(node_id: str, edges: list, node_outputs: Dict[str, Any], node_map: Dict[str, NodeConfig], fallback_input: Any = None) -> Dict[str, Any]:
    """
    Build state dictionary from all upstream node outputs.
    Each node's output is stored under its node ID as a namespace (except Output, which deep-merges).
    """
    state: Dict[str, Any] = {}
    target_node = node_map.get(node_id)
    is_output_node = target_node and target_node.type == "Output"

    upstream_nodes = set()
    for edge in edges:
        source = edge.source if hasattr(edge, 'source') else edge['source']
        target = edge.target if hasattr(edge, 'target') else edge['target']
        if target == node_id and source in node_outputs:
            upstream_nodes.add(source)

    if is_output_node:
        for source_id, source_output in node_outputs.items():
            if hasattr(source_output, 'model_dump'):
                source_data = source_output.model_dump()
            elif isinstance(source_output, dict):
                source_data = source_output
            else:
                continue
            state.update(source_data)
    else:
        if target_node and target_node.type == "PlaceExtract":
            print(f"[map_node_inputs] PlaceExtract {node_id}: upstream_nodes={upstream_nodes}, node_outputs keys={list(node_outputs.keys())}")

        mapped_any = False
        for source_id in upstream_nodes:
            source_output = node_outputs[source_id]
            if hasattr(source_output, 'model_dump'):
                state[source_id] = source_output.model_dump()
            elif isinstance(source_output, dict):
                state[source_id] = source_output
            mapped_any = True

            if target_node and target_node.type == "PlaceExtract":
                output_dict = state[source_id] if isinstance(state[source_id], dict) else {}
                print(f"[map_node_inputs] PlaceExtract {node_id}: Added output from {source_id}, keys={list(output_dict.keys())}")

        if not mapped_any and fallback_input is not None:
            if isinstance(fallback_input, dict) and fallback_input:
                state.update(fallback_input)
            else:
                state["input_data"] = fallback_input

        if target_node and target_node.type == "PlaceExtract" and not state:
            print(f"[map_node_inputs] PlaceExtract {node_id}: No upstream nodes via edges, searching all node_outputs for 'text' field")
            for source_id, source_output in node_outputs.items():
                output_dict = source_output.model_dump() if hasattr(source_output, 'model_dump') else source_output if isinstance(source_output, dict) else {}
                if isinstance(output_dict, dict) and 'text' in output_dict:
                    state[source_id] = output_dict
                    print(f"[map_node_inputs] PlaceExtract {node_id}: Found output with 'text' field from {source_id}, keys={list(output_dict.keys())}")
                    break

        if target_node and target_node.type == "PlaceExtract":
            print(f"[map_node_inputs] PlaceExtract {node_id}: Final state keys={list(state.keys())}")

    return state


@celery_app.task(name="worker.tasks.execute_graph")
def execute_graph(run_id: int, spec_json: str, input_payload: Dict[str, Any]):
    """
    Execute a graph with the given input.
    
    Args:
        run_id: Run ID to update
        spec_json: JSON string of GraphSpec
        input_payload: Input data for the graph (unused for multi-node graphs)
    """
    print(f"[Run {run_id}] Starting execution")
    
    session = get_session()
    
    try:
        # Update status to running
        run = session.get(Run, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        run.status = "running"
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()
        
        # Parse spec
        spec = GraphSpec.model_validate_json(spec_json)
        print(f"[Run {run_id}] Loaded graph: {spec.name}")
        
        if not spec.nodes:
            raise ValueError("Graph has no nodes")
        
        # Build execution levels for parallel execution
        print(f"[Run {run_id}] Building execution levels for {len(spec.nodes)} nodes")
        levels = build_execution_levels(spec.nodes, spec.edges)
        print(f"[Run {run_id}] Execution levels: {levels}")
        
        # Load project API keys and system prompt
        print(f"[Run {run_id}] Loading API keys for project {run.project_id}")
        try:
            api_keys = get_all_project_api_keys(session, run.project_id)
            print(f"[Run {run_id}] Loaded {len(api_keys)} API keys: {list(api_keys.keys())}")
        except Exception as e:
            print(f"[Run {run_id}] Warning: Failed to load API keys: {str(e)}")
            api_keys = {}
        
        # Load project system prompt
        project = session.get(Project, run.project_id)
        project_system_prompt = project.system_prompt if project else None
        if project_system_prompt:
            print(f"[Run {run_id}] Using project system prompt: {project_system_prompt[:100]}...")
        
        # Execute nodes level by level (parallel within each level)
        node_outputs = {}
        node_map = {node.id: node for node in spec.nodes}
        ctx = RunContext(
            run_id=str(run_id), 
            project_id=run.project_id, 
            api_keys=api_keys,
            project_system_prompt=project_system_prompt
        )
        
        for level_idx, level_node_ids in enumerate(levels):
            print(f"[Run {run_id}] Level {level_idx}: Executing {len(level_node_ids)} node(s) in parallel")
            
            # Prepare inputs for all nodes at this level
            level_configs = []
            level_inputs = {}
            
            for node_id in level_node_ids:
                node_config = node_map[node_id]
                print(f"[Run {run_id}]   - {node_config.type} (id={node_config.id})")
                
                # Build input from previous nodes or empty for input nodes
                if node_config.type in ["TextInput", "JSONInput"]:
                    # Input nodes don't take input from previous nodes
                    node_input = {}
                else:
                    # Map outputs from previous nodes
                    node_input = map_node_inputs(node_config.id, spec.edges, node_outputs, node_map, fallback_input=None)
                
                print(f"[Run {run_id}]     Input: {list(node_input.keys())}")
                
                level_configs.append(node_config)
                level_inputs[node_config.id] = node_input
            
            # Execute all nodes at this level in parallel
            print(f"[Run {run_id}] Starting parallel execution for level {level_idx}...")
            try:
                # Use timeout wrapper to allow Celery signals to interrupt
                level_timeout = max(TASK_SOFT_TIME_LIMIT - 60, int(TASK_SOFT_TIME_LIMIT * 0.9))
                level_outputs = execute_level_with_timeout(level_configs, level_inputs, ctx, timeout_seconds=level_timeout)
            except TimeoutError as e:
                print(f"[Run {run_id}] Level {level_idx} timed out: {str(e)}")
                raise
            print(f"[Run {run_id}] Level {level_idx} completed")
            
            # Store outputs
            for node_config, output in zip(level_configs, level_outputs):
                node_outputs[node_config.id] = output
                print(f"[Run {run_id}]   - {node_config.id} output: {type(output).__name__}")
        
        # Use the last level's first node output as the final output
        # (typically this will be an Output node that consolidates everything)
        final_node_id = levels[-1][0]
        final_output = node_outputs[final_node_id]
        
        # Update run with success
        run.status = "succeeded"
        run.output_json = final_output.model_dump_json()
        run.node_outputs_json = json.dumps({k: v.model_dump() for k, v in node_outputs.items()})
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()
        
        print(f"[Run {run_id}] Completed successfully")
        
        return {
            "status": "succeeded",
            "output": final_output.model_dump(),
            "node_outputs": {k: v.model_dump() for k, v in node_outputs.items()}
        }
        
    except Exception as e:
        print(f"[Run {run_id}] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update run with error
        run = session.get(Run, run_id)
        if run:
            run.status = "failed"
            run.error = str(e)
            run.updated_at = datetime.utcnow()
            session.add(run)
            session.commit()
        
        raise
    
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.execute_processed_item",
    bind=True,  # Required to access task instance for time limits
    soft_time_limit=TASK_SOFT_TIME_LIMIT,
    time_limit=TASK_HARD_TIME_LIMIT
)
def execute_processed_item(self, processed_item_id: int):
    """
    Execute a graph for a single ProcessedItem.
    
    Args:
        processed_item_id: ProcessedItem ID to process
    """
    # Log worker info for diagnostics
    worker_name = self.request.hostname if hasattr(self.request, 'hostname') else 'unknown'
    queue_name = self.request.delivery_info.get('routing_key', 'unknown') if hasattr(self.request, 'delivery_info') else 'unknown'
    print(f"[ProcessedItem {processed_item_id}] Starting execution on worker {worker_name}, queue {queue_name}")
    
    session = get_session()
    node_logs: Dict[str, List[str]] = {}
    log_handler = NodeLogHandler(node_logs)
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    previous_level = root_logger.level
    if previous_level > logging.INFO:
        root_logger.setLevel(logging.INFO)

    try:
        # Get ProcessedItem
        processed_item = session.get(ProcessedItem, processed_item_id)
        if not processed_item:
            raise ValueError(f"ProcessedItem {processed_item_id} not found")

        # Skip if this item has already been marked as finished/cancelled
        if processed_item.status != "pending":
            print(
                f"[ProcessedItem {processed_item_id}] Skipping execution because status is '{processed_item.status}'"
            )
            return {
                "status": "skipped",
                "processed_item_id": processed_item_id,
                "reason": f"Status is '{processed_item.status}'"
            }

        # Get the run and ensure it's still active
        run = session.get(Run, processed_item.run_id)
        if not run:
            raise ValueError(f"Run {processed_item.run_id} not found")

        if run.status not in ("pending", "running"):
            processed_item.status = "failed"
            processed_item.error = f"Run cancelled or completed (status={run.status})"
            processed_item.updated_at = datetime.utcnow()
            session.add(processed_item)
            session.commit()
            print(
                f"[ProcessedItem {processed_item_id}] Aborting because run status is '{run.status}'"
            )
            return {
                "status": "skipped",
                "processed_item_id": processed_item_id,
                "reason": f"Run status is '{run.status}'"
            }

        # Update status to running
        processed_item.status = "running"
        processed_item.updated_at = datetime.utcnow()
        session.add(processed_item)
        session.commit()

        from agate_db import Graph
        graph = session.get(Graph, run.graph_id)
        if not graph:
            raise ValueError(f"Graph {run.graph_id} not found")
        
        # Parse spec and input
        spec = GraphSpec.model_validate_json(graph.spec_json)
        input_data = json.loads(processed_item.input_json)
        
        print(f"[ProcessedItem {processed_item_id}] Loaded input_data: type={type(input_data)}, keys={list(input_data.keys()) if isinstance(input_data, dict) else 'not a dict'}")
        if isinstance(input_data, dict) and 'text' in input_data:
            print(f"[ProcessedItem {processed_item_id}] input_data has 'text' field: length={len(input_data['text']) if isinstance(input_data.get('text'), str) else 'not a string'}")
        
        print(f"[ProcessedItem {processed_item_id}] Processing graph: {spec.name}")
        if processed_item.source_file:
            print(f"[ProcessedItem {processed_item_id}] Source file: {processed_item.source_file}")
        
        # Build execution levels
        levels = build_execution_levels(spec.nodes, spec.edges)
        
        # Load project API keys and system prompt
        print(f"[ProcessedItem {processed_item_id}] Loading API keys for project {run.project_id}")
        try:
            api_keys = get_all_project_api_keys(session, run.project_id)
            print(f"[ProcessedItem {processed_item_id}] Loaded {len(api_keys)} API keys")
        except Exception as e:
            print(f"[ProcessedItem {processed_item_id}] Warning: Failed to load API keys: {str(e)}")
            api_keys = {}
        
        # Load project system prompt
        project = session.get(Project, run.project_id)
        project_system_prompt = project.system_prompt if project else None
        
        # Execute nodes level by level (parallel within each level)
        node_outputs = {}
        node_map = {node.id: node for node in spec.nodes}
        ctx = RunContext(
            run_id=str(processed_item.run_id),
            project_id=run.project_id, 
            api_keys=api_keys,
            project_system_prompt=project_system_prompt
        )
        
        # Add processed_item_id to context metadata for tracking
        ctx.set_metadata('processed_item_id', processed_item_id)
        
        # Add source_file to context metadata if available
        if processed_item.source_file:
            ctx.set_metadata('source_file', processed_item.source_file)

        for level_idx, level_node_ids in enumerate(levels):
            # Refresh run status to detect cancellation mid-flight
            session.refresh(run)
            if run.status not in ("pending", "running"):
                processed_item.status = "failed"
                processed_item.error = "Run cancelled during execution"
                processed_item.updated_at = datetime.utcnow()
                session.add(processed_item)
                session.commit()
                print(
                    f"[ProcessedItem {processed_item_id}] Stopping due to run status '{run.status}'"
                )
                return {
                    "status": "skipped",
                    "processed_item_id": processed_item_id,
                    "reason": "Run cancelled during execution"
                }
            
            print(f"[ProcessedItem {processed_item_id}] Level {level_idx}: Executing {len(level_node_ids)} node(s)")
            
            # Update current_node in database for running items
            if processed_item.status == "running":
                # Get node types for this level
                level_node_types = [node_map[nid].type for nid in level_node_ids if nid in node_map]
                if level_node_types:
                    # Update current_node field (if it exists) or store in a way we can retrieve
                    # For now, we'll store it in node_logs_json as metadata
                    try:
                        current_node_info = {
                            "level": level_idx,
                            "node_types": level_node_types,
                            "node_ids": level_node_ids
                        }
                        # Store as a special key in node_logs for easy retrieval
                        if not node_logs.get("_current"):
                            node_logs["_current"] = []
                        node_logs["_current"] = [json.dumps(current_node_info)]
                        # Update in database
                        processed_item.node_logs_json = json.dumps(node_logs)
                        session.add(processed_item)
                        session.commit()
                    except Exception as e:
                        print(f"[ProcessedItem {processed_item_id}] Warning: Failed to update current node info: {e}")
            
            # Prepare inputs for all nodes at this level
            level_configs = []
            level_inputs = {}
            
            for node_id in level_node_ids:
                node_config = node_map[node_id]

                # For DBInput, if input_data exists, it means this is a batch item created from articles array
                if node_config.type == "DBInput" and input_data:
                    from pydantic import BaseModel, ConfigDict

                    class InputPassthrough(BaseModel):
                        model_config = ConfigDict(extra='allow')

                    node_outputs[node_config.id] = InputPassthrough(**input_data)
                    print(f"[ProcessedItem {processed_item_id}] Skipped DBInput node, using ProcessedItem input data (batch item)")
                    continue

                # Build input from previous nodes or use ProcessedItem input for other input nodes
                if node_config.type in ["TextInput", "JSONInput"]:
                    node_input = input_data
                else:
                    # Map outputs from previous nodes
                    if node_config.type == "PlaceExtract":
                        print(f"[ProcessedItem {processed_item_id}] PlaceExtract: Before map_node_inputs, node_outputs keys: {list(node_outputs.keys())}")
                        print(f"[ProcessedItem {processed_item_id}] PlaceExtract: Edges: {[(e.source if hasattr(e, 'source') else e['source'], e.target if hasattr(e, 'target') else e['target']) for e in spec.edges if (e.target if hasattr(e, 'target') else e['target']) == node_config.id]}")
                    node_input = map_node_inputs(node_config.id, spec.edges, node_outputs, node_map, fallback_input=input_data)
                    if node_config.type == "PlaceExtract":
                        print(f"[ProcessedItem {processed_item_id}] PlaceExtract: After map_node_inputs, mapped input keys: {list(node_input.keys())}")
                        # If still empty and this is a batch item, fall back to the ProcessedItem input_data
                        if (not node_input or (isinstance(node_input, dict) and len(node_input) == 0)) and input_data:
                            node_input = input_data
                            print(f"[ProcessedItem {processed_item_id}] PlaceExtract: No mapped inputs; using ProcessedItem input_data keys: {list(input_data.keys()) if isinstance(input_data, dict) else 'not a dict'}")
                
                level_configs.append(node_config)
                level_inputs[node_config.id] = node_input
                
                # Log node input before execution
                input_dict = node_input.model_dump() if hasattr(node_input, 'model_dump') else node_input if isinstance(node_input, dict) else {}
                print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] EXECUTING with INPUT keys: {list(input_dict.keys()) if isinstance(input_dict, dict) else 'not a dict'}")
            
            # Execute all nodes at this level in parallel
            if level_configs:  # Only execute if there are nodes to execute
                try:
                    # Use timeout wrapper to allow Celery signals to interrupt
                    level_timeout = max(TASK_SOFT_TIME_LIMIT - 60, int(TASK_SOFT_TIME_LIMIT * 0.9))
                    level_outputs = execute_level_with_timeout(level_configs, level_inputs, ctx, timeout_seconds=level_timeout)
                except TimeoutError as e:
                    print(f"[ProcessedItem {processed_item_id}] Level {level_idx} timed out: {str(e)}")
                    raise
                
                # Store outputs and update current node info
                for node_config, output in zip(level_configs, level_outputs):
                    node_outputs[node_config.id] = output
                    
                    # Log node input and output for debugging
                    node_input = level_inputs.get(node_config.id, {})
                    input_dict = node_input.model_dump() if hasattr(node_input, 'model_dump') else node_input if isinstance(node_input, dict) else {}
                    output_dict = output.model_dump() if hasattr(output, 'model_dump') else output if isinstance(output, dict) else {}
                    
                    print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] INPUT keys: {list(input_dict.keys()) if isinstance(input_dict, dict) else 'not a dict'}")
                    print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] OUTPUT keys: {list(output_dict.keys()) if isinstance(output_dict, dict) else 'not a dict'}")
                    
                    # Special logging for JSONInput to check for text field
                    if node_config.type == "JSONInput":
                        if isinstance(output_dict, dict) and 'text' in output_dict:
                            print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] OUTPUT has 'text' field: length={len(output_dict['text']) if isinstance(output_dict.get('text'), str) else 'not a string'}")
                        else:
                            print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] OUTPUT does NOT have 'text' field!")
                    
                    # Special logging for PlaceExtract to check input sources
                    if node_config.type == "PlaceExtract":
                        if isinstance(input_dict, dict):
                            for input_key, input_value in input_dict.items():
                                if isinstance(input_value, dict):
                                    has_text = 'text' in input_value
                                    print(f"[ProcessedItem {processed_item_id}] [{node_config.type} {node_config.id}] INPUT[{input_key}] has 'text': {has_text}, keys: {list(input_value.keys())}")
                    
                    # Update current node info in node_logs for running items
                    if processed_item.status == "running":
                        try:
                            current_node_info = {
                                "level": level_idx,
                                "node_type": node_config.type,
                                "node_id": node_config.id
                            }
                            if not node_logs.get("_current"):
                                node_logs["_current"] = []
                            # Keep only the most recent node info
                            node_logs["_current"] = [json.dumps(current_node_info)]
                            # Also update in database periodically (every level)
                            processed_item.node_logs_json = json.dumps(node_logs)
                            session.add(processed_item)
                            session.commit()
                        except Exception as e:
                            print(f"[ProcessedItem {processed_item_id}] Warning: Failed to update current node info: {e}")
                    
                    # Special handling for DBInput: if it returns multiple articles, create ProcessedItems for each
                    if node_config.type == "DBInput" and level_idx == 0:
                        print(f"[ProcessedItem {processed_item_id}] Checking DBInput output for articles array (level {level_idx})")
                        output_dict = output.model_dump() if hasattr(output, 'model_dump') else output
                        print(f"[ProcessedItem {processed_item_id}] DBInput output keys: {list(output_dict.keys()) if isinstance(output_dict, dict) else 'not a dict'}")
                        articles = output_dict.get('articles') if isinstance(output_dict, dict) else None
                        print(f"[ProcessedItem {processed_item_id}] Articles found: {articles is not None}, type: {type(articles)}, length: {len(articles) if isinstance(articles, list) else 'N/A'}")
                        if articles and isinstance(articles, list) and len(articles) > 1:
                            print(f"[ProcessedItem {processed_item_id}] DBInput returned {len(articles)} articles. Creating ProcessedItems for articles 2-{len(articles)}")
                            
                            # Update current ProcessedItem's input_json to contain only the first article
                            # This ensures the current item processes the first article correctly
                            first_article = articles[0]
                            processed_item.input_json = json.dumps(first_article)
                            session.add(processed_item)
                            
                            # Create ProcessedItems for remaining articles (first one is processed in current item)
                            new_item_ids = []
                            for idx, article in enumerate(articles[1:], start=2):
                                # Create a new ProcessedItem with this article as input
                                new_item = ProcessedItem(
                                    run_id=run.id,
                                    input_json=json.dumps(article),
                                    status="pending",
                                    created_at=datetime.utcnow(),
                                    updated_at=datetime.utcnow()
                                )
                                session.add(new_item)
                                session.flush()  # Flush to get the ID
                                new_item_ids.append(new_item.id)
                                print(f"[ProcessedItem {processed_item_id}] Created ProcessedItem {new_item.id} for article {idx}/{len(articles)}")
                            
                            # Commit transaction BEFORE scheduling tasks to avoid race condition
                            session.commit()
                            # Refresh to ensure we have the latest state
                            session.refresh(processed_item)
                            print(f"[ProcessedItem {processed_item_id}] Created {len(articles) - 1} additional ProcessedItems for batch processing")
                            
                            # Schedule tasks AFTER commit to ensure ProcessedItems exist in database
                            # Use apply_async with countdown to give database time to make items visible across connections
                            # Route to queue based on item ID for round-robin distribution
                            NUM_QUEUES = int(os.getenv("CELERY_NUM_QUEUES", "4"))
                            for item_id in new_item_ids:
                                queue_index = item_id % NUM_QUEUES
                                queue = f"queue-{queue_index}"
                                execute_processed_item.apply_async(args=[item_id], queue=queue, countdown=0.5)
                                print(f"[ProcessedItem {processed_item_id}] Scheduled ProcessedItem {item_id} for execution (queue={queue}, 0.5s delay)")
        
        # Choose final output: first node of the last topological level
        final_output = None
        final_node_id = None
        candidate_final_node_id = levels[-1][0]
        if candidate_final_node_id in node_outputs:
            final_node_id = candidate_final_node_id
            final_output = node_outputs[final_node_id]

        # Fallback: if we have no final_output (e.g., parent skipped downstream nodes), return empty result
        if final_output is None:
            print(f"[ProcessedItem {processed_item_id}] No final output node found; using empty result to avoid failure")
            from pydantic import BaseModel
            class EmptyOutput(BaseModel):
                model_config = {"extra": "allow"}
            final_output = EmptyOutput()
        
        # Update ProcessedItem with success
        processed_item.status = "succeeded"
        processed_item.output_json = final_output.model_dump_json()
        processed_item.node_outputs_json = json.dumps({k: v.model_dump() for k, v in node_outputs.items()})
        processed_item.node_logs_json = json.dumps(node_logs)
        processed_item.updated_at = datetime.utcnow()
        session.add(processed_item)
        session.commit()

        print(f"[ProcessedItem {processed_item_id}] Completed successfully")
        
        return {
            "status": "succeeded",
            "processed_item_id": processed_item_id
        }
        
    except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
        # Handle timeout exceptions - mark as timed_out
        timeout_type = "soft" if isinstance(e, SoftTimeLimitExceeded) else "hard"
        print(f"[ProcessedItem {processed_item_id}] Task exceeded {timeout_type} time limit ({TASK_SOFT_TIME_LIMIT}s soft / {TASK_HARD_TIME_LIMIT}s hard)")
        
        # Update ProcessedItem with timeout status
        # Use a fresh session in case the current one is in a bad state
        try:
            timeout_session = get_session()
            processed_item = timeout_session.get(ProcessedItem, processed_item_id)
            if processed_item:
                processed_item.status = "timed_out"
                processed_item.error = f"Task exceeded {timeout_type} time limit ({TASK_SOFT_TIME_LIMIT}s soft / {TASK_HARD_TIME_LIMIT}s hard)"
                if node_logs:
                    processed_item.node_logs_json = json.dumps(node_logs)
                processed_item.updated_at = datetime.utcnow()
                timeout_session.add(processed_item)
                timeout_session.commit()
                print(f"[ProcessedItem {processed_item_id}] Marked as timed_out in database")
            timeout_session.close()
        except Exception as db_error:
            # If we can't update the database, log it but don't fail
            print(f"[ProcessedItem {processed_item_id}] Warning: Failed to update status to timed_out: {str(db_error)}")
        
        # Re-raise to let Celery handle it properly
        raise
        
    except TimeoutError as e:
        # Handle asyncio timeout errors from execute_level_with_timeout
        print(f"[ProcessedItem {processed_item_id}] Async operation timed out: {str(e)}")
        
        # Update ProcessedItem with timeout status
        try:
            timeout_session = get_session()
            processed_item = timeout_session.get(ProcessedItem, processed_item_id)
            if processed_item:
                processed_item.status = "timed_out"
                processed_item.error = f"Async operation timed out: {str(e)}"
                if node_logs:
                    processed_item.node_logs_json = json.dumps(node_logs)
                processed_item.updated_at = datetime.utcnow()
                timeout_session.add(processed_item)
                timeout_session.commit()
                print(f"[ProcessedItem {processed_item_id}] Marked as timed_out in database")
            timeout_session.close()
        except Exception as db_error:
            print(f"[ProcessedItem {processed_item_id}] Warning: Failed to update status to timed_out: {str(db_error)}")
        
        # Re-raise as a regular exception so it gets caught by the general exception handler
        raise Exception(f"Task timed out: {str(e)}")
        
    except Exception as e:
        print(f"[ProcessedItem {processed_item_id}] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update ProcessedItem with error
        processed_item = session.get(ProcessedItem, processed_item_id)
        if processed_item:
            if processed_item.status != "failed":
                processed_item.status = "failed"
            processed_item.error = str(e)
            processed_item.node_logs_json = json.dumps(node_logs)
            processed_item.updated_at = datetime.utcnow()
            session.add(processed_item)
            session.commit()
        
        return {
            "status": "failed",
            "processed_item_id": processed_item_id,
            "error": str(e)
        }
    
    finally:
        root_logger.removeHandler(log_handler)
        log_handler.close()
        root_logger.setLevel(previous_level)
        session.close()

