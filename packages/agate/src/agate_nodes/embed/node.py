"""Embed node for creating text embeddings using OpenAI."""

import os
from typing import List
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from openai import OpenAI


class EmbedInput(BaseModel):
    """Input schema - expects to find a node with 'text' field in state."""
    class Config:
        extra = "allow"  # Accept full state


class EmbedOutput(BaseModel):
    """Output schema for Embed node."""
    model_config = ConfigDict(extra='allow')
    
    # No top-level fields - embedding data is nested under the dynamic output_name field


class EmbedParams(BaseModel):
    """Parameters for Embed node."""
    model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use (must be text-embedding-3-small)"
    )
    dimensions: int = Field(
        default=1536,
        description="Embedding dimensions (model-dependent)"
    )
    output_name: str = Field(
        default="text_embedding",
        description="Name of the output field that will contain the embedding results"
    )


@register("Embed")
class Embed(NodeBase[EmbedInput, EmbedOutput, EmbedParams]):
    """
    Create text embeddings using OpenAI's embedding models.
    
    This node converts text into a vector representation that can be used
    for semantic search, similarity comparison, and other ML tasks.
    """
    
    name = "Embed"
    version = "0.1.0"
    category = "enrichment"
    
    Input = EmbedInput
    Output = EmbedOutput
    Params = EmbedParams
    
    def _get_client(self, api_key: str) -> OpenAI:
        """Get OpenAI client with provided API key."""
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        return OpenAI(api_key=api_key)
    
    async def run(
        self,
        inp: EmbedInput,
        params: EmbedParams,
        ctx: RunContext
    ) -> EmbedOutput:
        """
        Execute embedding - extract text from any upstream node.
        
        Args:
            inp: Input with namespaced state
            params: Parameters including model and dimensions
            ctx: Runtime context
            
        Returns:
            Output with embedding vector and metadata
        """
        # Find text in the state (look through all namespaced nodes)
        input_dict = inp.model_dump()
        text = None
        
        # Search through namespaced state for 'text' field
        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict) and 'text' in node_data:
                text = node_data['text']
                break
        
        if not text:
            raise ValueError("No 'text' field found in input state")
        
        # Get OpenAI API key from context
        openai_api_key = ctx.get_api_key("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in project API keys")
        
        client = self._get_client(openai_api_key)

        if params.model != "text-embedding-3-small":
            raise ValueError(
                "Embed node only supports text-embedding-3-small for this app."
            )
        
        # Create embedding
        response = client.embeddings.create(
            input=text,
            model=params.model,
            dimensions=params.dimensions,
        )
        
        # Extract embedding vector
        embedding = response.data[0].embedding
        
        # Create embedding result object
        embedding_result = {
            "text": text,  # Preserve original text
            "embedding": embedding,
            "embedding_model": params.model,
            "embedding_dimensions": len(embedding)
        }
        
        # Create output with dynamic field name for embedding result
        output_data = {
            params.output_name: embedding_result
        }
        
        # Preserve any additional fields from input state (like locations from PlaceExtract node)
        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict):
                for key, value in node_data.items():
                    if key not in ["text", params.output_name]:  # Don't override the text field or output_name
                        output_data[key] = value
        
        return EmbedOutput(**output_data)
