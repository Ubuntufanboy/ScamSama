from abc import ABC, abstractmethod
from neuro_api.api import NeuroAction
from typing import List, Optional


# This AbstractAction idea was taken from https://github.com/Kaya-Kaya/neuro-canvas
class AbstractAction(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def desc(self) -> str:
        pass

    @property
    def schema(self) -> Optional[dict]:
        return None

    def get_action(self) -> dict:
        """
        Returns a dict containing the name, description, and schema of the action.
        """
        return {
            "name": self.name,
            "description": self.desc,
            "schema": self.schema
        }

    @abstractmethod
    async def perform_action(self, actionData: NeuroAction) -> str:
        """
        Carries out the action.
        """
        pass

class MuteAction(AbstractAction):
    @property
    def name(self) -> str:
        return "mute"

    @property
    def desc(self) -> str:
        return "Mutes the Discord bot."

    @property
    def schema(self) -> Optional[dict]:
        return {
            "type": "object",
            "properties": {}
        }

    async def perform_action(self, actionData: NeuroAction) -> str:
        # Implement mute logic here
        return "Bot muted."

class UnmuteAction(AbstractAction):
    @property
    def name(self) -> str:
        return "unmute"

    @property
    def desc(self) -> str:
        return "Unmutes the Discord bot."

    @property
    def schema(self) -> Optional[dict]:
        return {
            "type": "object",
            "properties": {}
        }

    async def perform_action(self, actionData: NeuroAction) -> str:
        # Implement unmute logic here
        return "Bot unmuted."

# List of all actions
action_list: List[AbstractAction] = [
    MuteAction(),
    UnmuteAction(),
]