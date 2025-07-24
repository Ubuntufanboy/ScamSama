"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

import base64
import json
import audioop
from flask import Flask
from flask_sock import Sock
import state

# Flask works pretty well for this. Just make sure you are hosting the ngrok proxy as well for this to work properly
app = Flask(__name__)
sock = Sock(app)

@sock.route('/media')
def media(ws):
    state.ws_open = True
    state.twilio_websocket = ws
    print(">>> Twilio WebSocket connection established.")

    resample_state = None

    while state.ws_open:
        try:
            msg = ws.receive(timeout=10)
            if not msg:
                continue
            data = json.loads(msg)

            if data['event'] == 'start':
                state.stream_sid = data['start']['streamSid']
                print(f">>> Media stream started: {state.stream_sid}")

            elif data['event'] == 'media':
                audio_bytes = base64.b64decode(data['media']['payload'])
                pcm_8k_mono = audioop.ulaw2lin(audio_bytes, 2)

                pcm_48k_mono, resample_state = audioop.ratecv(
                    pcm_8k_mono, 2, 1, 8000, 48000, resample_state
                )

                pcm_48k_stereo = audioop.tostereo(pcm_48k_mono, 2, 1, 1)
                state.audio_queue.put(pcm_48k_stereo)

        except Exception as e:
            if "timed out" not in str(e).lower():
                print(f"WebSocket route error: {type(e).__name__}: {e}")
            break

    state.ws_open = False
    print(">>> Twilio WebSocket connection closed.")
    return ""
