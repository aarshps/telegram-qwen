"""
Centralized configuration for the Telegram-Qwen Agent.
All settings loaded from environment variables with sensible defaults.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = BOT_ROOT / "data" / "bot.log"

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("telegram-qwen")


class Config:
    """Central configuration."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_ID: str = os.environ.get("TELEGRAM_ADMIN_ID", "")

    # Paths
    BOT_ROOT: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BOT_ROOT / "data"
    CONVERSATION_DIR: Path = DATA_DIR / "conversations"
    TASK_DIR: Path = DATA_DIR / "tasks"
    WORKSPACE_DIR: Path = BOT_ROOT / "workspace"

    # Qwen
    QWEN_TIMEOUT: int = int(os.environ.get("QWEN_TIMEOUT", "600"))
    MAX_TOOL_TURNS: int = int(os.environ.get("MAX_TOOL_TURNS", "15"))
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "3"))

    # Memory
    MAX_HISTORY_LENGTH: int = int(os.environ.get("MAX_HISTORY_LENGTH", "50"))

    # Telegram limits
    MAX_MESSAGE_LENGTH: int = 4096
    MAX_OUTPUT_LENGTH: int = 4000

    # Rate limiting
    RATE_LIMIT_MESSAGES: int = int(os.environ.get("RATE_LIMIT_MESSAGES", "5"))
    RATE_LIMIT_WINDOW: int = int(os.environ.get("RATE_LIMIT_WINDOW", "10"))

    # Restart
    RESTART_EXIT_CODE: int = 42

    # Progress reporting interval for long tasks (seconds)
    PROGRESS_INTERVAL: int = 60

    @classmethod
    def ensure_dirs(cls):
        """Create all required data directories."""
        for d in [cls.DATA_DIR, cls.CONVERSATION_DIR, cls.TASK_DIR, cls.WORKSPACE_DIR]:
            d.mkdir(parents=True, exist_ok=True)
