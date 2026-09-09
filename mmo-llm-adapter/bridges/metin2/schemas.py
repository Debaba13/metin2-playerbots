from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class Metin2EventRequest(BaseModel):
    event_type: str                         # "whisper", "say", "party_invite", "party_command", "trade"
    bot_pid: int
    player_name: str
    message: Optional[str] = None
    bot_profile: Optional[Dict[str, Any]] = None
    world_context: Optional[Dict[str, Any]] = None

class BubbleSyncRequest(BaseModel):
    player_x: int
    player_y: int
    player_map: int
    bots: List[Dict[str, Any]]              # [{pid: 101, name: "Bot1", x: 100, y: 200, map_index: 21}, ...]

class Metin2ActionResponse(BaseModel):
    pid: int
    bot_name: str
    control_state: str                      # "autonomous", "llm_override", "resuming"
    primary_action: Optional[str] = None    # "whisper", "say", "follow_player", "attack_target", etc.
    arguments: Dict[str, Any] = Field(default_factory=dict)
    speech_reply: Optional[str] = None
    status: str = "ok"

