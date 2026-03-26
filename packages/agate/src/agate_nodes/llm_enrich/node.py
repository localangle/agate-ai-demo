"""LLMEnrich node for custom LLM-based enrichment with JSON output."""

import json
import re
from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field
from agate_core import NodeBase, RunContext, register
from agate_utils import call_llm


class LLMEnrichInput(BaseModel):
    """Input schema - expects to find text in namespaced state."""
    class Config:
        extra = "allow"  # Accept full state


class LLMEnrichOutput(BaseModel):
    """Output schema for LLMEnrich node."""
    class Config:
        extra = "allow"  # Allow additional fields


class LLMEnrichParams(BaseModel):
    """Parameters for LLMEnrich node."""
    model: str = Field(
        default="gpt-5.4-mini",
        description="LLM model to use (gpt-5.4-mini, gpt-5.4, or gpt-5.4-nano)"
    )
    prompt: str = Field(
        min_length=1,
        description="Prompt template with JSON path placeholders (e.g., {text}, {results.images}, {raw})"
    )
    json_format: str = Field(
        default="{}",
        description="Expected JSON output format as a string. This will be included in the prompt."
    )
    output_name: str = Field(
        default="meta_enriched_data",
        description="Name of the output field that will contain the LLM response data."
    )


@register("LLMEnrich")
class LLMEnrich(NodeBase[LLMEnrichInput, LLMEnrichOutput, LLMEnrichParams]):
    """
    Custom LLM enrichment node with JSON path templating.
    
    This node uses an LLM to process JSON data according to a custom prompt and returns
    structured JSON data. Supports flexible JSON path extraction using placeholders like
    {text}, {results.images}, {results.caption}, {results.caption, id}, and {raw}.
    """
    
    name = "LLMEnrich"
    version = "0.2.0"
    category = "enrichment"
    
    Input = LLMEnrichInput
    Output = LLMEnrichOutput
    Params = LLMEnrichParams
    
    def _extract_json_path(self, input_dict: Dict[str, Any], path_spec: str) -> Any:
        """
        Extract value from input_dict using JSON path notation.
        
        Args:
            input_dict: The input JSON structure
            path_spec: Path specification, can include:
                - Simple path: "text", "url"
                - Nested path: "results.images"
                - Array filtering: "results.caption" (extracts caption from array elements)
                - Multi-field filtering: "results.caption, id" (extracts multiple fields)
        
        Returns:
            Extracted value (can be any JSON type)
            
        Raises:
            ValueError: If path doesn't exist in input
        """
        # Check for multi-field specification (comma-separated)
        if ',' in path_spec:
            # This is a multi-field filter like "results.caption, id"
            # Split by comma and parse each field
            fields = [f.strip() for f in path_spec.split(',')]
            # The first field contains the path to the array, remaining are additional fields
            base_path = fields[0]
            additional_fields = fields[1:]
            
            # Parse the base path to get the array and the first field
            if '.' in base_path:
                # Split into path parts
                parts = base_path.split('.')
                # Navigate to parent (everything except last part)
                current = input_dict
                for part in parts[:-1]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        raise ValueError(f"Path '{'.'.join(parts[:-1])}' not found in input")
                
                # Last part is the field to extract
                first_field = parts[-1]
                
                # If current is an array, filter each element
                if isinstance(current, list):
                    all_fields = [first_field] + additional_fields
                    filtered = []
                    for item in current:
                        if isinstance(item, dict):
                            filtered_item = {field: item.get(field) for field in all_fields if field in item}
                            filtered.append(filtered_item)
                    return filtered
                else:
                    # Not an array, just extract the fields from the object
                    all_fields = [first_field] + additional_fields
                    if isinstance(current, dict):
                        return {field: current.get(field) for field in all_fields if field in current}
                    else:
                        raise ValueError(f"Cannot extract fields from non-object: {type(current)}")
            else:
                # No dot notation, treat as root-level multi-field extraction
                all_fields = [base_path] + additional_fields
                return {field: input_dict.get(field) for field in all_fields if field in input_dict}
        
        # Single path (no commas)
        if '.' not in path_spec:
            # Simple top-level field
            if path_spec not in input_dict:
                raise ValueError(f"Field '{path_spec}' not found in input")
            return input_dict[path_spec]
        
        # Nested path with dot notation
        parts = path_spec.split('.')
        current = input_dict
        
        # Navigate through all parts except the last
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"Path '{'.'.join(parts[:i+1])}' not found in input")
        
        # Handle the last part
        last_part = parts[-1]
        
        # If current is an array, we're trying to access a field of array elements
        if isinstance(current, list):
            # Filter array to only include the specified field from each element
            filtered = []
            for item in current:
                if isinstance(item, dict) and last_part in item:
                    filtered.append({last_part: item[last_part]})
            return filtered
        elif isinstance(current, dict):
            # Regular object access
            if last_part not in current:
                raise ValueError(f"Field '{path_spec}' not found in input")
            return current[last_part]
        else:
            raise ValueError(f"Cannot access field '{last_part}' of {type(current)}")
    
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
    
    def _build_prompt(self, input_dict: Dict[str, Any], prompt_template: str, json_format: str) -> str:
        """
        Build the complete prompt by replacing JSON path placeholders.
        Automatically sanitizes custom_geographies to remove geometry data.
        
        Args:
            input_dict: Full input JSON structure
            prompt_template: Template with {path} placeholders
            json_format: Expected output format
            
        Returns:
            Complete prompt with all placeholders replaced
            
        Raises:
            ValueError: If any JSON path doesn't exist in input
        """
        # Find all {placeholder} patterns
        placeholders = re.findall(r'\{([^}]+)\}', prompt_template)
        
        prompt = prompt_template
        for placeholder in placeholders:
            placeholder_key = placeholder.strip()
            
            try:
                # Handle special {raw} keyword
                if placeholder_key == 'raw':
                    value = input_dict
                else:
                    # Extract using JSON path
                    value = self._extract_json_path(input_dict, placeholder_key)
                
                # Sanitize geometry data before serializing
                sanitized_value = self._sanitize_for_prompt(value)
                
                # Serialize value as JSON string (pretty-printed)
                if isinstance(sanitized_value, (dict, list)):
                    serialized = json.dumps(sanitized_value, indent=2)
                elif isinstance(sanitized_value, str):
                    # Keep strings as-is (don't double-quote)
                    serialized = sanitized_value
                else:
                    # Numbers, booleans, etc.
                    serialized = json.dumps(sanitized_value)
                
                # Replace the placeholder
                prompt = prompt.replace(f'{{{placeholder}}}', serialized)
                
            except Exception as e:
                # Re-raise with more context
                raise ValueError(
                    f"Failed to extract JSON path '{placeholder_key}': {str(e)}\n"
                    f"Available top-level keys in input: {list(input_dict.keys())}"
                ) from e
        
        # Add JSON format instruction
        full_prompt = f"""{prompt}

Please respond with ONLY a valid, complete JSON object or array that matches this structure:
{json_format}

IMPORTANT: Your response must be valid JSON that can be parsed by json.loads(). 
- If showing an object property, wrap it in braces: {{"key": value}}
- Do not include any text before or after the JSON
- Do not include markdown code blocks or formatting"""
        
        return full_prompt
    
    async def run(
        self,
        inp: LLMEnrichInput,
        params: LLMEnrichParams,
        ctx: RunContext
    ) -> LLMEnrichOutput:
        """
        Execute LLM enrichment using JSON path templating.
        
        Args:
            inp: Input with full state (all fields from previous nodes)
            params: Parameters including model, prompt template, and JSON format
            ctx: Runtime context
            
        Returns:
            Output with enriched JSON data and preserved input fields
        """
        # Get full input as dictionary
        input_dict = inp.model_dump()
        
        # Flatten namespaced input structure into a single dict
        # This merges all fields from namespaced nodes (e.g., "node-0": {...}) into one flat structure
        flattened_input = {}
        for key, value in input_dict.items():
            if isinstance(value, dict):
                # If this is a namespaced node output, merge its fields
                flattened_input.update(value)
            else:
                flattened_input[key] = value
        
        # Build the complete prompt using JSON path extraction on flattened input
        prompt = self._build_prompt(flattened_input, params.prompt, params.json_format)
        
        # Call LLM with API keys from context
        response = call_llm(
            prompt=prompt,
            model=params.model,
            force_json=True,
            openai_api_key=ctx.get_api_key("OPENAI_API_KEY"),
            project_system_prompt=ctx.project_system_prompt
        )
        
        # Parse JSON response
        try:
            enriched_data = json.loads(response)
        except json.JSONDecodeError as e:
            # Try to fix common issues before giving up
            cleaned_response = response.strip()
            
            # Fix malformed numbers: extract numeric part from patterns like "0. nine"
            # Replace "number. word" with just the number part (defaulting to 0.0 if invalid)
            pattern = r'(\d+\.)\s+([a-zA-Z]+)'
            def fix_number(match):
                # Just extract the numeric part, discard the word
                return match.group(1) + '0'
            cleaned_response = re.sub(pattern, fix_number, cleaned_response, flags=re.IGNORECASE)
            
            # Try parsing again with cleaned response
            try:
                enriched_data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # If still fails, try wrapping in braces if it looks like a property fragment
                if cleaned_response.startswith('"') and '":' in cleaned_response[:50]:
                    try:
                        enriched_data = json.loads(f"{{{cleaned_response}}}")
                    except json.JSONDecodeError:
                        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
                else:
                    raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
        
        # Validate that response is a dictionary or list
        if not isinstance(enriched_data, (dict, list)):
            raise ValueError(f"LLM response must be a JSON object or array, got: {type(enriched_data)}")
        
        # Normalize numeric values: if it's a valid number, keep it; otherwise set to 0.0
        def normalize_numeric_values(obj: Any) -> Any:
            """Recursively normalize values - if numeric field is not a number, set to 0.0."""
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    # Check if field name suggests it should be numeric
                    is_numeric_field = (
                        isinstance(key, str) and 
                        any(suffix in key.lower() for suffix in ['_confidence', '_count', '_score', '_rate', '_ratio', '_percent', '_index'])
                    )
                    
                    if is_numeric_field:
                        # Simple check: if it's a valid float/int, keep it; otherwise set to 0.0
                        if isinstance(value, (int, float)):
                            result[key] = float(value)
                        else:
                            result[key] = 0.0
                    else:
                        # Recursively process non-numeric fields
                        result[key] = normalize_numeric_values(value)
                return result
            elif isinstance(obj, list):
                return [normalize_numeric_values(item) for item in obj]
            else:
                return obj
        
        enriched_data = normalize_numeric_values(enriched_data)
        
        # Create output with custom field name and all preserved fields
        output_data = {
            params.output_name: enriched_data,
            **flattened_input  # Preserve all input fields
        }
        
        return LLMEnrichOutput(**output_data)
