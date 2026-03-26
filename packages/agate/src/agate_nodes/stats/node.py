"""StatsNode for calculating text statistics."""

import re
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register


class StatsInput(BaseModel):
    """Input schema - expects to find text in namespaced state."""
    class Config:
        extra = "allow"  # Accept full state


class StatsOutput(BaseModel):
    """Output schema for StatsNode."""
    model_config = ConfigDict(extra='allow')
    
    # meta_stats will be included dynamically


class StatsParams(BaseModel):
    """Parameters for StatsNode."""
    enabled_stats: List[str] = Field(
        default=["word_count"],
        description="List of stat names to calculate (e.g., ['word_count'])"
    )


@register("StatsNode")
class StatsNode(NodeBase[StatsInput, StatsOutput, StatsParams]):
    """
    Calculate text statistics and output as meta_stats JSON object.
    
    This node processes text and calculates various statistics based on
    the selected stat types. Each stat is implemented as a separate function
    for easy extensibility.
    """
    
    name = "StatsNode"
    version = "0.1.0"
    category = "text"
    
    Input = StatsInput
    Output = StatsOutput
    Params = StatsParams
    
    def _calculate_word_count(self, text: str) -> int:
        """Count words in text."""
        if not text or not text.strip():
            return 0
        # Split by whitespace and filter out empty strings
        words = [w for w in text.split() if w.strip()]
        return len(words)
    
    def _calculate_character_count(self, text: str) -> int:
        """Count characters in text (including spaces)."""
        return len(text) if text else 0
    
    def _calculate_character_count_no_spaces(self, text: str) -> int:
        """Count characters in text excluding spaces."""
        if not text:
            return 0
        return len(text.replace(" ", ""))
    
    def _calculate_sentence_count(self, text: str) -> int:
        """Count sentences in text."""
        if not text or not text.strip():
            return 0
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text.strip())
        # Filter out empty strings
        sentences = [s for s in sentences if s.strip()]
        return len(sentences) if sentences else 0
    
    def _calculate_paragraph_count(self, text: str) -> int:
        """Count paragraphs in text."""
        if not text or not text.strip():
            return 0
        # Split by double newlines or single newlines with whitespace
        paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
        return len(paragraphs) if paragraphs else 0

    WORDS_PER_MINUTE = 250

    def _calculate_reading_time_minutes(self, text: str) -> float:
        """Estimate reading time in minutes at 250 words per minute."""
        word_count = self._calculate_word_count(text)
        if word_count == 0:
            return 0.0
        return round(word_count / self.WORDS_PER_MINUTE, 2)

    # Registry mapping stat names to calculation functions
    STAT_REGISTRY: Dict[str, Any] = {
        "word_count": lambda self, text: self._calculate_word_count(text),
        "character_count": lambda self, text: self._calculate_character_count(text),
        "character_count_no_spaces": lambda self, text: self._calculate_character_count_no_spaces(text),
        "sentence_count": lambda self, text: self._calculate_sentence_count(text),
        "paragraph_count": lambda self, text: self._calculate_paragraph_count(text),
        "reading_time_minutes": lambda self, text: self._calculate_reading_time_minutes(text),
    }
    
    async def run(
        self,
        inp: StatsInput,
        params: StatsParams,
        ctx: RunContext
    ) -> StatsOutput:
        """
        Calculate selected statistics for the input text.
        
        Args:
            inp: Input with namespaced state containing text
            params: Parameters including enabled_stats list
            ctx: Runtime context
            
        Returns:
            Output with meta_stats object containing calculated statistics
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
        
        # Calculate selected stats
        meta_stats = {}
        
        for stat_name in params.enabled_stats:
            if stat_name in self.STAT_REGISTRY:
                try:
                    stat_value = self.STAT_REGISTRY[stat_name](self, text)
                    meta_stats[stat_name] = stat_value
                except Exception as e:
                    print(f"[StatsNode] Error calculating {stat_name}: {e}")
                    # Continue with other stats even if one fails
            else:
                print(f"[StatsNode] Warning: Unknown stat '{stat_name}', skipping")
        
        # Flatten input to preserve all fields
        flattened_input = {}
        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict):
                for key, value in node_data.items():
                    if key not in ["text", "meta_stats"]:  # Don't override text or meta_stats
                        flattened_input[key] = value
        
        # Create output with meta_stats and all preserved fields
        output_data = {
            "meta_stats": meta_stats,
            **flattened_input  # Preserve all input fields
        }
        
        # Preserve text field
        if text:
            output_data["text"] = text
        
        return StatsOutput(**output_data)
