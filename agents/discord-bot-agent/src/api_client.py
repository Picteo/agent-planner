"""
Supercell API client for AliceIsBored Discord bot.
Implements rate limiting (max 5 requests per second per Supercell ID).
"""

import asyncio
import certifi
import logging
import os
import ssl
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class SupercellAPIClient:
    """Client for the Supercell Clash of Clans API with rate limiting."""

    BASE_URL = "https://api.clashofclans.com/v1/"

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None, rate_limit: float = 3.0):
        self.api_key = api_key
        self._session = session
        self._rate_limit = rate_limit  # max requests per second
        self._rate_lock = asyncio.Lock()
        self._last_request_time = 0.0
        self._should_close_session = session is None

        # Rate limit state from Supercell API headers (X-RateLimit-*)
        self._rate_limit_remaining = 0
        self._rate_limit_reset = 0.0  # Unix timestamp
        self._rate_limit_cooldown_until = 0.0  # monotonic timestamp until which to back off

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session with proper SSL context.

        Uses certifi's CA bundle for SSL verification. This avoids
        CERTIFICATE_VERIFY_FAILED errors caused by an outdated Windows
        system root store (common on Windows VMs where root certs
        haven't been updated).
        """
        if self._session is None:
            # Use certifi's CA bundle explicitly — this is always up to date
            # and avoids Windows system root store issues.
            cert_path = certifi.where()
            ssl_context = ssl.create_default_context(cafile=cert_path)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def _recreate_session_with_ssl(self):
        """Recreate the HTTP session with a proper SSL context.

        This is used to fix SSL certificate verification errors on the
        production VM where the Windows system root store is outdated.
        Must be called after bot startup to replace any pre-existing
        session that was created without a proper SSL context.
        """
        if self._session and not self._session.closed:
            await self._session.close()

        cert_path = certifi.where()
        ssl_context = ssl.create_default_context(cafile=cert_path)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(connector=connector)
        logger.info("API client session recreated with certifi SSL certificate store")

    async def close(self):
        """Close the HTTP session."""
        if self._session and self._should_close_session:
            await self._session.close()

    def parse_rate_limit_headers(self, headers: dict) -> None:
        """Parse Supercell API rate limit response headers.

        Supercell returns:
          X-RateLimit-Limit      – max requests per window
          X-RateLimit-Remaining  – remaining requests in current window
          X-RateLimit-Reset      – Unix timestamp when window resets

        On 403 responses, may also include Retry-After (seconds to wait).
        """
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        retry_after = headers.get("Retry-After")

        if remaining is not None:
            try:
                self._rate_limit_remaining = int(remaining)
            except (ValueError, TypeError):
                pass

        if reset is not None:
            try:
                self._rate_limit_reset = float(reset)
            except (ValueError, TypeError):
                pass

        if retry_after is not None:
            try:
                delay = float(retry_after)
                import time
                self._rate_limit_cooldown_until = time.monotonic() + delay
                logger.debug(
                    "API rate limit — Retry-After: %.1fs, backing off until %s",
                    delay,
                    datetime.fromtimestamp(self._rate_limit_reset, tz=timezone.utc).strftime("%H:%M:%S UTC"),
                )
            except (ValueError, TypeError):
                pass

    def reset_rate_limit_state(self):
        """Reset rate limit tracking state.

        Call this after a bot restart to clear stale cooldowns from the
        previous session. The Supercell API rate limit window is server-side
        so the local cooldown tracking is no longer valid after a restart.
        """
        self._rate_limit_remaining = 0
        self._rate_limit_reset = 0.0
        self._rate_limit_cooldown_until = 0.0
        self._last_request_time = 0.0
        logger.info("API rate limit state reset after restart")

    def get_rate_limit_remaining(self) -> int:
        """Return remaining API requests per Supercell ID in the current window."""
        return self._rate_limit_remaining

    def get_rate_limit_reset(self) -> float:
        """Return Unix timestamp when the rate limit window resets."""
        return self._rate_limit_reset

    def get_rate_limit_cooldown_remaining(self) -> float:
        """Return seconds remaining in the backoff cooldown (0 if not cooling down)."""
        import time
        if self._rate_limit_cooldown_until > 0:
            remaining = self._rate_limit_cooldown_until - time.monotonic()
            return max(0.0, remaining)
        return 0.0

    def _is_rate_limited_by_headers(self) -> bool:
        """Check if we should skip API calls based on parsed headers."""
        cooldown = self.get_rate_limit_cooldown_remaining()
        if cooldown > 0:
            logger.debug("Rate limit backoff active — %.1fs remaining (per Retry-After)", cooldown)
            return True
        return False

    async def _rate_limited_request(
        self, method: str, url: str, params: Optional[dict] = None
    ) -> dict:
        """Make a rate-limited API request."""
        async with self._rate_lock:
            # Enforce rate limiting (max 5 requests per second)
            elapsed = time.time() - self._last_request_time
            min_delay = 1.0 / self._rate_limit
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
            self._last_request_time = time.time()

        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self.api_key}"}

        logger.debug(f"{method} {url} params={params}")
        async with session.request(method, url, params=params, headers=headers) as resp:
            # Always parse rate limit headers from Supercell API responses
            self.parse_rate_limit_headers(dict(resp.headers))
            logger.debug(f"Response status: {resp.status} X-RateLimit-Remaining={self._rate_limit_remaining}")
            if resp.status == 200:
                return await resp.json(content_type=None)
            elif resp.status == 403:
                logger.error(
                    "Rate limit exceeded for URL: %s (remaining=%d, reset=%s, retry-after=%.0fs)",
                    url,
                    self._rate_limit_remaining,
                    datetime.fromtimestamp(self._rate_limit_reset, tz=timezone.utc).strftime("%H:%M:%S UTC") if self._rate_limit_reset else "N/A",
                    self.get_rate_limit_cooldown_remaining(),
                )
                raise RateLimitExceededError(f"Rate limit exceeded for {url}")
            elif resp.status == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            else:
                logger.error(f"API error: {resp.status} for {url}")
                resp_text = await resp.text()
                raise APIError(f"API error {resp.status}: {resp_text}")

    # --- Clan endpoints ---

    async def get_clan(self, tag: str) -> Optional[dict]:
        """Get clan details by tag.

        GET /v1/clans?tag={clanTag}
        """
        clean_tag = f"#{tag.lstrip('#')}"
        url = urljoin(self.BASE_URL, f"clans?tag={clean_tag}")
        return await self._rate_limited_request("GET", url)

    async def get_clan_wars(self, clan_id: str) -> Optional[dict]:
        """Get current and past war states for a clan.

        GET /v1/clans/{clanId}/warstates
        """
        url = urljoin(self.BASE_URL, f"clans/{clan_id}/warstates")
        return await self._rate_limited_request("GET", url)

    async def get_clan_warl_states(self, clan_id: str) -> Optional[dict]:
        """Get CWL history for a clan.

        GET /v1/clans/{clanId}/cwallstates
        """
        url = urljoin(self.BASE_URL, f"clans/{clan_id}/cwallstates")
        return await self._rate_limited_request("GET", url)

    async def get_clan_raid(self, clan_id: str) -> Optional[dict]:
        """Get raid states for a clan.

        GET /v1/clans/{clanId}/raidstates
        """
        url = urljoin(self.BASE_URL, f"clans/{clan_id}/raidstates")
        return await self._rate_limited_request("GET", url)

    async def get_clan_games(self, clan_id: str, season_id: str) -> Optional[dict]:
        """Get Clan Games data for a clan.

        GET /v1/clans/{clanId}/clanGames?seasonId={seasonId}
        """
        url = urljoin(self.BASE_URL, f"clans/{clan_id}/clanGames")
        return await self._rate_limited_request("GET", url, params={"seasonId": season_id})

    # --- Player endpoints ---

    async def get_player(self, tag: str) -> Optional[dict]:
        """Get player details by tag.

        GET /v1/players/{playerTag}
        """
        clean_tag = f"#{tag.lstrip('#')}"
        url = urljoin(self.BASE_URL, f"players/{clean_tag}")
        return await self._rate_limited_request("GET", url)

    # --- Clan list ---

    async def list_clans(self, params: Optional[dict] = None) -> Optional[dict]:
        """List clans with optional filters.

        GET /v1/clans
        """
        url = urljoin(self.BASE_URL, "clans")
        return await self._rate_limited_request("GET", url, params=params)


class APIError(Exception):
    """Base exception for API errors."""

    pass


class ClanInfo:
    """Data class for clan information."""

    def __init__(self, data: dict):
        self.name = data.get("name", "Unknown")
        self.tag = data.get("tags", "")
        self.clan_level = data.get("clanPointVictories", 0)
        self.member_count = len(data.get("members", []))
        self.description = data.get("description", "")
        self.clan_point = data.get("clanPoints", 0)
        self.clan_point_victories = data.get("clanPointVictories", 0)
        self.war_frequency = data.get("warFrequency", "Unknown")
        self.war_stage_frequency = data.get("warStageFrequency", "Unknown")
        self.required_trophies = data.get("requiredTrophies", 0)
        self.region = data.get("region", {}).get("name", "Unknown")
        self.members = [MemberInfo(m) for m in data.get("members", [])]


class PlayerInfo:
    """Data class for player information."""

    def __init__(self, data: dict):
        self.name = data.get("name", "Unknown")
        self.tag = data.get("tags", "")
        self.trophies = data.get("trophies", 0)
        self.flood_protection_time = data.get("floodProtectionTime", 0)
        self.attack_wins = data.get("attackWins", 0)
        self.role = data.get("role", "Member")
        self.badges = data.get("badges", [])
        self.league = LeagueInfo(data.get("league", {}))
        self.donations = data.get("donations", 0)
        self.donations_received = data.get("donationsReceived", 0)
        self.war_days = data.get("warDays", 0)
        self.clan = ClanInfo(data.get("clan", {})) if data.get("clan") else None


class MemberInfo:
    """Data class for clan member information."""

    def __init__(self, data: dict):
        self.name = data.get("name", "Unknown")
        self.tag = data.get("tags", "")
        self.trophies = data.get("trophies", 0)
        self.role = data.get("role", "Member")
        self.donations = data.get("donations", 0)
        self.donations_received = data.get("donationsReceived", 0)
        self.expperience = data.get("expLevel", 0)
        self.league = LeagueInfo(data.get("league", {}))


class LeagueInfo:
    """Data class for league information."""

    def __init__(self, data: dict):
        self.id = data.get("id", 0)
        self.name = data.get("name", "Unranked")
        self.icon_urls = data.get("iconUrls", "")


def parse_clan(data: dict) -> Optional[ClanInfo]:
    """Parse raw clan API response into ClanInfo object."""
    if data is None:
        return None
    return ClanInfo(data)


def parse_player(data: dict) -> Optional[PlayerInfo]:
    """Parse raw player API response into PlayerInfo object."""
    if data is None:
        return None
    return PlayerInfo(data)


class RateLimitExceededError(APIError):
    """Exception raised when the Supercell API rate limit is exceeded."""

    pass