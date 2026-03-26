"""Output node for consolidating results from multiple upstream nodes."""

from typing import Dict, Any, List, Optional
from collections import OrderedDict
from pydantic import BaseModel, ConfigDict
from agate_core import NodeBase, RunContext, register

# Preferred key order - these keys will always appear first in the output
PREFERRED_KEY_ORDER = [
    "publication",
    "headline",
    "url",
    "author",
    "pub_date",
    "updated",
    "text",
    "images",
]


class OutputInput(BaseModel):
    """
    Input accepts any fields from upstream nodes.
    This allows dynamic merging of different node outputs.
    """
    model_config = ConfigDict(extra='allow')


class OutputOutput(BaseModel):
    """Output schema - passes through the consolidated state."""
    model_config = ConfigDict(extra='allow')


class OutputParams(BaseModel):
    """Parameters for Output node."""
    exclude: Optional[List[str]] = None
    """List of keys to exclude from the output. If provided, these keys will be filtered out."""
    
    include: Optional[List[str]] = None
    """List of keys to include in the output (whitelist). If provided, only these keys will be included."""


@register("Output")
class Output(NodeBase[OutputInput, OutputOutput, OutputParams]):
    """
    Output node that consolidates results from multiple upstream nodes.
    
    This node accepts any input fields and returns them as a single
    consolidated data structure. Perfect for merging results from
    parallel enrich nodes.
    """
    
    name = "Output"
    version = "0.1.0"
    category = "output"
    
    Input = OutputInput
    Output = OutputOutput
    Params = OutputParams
    
    def _unwrap_node_data(self, data: Dict[str, Any], target: Dict[str, Any]) -> None:
        """
        Recursively unwrap namespaced node-X data structures.
        
        Args:
            data: Dictionary to process (may contain node-X keys)
            target: Dictionary to merge unwrapped data into
        """
        for key, value in data.items():
            # Check if this is a namespaced node key (node-X format)
            is_node_key = key.startswith("node-") and len(key) > 5 and key[5:].isdigit()
            
            if is_node_key:
                # Recursively unwrap nested node-X structures
                if isinstance(value, dict):
                    self._unwrap_node_data(value, target)
                else:
                    # Non-dict value in node-X key, preserve it
                    target[key] = value
            else:
                # Non-node-X key - merge into target (later values override earlier ones)
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    # Both are dicts - recursively merge
                    self._unwrap_node_data(value, target[key])
                else:
                    # Direct assignment (will override if key exists)
                    target[key] = value
    
    def _apply_filters(self, data: Dict[str, Any], params: OutputParams) -> Dict[str, Any]:
        """
        Apply include/exclude filters to the data.
        
        Args:
            data: Dictionary to filter
            params: Output parameters with exclude/include lists
            
        Returns:
            Filtered dictionary
        """
        exclude_set = set(params.exclude) if params.exclude else set()
        include_set = set(params.include) if params.include else None
        
        filtered = {}
        for key, value in data.items():
            # Apply exclude filter
            if key in exclude_set:
                continue
            
            # Apply include filter (whitelist)
            if include_set is not None and key not in include_set:
                continue
            
            filtered[key] = value
        
        return filtered
    
    def _reorder_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reorder dictionary keys to put preferred keys first.
        
        Args:
            data: Dictionary to reorder
            
        Returns:
            Dictionary with preferred keys first, followed by all other keys
        """
        ordered = OrderedDict()
        
        # First, add preferred keys in order (if they exist)
        for key in PREFERRED_KEY_ORDER:
            if key in data:
                ordered[key] = data[key]
        
        # Then, add all other keys in their original order
        for key, value in data.items():
            if key not in ordered:
                ordered[key] = value
        
        return dict(ordered)
    
    async def run(
        self,
        inp: OutputInput,
        params: OutputParams,
        ctx: RunContext
    ) -> OutputOutput:
        """
        Consolidate state from all upstream nodes, excluding intermediate node outputs.
        
        Args:
            inp: Input with deep-merged flat state (or namespaced upstream outputs)
            params: Parameters including optional exclude/include filters
            ctx: Runtime context
            
        Returns:
            Output with only final consolidated data (no intermediate node outputs)
        """
        input_dict = inp.model_dump()
        filtered_data = {}
        
        # Recursively unwrap all node-X structures
        self._unwrap_node_data(input_dict, filtered_data)
        
        # Apply include/exclude filters
        if params.exclude or params.include:
            filtered_data = self._apply_filters(filtered_data, params)
        
        # Reorder keys to put preferred keys first
        filtered_data = self._reorder_keys(filtered_data)
        
        return OutputOutput(**filtered_data)
