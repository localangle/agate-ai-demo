"""Shared types for the geocoding agent."""

from typing import TypedDict, Optional, Any
from agate_utils.geocoding.geocoding_types import GeocodingResult


class AgentState(TypedDict, total=False):
    """State for the geocoding agent."""
    location_text: str
    location_type: str
    location_components: dict
    original_text: str
    extra_fields: dict  # Additional fields from PlaceExtract (like 'mural', 'description', etc.)
    geocoding_result: Optional[GeocodingResult]
    geocoding_model: Optional[Any]  # The model instance used for geocoding
    geocoding_failure_reason: Optional[str]  # Reason for geocoding failure (e.g., "not addressable", "non-point geometry")
    openai_api_key: Optional[str]
    final_output: Optional[dict]
