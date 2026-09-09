from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseGameBridge(ABC):
    """
    Abstract interface for MMO game server bridges.
    Metin2 implementation connects r40250 PlayerBots;
    future implementations can connect WoW TrinityCore, L2J, etc.
    """

    @abstractmethod
    async def handle_game_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Receives a raw game event, routes to agent runtime, and returns actions."""
        pass

    @abstractmethod
    def get_supported_game(self) -> str:
        """Returns the game name identifier."""
        pass

