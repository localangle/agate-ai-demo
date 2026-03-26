"""PlaceFilter node for filtering locations from PlaceExtract based on LLM relevance judgments.

Description:
This node uses an LLM to process JSON data according to your custom prompt and returns structured JSON data.
Use JSON path placeholders in your prompt to extract specific fields:
  {text} - extracts the text field
  {url} - extracts the url field
  {results.images} - extracts nested results.images object/array
  {results.caption} - extracts only caption field from array elements
  {results.caption, id} - extracts multiple fields from array elements
  {raw} - passes entire input JSON
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from agate_utils.llm import call_llm
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

class PlaceFilterInput(BaseModel):
    """Input schema - expects to find locations in namespaced state."""
    model_config = ConfigDict(extra='allow')


class PlaceFilterParams(BaseModel):
    """Parameters for PlaceFilter node."""
    model: str = Field(
        default="gpt-5.4-mini",
        description="LLM model to use (gpt-5.4-mini, gpt-5.4, or gpt-5.4-nano)"
    )
    prompt_file: str = Field(
        default="prompts/filter.md",
        description="Path to the prompt file relative to the node directory. Defaults to prompts/filter.md"
    )
    output_format_file: str = Field(
        default="prompts/_filter_output.md",
        description="Path to the output format file relative to the node directory. Defaults to prompts/_filter_output.md"
    )
    prompt: str = Field(
        default="",
        description="Custom prompt override. If provided, this takes precedence over prompt_file."
    )
    json_format: str = Field(
        default='[{"index":0,"relevant":true,"reason":""}]',
        description="Example output JSON format. Braces will be escaped automatically in the prompt."
    )


class StateInfo(BaseModel):
    """State information."""
    name: str = Field(description="Full name of the state")
    abbr: str = Field(description="Postal abbreviation for the state")


class CountryInfo(BaseModel):
    """Country information."""
    name: str = Field(description="Full name of the country")
    abbr: str = Field(description="ISO 3166-1 country code")


class PlaceInfo(BaseModel):
    """Place information for named places."""
    name: str = Field(description="Name of the place")
    addressable: bool = Field(default=False, description="Whether the place has a findable street address")
    natural: bool = Field(default=False, description="Whether the place represents a natural location")


class StreetRoadInfo(BaseModel):
    """Street/road information."""
    name: str = Field(description="Name of the street")
    boundary: str = Field(default="", description="Geocodable boundary containing the street")


class SpanEndpoint(BaseModel):
    """Endpoint for a roadway span."""
    type: str = Field(description="Endpoint type (city or intersection)")
    location: str = Field(description="Geocodable representation of the endpoint")


class SpanInfo(BaseModel):
    """Span information for roadway sections."""
    start: Optional[SpanEndpoint] = Field(default=None, description="Starting endpoint")
    end: Optional[SpanEndpoint] = Field(default=None, description="Ending endpoint")


class LocationComponents(BaseModel):
    """Components of a location."""
    place: Optional[PlaceInfo] = Field(default=None, description="Place information if applicable")
    street_road: Optional[StreetRoadInfo] = Field(default=None, description="Street/road information if applicable")
    span: Optional[SpanInfo] = Field(default=None, description="Span information if applicable")
    address: Optional[str] = Field(default="", description="Street address if applicable")
    neighborhood: Optional[str] = Field(default="", description="Neighborhood name if applicable")
    city: Optional[str] = Field(default="", description="City name if applicable")
    county: Optional[str] = Field(default="", description="County name if applicable")
    state: Optional[StateInfo] = Field(default=None, description="State information if applicable")
    country: Optional[CountryInfo] = Field(default=None, description="Country information if applicable")


class LocationInfo(BaseModel):
    """Location information."""
    full: str = Field(description="The full geocodable location string")
    type: str = Field(description="The type of location (e.g., city, address, intersection_road)")
    components: LocationComponents = Field(description="Detailed components of the location")


class Place(BaseModel):
    """A place extracted from text."""
    original_text: str = Field(description="The original text from which this location was extracted")
    description: str = Field(description="Brief description of the location and its relevance")
    location: LocationInfo = Field(description="Location information with components")


class PlaceFilterOutput(BaseModel):
    """Output schema - returns filtered places and preserves input state."""
    model_config = ConfigDict(extra='allow')
    
    text: str = Field(description="Original input text")
    locations: List[Place] = Field(description="List of filtered locations")


@register("PlaceFilter")
class PlaceFilter(NodeBase[PlaceFilterInput, PlaceFilterOutput, PlaceFilterParams]):
    """Node for filtering locations from PlaceExtract based on LLM relevance judgments."""
    
    name = "PlaceFilter"
    version = "0.1.0"
    category = "filter"
    
    Input = PlaceFilterInput
    Output = PlaceFilterOutput
    Params = PlaceFilterParams
    
    def _extract_json_path(self, input_dict: Dict[str, Any], path_spec: str) -> Any:
        """
        Extract value from input_dict using JSON path notation (similar to LLMEnrich).
        Supports:
        - Simple path: "text", "locations"
        - Nested path: "results.images"
        - Multi-field (comma-separated): "results.caption, id"
        - {raw}: returns full input_dict
        """
        if path_spec == "raw":
            return input_dict
        
        if ',' in path_spec:
            fields = [f.strip() for f in path_spec.split(',')]
            base_path = fields[0]
            additional_fields = fields[1:]
            target = self._extract_json_path(input_dict, base_path)
            all_fields = [base_path.split('.')[-1]] + additional_fields
            
            def pick_fields(obj):
                if isinstance(obj, dict):
                    return {f: obj.get(f) for f in all_fields if f in obj}
                return obj
            
            if isinstance(target, list):
                return [pick_fields(item) for item in target if isinstance(item, dict)]
            return pick_fields(target)
        
        parts = path_spec.split('.')
        current: Union[Dict[str, Any], List[Any], Any] = input_dict
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                extracted = []
                for item in current:
                    if isinstance(item, dict) and part in item:
                        extracted.append(item[part])
                current = extracted
            else:
                raise ValueError(f"Path '{'.'.join(parts[:i+1])}' not found in input")
        return current
    
    def _sanitize_for_prompt(self, value: Any) -> Any:
        """
        Remove geometry data from custom_geographies to avoid huge token costs.
        Preserves essential fields like id, label, type, city, state, etc.
        """
        if isinstance(value, dict):
            # If this is a custom geography entry, strip geometry fields
            if "geocode" in value and isinstance(value["geocode"], dict):
                result = value["geocode"].get("result", {})
                if isinstance(result, dict):
                    # Remove geometry but keep other fields
                    sanitized_result = {k: v for k, v in result.items() if k not in ["geometry", "boundaries"]}
                    sanitized_geocode = {**value["geocode"], "result": sanitized_result}
                    return {**value, "geocode": sanitized_geocode}
            # Recursively sanitize nested dicts
            return {k: self._sanitize_for_prompt(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._sanitize_for_prompt(item) for item in value]
        return value
    
    def _build_prompt(self, input_dict: Dict[str, Any], prompt_template: str) -> str:
        """
        Replace {json_path} placeholders in prompt_template using the provided input_dict.
        Skips escaped braces ({{ and }}) to avoid treating them as placeholders.
        Automatically sanitizes custom_geographies to remove geometry data.
        """
        # Temporarily replace escaped braces with markers to avoid matching them
        # Use unique markers that won't appear in the actual content
        ESCAPED_OPEN = "___ESCAPED_OPEN_BRACE___"
        ESCAPED_CLOSE = "___ESCAPED_CLOSE_BRACE___"
        
        # Replace {{ with marker
        temp_template = prompt_template.replace("{{", ESCAPED_OPEN)
        temp_template = temp_template.replace("}}", ESCAPED_CLOSE)
        
        # Now find placeholders (these will only match unescaped braces)
        placeholders = re.findall(r'\{([^}]+)\}', temp_template)
        prompt = temp_template
        
        for placeholder in placeholders:
            placeholder_key = placeholder.strip()
            try:
                value = self._extract_json_path(input_dict, placeholder_key)
                # Sanitize geometry data before serializing
                sanitized_value = self._sanitize_for_prompt(value)
                if isinstance(sanitized_value, (dict, list)):
                    serialized = json.dumps(sanitized_value, indent=2)
                elif isinstance(sanitized_value, str):
                    serialized = sanitized_value
                else:
                    serialized = json.dumps(sanitized_value)
                prompt = prompt.replace(f'{{{placeholder}}}', serialized)
            except Exception as e:
                raise ValueError(
                    f"Failed to extract JSON path '{placeholder_key}': {str(e)}\n"
                    f"Available top-level keys in input: {list(input_dict.keys())}"
                ) from e
        
        # Restore escaped braces
        prompt = prompt.replace(ESCAPED_OPEN, "{{")
        prompt = prompt.replace(ESCAPED_CLOSE, "}}")
        
        return prompt
    
    def _escape_braces(self, s: str) -> str:
        """Escape braces so they are not treated as placeholders."""
        return s.replace("{", "{{").replace("}", "}}")
    
    async def run(
        self,
        inp: PlaceFilterInput,
        params: PlaceFilterParams,
        ctx: RunContext
    ) -> PlaceFilterOutput:
        """
        Execute place filtering - filter locations from namespaced state.
        """
        input_dict = inp.model_dump()
        
        # Flatten namespaced input to make JSON paths easier (similar to LLMEnrich)
        flattened_input: Dict[str, Any] = {}
        for key, value in input_dict.items():
            if isinstance(value, dict):
                flattened_input.update(value)
            else:
                flattened_input[key] = value
        
        text = flattened_input.get("text")
        locations = flattened_input.get("locations")
        
        # Backward compatibility: search namespaced entries
        if text is None or locations is None:
            for node_id, node_data in input_dict.items():
                if isinstance(node_data, dict):
                    if text is None and 'text' in node_data:
                        text = node_data['text']
                    if locations is None and 'locations' in node_data:
                        locations = node_data['locations']
        
        if not text:
            raise ValueError("No 'text' field found in input state")
        
        # Handle missing or empty locations gracefully - just return empty list
        if not locations:
            return PlaceFilterOutput(
                text=text,
                locations=[]
            )
        
        if not isinstance(locations, list):
            raise ValueError("Locations field must be a list")
        
        if len(locations) == 0:
            # No locations to filter, return empty result
            return PlaceFilterOutput(
                text=text,
                locations=[]
            )
        
        # Add locations into flattened_input so placeholders can reference them
        flattened_input["locations"] = locations
        
        # Use custom prompt if provided, otherwise load from prompt_file
        if params.prompt and params.prompt.strip():
            prompt_template = params.prompt
        else:
            prompt_template = self._load_prompt_template(params.prompt_file)
        
        # Load output format and append to prompt (always append, even for custom prompts)
        try:
            if params.json_format:
                output_format = params.json_format
            else:
                output_format = self._load_prompt_template(params.output_format_file)
            # Escape braces to avoid placeholder parsing
            escaped_format = self._escape_braces(output_format)
            full_prompt_template = prompt_template + "\n\n" + escaped_format
        except (FileNotFoundError, Exception) as e:
            # If output format file can't be loaded, just use the prompt template
            logger.warning(f"Failed to load output format file: {e}. Using prompt without output format.")
            full_prompt_template = prompt_template
        
        # Build prompt using JSON path placeholders
        prompt = self._build_prompt(flattened_input, full_prompt_template)
        
        # Log the prompt for debugging
        logger.info(f"[PlaceFilter] Prompt:\n{prompt}")
        
        # Log the prompt being submitted to LLM
        logger.info(f"PlaceFilter LLM Prompt (node: {self.name}):\n{prompt}")
        
        # Call the LLM with API keys from context
        response_text = call_llm(
            prompt=prompt,
            model=params.model,
            system_message="You are a specialized AI assistant for filtering place information. Return only valid JSON.",
            force_json=True,
            temperature=0.0,
            openai_api_key=ctx.get_api_key("OPENAI_API_KEY"),
            project_system_prompt=ctx.project_system_prompt
        )
        
        # Parse the response
        try:
            judgments = json.loads(response_text)
            
            if not isinstance(judgments, list):
                raise ValueError("Expected a list of judgments")
            
            # Validate judgments format
            for i, judgment in enumerate(judgments):
                if not isinstance(judgment, dict):
                    raise ValueError(f"Judgment {i} must be a dictionary")
                if 'index' not in judgment or 'relevant' not in judgment:
                    raise ValueError(f"Judgment {i} must have 'index' and 'relevant' fields")
                if not isinstance(judgment['index'], int):
                    raise ValueError(f"Judgment {i} index must be an integer")
                if not isinstance(judgment['relevant'], bool):
                    raise ValueError(f"Judgment {i} relevant must be a boolean")
            
            # Filter locations based on judgments
            filtered_locations = []
            for judgment in judgments:
                if judgment['relevant'] and 0 <= judgment['index'] < len(locations):
                    # Convert dict to Place object - handle new format
                    location_data = locations[judgment['index']]
                    
                    # Convert location data to Place object
                    place = self._convert_place(location_data)
                    filtered_locations.append(place)
            
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse LLM response as judgment data: {e}")
        
        # Create output with filtering results
        output_data = {
            "text": text,
            "locations": [location.model_dump() for location in filtered_locations]
        }
        
        # Preserve any additional fields from input state (like embedding from Embed node)
        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict):
                for key, value in node_data.items():
                    if key not in ["text", "locations"]:  # Don't override the text and locations fields
                        output_data[key] = value
        
        return PlaceFilterOutput(**output_data)
    
    def _convert_place(self, location_data: dict) -> Place:
        """Convert location data to Place object."""
        # Handle different formats: location as string (new format) or as object (old format)
        if 'location' in location_data and isinstance(location_data['location'], str):
            # New format: location is a string, type and components are at top level
            location_str = location_data['location']
            location_type = location_data.get('type', 'other')
            components_data = location_data.get('components')
        elif 'location' in location_data and isinstance(location_data['location'], dict):
            # Old format: location is already an object
            location_obj = location_data['location']
            location_str = location_obj.get('full', '')
            location_type = location_obj.get('type', 'other')
            components_data = location_obj.get('components')
        else:
            # Legacy format: minimal data
            location_str = location_data.get('location', '')
            location_type = location_data.get('type', 'other')
            components_data = None
        
        # Ensure components_data is always a dict
        if components_data is None:
            components_data = {}
        
        place_info: Optional[PlaceInfo] = None
        street_info: Optional[StreetRoadInfo] = None
        span_info: Optional[SpanInfo] = None
        state_info: Optional[StateInfo] = None
        country_info: Optional[CountryInfo] = None

        place_data = components_data.get('place')
        if isinstance(place_data, dict) and place_data.get('name') and place_data.get('name').strip():
            place_info = PlaceInfo(
                name=place_data['name'],
                addressable=place_data.get('addressable', False),
                natural=place_data.get('natural', False)
            )

        street_data = components_data.get('street_road')
        if isinstance(street_data, dict) and street_data.get('name') and street_data.get('name').strip():
            street_info = StreetRoadInfo(
                name=street_data['name'],
                boundary=street_data.get('boundary', "")
            )

        span_data = components_data.get('span')
        if isinstance(span_data, dict):
            start_data = span_data.get('start')
            end_data = span_data.get('end')
            start = None
            end = None
            if isinstance(start_data, dict) and start_data.get('type') and start_data.get('location'):
                start = SpanEndpoint(type=start_data['type'], location=start_data['location'])
            if isinstance(end_data, dict) and end_data.get('type') and end_data.get('location'):
                end = SpanEndpoint(type=end_data['type'], location=end_data['location'])
            if start or end:
                span_info = SpanInfo(start=start, end=end)

        state_data = components_data.get('state')
        if isinstance(state_data, dict) and state_data.get('name') and state_data.get('name').strip():
            state_info = StateInfo(
                name=state_data['name'],
                abbr=state_data['abbr']
            )

        country_data = components_data.get('country')
        if isinstance(country_data, dict) and country_data.get('name') and country_data.get('name').strip():
            country_info = CountryInfo(
                name=country_data['name'],
                abbr=country_data['abbr']
            )
        
        components = LocationComponents(
            place=place_info,
            street_road=street_info,
            span=span_info,
            address=components_data.get('address', ''),
            neighborhood=components_data.get('neighborhood', ''),
            city=components_data.get('city', ''),
            county=components_data.get('county', ''),
            state=state_info,
            country=country_info
        )
        
        # Create location info
        location_info = LocationInfo(
            full=location_str,
            type=location_type,
            components=components
        )
        
        # Create place
        return Place(
            original_text=location_data.get('original_text', ''),
            description=location_data.get('description', ''),
            location=location_info
        )
    
    def _load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from the specified file path."""
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Resolve the prompt file path relative to the node directory
        if os.path.isabs(prompt_file_path):
            prompt_file = prompt_file_path
        else:
            prompt_file = os.path.join(current_dir, prompt_file_path)
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template not found at {prompt_file}")
        except Exception as e:
            raise Exception(f"Failed to load prompt template: {e}")
