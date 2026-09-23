import os
import re
import tempfile
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_API_KEYS: List[str] = []


def mask_key(key: str) -> str:
    """Safely masks an API key for logs so secrets are never exposed."""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def get_api_keys() -> List[str]:
    """
    Dynamically loads Gemini API keys from environment variables:
    1. First checks for individually numbered keys: GEMINI_API_1, GEMINI_API_2, GEMINI_API_3, ...
    2. Sorts them in numeric order.
    3. If no numbered keys are found, falls back to comma-separated GEMINI_API_KEYS.
    4. If still empty, falls back to DEFAULT_API_KEYS.
    """
    indexed_keys = []
    pattern = re.compile(r"^GEMINI_API_(\d+)$", re.IGNORECASE)

    for env_k, env_v in os.environ.items():
        match = pattern.match(env_k.strip())
        if match and env_v.strip():
            index_num = int(match.group(1))
            indexed_keys.append((index_num, env_v.strip()))

    if indexed_keys:
        # Sort keys numerically (GEMINI_API_1, GEMINI_API_2, GEMINI_API_3...)
        indexed_keys.sort(key=lambda x: x[0])
        return [val for _, val in indexed_keys]

    # Fallback to comma-separated GEMINI_API_KEYS
    raw_keys = os.getenv("GEMINI_API_KEYS", "")
    if raw_keys.strip():
        keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if keys:
            return keys

    return list(DEFAULT_API_KEYS)


GEMINI_API_KEYS: List[str] = get_api_keys()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
TARGET_SITE: str = os.getenv("TARGET_SITE", "https://www.preciousedu.in/")

# Determine safe cache location (app dir or system temp)
default_cache = BASE_DIR / "site_cache.json"
try:
    default_cache.touch(exist_ok=True)
    CACHE_FILE = default_cache
except Exception:
    CACHE_FILE = Path(tempfile.gettempdir()) / "precious_edu_site_cache.json"

CACHE_TTL: int = int(os.getenv("CACHE_TTL_SECONDS", str(6 * 60 * 60)))  # 6 hours

# Render dynamically injects $PORT (default 10000 or 8000)
HOST: str = os.getenv("HOST", "0.0.0.0")
try:
    PORT: int = int(os.getenv("PORT", "8000"))
except ValueError:
    PORT = 8000

# CORS origins
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
if raw_origins.strip() == "*":
    ALLOWED_ORIGINS: List[str] = ["*"]
else:
    ALLOWED_ORIGINS: List[str] = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Security limits
MAX_MESSAGE_LENGTH: int = 2000
MAX_HISTORY_TURNS: int = 20
