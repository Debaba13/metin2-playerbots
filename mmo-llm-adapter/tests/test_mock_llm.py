import os
import pytest
from typing import List, Dict, Any, Optional

from core.agent import PlayerBotAgent, AgentProfile, AgentControlState
from llm.base import BaseLLMProvider, LLMResponse
from llm.prompts import PromptManager
from core.text import clean_model_reply

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")

class MockToolCallingLLM(BaseLLMProvider):
    def __init__(self, tool_name: str, tool_args: Dict[str, Any]):
        self.tool_name = tool_name
        self.tool_args = tool_args

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        return LLMResponse(
            content="",
            tool_calls=[{
                "id": "call_123",
                "name": self.tool_name,
                "arguments": self.tool_args
            }]
        )

@pytest.mark.asyncio
async def test_agent_tool_calling_follow():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    mock_llm = MockToolCallingLLM(
        tool_name="follow_player",
        tool_args={"player_name": "ProGamer"}
    )
    
    profile = AgentProfile(pid=101, name="SadikDost")
    agent = PlayerBotAgent(profile=profile)
    
    action = await agent.interact(
        player_name="ProGamer",
        content="Beni takip et, Vadiye gidiyoruz.",
        channel="whisper",
        prompt_manager=pm,
        llm_provider=mock_llm
    )
    
    assert action["pid"] == 101
    assert action["primary_action"] == "follow_player"
    assert action["arguments"]["player_name"] == "ProGamer"
    assert agent.state == AgentControlState.LLM_OVERRIDE

@pytest.mark.asyncio
async def test_agent_tool_calling_return_to_routine():
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    mock_llm = MockToolCallingLLM(
        tool_name="return_to_routine",
        tool_args={"farewell_message": "Ben slot kasmaya donuyorum."}
    )
    
    profile = AgentProfile(pid=102, name="YalnizKurt")
    agent = PlayerBotAgent(profile=profile)
    
    action = await agent.interact(
        player_name="ProGamer",
        content="Gorusuruz kanka",
        channel="whisper",
        prompt_manager=pm,
        llm_provider=mock_llm
    )
    
    assert action["primary_action"] == "return_to_routine"
    assert action["speech_reply"] == "Ben slot kasmaya donuyorum."
    # State transitions back to autonomous immediately on explicit farewell
    assert agent.state == AgentControlState.AUTONOMOUS


def test_agent_removes_reasoning_leak_and_limits_chat_reply():
    assert clean_model_reply(
        "<think>translate this</think> Assistant: Selam! Naber? Ucuncu cumle."
    ) == "Selam! Naber?"
