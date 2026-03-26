"""ImageEnrich node for generating structured metadata for images using LLM vision models."""

import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from agate_utils.llm import call_llm_with_image


class ImageEnrichInput(BaseModel):
    """Input schema - expects to find image objects in namespaced state."""
    model_config = ConfigDict(extra='allow')  # Accept full state


class ImageEnrichParams(BaseModel):
    """Parameters for ImageEnrich node."""
    prompt: str = Field(
        default="Analyze this image and extract structured metadata. Focus on visual elements, composition, subjects, and any relevant details.",
        description="Prompt template for image analysis. Use JSON path placeholders like {caption} or {text} to include context."
    )
    llm_model: str = Field(
        default="gpt-5.4-mini",
        description="Vision model to use (gpt-5.4-mini, gpt-5.4, or gpt-5.4-nano)"
    )
    json_format: str = Field(
        default="{}",
        description="Expected JSON output format as a string. This will be included in the prompt."
    )
    output_name: str = Field(
        default="image_metadata",
        description="Name of the output field that will contain the metadata (will be prefixed with 'meta_')"
    )


class ImageEnrichOutput(BaseModel):
    """Output schema for ImageEnrich node."""
    model_config = ConfigDict(extra='allow')  # Allow dynamic output field name


@register("ImageEnrich")
class ImageEnrich(NodeBase[ImageEnrichInput, ImageEnrichOutput, ImageEnrichParams]):
    """
    ImageEnrich node for generating structured metadata for images using LLM vision models.
    
    This node takes image objects (single or array), uses LLM vision models to analyze them,
    and returns structured JSON metadata for each image. Similar to LLMEnrich but specifically
    designed for image analysis.
    """
    
    name = "ImageEnrich"
    version = "0.1.0"
    category = "enrichment"
    
    Input = ImageEnrichInput
    Output = ImageEnrichOutput
    Params = ImageEnrichParams
    
    def _is_valid_image_object(self, obj: Any) -> bool:
        """
        Check if an object is a valid image object (dict with url or base64).
        
        Args:
            obj: Object to check
            
        Returns:
            True if object is a valid image dict
        """
        return isinstance(obj, dict) and ("url" in obj or "base64" in obj)
    
    def _get_image_key(self, image_obj: Dict[str, Any]) -> str:
        """
        Generate a unique key for an image object to use for deduplication.
        
        Args:
            image_obj: Image object
            
        Returns:
            Unique key (id, url, base64 hash, or combination)
        """
        # Prefer ID if available
        if "id" in image_obj and image_obj["id"]:
            return f"id:{image_obj['id']}"
        
        # Use URL if available
        if "url" in image_obj and image_obj["url"]:
            return f"url:{image_obj['url']}"
        
        # Use base64 hash (first 50 chars) if available
        if "base64" in image_obj and image_obj["base64"]:
            base64_str = str(image_obj["base64"])
            return f"base64:{base64_str[:50]}"
        
        # Fallback: use string representation (shouldn't happen for valid images)
        return f"fallback:{str(image_obj)}"
    
    def _extract_images_recursive(self, obj: Any, images: List[Dict[str, Any]], seen_keys: set) -> None:
        """
        Recursively search for image objects in nested structures with deduplication.
        
        Args:
            obj: Object to search (dict, list, or other)
            images: List to append found images to
            seen_keys: Set of image keys already seen (for deduplication)
        """
        if isinstance(obj, dict):
            # Check if this dict has "image" or "images" keys
            if "image" in obj:
                image_data = obj["image"]
                if isinstance(image_data, list):
                    # Filter to only valid image objects
                    for item in image_data:
                        if self._is_valid_image_object(item):
                            img_key = self._get_image_key(item)
                            if img_key not in seen_keys:
                                seen_keys.add(img_key)
                                images.append(item)
                elif self._is_valid_image_object(image_data):
                    img_key = self._get_image_key(image_data)
                    if img_key not in seen_keys:
                        seen_keys.add(img_key)
                        images.append(image_data)
            
            if "images" in obj:
                images_data = obj["images"]
                if isinstance(images_data, list):
                    # Filter to only valid image objects (skip strings, IDs, etc.)
                    for item in images_data:
                        if self._is_valid_image_object(item):
                            img_key = self._get_image_key(item)
                            if img_key not in seen_keys:
                                seen_keys.add(img_key)
                                images.append(item)
                elif self._is_valid_image_object(images_data):
                    img_key = self._get_image_key(images_data)
                    if img_key not in seen_keys:
                        seen_keys.add(img_key)
                        images.append(images_data)
            
            # Check if this dict itself is an image object (but not if it already has image/images keys)
            if ("url" in obj or "base64" in obj) and "image" not in obj and "images" not in obj:
                img_key = self._get_image_key(obj)
                if img_key not in seen_keys:
                    seen_keys.add(img_key)
                    images.append(obj)
                    # Stop recursing - this is itself an image object
                    return
            
            # Recursively search through all values in the dict
            for value in obj.values():
                self._extract_images_recursive(value, images, seen_keys)
        
        elif isinstance(obj, list):
            # Recursively search through all items in the list
            for item in obj:
                self._extract_images_recursive(item, images, seen_keys)
    
    def _normalize_images(self, input_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize image objects from input with deduplication.
        
        Handles:
        - Single image object: {"image": {...}} or {"images": {...}}
        - Array of images: {"image": [{...}, {...}]} or {"images": [{...}, {...}]}
        - Direct object: {"url": "...", "base64": "..."}
        - Namespaced state: {"node-X": {"image": {...}}} or {"node-X": {"images": [...]}}
        - Nested structures: {"node-X": {"node-Y": {"images": [...]}}}
        
        Returns:
            List of unique image objects (deduplicated by id, url, or base64)
        """
        images = []
        seen_keys = set()
        
        # Recursively search for images at any depth with deduplication
        self._extract_images_recursive(input_dict, images, seen_keys)
        
        return images
    
    def _extract_json_path(self, input_dict: Dict[str, Any], path_spec: str) -> Any:
        """
        Extract value from input_dict using JSON path notation.
        
        Args:
            input_dict: The input JSON structure
            path_spec: Path specification (e.g., "text", "caption", "results.images")
        
        Returns:
            Extracted value (can be any JSON type)
            
        Raises:
            ValueError: If path doesn't exist in input
        """
        # Simple top-level field
        if '.' not in path_spec:
            if path_spec not in input_dict:
                raise ValueError(f"Field '{path_spec}' not found in input")
            return input_dict[path_spec]
        
        # Nested path with dot notation
        parts = path_spec.split('.')
        current = input_dict
        
        # Navigate through all parts
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"Path '{'.'.join(parts[:i+1])}' not found in input")
        
        return current
    
    def _build_prompt(self, input_dict: Dict[str, Any], prompt_template: str, json_format: str) -> str:
        """
        Build the complete prompt by replacing JSON path placeholders.
        
        Args:
            input_dict: Full input JSON structure
            prompt_template: Template with {path} placeholders
            json_format: Expected output format
            
        Returns:
            Complete prompt with all placeholders replaced
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
                
                # Serialize value as JSON string (pretty-printed)
                if isinstance(value, (dict, list)):
                    serialized = json.dumps(value, indent=2)
                elif isinstance(value, str):
                    # Keep strings as-is (don't double-quote)
                    serialized = value
                else:
                    # Numbers, booleans, etc.
                    serialized = json.dumps(value)
                
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

Please respond with ONLY a valid, complete JSON object that matches this structure:
{json_format}

IMPORTANT: Your response must be valid JSON that can be parsed by json.loads(). 
- Wrap your response in braces: {{"key": value}}
- Do not include any text before or after the JSON
- Do not include markdown code blocks or formatting"""
        
        return full_prompt
    
    def _normalize_numeric_values(self, obj: Any) -> Any:
        """
        Recursively normalize values - if numeric field is not a number, set to 0.0.
        
        Args:
            obj: Object to normalize
            
        Returns:
            Normalized object
        """
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
                    result[key] = self._normalize_numeric_values(value)
            return result
        elif isinstance(obj, list):
            return [self._normalize_numeric_values(item) for item in obj]
        else:
            return obj
    
    async def run(
        self,
        inp: ImageEnrichInput,
        params: ImageEnrichParams,
        ctx: RunContext
    ) -> ImageEnrichOutput:
        """
        Process images: generate structured metadata using LLM vision models.
        
        Args:
            inp: Input with namespaced state containing image objects
            params: Parameters including prompt, model, json_format, and output_name
            ctx: Runtime context with API keys
            
        Returns:
            Output with array of metadata objects, one per image, with preserved input fields
        """
        # Get OpenAI API key from context (call_llm_with_image currently only supports OpenAI)
        openai_api_key = ctx.get_api_key("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY must be found in project API keys for image vision models")
        
        # Extract and normalize image objects
        input_dict = inp.model_dump()
        images = self._normalize_images(input_dict)
        
        # If no images found, return empty results instead of raising
        if not images:
            output_field_name = params.output_name
            output_data = {
                output_field_name: [],
                "warnings": [
                    "No image objects found in input. Expected 'image' or 'images' field (single object or array) or objects with 'url' or 'base64' fields."
                ]
            }
            return ImageEnrichOutput(**output_data)
        
        # Validate each image has url or base64
        for i, img in enumerate(images):
            if not isinstance(img, dict):
                raise ValueError(f"Image at index {i} is not an object: {type(img)}")
            if "url" not in img and "base64" not in img:
                raise ValueError(f"Image at index {i} must have either 'url' or 'base64' field")
        
        # Flatten namespaced input structure into a single dict for context extraction
        flattened_input = {}
        for key, value in input_dict.items():
            if isinstance(value, dict):
                # If this is a namespaced node output, merge its fields
                flattened_input.update(value)
            else:
                flattened_input[key] = value
        
        # Extract article text from input state (look for "text" at top level)
        article_text = None
        if "text" in flattened_input:
            article_text = flattened_input["text"]
        
        results = []
        
        # Process each image
        for i, image_obj in enumerate(images):
            try:
                # Get image input (url or base64)
                image_input = image_obj.get("url") or image_obj.get("base64")
                if not image_input:
                    raise ValueError(f"Image at index {i} has neither 'url' nor 'base64' field")
                
                # Extract caption from image object
                caption = image_obj.get("caption") or image_obj.get("alt") or None
                
                # Build context dict for prompt templating
                context_dict = dict(flattened_input)
                if caption:
                    context_dict["caption"] = caption
                if article_text:
                    # Truncate article text if too long
                    max_article_length = 2000  # characters
                    truncated_text = article_text[:max_article_length] if len(article_text) > max_article_length else article_text
                    if len(article_text) > max_article_length:
                        truncated_text += "..."
                    context_dict["text"] = truncated_text
                
                # Build the complete prompt using JSON path extraction
                enhanced_prompt = self._build_prompt(context_dict, params.prompt, params.json_format)
                
                # Call LLM with vision API to generate metadata
                response = call_llm_with_image(
                    prompt=enhanced_prompt,
                    image=image_input,
                    model=params.llm_model,
                    openai_api_key=openai_api_key,
                    force_json=True  # Force JSON response
                )
                
                # Parse JSON response
                try:
                    metadata = json.loads(response)
                except json.JSONDecodeError as e:
                    # Try to fix common issues before giving up
                    cleaned_response = response.strip()
                    
                    # Fix malformed numbers: extract numeric part from patterns like "0. nine"
                    pattern = r'(\d+\.)\s+([a-zA-Z]+)'
                    def fix_number(match):
                        return match.group(1) + '0'
                    cleaned_response = re.sub(pattern, fix_number, cleaned_response, flags=re.IGNORECASE)
                    
                    # Try parsing again with cleaned response
                    try:
                        metadata = json.loads(cleaned_response)
                    except json.JSONDecodeError:
                        # If still fails, try wrapping in braces if it looks like a property fragment
                        if cleaned_response.startswith('"') and '":' in cleaned_response[:50]:
                            try:
                                metadata = json.loads(f"{{{cleaned_response}}}")
                            except json.JSONDecodeError:
                                raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
                        else:
                            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
                
                # Validate that response is a dictionary
                if not isinstance(metadata, dict):
                    raise ValueError(f"LLM response must be a JSON object, got: {type(metadata)}")
                
                # Normalize numeric values
                metadata = self._normalize_numeric_values(metadata)
                
                # Build result object starting with all original image fields
                result_data = dict(image_obj)  # Preserve all original fields (url, base64, caption, etc.)
                
                # Add metadata fields
                result_data.update(metadata)
                
                results.append(result_data)
                
            except Exception as e:
                # On error, create a result with error info but preserve original fields
                error_result_data = dict(image_obj)
                error_result_data["error"] = f"Error processing image: {str(e)}"
                error_result_data["metadata"] = {}
                results.append(error_result_data)
        
        # Use output_name as provided (no automatic meta_ prefix)
        output_field_name = params.output_name
        
        # Create output with custom field name and all preserved fields
        output_data = {
            output_field_name: results,
            **flattened_input  # Preserve all input fields
        }
        
        return ImageEnrichOutput(**output_data)

