"""
Bot configuration for AliceIsBored Discord bot.
"""

import logging
import os
import sys
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)

# Simple .env loader fallback (no python-dotenv dependency)
_env_logger = logging.getLogger("config")


def _load_dotenv(path: str = None):
    """Load environment variables from a .env file if setenv is missing."""
    if path is None:
        # Build a prioritized list of candidate paths:
        #   1. Current working directory (covers production batch-file cwd)
        #   2. Parent directory of this config file (C:\ClashKing on production)
        #   3. Same directory as this config file (C:\ClashKing\src)
        candidates = []
        cwd = os.getcwd()
        candidates.append(os.path.join(cwd, ".env"))
        candidates.append(os.path.join(cwd, "..", ".env"))
        config_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(config_dir, "..", ".env"))   # parent of src/
        candidates.append(os.path.join(config_dir, ".env"))          # same dir as config.py
        candidates.append(os.path.join(config_dir, "..", "..", ".env"))  # grandparent
        # Windows production: C:\ClashKing\.env
        candidates.append(os.path.join("C:", os.sep, "ClashKing", ".env"))
        # Deduplicate while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            resolved = os.path.normpath(c)
            if resolved not in seen:
                seen.add(resolved)
                unique_candidates.append(resolved)
        for candidate in unique_candidates:
            if os.path.isfile(candidate):
                path = candidate
                break
    if not path or not os.path.isfile(path):
        return
    _env_logger.info("Loading environment variables from: %s", path)
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key:
                    os.environ[key] = value
        # Second pass: ensure values set earlier take precedence
        with open(path, "r", encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key and not os.getenv(key):
                    os.environ[key] = value
        _env_logger.info("Environment variables loaded successfully from .env file")
    except Exception:
        _env_logger.error("Failed to load .env file: %s", path, exc_info=True)


_load_dotenv()


@dataclass
class DashboardConfig:
    """Configuration for persistent dashboard messages."""

    enabled: bool = field(default_factory=lambda: os.getenv("DASHBOARD_ENABLED", "false").lower() == "true")
    update_interval_seconds: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_INTERVAL", "300")))
    leaderboard_top: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_LEADERBOARD_TOP", "10")))


@dataclass
class BotConfig:
    """Configuration for the Discord bot."""

    bot_token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    api_key: str = field(default_factory=lambda: os.getenv("SUPERCELL_API_KEY", ""))
    clan_tag: str = field(default_factory=lambda: os.getenv("CLAN_TAG", "AliceIsBored").lstrip("#"))
    api_region: str = field(default_factory=lambda: os.getenv("API_REGION", "eu"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    dashboard_channel_id: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_CHANNEL_ID", "0") or "0"))
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.bot_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        if not self.api_key:
            raise ValueError("SUPERCELL_API_KEY environment variable is required")
