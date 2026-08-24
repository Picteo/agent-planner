"""
Bot configuration for AliceIsBored Discord bot.
"""

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    clan_tag: str = field(default_factory=lambda: os.getenv("CLAN_TAG", ""))
    _resolved_clan_tag: str = ""
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

        # Validate Supercell API key format — must be a valid JWT (3 dot-separated base64 parts)
        self._validate_supercell_api_key(self.api_key)

        # Clean and validate clan_tag: strip '#', ensure it looks like a tag
        raw = self.clan_tag.lstrip("#")
        if not raw:
            raise ValueError("CLAN_TAG environment variable is required (e.g. #PQJL8GL)")
        if len(raw) < 3 or len(raw) > 16:
            _log.warning(
                "CLAN_TAG '%s' may be a clan name, not a tag. "
                "The bot will attempt to resolve it via the Supercell API on startup.",
                self.clan_tag,
            )
        # Store as a clean tag (no prefix) for internal use
        self._resolved_clan_tag = raw
        self.clan_tag = raw

    @staticmethod
    def _validate_supercell_api_key(api_key: str) -> None:
        """Validate that the Supercell API key looks like a proper JWT token.

        Supercell API keys are JWTs with 3 dot-separated base64url parts:
          header.payload.signature
        They are typically 300–500 characters long. Keys shorter than 50
        characters are almost certainly truncated, corrupted, or placeholder
        values and should be rejected immediately before any API call is made.
        """
        parts = api_key.split(".")
        if len(parts) != 3:
            raise ValueError(
                "SUPERCELL_API_KEY has invalid format. Expected a JWT token with "
                f"3 dot-separated parts (header.payload.signature), but got {len(parts)} "
                f"part(s). Key length: {len(api_key)} chars. "
                "This usually means the .env file was corrupted or truncated during deployment."
            )
        for i, part in enumerate(parts):
            if not part:
                raise ValueError(
                    f"SUPERCELL_API_KEY part {i + 1} (header/payload/signature) is empty. "
                    "The key appears corrupted."
                )
        if len(api_key) < 100:
            _log.warning(
                "SUPERCELL_API_KEY is unusually short (%d chars). "
                "Valid Supercell JWT keys are typically 300–500 chars. "
                "This key may be truncated, corrupted, or a placeholder.",
                len(api_key),
            )
            # Log a truncated preview for debugging (never log the full key)
            _log.warning(
                "API key preview (first 20 + last 20 chars): %s...%s",
                api_key[:20],
                api_key[-20:] if len(api_key) > 40 else "(too short to show suffix)",
            )

    def resolve_clan_tag(self, api_client) -> str:
        """Resolve a clan name to a proper Supercell clan tag via the API.

        If ``clan_tag`` looks like a valid Supercell tag (length 3-16,
        alphanumeric with possible ``-`` and ``#`` characters), return it
        unchanged.  Otherwise, call :meth:`SupercellAPIClient.list_clans`
        with the name parameter to find the matching clan.

        Args:
            api_client: An initialized :class:`SupercellAPIClient` instance.

        Returns:
            The resolved clan tag (without ``#`` prefix).
        """
        tag = self._resolved_clan_tag
        # If it already looks like a valid tag (no non-alphanumeric chars
        # except -), assume it's correct and skip API lookup.
        if all(c.isalnum() or c in "-#" for c in tag) and 3 <= len(tag) <= 16:
            return tag

        # Attempt API resolution
        logger = logging.getLogger("config")
        logger.info("Attempting to resolve clan name '%s' via Supercell API ...", tag)
        try:
            result = asyncio.run(_async_resolve_clan_name(self.api_key, tag))
            if result:
                resolved = result.lstrip("#")
                logger.info("Resolved clan name '%s' → tag '#%s'", tag, resolved)
                self._resolved_clan_tag = resolved
                return resolved
        except Exception as exc:
            logger.error("Failed to resolve clan name '%s': %s", tag, exc)

        # Fall back to the original (will likely get 404s from API)
        logger.warning(
            "Could not resolve clan name '%s'; using it as-is. "
            "Expected format: alphanumeric tag without '#'.",
            tag,
        )
        return tag


async def _async_resolve_clan_name(api_key: str, clan_name: str) -> Optional[str]:
    """Resolve a clan name to a Supercell clan tag using the ``list_clans`` endpoint.

    Returns the ``tag`` field of the first matching clan, or ``None``.
    """
    import certifi as _certifi
    import aiohttp as _aiohttp
    import ssl as _ssl

    cert_path = _certifi.where()
    ssl_context = _ssl.create_default_context(cafile=cert_path)
    connector = _aiohttp.TCPConnector(ssl=ssl_context)
    async with _aiohttp.ClientSession(connector=connector) as session:
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with session.get(
                "https://api.clashofclans.com/v1/clans",
                headers=headers,
                params={"name": clan_name},
                timeout=_aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    if items:
                        return items[0].get("tag", "")
        except Exception as exc:
            _log.warning("list_clans lookup for '%s' failed: %s", clan_name, exc)
    return None
