"""Type definitions for graphs and runs."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
from enum import Enum


class RunStatus(str, Enum):
    """Status of a run."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeConfig(BaseModel):
    """Configuration for a node in a graph."""
    id: str
    type: str
    params: Dict[str, Any] = {}
    position: Optional[Dict[str, float]] = None  # x, y coordinates for UI positioning


class Edge(BaseModel):
    """Edge connecting two nodes in a graph."""
    source: str  # source node id
    target: str  # target node id
    sourceHandle: Optional[str] = None  # output field name
    targetHandle: Optional[str] = None  # input field name


class GraphSpec(BaseModel):
    """Specification for a graph."""
    name: str
    nodes: List[NodeConfig]
    edges: Optional[List[Edge]] = None  # List of edges connecting nodes
    
    @field_validator('edges', mode='before')
    @classmethod
    def ensure_edges_list(cls, v):
        """Ensure edges is always a list (backward compatibility)."""
        if v is None:
            return []
        return v

