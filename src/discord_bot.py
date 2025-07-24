"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

#########################################################
###                README. Seriously...               ###
### DO NOT RUN THIS IN NEUROCORD OR ANY PUBLIC SERVER ###
###         CHANGE MULAW TO ALAW IF IN EUROPE.        ###
#########################################################

import asyncio
import base64
import json
import audioop
import discord
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink
import state
import config
from twilio_integration import twilio_client

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = discord.Client(intents=intents)

class TwilioAudioSource(discord.AudioSource):
    def __init__(self, queue):
        self.queue = queue

    def read(self):
        return self.queue.get()

class TwilioSink(AudioSink):
    def __init__(self):
        self.resample_state = None
        super().__init__()

    def wants_opus(self) -> bool:
        return False # Required function to start a call. It's annoying but required

    def write(self, user, voice_data):
        if not state.ws_open or not state.twilio_websocket:
            return
        try:
            mono_48k = audioop.tomono(voice_data.pcm, 2, 1, 1)

            pcm_8k, self.resample_state = audioop.ratecv(
                mono_48k, 2, 1, 48000, 8000, self.resample_state
            )
            if config.COUNTRY_CODE in ["US", "JP"]:
                transcoded = audioop.lin2ulaw(pcm_8k, 2)
            else:
                transcoded = audioop.lin2alaw(pcm_8k, 2)

            payload = base64.b64encode(transcoded).decode('utf-8')
            state.twilio_websocket.send(json.dumps({
                "event": "media",
                "streamSid": state.stream_sid,
                "media": {"payload": payload}
            }))
        except Exception as e:
            print(f"Error in TwilioSink.write: {e}")

    def cleanup(self):
        print("TwilioSink cleanup done.")

async def check_voice_channel():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(10)
        if state.voice_client and state.voice_client.is_connected():
            if len(state.voice_client.channel.members) == 1:
                try:
                    await state.voice_client.disconnect()
                finally:
                    state.voice_client = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(check_voice_channel())

@bot.event
async def on_message(message):
    # For implementation I strongly suggest Vedal whitelists himself for this command. It could cause issues. For testing purposes all users can run the command
    if message.author == bot.user:
        return

    if message.content.startswith('!callme'):
        if not message.author.voice:
            await message.channel.send('You must be in a voice channel.')
            return

        channel = message.author.voice.channel

        if state.voice_client and state.voice_client.is_connected():
            await state.voice_client.move_to(channel)
        else:
            try:
                await asyncio.sleep(1) # Add a small delay
                state.voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
            except discord.errors.ClientException as e:
                await message.channel.send(f"Error connecting to voice channel: {e}")
                state.voice_client = None
                return
            except Exception as e:
                await message.channel.send(f"An unexpected error occurred while connecting to voice: {e}")
                state.voice_client = None
                return

        await message.channel.send(f'Joined {channel.name}, calling given phone number...')

        try:
            loop = asyncio.get_running_loop()
            state.call_running = True
            call = await loop.run_in_executor(
                None,
                lambda: twilio_client.calls.create(
                    to=config.YOUR_NUMBER_TO_CALL,
                    from_=config.YOUR_TWILIO_PHONE_NUMBER,
                    twiml=f'<Response><Connect><Stream url="{config.NGROK_BASE_URL.replace("https", "wss")}/media"/></Connect></Response>',
                    status_callback=f'{config.NGROK_BASE_URL}/call-status',
                    status_callback_method='POST',
                    status_callback_event=['completed', 'no-answer'],
                )
            )
            await message.channel.send(f"Call SID: `{call.sid}`")
        except Exception as e:
            await message.channel.send(f"Error making call: {e}")
            if state.voice_client:
                await state.voice_client.disconnect()
            return

        while not state.audio_queue.empty():
            state.audio_queue.get_nowait()

        state.voice_client.listen(TwilioSink())
        state.voice_client.play(TwilioAudioSource(state.audio_queue), after=lambda e: print(f'Player error: {e}') if e else None)

        while state.call_running and state.voice_client and state.voice_client.is_connected():
            await asyncio.sleep(1)

        if state.voice_client and state.voice_client.is_connected():
            if not state.call_running:
                # Need to check the status from the Twilio API
                call = twilio_client.calls(call.sid).fetch()
                if call.status == 'no-answer':
                    await message.channel.send("The phone number did not pick up.")
                else:
                    await message.channel.send("The client has disconnected the call.")
            state.voice_client.stop_listening()
            state.voice_client.stop()
            await asyncio.sleep(0.5)
            await state.voice_client.disconnect()
            state.voice_client = None

    elif message.content.startswith('!hangup'):
        if state.voice_client and state.voice_client.is_connected():
            try:
                state.voice_client.stop_listening()
                state.voice_client.stop()
                await asyncio.sleep(0.5)
                await state.voice_client.disconnect()
            finally:
                state.voice_client = None
                await message.channel.send('Disconnected...')
        else:
            await message.channel.send('Not in a voice channel.')
