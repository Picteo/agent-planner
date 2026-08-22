"""
Autonomous dashboard messages for the AliceIsBored Discord bot.

Manages persistent dashboard messages that update on a schedule.
Dashboard types: leaderboard, clan info, and combined status.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import discord

from database import (
    Clan,
    ClanGamesEvents,
    ContributionScores,
    CwEvents,
    CwlEvents,
    Members,
    RaidEvents,
)

logger = logging.getLogger(__name__)

CLAN_GUILD_EMOJI = "\U0001f3db"
TROPHY_EMOJI = "\U0001f3c6"
LEADERBOARD_EMOJI = "\U0001f3c6"
CHART_EMOJI = "\U0001f4ca"
CALENDAR_EMOJI = "\U0001f4c5"


class DashboardManager:
    """Manages persistent, auto-updating dashboard messages."""

    # Circuit breaker: after 3 consecutive API failures, stop calling
    # the API for a full hour instead of every 5 minutes.
    _API_FAILURE_THRESHOLD = 3
    _API_COOLDOWN_SECONDS = 3600  # 1 hour cooldown after consecutive failures
    _api_failure_count = 0
    _api_cooldown_until = 0.0  # monotonic timestamp

    def __init__(self, bot, channel_id: int, leaderboard_top: int = 10):
        self.bot = bot
        self.channel_id = channel_id
        self.leaderboard_top = leaderboard_top
        self._messages: Dict[str, discord.Message] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False

        self._dashboards = {
            "leaderboard": self._build_leaderboard_embed,
            "clan_info": self._build_clan_info_embed,
        }

    @classmethod
    def _check_api_circuit_breaker(cls) -> bool:
        """Check if the API circuit breaker is tripped.

        Returns True if the API call is allowed, False if we're in cooldown.
        Also respects the API client's header-based cooldown (from Retry-After).
        Resets the failure count on first successful return.
        """
        now = time.monotonic()

        # Also check API client's header-based cooldown (Retry-After)
        if cls._api_cooldown_until > 0 and now < cls._api_cooldown_until:
            remaining = int(cls._api_cooldown_until - now)
            logger.debug(
                "API circuit breaker active — %ds remaining (%d consecutive failures)",
                remaining,
                cls._api_failure_count,
            )
            return False

        # Cooldown expired — allow next call
        if cls._api_cooldown_until > 0:
            logger.info(
                "API circuit breaker cooldown expired — resuming API calls"
            )
            cls._api_cooldown_until = 0.0

        return True

    @classmethod
    def _record_api_success(cls) -> None:
        """Reset the circuit breaker failure counter."""
        cls._api_failure_count = 0
        cls._api_cooldown_until = 0.0

    @classmethod
    def _record_api_failure(cls, cooldown_seconds: float = 0) -> None:
        """Record an API failure; trip the circuit breaker if threshold exceeded.

        If cooldown_seconds > 0 (from Retry-After header), use that as the
        cooldown duration instead of the fixed _API_COOLDOWN_SECONDS.
        """
        cls._api_failure_count += 1
        # Use API client's header-based cooldown if it's shorter than the
        # fixed threshold cooldown — don't extend the ban unnecessarily
        if cooldown_seconds > 0:
            cls._api_cooldown_until = time.monotonic() + cooldown_seconds
            logger.info(
                "API failure (attempt %d/3) — using Retry-After cooldown of %.0fs",
                cls._api_failure_count,
                cooldown_seconds,
            )
        if cls._api_failure_count >= cls._API_FAILURE_THRESHOLD:
            if cooldown_seconds <= 0:
                cls._api_cooldown_until = time.monotonic() + cls._API_COOLDOWN_SECONDS
            logger.warning(
                "API circuit breaker TRIPPED after %d consecutive failures — "
                "cooldown %ds. Will retry in ~%d minutes.",
                cls._api_failure_count,
                cls._API_COOLDOWN_SECONDS,
                cls._API_COOLDOWN_SECONDS // 60,
            )

    @classmethod
    def reset_circuit_breaker(cls):
        """Reset circuit breaker state after a bot restart.

        The failure count and cooldown from a previous session are
        no longer valid after the bot restarts.
        """
        cls._api_failure_count = 0
        cls._api_cooldown_until = 0.0
        logger.info("Dashboard circuit breaker reset after restart")

    @classmethod
    def get_circuit_breaker_status(cls) -> dict:
        """Return current circuit breaker status for display in embeds."""
        now = time.monotonic()
        cooldown_remaining = max(0, int(cls._api_cooldown_until - now)) if cls._api_cooldown_until > 0 else 0
        return {
            "active": cooldown_remaining > 0,
            "remaining_seconds": cooldown_remaining,
            "failure_count": cls._api_failure_count,
            "threshold": cls._API_FAILURE_THRESHOLD,
        }

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info(
            "Dashboard updater started (channel=%s, interval=%ds)",
            self.channel_id,
            self.bot.config.dashboard.update_interval_seconds,
        )

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        for name, msg in list(self._messages.items()):
            try:
                await msg.delete()
            except Exception:
                pass
        self._messages.clear()

    async def delete_dashboard(self, dashboard_type: str) -> bool:
        msg = self._messages.pop(dashboard_type, None)
        if msg:
            try:
                await msg.delete()
                logger.info("Manually deleted dashboard: %s", dashboard_type)
                return True
            except Exception:
                return False
        return False

    async def update_dashboard(self, dashboard_type: str) -> Optional[discord.Message]:
        if dashboard_type not in self._dashboards:
            logger.error("Unknown dashboard type: %s", dashboard_type)
            return None

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            logger.error("Dashboard channel %s not found.", self.channel_id)
            return None

        embed = await self._dashboards[dashboard_type]()
        msg = self._messages.get(dashboard_type)

        if msg:
            try:
                await msg.edit(embed=embed)
            except Exception:
                msg = await channel.send(embed=embed)
                self._messages[dashboard_type] = msg
        else:
            msg = await channel.send(embed=embed)
            self._messages[dashboard_type] = msg

        return msg

    async def update_all_dashboards(self):
        for dashboard_type in self._dashboards:
            try:
                await self.update_dashboard(dashboard_type)
            except Exception:
                logger.exception("Error updating dashboard: %s", dashboard_type)

    async def _update_loop(self):
        interval = self.bot.config.dashboard.update_interval_seconds
        while self._running:
            try:
                await self.update_all_dashboards()
            except Exception:
                logger.exception("Error in dashboard update loop")
            await asyncio.sleep(interval)

    async def _build_leaderboard_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{LEADERBOARD_EMOJI} Clan Contribution Rankings",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc),
        )

        if not self.bot.contribution_service:
            embed.description = "Contribution service not available."
            embed.set_footer(text=f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            return embed

        leaderboard = await self.bot.contribution_service.get_leaderboard(
            clan_tag=self.bot.config.clan_tag,
            top=self.leaderboard_top,
        )

        if not leaderboard:
            embed.description = (
                "\u26a0\ufe0f No contribution scores found. Run `/sync` first."
            )
        else:
            lines = []
            for entry in leaderboard:
                total = int(entry["total_score"])
                lines.append(
                    f"{entry['rank']}. `{entry['player_tag']}` \u2014 {total:,} pts  "
                    f"(CWL: {int(entry['cwl_score']):,}, CW: {int(entry['cw_score']):,}, "
                    f"Raid: {int(entry['raid_score']):,}, CG: {int(entry['clan_games_score']):,})"
                )
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        return embed

    async def _build_error_embed(self, message: str) -> discord.Embed:
        """Build a red error embed for database-unavailable state."""
        embed = discord.Embed(
            title=f"{CLAN_GUILD_EMOJI} Error",
            description=f"\u26a0\ufe0f {message}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        return embed

    async def _build_clan_info_embed(self) -> discord.Embed:
        session = self.bot.db_manager.session()
        if session is None:
            return self._build_error_embed(
                "Database unavailable. Run `/sync` later when database is back."
            )
        try:
            clan_count = session.query(Clan).count()
            cwl_events = session.query(CwlEvents).count()
            cw_events = session.query(CwEvents).count()
            raid_events = session.query(RaidEvents).count()
            cg_events = session.query(ClanGamesEvents).count()
            verified_members = session.query(Members).count()
            contribution_records = session.query(ContributionScores).count()

            clan_data = None
            if self._check_api_circuit_breaker():
                try:
                    clan_data = await self.bot.api_client.get_clan(self.bot.config.clan_tag)
                    self._record_api_success()
                except Exception:
                    # Extract Retry-After cooldown from API client for accurate timing
                    retry_after = self.bot.api_client.get_rate_limit_cooldown_remaining()
                    self._record_api_failure(cooldown_seconds=retry_after)
                    logger.debug("Clan API call failed (circuit breaker tracking)")
            else:
                logger.debug("Skipping clan API call — circuit breaker active")

            embed = discord.Embed(
                title=f"{CLAN_GUILD_EMOJI} #{self.bot.config.clan_tag} \u2014 Clan Stats",
                description="Real-time clan activity overview",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc),
            )

            if clan_data:
                members_count = clan_data.get("memberCount", 0)
                clan_arena = clan_data.get("clanArena", {})
                arena_rank = clan_arena.get("arenaRank", "N/A")
                embed.add_field(
                    name="Clan Arena",
                    value=f"Rank #{arena_rank}" if arena_rank != "N/A" else "No arena data",
                    inline=True,
                )
                clan_war_frequency = clan_data.get("clanWarFrequency", "unknown")
                embed.add_field(
                    name="War Frequency",
                    value=clan_war_frequency,
                    inline=True,
                )
                total_members = clan_data.get("totalMembers", 0)
                embed.add_field(
                    name="Members",
                    value=str(total_members),
                    inline=True,
                )

            embed.add_field(
                name=f"{TROPHY_EMOJI} Verified Members",
                value=str(verified_members),
                inline=True,
            )
            embed.add_field(
                name=f"{CHART_EMOJI} Contribution Records",
                value=str(contribution_records),
                inline=True,
            )
            embed.add_field(
                name=f"{CALENDAR_EMOJI} Events Synced",
                value=(
                    f"CWL: {cwl_events} | CW: {cw_events}\n"
                    f"Raids: {raid_events} | Clan Games: {cg_events}"
                ),
                inline=False,
            )

            embed.set_footer(text=f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

            # Add rate limit / circuit breaker status
            api_remaining = self.bot.api_client.get_rate_limit_remaining()
            api_reset = self.bot.api_client.get_rate_limit_reset()
            cb_status = self.get_circuit_breaker_status()

            rate_limit_parts = []
            if api_remaining >= 0:
                rate_limit_parts.append(f"API quota: {api_remaining} remaining")
            if api_reset > 0:
                reset_time = datetime.fromtimestamp(api_reset, tz=timezone.utc).strftime("%H:%M:%S UTC")
                rate_limit_parts.append(f"Reset at: {reset_time}")
            if cb_status["active"]:
                cb_remaining = cb_status["remaining_seconds"]
                rate_limit_parts.append(
                    f"⏸ Circuit breaker: {cb_remaining}s ({cb_status['failure_count']}/{cb_status['threshold']} failures)"
                )
            elif cb_status["failure_count"] > 0:
                rate_limit_parts.append(
                    f"Circuit breaker: {cb_status['failure_count']}/{cb_status['threshold']} consecutive failures"
                )
            else:
                rate_limit_parts.append("Circuit breaker: healthy")

            embed.add_field(
                name=f"{'🔄' if api_remaining == 0 else '📊'} API Status",
                value="\n".join(rate_limit_parts),
                inline=False,
            )

            return embed

        except Exception:
            logger.exception("Error building clan info embed")
            return discord.Embed(
                title=f"{CLAN_GUILD_EMOJI} Clan Stats",
                description="\u26a0\ufe0f Error fetching clan data.",
                color=discord.Color.red(),
            )
        finally:
            session.close()
