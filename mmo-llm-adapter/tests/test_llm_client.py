import json
import httpx
import pytest

from llm.client import OpenAICompatibleProvider, OllamaNativeProvider


def _mock_client_factory(monkeypatch, handler):
    """Patches httpx.AsyncClient so requests are answered by `handler` instead of a real server."""
    transport = httpx.MockTransport(handler)

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _PatchedAsyncClient)


@pytest.mark.asyncio
async def test_openai_compatible_parses_normal_content(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "choices": [{
                "message": {"content": "Selam kanka!", "tool_calls": []}
            }]
        })

    _mock_client_factory(monkeypatch, handler)
    provider = OpenAICompatibleProvider(model="qwen2.5:7b")
    result = await provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    assert result.content == "Selam kanka!"
    assert result.tool_calls == []


@pytest.mark.asyncio
async def test_openai_compatible_sends_think_false_when_enabled(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    _mock_client_factory(monkeypatch, handler)
    provider = OpenAICompatibleProvider(model="qwythos-9b:latest", disable_thinking=True)
    await provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    assert captured["payload"]["think"] is False


@pytest.mark.asyncio
async def test_openai_compatible_omits_think_by_default(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    _mock_client_factory(monkeypatch, handler)
    provider = OpenAICompatibleProvider(model="qwen2.5:7b")
    await provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    # Backward compatibility: LM Studio/vLLM/older Ollama must see the same payload shape
    # as before this feature was added.
    assert "think" not in captured["payload"]


@pytest.mark.asyncio
async def test_ollama_native_reproduces_thinking_model_bug_on_openai_route(monkeypatch):
    """
    Regression test for MMO_LLM_ADAPTER_MASTER_PLAN.md section 6.1: a thinking model
    burns its whole token budget on the hidden reasoning trace over the OpenAI-compatible
    route and leaves `content` empty. OllamaNativeProvider must return the real answer
    the native `/api/chat` + `think:false` request gets instead.
    """
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert payload["think"] is False
        return httpx.Response(200, json={
            "message": {
                "content": "Selam! Su an Kazankoyu civarinda dolasiyorum. Nereye ugrayacaksin?",
                "tool_calls": []
            },
            "done_reason": "stop",
            "eval_count": 42
        })

    _mock_client_factory(monkeypatch, handler)
    provider = OllamaNativeProvider(model="qwythos-9b:latest", think=False)
    result = await provider.generate_response(messages=[{"role": "user", "content": "Selam"}])

    assert result.content.startswith("Selam!")
    assert result.tool_calls == []


@pytest.mark.asyncio
async def test_ollama_native_accepts_v1_base_url(monkeypatch):
    """Config authors can keep the OpenAI-style base_url when switching providers."""
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"message": {"content": "ok"}})

    _mock_client_factory(monkeypatch, handler)
    provider = OllamaNativeProvider(base_url="http://localhost:11434/v1", model="qwythos-9b:latest")
    await provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    assert seen_urls == ["http://localhost:11434/api/chat"]


@pytest.mark.asyncio
async def test_ollama_native_parses_tool_calls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "function": {"name": "follow_player", "arguments": {"player_name": "ProGamer"}}
                }]
            }
        })

    _mock_client_factory(monkeypatch, handler)
    provider = OllamaNativeProvider(model="qwythos-9b:latest")
    result = await provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "follow_player"
    assert result.tool_calls[0]["arguments"] == {"player_name": "ProGamer"}


@pytest.mark.asyncio
async def test_connect_error_returns_offline_message_for_both_providers(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    _mock_client_factory(monkeypatch, handler)

    openai_provider = OpenAICompatibleProvider(model="qwen2.5:7b")
    native_provider = OllamaNativeProvider(model="qwythos-9b:latest")

    r1 = await openai_provider.generate_response(messages=[{"role": "user", "content": "hi"}])
    r2 = await native_provider.generate_response(messages=[{"role": "user", "content": "hi"}])

    assert "offline" in r1.content
    assert "offline" in r2.content
