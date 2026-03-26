"""LLM utilities for calling OpenAI API."""

import time
import os
import base64
from openai import OpenAI
from typing import Optional, Union


def _get_openai_client(api_key: Optional[str] = None, timeout: float = 300.0) -> OpenAI:
    """Get or create OpenAI client with provided API key and timeout.

    Args:
        api_key: OpenAI API key
        timeout: Request timeout in seconds (default: 300s / 5 minutes)
    """
    if api_key is None:
        raise ValueError("OPENAI_API_KEY must be provided (configure in project settings)")

    return OpenAI(api_key=api_key, timeout=timeout)


def _clean_json_response(response_text: str) -> str:
    """
    Clean up markdown code blocks from LLM responses.

    Args:
        response_text: Raw response text from LLM

    Returns:
        Cleaned response text without markdown formatting
    """
    cleaned = response_text.strip()

    # Remove markdown code blocks if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]  # Remove ```json
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]  # Remove ```
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]  # Remove trailing ```

    return cleaned.strip()


def call_llm(
    prompt: str,
    model: Optional[str] = None,
    system_message: Optional[str] = None,
    force_json: bool = True,
    max_retries: int = 3,
    temperature: float = 0.0,
    max_tokens: int = 4000,
    openai_api_key: Optional[str] = None,
    project_system_prompt: Optional[str] = None,
    timeout: float = 300.0,
) -> str:
    """
    Call an LLM with the given prompt and model with exponential backoff retries.

    Args:
        prompt: The prompt to send to the LLM
        model: The model name (e.g., 'gpt-5.4-mini').
               Defaults to os.getenv("DEFAULT_MODEL", "gpt-5.4-mini")
        system_message: Optional system message. If not provided and force_json is True,
                       uses a default JSON system message.
        force_json: Whether to force JSON output (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        temperature: Temperature for generation (default: 0.0)
        max_tokens: Maximum tokens to generate (default: 4000)
        openai_api_key: OpenAI API key (required)
        project_system_prompt: Optional project-level system prompt (takes precedence over system_message)
        timeout: Request timeout in seconds (default: 300s / 5 minutes)

    Returns:
        The LLM response text

    Raises:
        ValueError: If prompt is empty or no API key is available
        Exception: If the LLM call fails after all retries
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    # Get model from environment if not specified
    if not model:
        model = os.getenv("DEFAULT_MODEL", "gpt-5.4-mini")

    # Set system message - project system prompt takes precedence
    if project_system_prompt:
        system_message = project_system_prompt
    elif system_message is None:
        if force_json:
            system_message = "You are a helpful assistant that returns only structured JSON output."
        else:
            system_message = (
                "You are a helpful assistant that returns direct, concise responses "
                "without markdown formatting or explanations."
            )

    client = _get_openai_client(openai_api_key, timeout=timeout)

    # GPT-5 models only support the default temperature (1.0); any other value returns 400.
    is_gpt5 = model.startswith("gpt-5")
    should_skip_temperature = is_gpt5

    for attempt in range(max_retries):
        try:
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
            }

            if not should_skip_temperature:
                request_params["temperature"] = temperature

            response = client.chat.completions.create(**request_params)
            response_text = response.choices[0].message.content.strip()
            return _clean_json_response(response_text) if force_json else response_text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"OpenAI API call failed after {max_retries} attempts: {str(e)}") from e

    raise Exception("Unexpected error in call_llm")


def call_llm_with_image(
    prompt: str,
    image: Union[str, bytes],
    image_format: str = "auto",
    model: Optional[str] = None,
    system_message: Optional[str] = None,
    force_json: bool = True,
    max_retries: int = 3,
    max_tokens: int = 4000,
    openai_api_key: Optional[str] = None,
    project_system_prompt: Optional[str] = None,
) -> str:
    """
    Call OpenAI LLM with image input (URL or base64 encoded).

    Args:
        prompt: Text prompt to send with the image
        image: Image input - can be:
            - URL string (e.g., "https://example.com/image.jpg")
            - Base64 encoded string (e.g., base64 string or "data:image/jpeg;base64,...")
            - Bytes (will be base64 encoded)
            - File path (will be read and base64 encoded)
        image_format: Format hint for the image. If "auto", will try to detect from:
            - URL: from extension or data URI
            - Base64: from data URI prefix
            - Bytes: default to "image/jpeg"
        model: The OpenAI model name (e.g., 'gpt-5.4-mini').
               Defaults to os.getenv("DEFAULT_MODEL", "gpt-5.4-mini")
        system_message: Optional system message. If not provided and force_json is True,
                       uses a default JSON system message.
        force_json: Whether to force JSON output (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        max_tokens: Maximum tokens to generate (default: 4000)
        openai_api_key: OpenAI API key (required)
        project_system_prompt: Optional project-level system prompt (takes precedence over system_message)

    Returns:
        The LLM response text

    Raises:
        ValueError: If prompt is empty, no API key is available, or model is not an OpenAI model
        Exception: If the LLM call fails after all retries
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    # Get model from environment if not specified
    if not model:
        model = os.getenv("DEFAULT_MODEL", "gpt-5.4-mini")

    # Check if model is an OpenAI model
    if not model.startswith("gpt"):
        raise ValueError(f"Image input is only supported for OpenAI models. Got model: {model}")

    # Set system message - project system prompt takes precedence
    if project_system_prompt:
        system_message = project_system_prompt
    elif system_message is None:
        if force_json:
            system_message = "You are a helpful assistant that returns only structured JSON output."
        else:
            system_message = (
                "You are a helpful assistant that returns direct, concise responses "
                "without markdown formatting or explanations."
            )

    # Combine system message with prompt
    full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt

    # Process image input
    image_url = None

    if isinstance(image, bytes):
        # Bytes input - encode to base64
        base64_image = base64.b64encode(image).decode("utf-8")
        # Determine MIME type from image_format or default to jpeg
        if image_format == "auto":
            mime_type = "image/jpeg"
        else:
            mime_type = image_format if "/" in image_format else f"image/{image_format}"
        image_url = f"data:{mime_type};base64,{base64_image}"
    elif isinstance(image, str):
        if image.startswith("http://") or image.startswith("https://"):
            # URL input
            image_url = image
        elif image.startswith("data:image/"):
            # Already in data URI format
            image_url = image
        elif os.path.exists(image):
            # File path - read and encode
            with open(image, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            # Try to determine MIME type from file extension
            if image_format == "auto":
                ext = os.path.splitext(image)[1].lower()
                mime_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                mime_type = mime_map.get(ext, "image/jpeg")
            else:
                mime_type = image_format if "/" in image_format else f"image/{image_format}"
            image_url = f"data:{mime_type};base64,{base64_image}"
        else:
            # Assume it's a base64 string (without data URI prefix)
            if image_format == "auto":
                mime_type = "image/jpeg"
            else:
                mime_type = image_format if "/" in image_format else f"image/{image_format}"
            image_url = f"data:{mime_type};base64,{image}"
    else:
        raise ValueError(
            f"Invalid image input type: {type(image)}. Expected str (URL/path/base64) or bytes."
        )

    # Get OpenAI client (use default timeout for image calls)
    client = _get_openai_client(openai_api_key, timeout=300.0)

    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": full_prompt},
                            {
                                "type": "input_image",
                                "image_url": image_url,
                            },
                        ],
                    }
                ],
            )
            response_text = response.output_text.strip()
            return _clean_json_response(response_text) if force_json else response_text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(
                    f"OpenAI API call with image failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(
                    f"OpenAI API call with image failed after {max_retries} attempts: {str(e)}"
                ) from e

    raise Exception("Unexpected error in call_llm_with_image")
