import os
import sys
import yaml
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure adapter root is in Python path
ADAPTER_ROOT = os.path.dirname(os.path.abspath(__file__))
if ADAPTER_ROOT not in sys.path:
    sys.path.insert(0, ADAPTER_ROOT)

from llm.client import OpenAICompatibleProvider, OllamaNativeProvider
from llm.prompts import PromptManager
from core.bubble import AttentionBubbleManager
from bridges.metin2.connector import Metin2Bridge
from bridges.metin2.schemas import Metin2EventRequest, Metin2ActionResponse, BubbleSyncRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mmo_adapter")

# Load Configuration
CONFIG_PATH = os.path.join(ADAPTER_ROOT, "config.yaml")
LOCALES_PATH = os.path.join(ADAPTER_ROOT, "locales")

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"Config file not found at {CONFIG_PATH}, using defaults.")
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

config = load_config()
active_lang = config.get("language", "tr")

# Instantiate Services
prompt_mgr = PromptManager(locales_dir=LOCALES_PATH, default_lang=active_lang)

llm_cfg = config.get("llm", {})

def build_llm_provider(cfg: Dict[str, Any]):
    """
    Builds the configured LLM provider.
    - "openai_compatible" (default): works against Ollama/LM Studio/vLLM's
      `/v1/chat/completions`. Set `think: false` under `llm:` to opt a thinking
      model into the (unverified on all Ollama builds) OpenAI-route think flag.
    - "ollama_native": Ollama's own `/api/chat` with `think: false`, the confirmed
      fix for thinking models (e.g. Qwen3.5-based) returning empty content on the
      OpenAI-compatible route (see MMO_LLM_ADAPTER_MASTER_PLAN.md section 6.1).
    """
    provider = cfg.get("provider", "openai_compatible")

    if provider == "ollama_native":
        return OllamaNativeProvider(
            base_url=cfg.get("base_url", "http://localhost:11434/v1"),
            model=cfg.get("model", "qwen2.5:7b"),
            default_temperature=cfg.get("temperature", 0.7),
            default_max_tokens=cfg.get("max_tokens", 200),
            timeout_sec=cfg.get("timeout_sec", 15.0),
            think=cfg.get("think", False)
        )

    return OpenAICompatibleProvider(
        base_url=cfg.get("base_url", "http://localhost:11434/v1"),
        api_key=cfg.get("api_key", "not-needed"),
        model=cfg.get("model", "qwen2.5:7b"),
        default_temperature=cfg.get("temperature", 0.7),
        default_max_tokens=cfg.get("max_tokens", 200),
        timeout_sec=cfg.get("timeout_sec", 15.0),
        disable_thinking=cfg.get("disable_thinking", False)
    )

llm_client = build_llm_provider(llm_cfg)

bubble_cfg = config.get("attention_bubble", {})
bubble_mgr = AttentionBubbleManager(
    max_active_bots=bubble_cfg.get("max_active_bots", 50),
    bubble_radius=bubble_cfg.get("bubble_radius", 3500.0),
    ambient_cooldown_sec=bubble_cfg.get("ambient_cooldown_sec", 15.0)
)

handover_cfg = config.get("handover", {})
metin2_bridge = Metin2Bridge(
    prompt_manager=prompt_mgr,
    llm_provider=llm_client,
    bubble_manager=bubble_mgr,
    interaction_ttl_sec=handover_cfg.get("interaction_ttl_sec", 120.0),
    graceful_farewell=handover_cfg.get("graceful_farewell", True)
)

# Background Lease Sweeper
async def lease_sweeper_task():
    """Periodically checks bots for 120s TTL expiry and hands control back to PlayerBots."""
    while True:
        try:
            await asyncio.sleep(5.0)
            farewells = metin2_bridge.sweep_expired_leases()
            if farewells:
                for f in farewells:
                    logger.info(f"Lease expired for {f['bot_name']} (PID: {f['pid']}): Returned to PlayerBots.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in lease sweeper: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(lease_sweeper_task())
    logger.info("MMO LLM Adapter started successfully.")
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    logger.info("MMO LLM Adapter stopped.")

app = FastAPI(
    title="MMO LLM Adapter for PlayerBots",
    description="Decoupled cognitive layer providing local LLM intelligence to game bot systems.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "supported_game": metin2_bridge.get_supported_game(),
        "active_language": prompt_mgr.active_lang,
        "available_languages": list(prompt_mgr.locales.keys()),
        "llm_model": llm_client.model,
        "llm_endpoint": llm_client.base_url,
        "active_bubble_bots": len(bubble_mgr.active_bots),
        "tracked_agents": len(metin2_bridge.agents)
    }

class LanguageUpdateRequest(BaseModel):
    language: str

@app.post("/v1/config/language")
async def set_language(req: LanguageUpdateRequest):
    if req.language not in prompt_mgr.locales:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{req.language}' not available. Installed: {list(prompt_mgr.locales.keys())}"
        )
    prompt_mgr.set_language(req.language)
    logger.info(f"Active language changed to: {req.language}")
    return {"status": "ok", "active_language": prompt_mgr.active_lang}

@app.post("/v1/metin2/event", response_model=Metin2ActionResponse)
async def receive_metin2_event(req: Metin2EventRequest):
    """Receives game interaction events (whisper, say, party command) and returns bot actions."""
    try:
        response = await metin2_bridge.handle_game_event(req.model_dump())
        return response
    except Exception as e:
        logger.error(f"Failed to handle event for PID {req.bot_pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/metin2/bubble")
async def sync_attention_bubble(req: BubbleSyncRequest):
    """Updates the player's coordinate and selects the 30-50 nearest bots for active awareness."""
    active_pids = metin2_bridge.sync_bubble(req)
    return {
        "status": "ok",
        "active_pids_count": len(active_pids),
        "active_pids": active_pids
    }

@app.get("/v1/agents/{pid}/state")
async def get_agent_state(pid: int):
    """Inspects a bot's current cognitive state, lease status, and recent chat history."""
    if pid not in metin2_bridge.agents:
        raise HTTPException(status_code=404, detail=f"Bot PID {pid} not found in active memory.")
    agent = metin2_bridge.agents[pid]
    return {
        "pid": agent.profile.pid,
        "name": agent.profile.name,
        "control_state": agent.state.value,
        "is_leash_expired": agent.is_leash_expired(),
        "current_player": agent.current_interactive_player,
        "last_interaction": agent.last_interaction_time,
        "recent_chats": [c.model_dump() for c in agent.memory.chat_history]
    }

if __name__ == "__main__":
    import uvicorn
    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = server_cfg.get("port", 8080)
    logger.info(f"Starting MMO LLM Adapter on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)

