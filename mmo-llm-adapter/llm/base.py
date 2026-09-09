import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = []
    raw_response: Optional[Dict[str, Any]] = None

def parse_message_to_llm_response(message: Dict[str, Any], raw_response: Dict[str, Any]) -> LLMResponse:
    """
    Shared parser for a chat "message" object into a normalized LLMResponse.
    Used by both the OpenAI-compatible endpoint (`choices[0].message`) and the
    Ollama native endpoint (`message`), whose shapes are close but not identical:
    - OpenAI-compatible tool call arguments are a JSON-encoded string.
    - Ollama native tool call arguments are already a dict.
    """
    content = message.get("content") or ""
    raw_tool_calls = message.get("tool_calls") or []

    parsed_tool_calls = []
    for tc in raw_tool_calls:
        func = tc.get("function", {})
        args = func.get("arguments", "{}")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"raw_args": args}
        parsed_tool_calls.append({
            "id": tc.get("id", "call_0"),
            "name": func.get("name"),
            "arguments": args
        })

    # Check if LLM output raw JSON with an action inside content directly
    if not parsed_tool_calls and content.strip().startswith("{") and content.strip().endswith("}"):
        try:
            direct_json = json.loads(content.strip())
            if "action" in direct_json or "name" in direct_json:
                name = direct_json.get("action") or direct_json.get("name")
                args = direct_json.get("arguments") or direct_json.get("params") or direct_json
                parsed_tool_calls.append({
                    "id": "direct_json",
                    "name": name,
                    "arguments": args
                })
        except json.JSONDecodeError:
            pass

    return LLMResponse(
        content=content,
        tool_calls=parsed_tool_calls,
        raw_response=raw_response
    )

class BaseLLMProvider(ABC):
    """Abstract interface for pluggable LLM providers (Ollama, LM Studio, vLLM, etc.)"""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generates a structured LLM response given a conversation context and optional tools."""
        pass

