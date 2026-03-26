"""WorksExtract node for extracting works from text using LLM."""

import os
import asyncio
import time
import json
import re
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from agate_core import NodeBase, RunContext, register
from agate_utils.llm import call_llm

TASK_SOFT_TIME_LIMIT = int(os.getenv("TASK_SOFT_TIME_LIMIT", "3600"))


def _capitalize_first_letter_of_first_word(name: str) -> str:
    """Ensure the first alphabetic character of the first word is uppercase.

    Skips brand-like tokens where lowercase first letter is followed by uppercase
    (e.g. iPhone, eBay) so we do not produce "IPhone".
    """
    s = name.strip()
    if not s:
        return s
    if not s[0].isalpha() or not s[0].islower():
        return s
    if len(s) > 1 and s[1].isupper():
        return s
    return s[0].upper() + s[1:]


class WorksExtractInput(BaseModel):
    """Input schema - expects to find text in namespaced state."""
    model_config = ConfigDict(extra="allow")


class WorksExtractParams(BaseModel):
    """Parameters for WorksExtract node."""
    model: str = Field(
        default="gpt-5.4-mini",
        description="LLM model to use",
    )
    prompt_file: str = Field(
        default="prompts/extract.md",
        description="Path to the prompt file",
    )
    prompt: str = Field(default="", description="Custom prompt override")
    llmTimeout: int = Field(default=600, ge=60, le=1800, description="Timeout in seconds")
    json_format: str = Field(
        default='{ "works": [] }',
        description="Example output JSON format",
    )


class WorkMention(BaseModel):
    """A mention of a work in the text (no quote for works)."""
    text: str = Field(description="The text containing the mention")


class Work(BaseModel):
    """A work extracted from text."""
    name: str = Field(description="Work name")
    type: str = Field(default="other", description="Work type (snake_case)")
    role_in_story: str = Field(description="Brief description of the work's role")
    mentions: List[WorkMention] = Field(description="List of mentions of this work")
    model_config = ConfigDict(extra="allow")


class WorksExtractOutput(BaseModel):
    """Output schema - returns extracted works and preserves input state."""
    model_config = ConfigDict(extra="allow")
    text: str = Field(description="Original input text")
    works: List[Work] = Field(description="List of extracted works")


