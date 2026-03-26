"""EmbedImages node for generating descriptions and embeddings for images using OpenAI."""

import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from agate_utils.llm import call_llm_with_image
from openai import OpenAI


class EmbedImagesInput(BaseModel):
    """Input schema - expects to find image objects in namespaced state."""
    model_config = ConfigDict(extra='allow')  # Accept full state


class EmbedImagesParams(BaseModel):
    """Parameters for EmbedImages node."""
    prompt: str = Field(
        default="Describe this image in detail. Use the provided context (caption and article text) to inform your description, but focus primarily on what you see in the image itself.",
        description="Prompt to use for image analysis. The image caption and article text will be automatically included as context."
    )
    llm_model: str = Field(
        default="gpt-5.4-mini",
        description="OpenAI vision model to use (gpt-5.4-mini, gpt-5.4, or gpt-5.4-nano)"
    )
    output_name: str = Field(
        default="image_embeddings",
        description="Name of the output field that will contain the image processing results"
    )


class ImageResult(BaseModel):
    """Output schema for a single image result."""
    model_config = ConfigDict(extra='allow')  # Preserve all input fields
    
    url: Optional[str] = Field(default=None, description="Original image URL")
    base64: Optional[str] = Field(default=None, description="Original base64 image")
    generated_text: str = Field(description="LLM-generated description of the image")
    embedding: List[float] = Field(description="Text embedding vector")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model used")
    embedding_dimensions: int = Field(default=1536, description="Embedding dimensions")


class EmbedImagesOutput(BaseModel):
    """Output schema for EmbedImages node."""
    model_config = ConfigDict(extra='allow')  # Allow dynamic output field name


@register("EmbedImages")
class EmbedImages(NodeBase[EmbedImagesInput, EmbedImagesOutput, EmbedImagesParams]):
    """
    EmbedImages node for generating text descriptions and embeddings for images.
    
    This node takes image objects (single or array), generates descriptions using
    OpenAI vision models, then embeds those descriptions using OpenAI embedding models.
    """
    
    name = "EmbedImages"
    version = "0.1.0"
    category = "enrichment"
    
    Input = EmbedImagesInput
    Output = EmbedImagesOutput
    Params = EmbedImagesParams
    
    def _get_client(self, api_key: str) -> OpenAI:
        """Get OpenAI client with provided API key."""
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        return OpenAI(api_key=api_key)
    
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
                # Continue searching in case there are more images in nested structures
            
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
                # Continue searching in case there are more images in nested structures
            
            # Check if this dict itself is an image object (but not if it already has image/images keys)
            if ("url" in obj or "base64" in obj) and "image" not in obj and "images" not in obj:
                img_key = self._get_image_key(obj)
                if img_key not in seen_keys:
                    seen_keys.add(img_key)
                    images.append(obj)
                    # Stop recursing - this is itself an image object
                    return
            
            # Recursively search through all values in the dict
            # (this will find nested image/images keys even after we found some)
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
    
    async def run(
        self,
        inp: EmbedImagesInput,
        params: EmbedImagesParams,
        ctx: RunContext
    ) -> EmbedImagesOutput:
        """
        Process images: generate descriptions and create embeddings.
        
        Args:
            inp: Input with namespaced state containing image objects
            params: Parameters including prompt and LLM model
            ctx: Runtime context with API keys
            
        Returns:
            Output with array of results, each containing original image data,
            generated text, and embedding
        """
        # Get OpenAI API key from context
        openai_api_key = ctx.get_api_key("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in project API keys")
        
        # Extract and normalize image objects
        input_dict = inp.model_dump()
        images = self._normalize_images(input_dict)
        
        # If no images found, return empty results instead of raising
        if not images:
            output_data = {
                params.output_name: [],
                "warnings": [
                    "No image objects found in input. Expected 'image' or 'images' field (single object or array) or objects with 'url' or 'base64' fields."
                ]
            }
            return EmbedImagesOutput(**output_data)
        
        # Validate each image has url or base64
        for i, img in enumerate(images):
            if not isinstance(img, dict):
                raise ValueError(f"Image at index {i} is not an object: {type(img)}")
            if "url" not in img and "base64" not in img:
                raise ValueError(f"Image at index {i} must have either 'url' or 'base64' field")
        
        # Get OpenAI client for embeddings
        client = self._get_client(openai_api_key)
        
        # Hardcoded embedding configuration
        embedding_model = "text-embedding-3-small"
        embedding_dimensions = 1536
        
        results = []
        
        # Extract article text from input state (look for "text" at top level)
        article_text = None
        if "text" in input_dict:
            article_text = input_dict["text"]
        # Also check in nested node outputs
        if not article_text:
            for key, value in input_dict.items():
                if isinstance(value, dict) and "text" in value:
                    article_text = value.get("text")
                    break
        
        # Process each image
        for i, image_obj in enumerate(images):
            try:
                # Get image input (url or base64)
                image_input = image_obj.get("url") or image_obj.get("base64")
                if not image_input:
                    raise ValueError(f"Image at index {i} has neither 'url' nor 'base64' field")
                
                # Extract caption from image object
                caption = image_obj.get("caption") or image_obj.get("alt") or None
                
                # Build enhanced prompt with context
                enhanced_prompt = params.prompt
                
                # Add context sections if available
                context_parts = []
                if caption:
                    context_parts.append(f"Image caption: {caption}")
                if article_text:
                    # Truncate article text if too long (to avoid token limits)
                    max_article_length = 2000  # characters
                    truncated_text = article_text[:max_article_length] if len(article_text) > max_article_length else article_text
                    if len(article_text) > max_article_length:
                        truncated_text += "..."
                    context_parts.append(f"Article text: {truncated_text}")
                
                if context_parts:
                    context_section = "\n\nContext:\n" + "\n".join(context_parts)
                    enhanced_prompt = params.prompt + context_section
                
                # Call LLM to generate description
                generated_text = call_llm_with_image(
                    prompt=enhanced_prompt,
                    image=image_input,
                    model=params.llm_model,
                    openai_api_key=openai_api_key,
                    force_json=False  # Get plain text description
                )
                
                # Create embedding of the generated text
                embedding_response = client.embeddings.create(
                    input=generated_text,
                    model=embedding_model,
                    dimensions=embedding_dimensions
                )
                embedding = embedding_response.data[0].embedding
                
                # Build result object starting with all original fields
                result_data = dict(image_obj)  # Preserve all original fields (url, base64, caption, etc.)
                
                # Add new fields
                result_data["generated_text"] = generated_text
                result_data["embedding"] = embedding
                result_data["embedding_model"] = embedding_model
                result_data["embedding_dimensions"] = len(embedding)
                
                results.append(ImageResult(**result_data))
                
            except Exception as e:
                # On error, create a result with error info but preserve original fields
                error_result_data = dict(image_obj)
                error_result_data["generated_text"] = f"Error processing image: {str(e)}"
                error_result_data["embedding"] = []
                error_result_data["embedding_model"] = embedding_model
                error_result_data["embedding_dimensions"] = 0
                results.append(ImageResult(**error_result_data))
        
        # Create output with dynamic field name
        output_data = {
            params.output_name: results
        }
        
        return EmbedImagesOutput(**output_data)
