import logging
import httpx
from typing import Dict, Any, List, Optional
from .base import BaseLLMProvider, LLMResponse, parse_message_to_llm_response

logger = logging.getLogger("mmo_adapter.llm")

class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Standard OpenAI-compatible provider for local LLM engines:
    - Ollama (http://localhost:11434/v1)
    - LM Studio (http://localhost:1234/v1)
    - vLLM (http://localhost:8000/v1)
    - LocalAI / llama.cpp server
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "not-needed",
        model: str = "qwen2.5:7b",
        default_temperature: float = 0.7,
        default_max_tokens: int = 200,
        timeout_sec: float = 15.0,
        disable_thinking: bool = False
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.timeout = timeout_sec
        # Some Ollama builds accept "think": false on the OpenAI-compatible route too;
        # this is opt-in (default False) so LM Studio/vLLM/older Ollama, which ignore or
        # reject unknown fields, keep their current behaviour untouched.
        self.disable_thinking = disable_thinking

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"******"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
        }

        if self.disable_thinking:
            payload["think"] = False

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            return parse_message_to_llm_response(message, data)

        except httpx.ConnectError as e:
            logger.warning(f"Could not connect to local LLM server at {self.base_url}: {e}")
            return LLMResponse(
                content="[Local LLM offline or unreachable]",
                tool_calls=[],
                raw_response={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error during LLM request: {e}")
            return LLMResponse(
                content=f"[LLM error: {e}]",
                tool_calls=[],
                raw_response={"error": str(e)}
            )


class OllamaNativeProvider(BaseLLMProvider):
    """
    Provider for Ollama's native `/api/chat` endpoint.

    This exists because Ollama's OpenAI-compatible `/v1/chat/completions` route does not
    reliably expose a `think: false` control for "thinking" models (e.g. Qwen3.5-based
    models): the entire token budget can be consumed by the hidden reasoning trace, leaving
    `content` empty even at generous `max_tokens`. The native endpoint accepts `think: false`
    directly and returns the same model's real answer in `message.content` (see
    MMO_LLM_ADAPTER_MASTER_PLAN.md section 6.1 for the reproduction).

    Use this provider (config: `llm.provider: "ollama_native"`) for thinking-capable local
    models. Non-thinking models and other engines (LM Studio, vLLM, LocalAI) should keep
    using `OpenAICompatibleProvider` unchanged.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        default_temperature: float = 0.7,
        default_max_tokens: int = 200,
        timeout_sec: float = 15.0,
        think: bool = False
    ):
        # Accept either the bare host or an OpenAI-style "/v1" base_url so switching
        # `llm.provider` in config.yaml doesn't also require rewriting `base_url`.
        base_url = base_url.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[: -len("/v1")]
        self.base_url = base_url
        self.model = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.timeout = timeout_sec
        self.think = think

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": self.think,
            "options": {
                "temperature": temperature if temperature is not None else self.default_temperature,
                "num_predict": max_tokens if max_tokens is not None else self.default_max_tokens,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            message = data.get("message", {})
            return parse_message_to_llm_response(message, data)

        except httpx.ConnectError as e:
            logger.warning(f"Could not connect to local LLM server at {self.base_url}: {e}")
            return LLMResponse(
                content="[Local LLM offline or unreachable]",
                tool_calls=[],
                raw_response={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error during LLM request: {e}")
            return LLMResponse(
                content=f"[LLM error: {e}]",
                tool_calls=[],
                raw_response={"error": str(e)}
            )
