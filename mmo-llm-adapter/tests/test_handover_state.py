import time
import pytest
from core.agent import PlayerBotAgent, AgentProfile, AgentControlState
from llm.prompts import PromptManager
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")

def test_initial_state_is_autonomous():
    profile = AgentProfile(pid=501, name="MetinFarmer")
    agent = PlayerBotAgent(profile=profile, interaction_ttl_sec=2.0)
    assert agent.state == AgentControlState.AUTONOMOUS
    assert agent.is_leash_expired() is False

def test_touch_interaction_switches_to_llm_override():
    profile = AgentProfile(pid=501, name="MetinFarmer")
    agent = PlayerBotAgent(profile=profile, interaction_ttl_sec=2.0)
    
    agent.touch_interaction("WarriorKing")
    assert agent.state == AgentControlState.LLM_OVERRIDE
    assert agent.current_interactive_player == "WarriorKing"
    assert agent.is_leash_expired() is False

def test_ttl_expiry_returns_to_autonomous():
    profile = AgentProfile(pid=501, name="MetinFarmer")
    pm = PromptManager(locales_dir=LOCALES_DIR, default_lang="tr")
    # Short TTL of 0.2s for testing
    agent = PlayerBotAgent(profile=profile, interaction_ttl_sec=0.2)
    
    agent.touch_interaction("WarriorKing")
    assert agent.state == AgentControlState.LLM_OVERRIDE
    
    # Wait for TTL to expire
    time.sleep(0.3)
    assert agent.is_leash_expired() is True
    
    farewell = agent.check_and_apply_ttl(pm)
    assert agent.state == AgentControlState.AUTONOMOUS
    assert farewell is not None
    assert farewell["action"] == "whisper"
    assert farewell["target_player"] == "WarriorKing"
    assert farewell["reason"] == "lease_expired"

def test_party_membership_prevents_ttl_expiration():
    profile = AgentProfile(pid=501, name="MetinFarmer", in_party=True, party_leader="WarriorKing")
    agent = PlayerBotAgent(profile=profile, interaction_ttl_sec=0.2)
    
    agent.touch_interaction("WarriorKing")
    time.sleep(0.3)
    
    # Still engaged because in party with the player
    assert agent.is_leash_expired() is False

