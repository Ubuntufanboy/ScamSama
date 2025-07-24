import os
from dotenv import load_dotenv

# We run this from inside src/ and .env is in the root directory of the project
load_dotenv("../.env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
YOUR_PERSONAL_PHONE_NUMBER = os.getenv("YOUR_PERSONAL_PHONE_NUMBER")
YOUR_TWILIO_PHONE_NUMBER = os.getenv("YOUR_TWILIO_PHONE_NUMBER")
NGROK_BASE_URL = os.getenv("NGROK_BASE_URL")
