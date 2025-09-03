"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my
code! I hope you enjoy it!
"""

from __future__ import annotations

from queue import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext.voice_recv.voice_client import VoiceRecvClient

# These values are state values that change during the operation of the program.
voice_client: VoiceRecvClient | None = None
twilio_websocket = None
twilio_websocket_closed: bool = True
audio_queue: Queue[bytes] = Queue()
stream_sid: int = -1
ws_open: bool = False
call_running: bool = False
call_sid: int = -1
