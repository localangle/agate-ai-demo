"""JSONInput node for providing JSON data with required text field."""

from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator
from agate_core import NodeBase, RunContext, register


class JSONInputInput(BaseModel):
    """Input schema - no input needed for input nodes."""
    pass


class JSONInputParams(BaseModel):
    """Parameters for JSONInput node - accepts any JSON with required text field."""
    class Config:
        extra = "allow"  # Allow any additional fields
    
    text: str = Field(
        min_length=1,
        description="Required text field for downstream processing"
    )


class JSONInputOutput(BaseModel):
    """Output schema - passes through text and all additional fields."""
    class Config:
        extra = "allow"  # Allow all fields to pass through
    
    text: str = Field(description="Text for downstream processing")


@register("JSONInput")
class JSONInput(NodeBase[JSONInputInput, JSONInputOutput, JSONInputParams]):
    """
    JSON input node that provides structured data to the flow.
    
    This node requires a 'text' field for downstream text processing, but also
    accepts any additional JSON attributes that will be passed along to downstream
    nodes. This is useful for providing context, metadata, or additional structured
    data alongside the text.
    
    Example:
    {
        "text": "Article content here...",
        "title": "Article Title",
        "author": "John Doe",
        "published_date": "2025-10-21",
        "tags": ["politics", "economy"]
    }
    """
    
    name = "JSONInput"
    version = "0.1.0"
    category = "input"
    
    Input = JSONInputInput
    Output = JSONInputOutput
    Params = JSONInputParams
    
    async def run(
        self,
        inp: JSONInputInput,
        params: JSONInputParams,
        ctx: RunContext
    ) -> JSONInputOutput:
        """
        Output the JSON data with required text field.
        
        Args:
            inp: Empty input (input nodes don't receive data)
            params: JSON data with required text field and optional additional fields
            ctx: Runtime context
            
        Returns:
            Output containing text and all additional fields from params
        """
        # Validate that text is non-empty
        if not params.text or not params.text.strip():
            raise ValueError("JSONInput node requires non-empty text field.")
        
        # Convert params to dict to get all fields (including extras)
        params_dict = params.model_dump()
        
        print(f"[JSONInput] Text length: {len(params.text)} characters")
        print(f"[JSONInput] Additional fields: {[k for k in params_dict.keys() if k != 'text']}")
        
        # Return all params as output
        return JSONInputOutput(**params_dict)

