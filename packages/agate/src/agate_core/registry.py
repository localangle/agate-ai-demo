"""Node registry for discovering and instantiating nodes."""

from typing import Dict, Type, List, Callable
from .node_base import NodeBase

# Global registry of node types
_REGISTRY: Dict[str, Type[NodeBase]] = {}


def register(name: str) -> Callable:
    """
    Decorator to register a node type.
    
    Example:
        @register("ClassifyArticle")
        class ClassifyArticle(NodeBase[...]):
            pass
    
    Args:
        name: Unique name for the node type
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[NodeBase]) -> Type[NodeBase]:
        if name in _REGISTRY:
            raise ValueError(f"Node '{name}' is already registered")
        _REGISTRY[name] = cls
        cls.name = name  # Set the name on the class
        return cls
    return decorator


def get(name: str) -> Type[NodeBase]:
    """
    Get a node class by name.
    
    Args:
        name: Node type name
        
    Returns:
        Node class
        
    Raises:
        KeyError: If node type is not registered
    """
    if name not in _REGISTRY:
        raise KeyError(f"Node type '{name}' not found in registry. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]


def list_nodes() -> List[str]:
    """
    List all registered node types.
    
    Returns:
        List of node type names
    """
    return list(_REGISTRY.keys())

