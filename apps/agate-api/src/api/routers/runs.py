"""Run execution endpoints."""

import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from sqlalchemy import case
from pydantic import BaseModel
from datetime import datetime
from agate_db import Graph, Run, ProcessedItem, get_session_generator as get_session
from api.queue import celery_app, get_queue_for_item
import os

router = APIRouter(prefix="/runs", tags=["runs"])


def calculate_run_status(pending: int, running: int, succeeded: int, failed: int) -> str:
    """Calculate run status from ProcessedItem counts."""
    if pending > 0 or running > 0:
        if succeeded > 0 or failed > 0:
            return "running"  # Some items done, some still processing
        return "pending"  # All items still waiting
    # All items are done (succeeded or failed)
    if failed > 0:
        return "completed_with_errors"
    return "completed"


class RunCreate(BaseModel):
    """Request to create a run."""
    input: Dict[str, Any]


class ProcessedItemSummary(BaseModel):
    """Minimal processed item summary for run detail pages."""
    id: int
    run_id: int
    source_file: Optional[str] = None
    status: str
    error: Optional[str] = None
    created_at: str
    updated_at: str
    # Minimal output info - only s3_bucket and s3_key for download links
    output_s3_bucket: Optional[str] = None
    output_s3_key: Optional[str] = None
    # Input preview for DB Input items
    input_article_id: Optional[int] = None
    input_headline: Optional[str] = None
    # Current node info for running items
    current_node_types: Optional[List[str]] = None
    # Flag to indicate if item was created by ArraySplitter
    is_array_splitter_item: bool = False


class ProcessedItemResponse(BaseModel):
    """Full processed item response with all JSON data."""
    id: int
    run_id: int
    source_file: Optional[str] = None
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    node_outputs: Optional[Dict[str, Any]] = None
    node_logs: Optional[Dict[str, List[str]]] = None
    status: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


class RunResponse(BaseModel):
    """Run response with aggregated ProcessedItem stats."""
    id: int
    graph_id: int
    project_id: int
    status: str  # pending, running, completed, completed_with_errors
    created_at: str
    updated_at: str
    # Aggregated stats from ProcessedItems
    total_items: int = 0
    pending_items: int = 0
    running_items: int = 0
    succeeded_items: int = 0
    failed_items: int = 0
    # Optional: include minimal item summaries for list view (not full JSON data)
    items: Optional[List[ProcessedItemSummary]] = None


def handle_s3_input_run(
    _run: Run,
    _graph_spec: Dict[str, Any],
    _session: Session,
    *,
    folder_override: Optional[str] = None,
    bucket_override: Optional[str] = None,
) -> List[ProcessedItem]:
    """S3Input/APIInput multi-file runs are not supported in this demo (nodes removed)."""
    return []