@register("WorksExtract")
class WorksExtract(
    NodeBase[WorksExtractInput, WorksExtractOutput, WorksExtractParams]
):
    """Node for extracting works from text using LLM."""

    name = "WorksExtract"
    version = "0.1.0"
    category = "extraction"

    Input = WorksExtractInput
    Output = WorksExtractOutput
    Params = WorksExtractParams

    def _extract_json_path(self, input_dict: Dict[str, Any], path_spec: str) -> Any:
        if path_spec == "raw":
            return input_dict
        if "," in path_spec:
            fields = [f.strip() for f in path_spec.split(",")]
            base_path = fields[0]
            additional_fields = fields[1:]
            target = self._extract_json_path(input_dict, base_path)
            all_fields = [base_path.split(".")[-1]] + additional_fields

            def pick_fields(obj):
                if isinstance(obj, dict):
                    return {f: obj.get(f) for f in all_fields if f in obj}
                return obj

            if isinstance(target, list):
                return [pick_fields(item) for item in target if isinstance(item, dict)]
            return pick_fields(target)

        parts = path_spec.split(".")
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

    def _build_prompt(self, input_dict: Dict[str, Any], prompt_template: str) -> str:
        ESCAPED_OPEN = "___ESCAPED_OPEN_BRACE___"
        ESCAPED_CLOSE = "___ESCAPED_CLOSE_BRACE___"
        temp_template = prompt_template.replace("{{", ESCAPED_OPEN).replace("}}", ESCAPED_CLOSE)
        placeholders = re.findall(r"\{([^}]+)\}", temp_template)
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
                prompt = prompt.replace(f"{{{placeholder}}}", serialized)
            except Exception as e:
                raise ValueError(
                    f"Failed to extract JSON path '{placeholder_key}': {str(e)}\n"
                    f"Available top-level keys: {list(input_dict.keys())}"
                ) from e
        prompt = prompt.replace(ESCAPED_OPEN, "{{").replace(ESCAPED_CLOSE, "}}")
        return prompt

    def _escape_braces(self, s: str) -> str:
        return s.replace("{", "{{").replace("}", "}}")

    async def run(
        self,
        inp: WorksExtractInput,
        params: WorksExtractParams,
        ctx: RunContext,
    ) -> WorksExtractOutput:
        start_time = time.time()
        CELERY_TIMEOUT_BUFFER = 300

        input_dict = inp.model_dump()
        flattened_input: Dict[str, Any] = {}
        for key, value in input_dict.items():
            is_node_key = key.startswith("node-") and len(key) > 5 and key[5:].isdigit()
            if is_node_key and isinstance(value, dict):
                flattened_input.update(value)
            else:
                flattened_input[key] = value

        text = flattened_input.get("text")
        if not text:
            for node_id, node_data in input_dict.items():
                if isinstance(node_data, dict) and "text" in node_data:
                    text = node_data["text"]
                    break
        if not text and "text" in input_dict and isinstance(input_dict["text"], str):
            text = input_dict["text"]
        if not text:
            raise ValueError(
                f"No 'text' field found in input state. Available keys: {list(input_dict.keys())}"
            )

        if params.prompt and params.prompt.strip():
            prompt_template = params.prompt
        else:
            prompt_template = self._load_prompt_template(params.prompt_file)

        prompt = self._build_prompt(flattened_input, prompt_template)
        if params.json_format:
            escaped_format = self._escape_braces(params.json_format)
            prompt = f"{prompt}\n\nExpected output format:\n{escaped_format}"

        elapsed_time = time.time() - start_time
        max_safe_runtime = TASK_SOFT_TIME_LIMIT - CELERY_TIMEOUT_BUFFER
        if elapsed_time > max_safe_runtime:
            raise TimeoutError(
                f"Node has been running for {elapsed_time:.1f}s, which exceeds safe runtime limit."
            )
        remaining_safe_time = max_safe_runtime - elapsed_time
        effective_timeout = min(params.llmTimeout, remaining_safe_time)
        if effective_timeout < 60:
            raise TimeoutError(
                f"Insufficient time remaining ({effective_timeout:.1f}s) for LLM call."
            )

        try:
            response_text = await asyncio.wait_for(
                asyncio.to_thread(
                    call_llm,
                    prompt=prompt,
                    model=params.model,
                    system_message="You are a specialized AI assistant for extracting works from text. Return only valid JSON.",
                    force_json=True,
                    temperature=0.0,
                    timeout=effective_timeout,
                    openai_api_key=ctx.get_api_key("OPENAI_API_KEY"),
                    project_system_prompt=ctx.project_system_prompt,
                ),
                timeout=effective_timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"WorksExtract LLM call exceeded timeout of {effective_timeout}s"
            )

        response_data = None
        try:
            response_data = json.loads(response_text)
            if isinstance(response_data, list):
                works_data = response_data
            elif isinstance(response_data, dict) and "works" in response_data:
                works_data = response_data["works"]
            else:
                raise ValueError(
                    "Expected a list of works or an object with 'works' field"
                )
            if not isinstance(works_data, list):
                raise ValueError("Expected a list of works")

            works = []
            for work_data in works_data:
                required_fields = ["name", "role_in_story", "mentions"]
                for field in required_fields:
                    if field not in work_data:
                        raise ValueError(f"Missing required field '{field}' in work data")
                if not isinstance(work_data.get("mentions"), list):
                    raise ValueError("'mentions' field must be a list")

                mentions_list = []
                for m in work_data["mentions"]:
                    if not isinstance(m, dict):
                        continue
                    text_val = m.get("text", "").strip()
                    mentions_list.append(WorkMention(text=text_val))

                work_type = work_data.get("type", "other")
                if isinstance(work_type, str):
                    work_type = work_type.strip() or "other"
                else:
                    work_type = "other"

                raw_name = str(work_data["name"]).strip()
                works.append(
                    Work(
                        name=_capitalize_first_letter_of_first_word(raw_name),
                        type=work_type,
                        role_in_story=str(work_data.get("role_in_story", "")),
                        mentions=mentions_list,
                    )
                )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse LLM response as works data: {e}")

        output_data = {
            "text": text,
            "works": [w.model_dump() for w in works],
        }

        for key, value in flattened_input.items():
            if key not in ["text"] and key not in output_data:
                output_data[key] = value

        if isinstance(response_data, dict):
            for key, value in response_data.items():
                if key != "works" and key not in output_data:
                    output_data[key] = value

        for node_id, node_data in input_dict.items():
            if isinstance(node_data, dict):
                for key, value in node_data.items():
                    if key not in ["text"] and key not in output_data:
                        output_data[key] = value

        return WorksExtractOutput(**output_data)

    def _load_prompt_template(self, prompt_file_path: str) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file = (
            prompt_file_path
            if os.path.isabs(prompt_file_path)
            else os.path.join(current_dir, prompt_file_path)
        )
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
