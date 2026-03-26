"""TextInput node for providing text to downstream nodes."""

from pydantic import BaseModel, Field
from agate_core import NodeBase, RunContext, register


class TextInputInput(BaseModel):
    """Input schema - accepts full state but requires no specific fields."""
    class Config:
        extra = "allow"


class TextInputOutput(BaseModel):
    """Output the text."""
    text: str = Field(description="The input text")


class TextInputParams(BaseModel):
    """Parameters for TextInput node."""
    text: str = Field(default="", min_length=1, description="The text to output")


@register("TextInput")
class TextInput(NodeBase[TextInputInput, TextInputOutput, TextInputParams]):
    """
    Input node that provides text to downstream nodes.
    This is always the first node in a graph.
    """
    
    name = "TextInput"
    version = "0.1.0"
    category = "input"
    
    Input = TextInputInput
    Output = TextInputOutput
    Params = TextInputParams
    
    async def run(
        self,
        inp: TextInputInput,
        params: TextInputParams,
        ctx: RunContext
    ) -> TextInputOutput:
        """Execute the text input node."""
        if not params.text or not params.text.strip():
            raise ValueError("TextInput node requires non-empty text. Please add text to the TextInput node before running the flow.")
        return TextInputOutput(text=params.text)
