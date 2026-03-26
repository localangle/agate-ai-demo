"""Base class for all nodes in the Agate AI Platform."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar
from pydantic import BaseModel

I = TypeVar("I", bound=BaseModel)
O = TypeVar("O", bound=BaseModel)
P = TypeVar("P", bound=BaseModel)


class NodeBase(ABC, Generic[I, O, P]):
    """
    Abstract base class for all nodes.
    
    Each node must define three Pydantic models:
    - Input: Schema for input data
    - Output: Schema for output data
    - Params: Schema for node parameters
    
    Each node must also define a category:
    - input: Nodes that provide initial data
    - enrichment: Nodes that add data to existing input
    - extraction: Nodes that extract specific information
    - output: Nodes that consolidate and return final results
    
    Example:
        @register("MyNode")
        class MyNode(NodeBase[MyInput, MyOutput, MyParams]):
            name = "MyNode"
            version = "0.1.0"
            category = "enrichment"
            
            async def run(self, inp: MyInput, params: MyParams, ctx: RunContext) -> MyOutput:
                # Node logic here
                return MyOutput(result=...)
    """
    
    name: str
    version: str = "0.1.0"
    category: str  # Must be: "input", "enrichment", "extraction", or "output"
    
    # These will be set by subclasses
    Input: Type[I]
    Output: Type[O]
    Params: Type[P]
    
    @abstractmethod
    async def run(self, inp: I, params: P, ctx: "RunContext") -> O:
        """
        Execute the node logic.
        
        Args:
            inp: Validated input data
            params: Node parameters
            ctx: Runtime context with run_id, secrets, etc.
            
        Returns:
            Output data that will be validated against the Output schema
        """
        pass

