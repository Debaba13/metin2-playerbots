import time
import logging
from typing import Dict, Any, Optional, List
from bridges.base import BaseGameBridge
from bridges.metin2.schemas import Metin2EventRequest, Metin2ActionResponse, BubbleSyncRequest
from core.agent import PlayerBotAgent, AgentProfile, AgentControlState
from core.bubble import AttentionBubbleManager
from llm.prompts import PromptManager
from llm.base import BaseLLMProvider

logger = logging.getLogger("mmo_adapter.metin2")

class Metin2Bridge(BaseGameBridge):
    """
    Bridge connecting Metin2 r40250 server (PlayerBots) to the cognitive LLM adapter.
    """

    def __init__(
        self,
        prompt_manager: PromptManager,
        llm_provider: BaseLLMProvider,
        bubble_manager: AttentionBubbleManager,
        interaction_ttl_sec: float = 120.0,
        graceful_farewell: bool = True
    ):
        self.prompt_manager = prompt_manager
        self.llm_provider = llm_provider
        self.bubble_manager = bubble_manager
        self.interaction_ttl_sec = interaction_ttl_sec
        self.graceful_farewell = graceful_farewell
        self.agents: Dict[int, PlayerBotAgent] = {}

    def get_supported_game(self) -> str:
        return "Metin2"

    def get_or_create_agent(self, pid: int, profile_data: Optional[Dict[str, Any]] = None) -> PlayerBotAgent:
        if pid not in self.agents:
            data = profile_data or {}
            profile = AgentProfile(
                pid=pid,
                name=data.get("name", f"PlayerBot_{pid}"),
                job=data.get("job", "warrior"),
                level=data.get("level", 30),
                map_name=data.get("map_name", "Bokjung"),
                map_index=data.get("map_index", 21),
                hp_percent=data.get("hp_percent", 100),
                current_activity=data.get("current_activity", "Kasilma"),
                in_party=data.get("in_party", False),
                party_leader=data.get("party_leader", None),
                stance=data.get("stance", "defensive"),
                personality=data.get("personality", ""),
                personality_id=data.get("personality_id", 0),
                backstory=data.get("backstory", ""),
                speech_quirks=data.get("speech_quirks", ""),
                typo_rate=data.get("typo_rate", 0.0),
            )
            self.agents[pid] = PlayerBotAgent(
                profile=profile,
                interaction_ttl_sec=self.interaction_ttl_sec,
                graceful_farewell=self.graceful_farewell
            )
        elif profile_data:
            # Update existing profile
            for k, v in profile_data.items():
                if hasattr(self.agents[pid].profile, k):
                    setattr(self.agents[pid].profile, k, v)

        return self.agents[pid]

    def sync_bubble(self, req: BubbleSyncRequest) -> List[int]:
        """Syncs the 30-50 nearest bots around the human player."""
        return self.bubble_manager.update_player_proximity(
            player_x=req.player_x,
            player_y=req.player_y,
            player_map=req.player_map,
            all_bots=req.bots
        )

    def sweep_expired_leases(self) -> List[Dict[str, Any]]:
        """
        Sweeps all agents and checks for 120s TTL expiration.
        Returns any farewell actions needed to inform players that the bot has returned to routine.
        """
        farewell_actions = []
        for pid, agent in self.agents.items():
            result = agent.check_and_apply_ttl(self.prompt_manager)
            if result:
                result["pid"] = pid
                result["bot_name"] = agent.profile.name
                farewell_actions.append(result)
        return farewell_actions

    async def handle_game_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        req = Metin2EventRequest.model_validate(event_data)
        agent = self.get_or_create_agent(req.bot_pid, req.bot_profile)

        channel = "whisper" if req.event_type == "whisper" else "say"

        # Ambient rate limiter check for nearby say events
        if req.event_type == "say":
            if not self.bubble_manager.can_react_ambiently(req.bot_pid):
                return Metin2ActionResponse(
                    pid=agent.profile.pid,
                    bot_name=agent.profile.name,
                    control_state=agent.state.value,
                    status="ignored_cooldown"
                ).model_dump()

        # Execute cognitive interaction
        result = await agent.interact(
            player_name=req.player_name,
            content=req.message or "",
            channel=channel,
            prompt_manager=self.prompt_manager,
            llm_provider=self.llm_provider
        )

        response = Metin2ActionResponse(
            pid=agent.profile.pid,
            bot_name=agent.profile.name,
            control_state=result.get("control_state", agent.state.value),
            primary_action=result.get("primary_action"),
            arguments=result.get("arguments", {}),
            speech_reply=result.get("speech_reply"),
            status="ok"
        )
        return response.model_dump()
