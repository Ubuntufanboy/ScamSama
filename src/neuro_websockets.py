"""Abstract Neuro API for Asyncio Websockets library."""

# Programmed by CoolCat467

from __future__ import annotations

from neuro_api.api import AbstractNeuroAPI
import websockets


class AbstractAsyncioWebsocketsNeuroAPI(AbstractNeuroAPI):
    """Abstract base class for the Neuro Game Interaction API.

    Provides a foundational interface for managing game actions and
    interactions with the Neuro system. This class is designed to be
    subclassed by specific game implementations.

    Attributes:
        game_title (str): The title or name of the game being integrated.
        _currently_registered (dict[str, tuple[str, dict[str, object] | None]]):
            Internal registry of currently registered actions, mapping
            action names to their details.
        websocket (websockets.ClientConnection): Websocket connection.

    Note:
        This is an abstract base class that requires implementation
        of specific game interaction methods in subclasses.

    """
    __slots__ = ("websocket",)

    def __init__(
        self,
        game_title: str,
        websocket: websockets.ClientConnection,
    ) -> None:
        """Initialize NeuroAPI.""" 
        super().__init__(game_title)
        self.websocket = websocket

    def is_websocket_closed(self) -> bool:
        """Return if websocket is closed."""
        # FIX: Use hasattr to safely check if 'closed' attribute exists
        # Some versions of websockets use different properties to check connection state
        return (
            (
                hasattr(self.websocket, "closed")
                and self.websocket.closed
            )
            or (
                hasattr(self.websocket, "state")
                and self.websocket.state == websockets.protocol.State.CLOSED
            )
        )

    async def read_from_websocket(self) -> bytes | bytearray | memoryview | str:
        """Return message read from websocket."""
        return await self.websocket.recv()

    async def write_to_websocket(self, data: str) -> None:
        """Write message to websocket."""
        if self.is_websocket_closed():
            logger.warning("Cannot write to websocket: Connection is closed")
            return
        await self.websocket.send(data)

    async def send_context(self, message: str, silent: bool = True) -> None:
        await super().send_context(message, silent)
        logger.info(f"✓✓✓ SENT CONTEXT TO TONY: {message[:200]}{'...' if len(message) > 200 else ''}")
