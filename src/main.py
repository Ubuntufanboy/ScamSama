"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

import threading
import discord
import config
from discord_bot import bot
from web_server import app

if __name__ == '__main__':
    # DO NOT RUN THIS ON ANY PUBLICLY FACING NETWORK. THIS SHOULD BE BEHIND A FIREWALL FOR SECURITY.
    # DOUBLE CHECK INTERFACE ONLY RUNS ON LOCALHOST AND PRIVATE CLASS C NETWORK
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True)
    flask_thread.start()
    try:
        bot.run(config.DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord Bot Token. Please check your DISCORD_BOT_TOKEN.")
