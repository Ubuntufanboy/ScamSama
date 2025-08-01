"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

import argparse
import threading
import discord
import config
from discord_bot import bot
from web_server import app
from typing import Literal

def start_bot_mode():
    """Start the Discord bot mode with Flask web server."""
    print("Starting ScamSama in bot mode...")
    
    # DO NOT RUN THIS ON ANY PUBLICLY FACING NETWORK. THIS SHOULD BE BEHIND A FIREWALL FOR SECURITY.
    # DOUBLE CHECK INTERFACE ONLY RUNS ON LOCALHOST AND PRIVATE CLASS C NETWORK
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True)
    flask_thread.start()
    
    try:
        bot.run(config.DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord Bot Token. Please check your DISCORD_BOT_TOKEN.")

API_TYPES = Literal["bot", "direct"]

def start_api_mode(type: API_TYPES):
    """Start the Neuro API mode (to be implemented later)."""
    print("Starting ScamSama in API mode...")
    print("API mode is not yet implemented. Please implement this mode.")
    # TODO: Implement API mode functionality here

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ScamSama')
    parser.add_argument('--mode', 
                       choices=['bot', 'api'], 
                       help='Mode to run ScamSama in: bot (Discord bot mode) or api (API mode)')
    
    args = parser.parse_args()
    
    if args.mode.lower() == 'bot':
        start_bot_mode()
    elif args.mode.lower() == 'botapi':
        start_api_mode("bot")
    elif args.mode.lower() == 'directapi':
        start_api_mode("direct")
    else:
        print(f"Unknown mode: {args.mode}")
        parser.print_help()
