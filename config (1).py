import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

AMAZON_TAG = os.getenv("AMAZON_TAG", "")
FLIPKART_AFFILIATE_ID = os.getenv("FLIPKART_AFFILIATE_ID", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ENABLE_AI = os.getenv("ENABLE_AI", "false").lower() == "true"

DEFAULT_JOIN_CHANNEL_URL = os.getenv(
    "DEFAULT_JOIN_CHANNEL_URL",
    "[t.me](https://t.me/yourchannel)"
)
