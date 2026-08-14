"""
Bot configuration for AliceIsBored Discord bot.
"""

import os
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    """Configuration for the Discord bot."""

    bot_token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    api_key: str = field(default_factory=lambda: os.getenv("SUPERCELL_API_KEY", ""))
    clan_tag: str = field(default_factory=lambda: os.getenv("CLAN_TAG", "AliceIsBored").lstrip("#"))
    api_region: str = field(default_factory=lambda: os.getenv("API_REGION", "eu"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.bot_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        if not self.api_key:
            raise ValueError("SUPERCELL_API_KEY environment variable is required")