def _create_run_for_graph(
    session: Session,
    graph: Graph,
    run_create: RunCreate,
) -> RunResponse:
    graph_spec = json.loads(graph.spec_json)

    run = Run(
        graph_id=graph.id,
        project_id=graph.project_id,
        status="pending"
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    has_s3_input = any(n['type'] == 'S3Input' for n in graph_spec['nodes'])

    if has_s3_input:
        processed_items = handle_s3_input_run(
            run,
            graph_spec,
            session,
            folder_override=(
                run_create.input.get("folder_path_override")
                or run_create.input.get("object_key")
                or run_create.input.get("folder_path")
            ),
        )
        total_items = len(processed_items)
    else:
        processed_item = ProcessedItem(
            run_id=run.id,
            source_file=None,
            input_json=json.dumps(run_create.input),
            status="pending"
        )
        session.add(processed_item)
        session.commit()
        session.refresh(processed_item)

        # Route to queue based on item ID for round-robin distribution
        queue = get_queue_for_item(processed_item.id)
        print(f"[API] Enqueueing task for ProcessedItem {processed_item.id} to queue {queue}")
        result = celery_app.send_task(
            "worker.tasks.execute_processed_item",
            args=[processed_item.id],
            queue=queue
        )
        print(f"[API] Task enqueued: task_id={result.id}, queue={queue}, item_id={processed_item.id}")

        total_items = 1

    return RunResponse(
        id=run.id,
        graph_id=run.graph_id,
        project_id=run.project_id,
        status=run.status,
        created_at=run.created_at.isoformat(),
        updated_at=run.updated_at.isoformat(),
        total_items=total_items,
        pending_items=total_items,
        running_items=0,
        succeeded_items=0,
        failed_items=0,
    )


@router.post("/{graph_id}", response_model=RunResponse)
def create_run(
    graph_id: int,
    run_create: RunCreate,
    session: Session = Depends(get_session),
):
    """Create and execute a new run with ProcessedItem(s)."""
    graph = session.get(Graph, graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    return _create_run_for_graph(session, graph, run_create)


@router.get("", response_model=List[RunResponse])
def list_runs(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """List runs with aggregated ProcessedItem stats (demo: no access control).

    Args:
        limit: Maximum number of runs to return (default: 50)
        offset: Number of runs to skip (default: 0)
    """
    base_query = select(Run).order_by(Run.created_at.desc())

    # Apply pagination
    paginated_query = base_query.limit(limit).offset(offset)
    runs = session.exec(paginated_query).all()
    
    if not runs:
        return []
    
    # Get all run IDs
    run_ids = [run.id for run in runs]
    
    # Optimize: Use a single query with GROUP BY to get aggregated stats for all runs
    # This avoids N+1 query problem
    stats_query = (
        select(
            ProcessedItem.run_id,
            func.count(ProcessedItem.id).label('total'),
            func.sum(case((ProcessedItem.status == 'pending', 1), else_=0)).label('pending'),
            func.sum(case((ProcessedItem.status == 'running', 1), else_=0)).label('running'),
            func.sum(case((ProcessedItem.status == 'succeeded', 1), else_=0)).label('succeeded'),
            # Count both 'failed' and 'timed_out' as failed for run status calculation
            func.sum(case(((ProcessedItem.status == 'failed') | (ProcessedItem.status == 'timed_out'), 1), else_=0)).label('failed'),
        )
        .where(ProcessedItem.run_id.in_(run_ids))
        .group_by(ProcessedItem.run_id)
    )
    
    # Execute the aggregated query
    stats_results = session.exec(stats_query).all()
    
    # Create a dictionary mapping run_id to stats
    stats_by_run_id = {
        row.run_id: {
            'total': row.total or 0,
            'pending': row.pending or 0,
            'running': row.running or 0,
            'succeeded': row.succeeded or 0,
            'failed': row.failed or 0,
        }
        for row in stats_results
    }
    
    # Batch status updates
    runs_to_update = []
    result = []
    
    for run in runs:
        # Get stats for this run (default to 0 if no items)
        stats = stats_by_run_id.get(run.id, {
            'total': 0,
            'pending': 0,
            'running': 0,
            'succeeded': 0,
            'failed': 0,
        })
        
        # Calculate and update run status
        new_status = calculate_run_status(
            stats['pending'],
            stats['running'],
            stats['succeeded'],
            stats['failed']
        )
        if run.status != new_status:
            run.status = new_status
            run.updated_at = datetime.utcnow()
            runs_to_update.append(run)

        result.append(RunResponse(
            id=run.id,
            graph_id=run.graph_id,
            project_id=run.project_id,
            status=run.status,
            created_at=run.created_at.isoformat(),
            updated_at=run.updated_at.isoformat(),
            total_items=stats['total'],
            pending_items=stats['pending'],
            running_items=stats['running'],
            succeeded_items=stats['succeeded'],
            failed_items=stats['failed'],
        ))
    
    # Batch commit all status updates at once
    if runs_to_update:
        for run in runs_to_update:
            session.add(run)
        session.commit()
    
    return result


@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    run_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific run with all ProcessedItems."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Get all ProcessedItems for this run
    items = session.exec(
        select(ProcessedItem).where(ProcessedItem.run_id == run_id)
    ).all()
    
    # Aggregate stats
    total = len(items)
    pending = sum(1 for item in items if item.status == 'pending')
    running = sum(1 for item in items if item.status == 'running')
    succeeded = sum(1 for item in items if item.status == 'succeeded')
    # Count both 'failed' and 'timed_out' as failed for run status calculation
    failed = sum(1 for item in items if item.status == 'failed' or item.status == 'timed_out')
    
    # Calculate and update run status
    new_status = calculate_run_status(pending, running, succeeded, failed)
    if run.status != new_status:
        run.status = new_status
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()
    
    # Convert items to minimal summary format (no JSON parsing to save memory)
    item_summaries = []
    for item in items:
        # Extract minimal S3 info from output_json without full parsing
        output_s3_bucket = None
        output_s3_key = None
        if item.output_json:
            try:
                # Quick parse just to get s3_bucket and s3_key
                output_data = json.loads(item.output_json)
                output_s3_bucket = output_data.get('s3_bucket')
                output_s3_key = output_data.get('s3_key')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Extract input preview for DB Input items (article_id and headline)
        input_article_id = None
        input_headline = None
        if not item.source_file and item.input_json:
            try:
                input_data = json.loads(item.input_json)
                # Check if this looks like article data from DB Input
                if isinstance(input_data, dict):
                    input_article_id = input_data.get('article_id')
                    input_headline = input_data.get('headline')
                    # If article_id is a string, try to convert to int
                    if isinstance(input_article_id, str):
                        try:
                            input_article_id = int(input_article_id)
                        except (ValueError, TypeError):
                            input_article_id = None
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        
        # Extract current node info from node_logs_json for running items
        current_node_types = None
        if item.status == 'running' and item.node_logs_json:
            try:
                node_logs = json.loads(item.node_logs_json)
                if isinstance(node_logs, dict) and '_current' in node_logs:
                    current_info_str = node_logs['_current'][0] if isinstance(node_logs['_current'], list) and len(node_logs['_current']) > 0 else None
                    if current_info_str:
                        current_info = json.loads(current_info_str)
                        current_node_types = current_info.get('node_types', [])
            except (json.JSONDecodeError, AttributeError, KeyError):
                pass
        
        # Check if this item was created by ArraySplitter by checking Redis batches
        is_array_splitter_item = False
        if not item.source_file:  # Only check for items without source_file
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                redis_client = redis.from_url(redis_url)
                batch_keys = redis_client.keys("array_batch:*")
                for batch_key in batch_keys:
                    batch_key_str = batch_key.decode() if isinstance(batch_key, bytes) else batch_key
                    if ":completed" in batch_key_str:
                        continue
                    batch_data_str = redis_client.get(batch_key)
                    if batch_data_str:
                        batch_data = json.loads(batch_data_str)
                        item_ids = [int(id) for id in batch_data.get("item_ids", [])]
                        if item.id in item_ids:
                            is_array_splitter_item = True
                            break
            except Exception:
                # Continue if Redis check fails
                pass
        
        item_summaries.append(ProcessedItemSummary(
            id=item.id,
            run_id=item.run_id,
            source_file=item.source_file,
            status=item.status,
            error=item.error,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            output_s3_bucket=output_s3_bucket,
            output_s3_key=output_s3_key,
            input_article_id=input_article_id,
            input_headline=input_headline,
            current_node_types=current_node_types,
            is_array_splitter_item=is_array_splitter_item
        ))
    
    return RunResponse(
        id=run.id,
        graph_id=run.graph_id,
        project_id=run.project_id,
        status=run.status,
        created_at=run.created_at.isoformat(),
        updated_at=run.updated_at.isoformat(),
        total_items=total,
        pending_items=pending,
        running_items=running,
        succeeded_items=succeeded,
        failed_items=failed,
        items=item_summaries,
    )


class RerunItemResponse(BaseModel):
    """Response when rerunning a processed item in place."""
    item_id: int
    run_id: int
    status: str
    message: str


@router.post("/{run_id}/items/{item_id}/rerun", response_model=RerunItemResponse)
def rerun_processed_item(
    run_id: int,
    item_id: int,
    session: Session = Depends(get_session),
):
    """Rerun a single processed item in place within its existing run.

    Resets the item status to pending, clears output/errors, and re-enqueues for processing.
    """
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Ensure the run is marked active again so workers can process items
    if run.status != "running":
        run.status = "running"
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()
        session.refresh(run)

    # Load the processed item
    item = session.get(ProcessedItem, item_id)
    if not item or item.run_id != run_id:
        raise HTTPException(status_code=404, detail="Processed item not found for this run")

    # Reset the item to pending state
    item.status = "pending"
    item.output_json = None
    item.node_outputs_json = None
    item.node_logs_json = None
    item.error = None
    item.updated_at = datetime.utcnow()
    
    session.add(item)
    session.commit()
    session.refresh(item)

    # Re-enqueue the task
    # Route to queue based on item ID for round-robin distribution
    queue = get_queue_for_item(item.id)
    print(f"[API] Enqueueing rerun task for ProcessedItem {item.id} to queue {queue}")
    result = celery_app.send_task(
        "worker.tasks.execute_processed_item",
        args=[item.id],
        queue=queue
    )
    print(f"[API] Rerun task enqueued: task_id={result.id}, queue={queue}, item_id={item.id}, run_id={run_id}")

    return RerunItemResponse(
        item_id=item.id,
        run_id=run.id,
        status=item.status,
        message=f"Item #{item.id} reset to pending and re-queued for processing"
    )


@router.get("/{run_id}/items/{item_id}", response_model=ProcessedItemResponse)
def get_processed_item(
    run_id: int,
    item_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific processed item with full JSON data."""
    item = session.get(ProcessedItem, item_id)
    if not item or item.run_id != run_id:
        raise HTTPException(status_code=404, detail="Processed item not found")

    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Parse JSON fields (only when explicitly requested)
    return ProcessedItemResponse(
        id=item.id,
        run_id=item.run_id,
        source_file=item.source_file,
        input=json.loads(item.input_json),
        output=json.loads(item.output_json) if item.output_json else None,
        node_outputs=json.loads(item.node_outputs_json) if item.node_outputs_json else None,
        node_logs=json.loads(item.node_logs_json) if item.node_logs_json else None,
        status=item.status,
        error=item.error,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat()
    )


@router.post("/{run_id}/cancel", response_model=RunResponse)
def cancel_run(
    run_id: int,
    session: Session = Depends(get_session),
):
    """Cancel a running or pending run.

    This marks all pending items as failed and attempts to revoke running tasks.
    """
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Only allow cancelling if run is pending or running
    if run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel run with status '{run.status}'. Only pending or running runs can be cancelled."
        )
    
    # Get all items for this run
    items = session.exec(
        select(ProcessedItem).where(ProcessedItem.run_id == run_id)
    ).all()
    
    cancelled_count = 0
    
    # Collect batch IDs from ArraySplitter items to clean up Redis keys
    batch_ids_to_cleanup = set()
    
    for item in items:
        if item.status == "pending":
            # Mark pending items as failed with cancellation message
            item.status = "failed"
            item.error = "Run cancelled by user"
            item.updated_at = datetime.utcnow()
            session.add(item)
            cancelled_count += 1
        elif item.status == "running":
            # For running items, we can't easily stop them mid-execution
            # but we can mark them for cancellation
            # Note: Celery task revocation would require task IDs which we don't store
            # For now, just mark them as failed
            item.status = "failed"
            item.error = "Run cancelled by user (was running)"
            item.updated_at = datetime.utcnow()
            session.add(item)
            cancelled_count += 1
    
    # Update run status
    run.status = "completed_with_errors"  # Cancelled runs are "completed with errors"
    run.updated_at = datetime.utcnow()
    session.add(run)
    
    session.commit()
    session.refresh(run)
    
    # Clean up Redis batch keys for this run
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        
        # Find all batch keys for this run
        batch_keys = redis_client.keys("array_batch:*")
        for batch_key in batch_keys:
            batch_key_str = batch_key.decode() if isinstance(batch_key, bytes) else batch_key
            if ":completed" in batch_key_str:
                continue
            
            batch_data_str = redis_client.get(batch_key)
            if batch_data_str:
                try:
                    batch_data = json.loads(batch_data_str)
                    if batch_data.get("run_id") == run_id:
                        batch_id = batch_data.get("batch_id")
                        if batch_id:
                            # Delete batch key and completed key
                            redis_client.delete(batch_key_str)
                            completed_key = f"array_batch:{batch_id}:completed"
                            redis_client.delete(completed_key)
                            print(f"[API] Cleaned up Redis batch keys for batch {batch_id} (run {run_id})")
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
    except Exception as e:
        print(f"[API] Warning: Failed to clean up Redis batch keys for run {run_id}: {e}")
    
    # Get updated stats
    items = session.exec(
        select(ProcessedItem).where(ProcessedItem.run_id == run_id)
    ).all()
    
    total = len(items)
    pending = sum(1 for item in items if item.status == 'pending')
    running = sum(1 for item in items if item.status == 'running')
    succeeded = sum(1 for item in items if item.status == 'succeeded')
    failed = sum(1 for item in items if item.status == 'failed')
    
    # Create minimal summaries (no JSON parsing)
    item_summaries = []
    for item in items:
        output_s3_bucket = None
        output_s3_key = None
        if item.output_json:
            try:
                output_data = json.loads(item.output_json)
                output_s3_bucket = output_data.get('s3_bucket')
                output_s3_key = output_data.get('s3_key')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Extract input preview for DB Input items (article_id and headline)
        input_article_id = None
        input_headline = None
        if not item.source_file and item.input_json:
            try:
                input_data = json.loads(item.input_json)
                # Check if this looks like article data from DB Input
                if isinstance(input_data, dict):
                    input_article_id = input_data.get('article_id')
                    input_headline = input_data.get('headline')
                    # If article_id is a string, try to convert to int
                    if isinstance(input_article_id, str):
                        try:
                            input_article_id = int(input_article_id)
                        except (ValueError, TypeError):
                            input_article_id = None
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        
        # Check if this item was created by ArraySplitter by checking Redis batches
        is_array_splitter_item = False
        if not item.source_file:  # Only check for items without source_file
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                redis_client = redis.from_url(redis_url)
                batch_keys = redis_client.keys("array_batch:*")
                for batch_key in batch_keys:
                    batch_key_str = batch_key.decode() if isinstance(batch_key, bytes) else batch_key
                    if ":completed" in batch_key_str:
                        continue
                    batch_data_str = redis_client.get(batch_key)
                    if batch_data_str:
                        batch_data = json.loads(batch_data_str)
                        item_ids = [int(id) for id in batch_data.get("item_ids", [])]
                        if item.id in item_ids:
                            is_array_splitter_item = True
                            break
            except Exception:
                # Continue if Redis check fails
                pass
        
        item_summaries.append(ProcessedItemSummary(
            id=item.id,
            run_id=item.run_id,
            source_file=item.source_file,
            status=item.status,
            error=item.error,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            output_s3_bucket=output_s3_bucket,
            output_s3_key=output_s3_key,
            input_article_id=input_article_id,
            input_headline=input_headline,
            is_array_splitter_item=is_array_splitter_item
        ))
    
    print(f"[API] Cancelled run {run_id}: {cancelled_count} items cancelled")
    
    return RunResponse(
        id=run.id,
        graph_id=run.graph_id,
        project_id=run.project_id,
        status=run.status,
        created_at=run.created_at.isoformat(),
        updated_at=run.updated_at.isoformat(),
        total_items=total,
        pending_items=pending,
        running_items=running,
        succeeded_items=succeeded,
        failed_items=failed,
        items=item_summaries,
    )

