"""
ScamSama v1.0.0
Ubuntufanboy July 23rd 2025 https://github.com/Ubuntufanboy/ScamSama

Licenced under LGPL-2.1 license.

Thank you VedalAI for creating such a wonderful platform and using my code! I hope you enjoy it!
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: root_dir / 'subdir'
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
YOUR_NUMBER_TO_CALL = os.getenv("YOUR_NUMBER_TO_CALL")
YOUR_TWILIO_PHONE_NUMBER = os.getenv("YOUR_TWILIO_PHONE_NUMBER")
NGROK_BASE_URL = os.getenv("NGROK_BASE_URL")
COUNTRY_CODE = os.getenv("COUNTRY_CODE", "US") # Default to US
