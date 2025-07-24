"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

from queue import Queue

# These values are state values that change during the operation of the program.
voice_client = None
twilio_websocket = None
audio_queue = Queue()
stream_sid = None
ws_open = False
