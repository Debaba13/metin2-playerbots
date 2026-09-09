import pytest
from fastapi.testclient import TestClient
from main import app, metin2_bridge, prompt_mgr
from llm.base import BaseLLMProvider, LLMResponse

class FastMockLLM(BaseLLMProvider):
    async def generate_response(self, messages, tools=None, temperature=None, max_tokens=None):
        return LLMResponse(content="Tamamdir, geliyorum!", tool_calls=[])

@pytest.fixture(autouse=True)
def override_llm():
    # Substitute real LLM client with mock so tests run instantly and offline
    metin2_bridge.llm_provider = FastMockLLM()

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["supported_game"] == "Metin2"
    assert "tr" in data["available_languages"]

def test_language_switch_endpoint():
    res = client.post("/v1/config/language", json={"language": "en"})
    assert res.status_code == 200
    assert res.json()["active_language"] == "en"
    assert prompt_mgr.active_lang == "en"
    
    # Restore to Turkish
    client.post("/v1/config/language", json={"language": "tr"})

def test_metin2_whisper_event_endpoint():
    payload = {
        "event_type": "whisper",
        "bot_pid": 777,
        "player_name": "KralOyuncu",
        "message": "Selam, loncaya gelmek ister misin?",
        "bot_profile": {
            "name": "SeyisOglu",
            "job": "warrior",
            "level": 35
        }
    }
    res = client.post("/v1/metin2/event", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["pid"] == 777
    assert data["bot_name"] == "SeyisOglu"
    assert data["control_state"] == "llm_override"
    assert data["speech_reply"] == "Tamamdir, geliyorum!"

def test_bubble_sync_endpoint():
    payload = {
        "player_x": 1000,
        "player_y": 2000,
        "player_map": 21,
        "bots": [
            {"pid": 1, "name": "B1", "x": 1050, "y": 2050, "map_index": 21},
            {"pid": 2, "name": "B2", "x": 9000, "y": 9000, "map_index": 21}
        ]
    }
    res = client.post("/v1/metin2/bubble", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["active_pids_count"] == 1
    assert data["active_pids"] == [1]

