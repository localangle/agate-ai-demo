"""PeopleExtract node for extracting people information from text using LLM.

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

import os
import asyncio
import time
import json
import re
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from agate_utils.llm import call_llm

# Get Celery timeout limits from environment (defaults match worker/tasks.py)
TASK_SOFT_TIME_LIMIT = int(os.getenv("TASK_SOFT_TIME_LIMIT", "3600"))  # 60 minutes default


class PeopleExtractInput(BaseModel):
    """Input schema - expects to find text in namespaced state."""
    model_config = ConfigDict(extra='allow')


class PeopleExtractParams(BaseModel):
    """Parameters for PeopleExtract node."""
    model: str = Field(
        default="gpt-5.4-mini",
        description="LLM model to use (gpt-5.4-mini, gpt-5.4, or gpt-5.4-nano)"
    )
    prompt_file: str = Field(
        default="prompts/extract.md",
        description="Path to the prompt file relative to the node directory. Defaults to prompts/extract.md"
    )
    prompt: str = Field(
        default="",
        description="Custom prompt override. If provided, this takes precedence over prompt_file."
    )
    llmTimeout: int = Field(
        default=600,
        ge=60,
        le=1800,
        description="Timeout in seconds for the LLM call (default: 10 minutes, max: 30 minutes)"
    )
    json_format: str = Field(
        default='''{
  "people": [
    {
      "name": {"full": "John Smith", "first": "John", "last": "Smith"},
      "title": "Mayor",
      "affiliation": "City of Chicago",
      "public_figure": true,
      "role_in_story": "Announced new policy initiative",
      "mentions": [
        {"text": "Mayor John Smith announced a new policy initiative on Monday.", "quote": false},
        {"text": "\\"This will benefit all residents,\\" Smith said.", "quote": true}
      ]
    },
    {
      "name": {"full": "Jane Doe", "first": "Jane", "last": "Doe"},
      "title": "",
      "affiliation": "",
      "public_figure": false,
      "role_in_story": "Resident affected by the policy",
      "mentions": [
        {"text": "Jane Doe, a local resident, expressed concerns about the new policy.", "quote": false}
      ]
    }
  ]
}''',
        description="Example output JSON format. Braces will be escaped automatically in the prompt."
    )


class PersonName(BaseModel):
    """Name components for a person."""
    full: str = Field(description="Full name of the person")
    first: str = Field(default="", description="First name")
    last: str = Field(default="", description="Last name")


class Mention(BaseModel):
    """A mention of a person in the text."""
    text: str = Field(description="The text containing the mention")
    quote: bool = Field(default=False, description="Whether this mention contains a quote from the person")
    verified: bool = Field(default=False, description="Whether this mention was found in the original text")


class Person(BaseModel):
    """A person extracted from text."""
    name: PersonName = Field(description="Name information for the person")
    title: str = Field(default="", description="Title or role (official or informal, e.g. Mayor, shortstop, advocate)")
    affiliation: str = Field(default="", description="Institution or organization")
    public_figure: bool = Field(default=False, description="Whether this person is a public figure")
    role_in_story: str = Field(description="Brief description of the person's role in the story")
    mentions: List[Mention] = Field(description="List of mentions of this person in the text")
    model_config = ConfigDict(extra='allow')  # Allow additional fields


class PeopleExtractOutput(BaseModel):
    """Output schema - returns extracted people and preserves input state."""
    model_config = ConfigDict(extra='allow')
    
    text: str = Field(description="Original input text")
    people: List[Person] = Field(description="List of extracted people")


@register("PeopleExtract")
class PeopleExtract(NodeBase[PeopleExtractInput, PeopleExtractOutput, PeopleExtractParams]):
    """Node for extracting people information from text using LLM."""
    
    name = "PeopleExtract"
    version = "0.1.0"
    category = "extraction"
    
    Input = PeopleExtractInput
    Output = PeopleExtractOutput
    Params = PeopleExtractParams
    
    def _extract_json_path(self, input_dict: Dict[str, Any], path_spec: str) -> Any:
        """
        Extract value from input_dict using JSON path notation (similar to LLMEnrich).
        Supports:
        - Simple path: "text", "url"
        - Nested path: "results.images"
        - Multi-field (comma-separated): "results.caption, id"
        - {raw}: returns full input_dict
        """
        if path_spec == "raw":
            return input_dict
        
        # Multi-field spec
        if ',' in path_spec:
            fields = [f.strip() for f in path_spec.split(',')]
            base_path = fields[0]
            additional_fields = fields[1:]
            
            # Navigate base_path
            target = self._extract_json_path(input_dict, base_path)
            all_fields = [base_path.split('.')[-1]] + additional_fields
            
            def pick_fields(obj):
                if isinstance(obj, dict):
                    return {f: obj.get(f) for f in all_fields if f in obj}
                return obj
            
            if isinstance(target, list):
                return [pick_fields(item) for item in target if isinstance(item, dict)]
            return pick_fields(target)
        
        # Simple or dotted path
        parts = path_spec.split('.')
        current: Union[Dict[str, Any], List[Any], Any] = input_dict
        for i, part in enumerate(parts):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                # Extract field from each element if list
                extracted = []
                for item in current:
                    if isinstance(item, dict) and part in item:
                        extracted.append(item[part])
                current = extracted
            else:
                raise ValueError(f"Path '{'.'.join(parts[:i+1])}' not found in input")
        return current
    
    def _build_prompt(self, input_dict: Dict[str, Any], prompt_template: str) -> str:
        """
        Replace {json_path} placeholders in prompt_template using the provided input_dict.
        Skips escaped braces ({{ and }}) to avoid treating them as placeholders.
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
                if isinstance(value, (dict, list)):
                    serialized = json.dumps(value, indent=2)
                elif isinstance(value, str):
                    serialized = value
                else:
                    serialized = json.dumps(value)
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
        inp: PeopleExtractInput,
        params: PeopleExtractParams,
        ctx: RunContext
    ) -> PeopleExtractOutput:
        """
        Execute people extraction - extract text from namespaced state.
        """
        # Track start time for timeout calculations
        start_time = time.time()
        CELERY_TIMEOUT_BUFFER = 300  # Stop 5 minutes before Celery timeout to allow cleanup
        
        input_dict = inp.model_dump()
        
        # Flatten namespaced input to make JSON paths easier (similar to LLMEnrich)
        # Only unwrap namespaced node-* dictionaries; preserve normal dict fields (like meta_* objects)
        flattened_input: Dict[str, Any] = {}
        for key, value in input_dict.items():
            is_node_key = key.startswith("node-") and len(key) > 5 and key[5:].isdigit()
            if is_node_key and isinstance(value, dict):
                flattened_input.update(value)
            else:
                flattened_input[key] = value
        
        # Debug logging to trace meta fields
        try:
            meta_keys = [k for k in flattened_input.keys() if k.startswith("meta_")]
            print(f"[PeopleExtract] Input keys: {list(input_dict.keys())}")
            print(f"[PeopleExtract] Flattened keys: {list(flattened_input.keys())}")
            if meta_keys:
                print(f"[PeopleExtract] Found meta_* keys: {meta_keys}")
            else:
                print(f"[PeopleExtract] WARNING: No meta_* keys in flattened_input")
        except Exception:
            pass
        
        # Prefer text from flattened input
        text = flattened_input.get("text")
        
        # Backward compatibility: try to find text in namespaced dicts if not found
        if not text:
            for node_id, node_data in input_dict.items():
                if isinstance(node_data, dict) and 'text' in node_data:
                    text = node_data['text']
                    break
        
        # If still not found, accept top-level text field even if not namespaced
        if not text and "text" in input_dict and isinstance(input_dict["text"], str):
            text = input_dict["text"]
        
        if not text:
            raise ValueError(
                f"No 'text' field found in input state. Available keys: {list(input_dict.keys())}, "
                f"Node data keys: {[list(v.keys()) if isinstance(v, dict) else 'not dict' for v in input_dict.values()]}"
            )
        
        # Use custom prompt if provided, otherwise load from prompt_file
        if params.prompt and params.prompt.strip():
            prompt_template = params.prompt
        else:
            prompt_template = self._load_prompt_template(params.prompt_file)
        
        # Build prompt using JSON path placeholders
        prompt = self._build_prompt(flattened_input, prompt_template)
        
        # Append escaped output format example to avoid placeholder parsing
        if params.json_format:
            escaped_format = self._escape_braces(params.json_format)
            prompt = f"{prompt}\n\nExpected output format:\n{escaped_format}"
        
        # Log the prompt for debugging
        print(f"[PeopleExtract] Prompt:\n{prompt}")
        
        # Check if we're approaching Celery timeout before making LLM call
        # Calculate elapsed time since node start
        elapsed_time = time.time() - start_time
        
        # Use a conservative estimate: assume we're already partway through the task
        # We'll use elapsed_time as a proxy, but be conservative by assuming we need buffer
        # If we've been running for more than (TASK_SOFT_TIME_LIMIT - CELERY_TIMEOUT_BUFFER), stop
        max_safe_runtime = TASK_SOFT_TIME_LIMIT - CELERY_TIMEOUT_BUFFER
        
        if elapsed_time > max_safe_runtime:
            raise TimeoutError(
                f"Node has been running for {elapsed_time:.1f}s, which exceeds safe runtime limit "
                f"({max_safe_runtime}s). Cannot safely execute PeopleExtract LLM call."
            )
        
        # Calculate effective timeout: use the smaller of user timeout or remaining safe time
        remaining_safe_time = max_safe_runtime - elapsed_time
        effective_timeout = min(params.llmTimeout, remaining_safe_time)
        
        if effective_timeout < 60:
            raise TimeoutError(
                f"Insufficient time remaining ({effective_timeout:.1f}s) for LLM call. "
                f"Need at least 60 seconds. Elapsed: {elapsed_time:.1f}s"
            )
        
        print(
            f"[PeopleExtract] Executing LLM call with timeout: {effective_timeout}s "
            f"(elapsed: {elapsed_time:.1f}s, remaining safe time: {remaining_safe_time:.1f}s)"
        )
        
        # Call the LLM with API keys from context, wrapped in asyncio timeout
        # Since call_llm is synchronous, we need to run it in a thread pool
        try:
            response_text = await asyncio.wait_for(
                asyncio.to_thread(
                    call_llm,
                    prompt=prompt,
                    model=params.model,
                    system_message="You are a specialized AI assistant for extracting people information from text. Return only valid JSON.",
                    force_json=True,
                    temperature=0.0,
                    timeout=effective_timeout,  # Pass timeout to call_llm as well
                    openai_api_key=ctx.get_api_key("OPENAI_API_KEY"),
                    project_system_prompt=ctx.project_system_prompt
                ),
                timeout=effective_timeout
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            raise TimeoutError(
                f"PeopleExtract LLM call exceeded timeout of {effective_timeout}s "
                f"(elapsed: {elapsed:.1f}s). The text may be too long or the LLM may be slow."
            )
        
        elapsed = time.time() - start_time
        print(f"[PeopleExtract] LLM call completed in {elapsed:.1f}s")
        
        # Parse the response
        response_data = None
        try:
            response_data = json.loads(response_text)
            
            # Handle both old format (direct array) and new format (with "people" wrapper)
            if isinstance(response_data, list):
                people_data = response_data
            elif isinstance(response_data, dict) and 'people' in response_data:
                people_data = response_data['people']
            else:
                raise ValueError("Expected a list of people or an object with 'people' field")
            
            if not isinstance(people_data, list):
                raise ValueError("Expected a list of people")
            
            # Convert to Person objects
            people = []
            for person_data in people_data:
                # Validate required fields
                if 'role_in_story' not in person_data:
                    raise ValueError("Missing required field 'role_in_story' in person data")
                if 'mentions' not in person_data:
                    raise ValueError("Missing required field 'mentions' in person data")

                # Normalize name - accept object, string, or derive from alternate fields
                name_raw = person_data.get('name')
                full_from_alt = person_data.get('full_name') or person_data.get('name_full') or person_data.get('fullName')
                if isinstance(name_raw, str) and name_raw.strip():
                    name_data = {'full': name_raw.strip(), 'first': '', 'last': ''}
                elif isinstance(name_raw, dict):
                    full = (name_raw.get('full') or '').strip() or (
                        (name_raw.get('first') or '') + ' ' + (name_raw.get('last') or '')
                    ).strip()
                    if full:
                        name_data = {'full': full, 'first': name_raw.get('first', ''), 'last': name_raw.get('last', '')}
                    else:
                        name_data = None
                else:
                    name_data = None
                if not name_data and full_from_alt and str(full_from_alt).strip():
                    name_data = {'full': str(full_from_alt).strip(), 'first': '', 'last': ''}
                if not name_data:
                    raise ValueError(
                        "Missing required field 'name' in person data. "
                        "Each person must have 'name' as object with 'full', or 'name' as string, or 'full_name'."
                    )
                
                if not name_data.get('full', '').strip():
                    raise ValueError("'name.full' (or name as string) is required and must be non-empty")
                
                # Validate mentions structure
                if not isinstance(person_data.get('mentions'), list):
                    raise ValueError("'mentions' field must be a list")
                
                # Convert name to PersonName
                person_data['name'] = PersonName(
                    full=name_data.get('full', ''),
                    first=name_data.get('first', ''),
                    last=name_data.get('last', '')
                )
                
                # Convert mentions to Mention objects and verify them
                mentions_list = []
                for mention_data in person_data['mentions']:
                    if isinstance(mention_data, str):
                        mention_text = mention_data.strip()
                        is_quote = False
                    elif isinstance(mention_data, dict):
                        mention_text = mention_data.get('text') or mention_data.get('content') or ''
                        if isinstance(mention_text, str):
                            mention_text = mention_text.strip()
                        else:
                            mention_text = str(mention_text) if mention_text else ''
                        is_quote = bool(mention_data.get('quote', False))
                    else:
                        raise ValueError(
                            f"Each mention must be an object {{'text': string, 'quote': boolean}} or a string. "
                            f"Got {type(mention_data).__name__}"
                        )
                    # Verify if mention text appears in original text (case-insensitive)
                    is_verified = mention_text.lower() in text.lower() if mention_text else False
                    
                    mentions_list.append(Mention(
                        text=mention_text,
                        quote=is_quote,
                        verified=is_verified
                    ))
                person_data['mentions'] = mentions_list
                
                # Create Person object - preserve all fields from person_data
                people.append(Person(**person_data))
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse LLM response as people data: {e}")
        
        # Create output with extraction results
        output_data = {
            "text": text,
            "people": [person.model_dump() for person in people]
        }
        
        # Handle top-level fields from LLM response (if response_data is a dict with fields beyond 'people')
        # Store these temporarily to check against meta_* fields
        llm_top_level_fields = {}
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                if key != "people":
                    llm_top_level_fields[key] = value
                    try:
                        print(f"[PeopleExtract] LLM top-level field: {key} (type={type(value).__name__})")
                    except Exception:
                        pass
        
        # Preserve any additional fields from flattened input (like url, headline, meta_* fields, etc. from upstream nodes)
        # Priority: meta_* fields from flattened_input > LLM top-level fields > other flattened_input fields
        for key, value in flattened_input.items():
            if key not in ["text"]:  # Don't override the text field
                # Always preserve meta_* fields from flattened_input (they take highest priority)
                if key.startswith("meta_"):
                    output_data[key] = value
                    try:
                        print(f"[PeopleExtract] Preserved meta field: {key} (type={type(value).__name__})")
                    except Exception:
                        pass
                elif key not in output_data:
                    # For non-meta fields, only add if not already present
                    output_data[key] = value
        
        # Add LLM top-level fields only if they don't conflict with meta_* fields
        for key, value in llm_top_level_fields.items():
            meta_key = f"meta_{key}"
            if meta_key not in flattened_input and key not in output_data:
                output_data[key] = value
                try:
                    print(f"[PeopleExtract] Added LLM field: {key} (type={type(value).__name__})")
                except Exception:
                    pass
        
        # Also preserve fields from namespaced input state (like embedding from Embed node)
        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict):
                for key, value in node_data.items():
                    if key not in ["text"] and key not in output_data:  # Don't override existing fields
                        output_data[key] = value
        
        return PeopleExtractOutput(**output_data)
    
    def _load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from the prompts directory."""
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Resolve path relative to node directory
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

