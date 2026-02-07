"""
ScamSama v1.0.8 - Neuro API WebSocket Client Integration with Guaranteed Context Updates
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

from __future__ import annotations

#########################################################
###                README. Seriously...               ###
### DO NOT RUN THIS IN NEUROCORD OR ANY PUBLIC SERVER ###
#########################################################

import asyncio
import base64
import json
import audioop
import logging
import traceback
import uuid
from typing import Any, TYPE_CHECKING

from scam_sama import state
from scam_sama import config
from scam_sama.twilio_integration import twilio_client
from scam_sama.neuro_websockets import AbstractAsyncioWebsocketsNeuroAPI

# Import websockets library for Neuro API communication
import websockets
import discord
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink
from neuro_api.command import Action
from neuro_api.api import NeuroAction

if TYPE_CHECKING:
    import queue

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=(
        logging.FileHandler("scamsama.log"),
        logging.StreamHandler()
    )
)
logger = logging.getLogger("ScamSama")

is_muted_outbound = False
# Track the channel where we should send status messages
command_channel = None
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = discord.Client(intents=intents)


class TwilioAudioSource(discord.AudioSource):
    """Audio source that pulls data from a queue for sending to Twilio."""
    def __init__(self, queue: queue.Queue[bytes]) -> None:
        self.queue = queue

    def read(self) -> bytes:
        return self.queue.get()


class TwilioSink(AudioSink):
    """Audio sink that processes incoming voice data and sends it to Twilio."""
    def __init__(self) -> None:
        self.resample_state = None
        # Precompute silence packets for both codecs (160 bytes = 20ms @ 8kHz)
        self.silence_ulaw = b'\xFF' * 160  # ULAW silence value
        self.silence_alaw = b'\xD5' * 160  # ALAW silence value
        super().__init__()
        self.is_closed = False

    def wants_opus(self) -> bool:
        return False

    def write(self, user, voice_data) -> None:
        """Process incoming voice data and send it to Twilio."""
        global is_muted_outbound
        if self.is_closed or not state.ws_open or not state.twilio_websocket:
            return

        try:
            # MUTE HANDLING: Send precomputed silence when muted
            if is_muted_outbound:
                payload = base64.b64encode(
                    self.silence_ulaw if config.COUNTRY_CODE in ("US", "JP")
                    else self.silence_alaw
                ).decode('utf-8')
                state.twilio_websocket.send(json.dumps({
                    "event": "media",
                    "streamSid": state.stream_sid,
                    "media": {"payload": payload}
                }))
                return

            # Normal processing when not muted
            mono_48k = audioop.tomono(voice_data.pcm, 2, 1, 1)
            pcm_8k, self.resample_state = audioop.ratecv(
                mono_48k, 2, 1, 48000, 8000, self.resample_state
            )
            transcoded = audioop.lin2ulaw(pcm_8k, 2) if config.COUNTRY_CODE in ["US", "JP"] \
                         else audioop.lin2alaw(pcm_8k, 2)

            payload = base64.b64encode(transcoded).decode('utf-8')
            state.twilio_websocket.send(json.dumps({
                "event": "media",
                "streamSid": state.stream_sid,
                "media": {"payload": payload}
            }))
        except Exception as e:
            logger.error(f"Error in TwilioSink.write: {e}")
            logger.debug(traceback.format_exc())

    def cleanup(self) -> None:
        logger.info("TwilioSink cleanup done.")
        self.is_closed = True

    def on_websocket_closed(self, code: int, reason: str) -> None:
        """Handle Twilio WebSocket closure immediately."""
        logger.warning(f"Twilio WebSocket closed with code {code}: {reason}")
        self.is_closed = True

        # Set a flag to trigger immediate status check
        state.twilio_websocket_closed = True

        # Handle WebSocket closure
        if state.call_running:
            logger.info("Handling WebSocket closure during active call")
            # Use the bot loop to schedule the handling
            bot.loop.create_task(handle_twilio_websocket_closure(code, reason))


class ScamSamaNeuroAPI(AbstractAsyncioWebsocketsNeuroAPI):
    __slots__ = ()

    def __init__(self, websocket: websockets.ClientConnection) -> None:
        super().__init__("ScamSama", websocket)

    async def setup(self) -> None:
        """Handle setup."""
        # 1. Send startup message (must be first)
        await self.send_startup_command()
        logger.info("✓ Sent startup message to Tony")

        # 2. Register available actions
        actions = [
            Action(
                "mute",
                "Mutes the outbound audio (so the victim can't hear you)",
            ),
            Action(
                "unmute",
                "Unmutes the outbound audio",
            ),
            Action(
                "join",
                "Initiates a call to the target phone number",
            ),
            Action(
                "hangup",
                "Ends the current call",
            ),
        ]

        await self.register_actions(actions)
        logger.info(f"✓ Registered {len(actions)} actions with Tony")

    async def handle_action(self, action: NeuroAction) -> None:
        """Handle an Action from Neuro."""
        # Data is JSON-stringified, so we need to parse it
        action_params = json.loads(action.data) if action.data is not None else {}

        logger.info(f"→ Received action request: {action.name} (ID: {action.id_})")

        success = True
        message: str | None = None

        # Execute the action
        if action.name == "mute":
            success, message = await self.handle_mute_action()
        elif action.name == "unmute":
            success, message = await self.handle_unmute_action()
        elif action.name == "join":
            success, message = await self.handle_join_action()
        elif action.name == "hangup":
            success, message = await self.handle_hangup_action()
        else:
            logger.warning(f"Unknown action received: {action.name}")
            message = f"Unknown action: {action.name}"

        # 4. Send action result back to Tony
        await self.send_action_result(action.id_, success, message)
        logger.info(f"← Sent action result for {action.name}: success={success}")

    # Neuro API Action Handlers
    # These functions implement the same functionality as the former Discord commands
    # but are now triggered by WebSocket messages instead of Discord messages
    # Each returns a tuple: (success: bool, message: str)

    async def handle_mute_action(self) -> tuple[bool, str]:
        """Handles the 'mute' Neuro API action."""
        global is_muted_outbound
        is_muted_outbound = True
        logger.info("Outbound audio muted")
        await send_status_message("Muted!")

        # Send context to Tony about the mute action
        await self.send_context("I have muted the outbound audio. The scammer cannot hear me now.")

        return True, "Successfully muted"

    async def handle_unmute_action(self) -> tuple[bool, str]:
        """Handles the 'unmute' Neuro API action."""
        global is_muted_outbound
        is_muted_outbound = False
        logger.info("Outbound audio unmuted")
        await send_status_message("Unmuted!")

        # Send context to Tony about the unmute action
        await self.send_context("I have unmuted the outbound audio. The scammer can now hear me.")

        return True, "Successfully unmuted"

    async def handle_join_action(self) -> tuple[bool, str]:
        """Handles the 'join' Neuro API action (initiates a call)."""
        logger.info("Processing 'join' action to initiate call")

        # First, make sure we're not already in a call
        if state.call_running:
            warning_msg = "Already in a call. Please hang up first."
            logger.warning(warning_msg)
            await send_status_message(warning_msg)

            # Send context to Tony
            await self.send_context(
                "I'm already in a call. You need to hang up before initiating a new call.",
                silent=False
            )

            return False, warning_msg

        # Make sure we're not already connected to a voice channel
        if state.voice_client and state.voice_client.is_connected():
            logger.info("Already connected to voice channel, disconnecting first...")
            await cleanup_voice_connection()

        # Find a voice channel to join (first available in the first guild)
        if len(bot.guilds) == 0:
            error_msg = "Error: Bot is not in any guilds"
            logger.error(error_msg)
            await send_status_message(error_msg)
            return False, error_msg

        guild = bot.guilds[0]
        voice_channel = next((c for c in guild.channels if isinstance(c, discord.VoiceChannel)), None)

        if not voice_channel:
            error_msg = "Error: No voice channels available"
            logger.error(error_msg)
            await send_status_message(error_msg)
            return False, error_msg

        try:
            logger.info(f"Connecting to voice channel: {voice_channel.name}")
            await asyncio.sleep(1)  # Add a small delay
            state.voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
            await send_status_message(f'Joined {voice_channel.name}')
        except discord.errors.ClientException as e:
            error_msg = f"Error connecting to voice channel: {e}"
            logger.error(error_msg)
            await send_status_message(error_msg)
            state.voice_client = None
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error while connecting to voice: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            await send_status_message(error_msg)
            state.voice_client = None
            return False, error_msg

        try:
            loop = asyncio.get_running_loop()
            state.call_running = True
            ngrok_base_url = config.NGROK_BASE_URL
            assert ngrok_base_url is not None
            call = await loop.run_in_executor(
                None,
                lambda: twilio_client.calls.create(
                    to=config.YOUR_NUMBER_TO_CALL,
                    from_=config.YOUR_TWILIO_PHONE_NUMBER,
                    twiml=f'<Response><Connect><Stream url="{ngrok_base_url.replace("https", "wss")}/media"/></Connect></Response>',
                    status_callback=f'{ngrok_base_url}/call-status',
                    status_callback_method='POST',
                    status_callback_event=('completed', 'no-answer', 'canceled', 'failed', 'busy'),
                )
            )
            logger.info(f"✓ Call initiated with SID: {call.sid}")
            await send_status_message(f"Call SID: `{call.sid}`")

            # Store the call SID for monitoring
            state.call_sid = call.sid

            # Clear any pending audio
            while not state.audio_queue.empty():
                state.audio_queue.get_nowait()

            # Start listening and playing
            assert state.voice_client is not None
            state.voice_client.listen(TwilioSink())
            state.voice_client.play(TwilioAudioSource(state.audio_queue),
                                   after=lambda e: logger.error(f'Player error: {e}') if e else None)

            # Send context to Tony that we've initiated a call
            await self.send_context(
                "I've successfully initiated a call to the scammer. "
                "We are now connected and I'm listening to the call. "
                "Please provide guidance on how to proceed.",
                silent=False
            )

            return True, f"Call initiated with SID: {call.sid}"

        except Exception as e:
            error_msg = f"Error making call: {e}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            await send_status_message(error_msg)

            # Clean up voice connection on call failure
            await cleanup_voice_connection()

            # Send context to Tony about the error
            await self.send_context(
                f"Failed to initiate call: {str(e)}. I've disconnected from the voice channel to prevent errors.",
                silent=False
            )

            return False, error_msg

    async def handle_hangup_action(self) -> tuple[bool, str]:
        """Handles the 'hangup' Neuro API action (ends the call)."""
        logger.info("Processing 'hangup' action to end call")

        # If we're not in a call, just return
        if not state.call_running:
            warning_msg = "Not currently in a call"
            logger.warning(warning_msg)
            await send_status_message(warning_msg)

            # Send context to Tony
            await self.send_context(
                "I'm not currently in a call, so there's nothing to hang up.",
                silent=False
            )

            return False, warning_msg

        # Clean up the voice connection
        await cleanup_voice_connection()

        # Send context to Tony that we've hung up
        await self.send_context(
            "I've ended the call as requested. We are no longer connected to the scammer.",
            silent=False
        )

        return True, "Successfully hung up"


# Global reference to the current Tony websocket connection
tony_api: ScamSamaNeuroAPI | None = None


def get_tony_api() -> ScamSamaNeuroAPI | None:
    """Return the current Tony websocket connection if available."""
    global tony_api
    return tony_api


async def send_context_to_tony(message: str, silent: bool=False) -> bool:
    """
    Sends a context message to the Tony server.

    This function now properly checks if the connection is available before sending.
    """
    api = get_tony_api()

    if api is None or api.is_websocket_closed():
        logger.warning("Cannot send context: No active Tony connection or connection is closed")
        return False

    try:
        await api.send_context(message, silent)
        return True
    except websockets.ConnectionClosed as e:
        logger.error(f"Tony connection closed while sending context: {e}")
        # Clear the reference since the connection is closed
        set_tony_api(None)
        return False
    except Exception as e:
        logger.error(f"Failed to send context to Tony: {e}", exc_info=True)
        return False


def set_tony_api(api: ScamSamaNeuroAPI | None) -> None:
    """Sets the global Tony websocket connection reference."""
    global tony_api
    tony_api = api
    if api:
        logger.info("Tony websocket connection established")
    else:
        logger.info("Tony websocket connection cleared")


async def cleanup_voice_connection() -> None:
    """Safely cleans up the voice connection and resets state."""
    logger.info("Cleaning up voice connection...")

    try:
        # Stop listening and playing
        if state.voice_client:
            if state.voice_client.is_listening():
                state.voice_client.stop_listening()
            if state.voice_client.is_playing():
                state.voice_client.stop()

            # Disconnect from voice channel
            if state.voice_client.is_connected():
                await state.voice_client.disconnect()
                logger.info("Disconnected from voice channel")

            state.voice_client = None
    except Exception as e:
        logger.error(f"Error during voice connection cleanup: {e}", exc_info=True)

    # Reset call state
    state.call_running = False
    if hasattr(state, 'call_sid'):
        logger.info(f"Clearing call SID: {state.call_sid}")
        del state.call_sid


async def handle_twilio_websocket_closure(code: int, reason: str) -> None:
    """
    Handles Twilio WebSocket closure immediately.

    This function no longer sends context updates directly - that's handled
    by the status monitor which has the actual call status from Twilio API.
    """
    logger.info(f"Handling Twilio WebSocket closure (code {code}): {reason}")

    # Clean up voice connection
    await cleanup_voice_connection()


async def monitor_call_status() -> None:
    """Periodically checks if the call has ended and handles disconnects."""
    await bot.wait_until_ready()
    logger.info("Call status monitoring task started")

    # Initialize the flag if it doesn't exist
    if not hasattr(state, 'twilio_websocket_closed'):
        state.twilio_websocket_closed = False

    while not bot.is_closed():
        # Check if we need to check immediately due to WebSocket closure
        if state.twilio_websocket_closed:
            state.twilio_websocket_closed = False
            immediate_check = True
        else:
            immediate_check = False
            await asyncio.sleep(1)  # Check every 1 second for more responsiveness

        # Only monitor if we have a call SID
        if hasattr(state, 'call_sid') and state.call_sid:
            try:
                # Get current call status from Twilio
                call = twilio_client.calls(state.call_sid).fetch()
                logger.debug(f"Current call status: {call.status}")

                # Check for terminal statuses
                terminal_statuses = ["completed", "no-answer", "canceled", "failed", "busy"]
                if call.status in terminal_statuses:
                    status_messages = {
                        "completed": "Call ended normally (scammer hung up)",
                        "no-answer": "Scammer did not pick up the phone",
                        "canceled": "Call was canceled (scammer didn't pick up)",
                        "failed": "Call failed to connect",
                        "busy": "Scammer's line was busy"
                    }

                    status_msg = status_messages.get(call.status, f"Call ended with status: {call.status}")
                    logger.info(f"CALL ENDED (MONITOR): {status_msg}")

                    # Send context to Tony server about the disconnect
                    await send_context_to_tony(
                        f"Call ended: {status_msg}. "
                        "I've detected the call has ended and disconnected from the voice channel.",
                        silent=False
                    )

                    # Send message to Discord
                    await send_status_message(f"⚠️ {status_msg}")

                    # Clean up voice connection
                    await cleanup_voice_connection()

            except Exception as e:
                logger.error(f"Error checking call status: {e}", exc_info=True)
                # Clean up on error
                await cleanup_voice_connection()
                await send_context_to_tony(
                    f"Error monitoring call status: {str(e)}. "
                    "I've disconnected from the voice channel to prevent errors.",
                    silent=False
                )

        if not immediate_check:
            await asyncio.sleep(0.5)  # Wait before next check


@bot.event
async def on_ready() -> None:
    """Handler for when bot is ready and connected to Discord."""
    logger.info(f"Logged in as {bot.user}")
    bot.loop.create_task(check_voice_channel())
    bot.loop.create_task(monitor_call_status())  # Start call status monitoring
    # Start the Neuro API WebSocket client connection
    bot.loop.create_task(connect_to_tony())


# ADDED THIS MISSING FUNCTION - THIS WAS CAUSING THE ERROR
async def check_voice_channel() -> None:
    """Check if we need to join a voice channel or maintain connection."""
    await bot.wait_until_ready()
    logger.info("Voice channel monitoring task started")

    while not bot.is_closed():
        try:
            # Check if we're supposed to be in a call but not connected to voice
            if state.call_running and (not state.voice_client or not state.voice_client.is_connected()):
                logger.warning("Call running but not connected to voice channel. Attempting to reconnect...")

                # Find a voice channel to join (first available in the first guild)
                if len(bot.guilds) == 0:
                    logger.error("Cannot reconnect: Bot is not in any guilds")
                    await send_status_message("Error: Bot is not in any guilds")
                    await cleanup_voice_connection()
                    continue

                guild = bot.guilds[0]
                voice_channel = next((c for c in guild.channels if isinstance(c, discord.VoiceChannel)), None)

                if not voice_channel:
                    logger.error("Cannot reconnect: No voice channels available")
                    await send_status_message("Error: No voice channels available")
                    await cleanup_voice_connection()
                    continue

                try:
                    logger.info(f"Reconnecting to voice channel: {voice_channel.name}")
                    state.voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
                    # Restart audio processing
                    state.voice_client.listen(TwilioSink())
                    state.voice_client.play(TwilioAudioSource(state.audio_queue),
                                         after=lambda e: logger.error(f'Player error: {e}') if e else None)
                except Exception as e:
                    logger.error(f"Failed to reconnect to voice channel: {e}")
                    await send_status_message(f"Error reconnecting to voice: {str(e)}")

            # Check if we're connected to voice but not supposed to be in a call
            elif not state.call_running and state.voice_client and state.voice_client.is_connected():
                logger.info("Connected to voice channel but not in a call. Disconnecting...")
                await cleanup_voice_connection()

        except Exception as e:
            logger.error(f"Error in voice channel monitoring: {e}", exc_info=True)

        await asyncio.sleep(5)  # Check every 5 seconds


NEURO_API_LOCK = asyncio.Lock()


async def connect_to_tony() -> None:
    """
    Connects to the Tony server as a Neuro API client.

    Implements the Neuro API specification:
    1. Sends 'startup' message first
    2. Registers actions with 'actions/register'
    3. Listens for 'action' messages from server
    4. Executes actions and sends 'action/result' responses
    """
    if NEURO_API_LOCK.locked():
        logger.warning("Attempted to start neuro-api websocket handler when one is already running")
        return

    async with NEURO_API_LOCK:
        await bot.wait_until_ready()
        tony_url = "ws://localhost:8000"  # URL of the Tony server

        while not bot.is_closed():  # Auto-reconnect loop
            try:
                logger.info(f"Attempting to connect to Tony server at {tony_url}...")
                websocket = await websockets.connect(tony_url)
                api = ScamSamaNeuroAPI(websocket)

                # Set the global reference to this connection
                set_tony_api(api)
                logger.info(f"✓ Connected to Tony server at {tony_url}")

                await api.setup()

                # Main message handling loop
                while True:
                    try:
                        await api.read_message()
                    except websockets.ConnectionClosed:
                        logger.info("Tony server connection closed")
                        set_tony_api(None)
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"❌ Connection to Tony failed: {e}", exc_info=True)
                logger.info("Reconnecting to Tony in 5 seconds...")
                set_tony_api(None)
                await asyncio.sleep(5)


async def send_status_message(message: str) -> None:
    """
    Sends a status message to the command channel.

    Since Neuro API commands don't have a direct Discord message context,
    we send status updates to a designated channel (the first text channel
    in the guild where the bot is a member).
    """
    global command_channel

    # If we don't have a command channel yet, find one
    if command_channel is None and len(bot.guilds) > 0:
        guild = bot.guilds[0]
        # Find the first text channel we can send messages to
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                command_channel = channel
                logger.info(f"Using {channel.name} as command status channel")
                break

    if command_channel:
        try:
            await command_channel.send(message)
        except Exception as e:
            logger.error(f"Failed to send status message: {e}")
    else:
        logger.warning("No command channel available to send status message")


def run() -> None:
    logger.info("Starting ScamSama Discord bot with Neuro API client integration")
    token = config.DISCORD_BOT_TOKEN
    assert token is not None, "Need DISCORD_BOT_TOKEN to be set"
    bot.run(token)

# Start the bot
if __name__ == "__main__":
    run()
