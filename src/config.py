import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DB_PATH = os.getenv("DB_PATH", "/app/db/anonbot.db")

# Rate limiting
RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "5"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# Admin IDs (can create links)
_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: set[int] = {int(x.strip()) for x in _admin_ids.split(",") if x.strip()}
