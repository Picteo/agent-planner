"""
Discord Bot for AliceIsBored Clan - Main Entry Point
Implements: Work Item #7 - Discord bot framework with Supercell API integration
"""

import os
import sys

# Ensure the src/ directory is on sys.path so relative imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
import signal
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

from config import BotConfig
from api_client import SupercellAPIClient, APIError
from database import Clan, DatabaseManager, get_default_database_url
from cwl_service import CwlService
from cw_service import CwService
from raid_service import RaidService
from clan_games_service import ClanGamesService
from verification_service import VerificationService
from contribution_service import ContributionService
from dashboard import DashboardManager

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AliceIsBoredBot(commands.Bot):
    """Main Discord bot client for AliceIsBored clan."""

    def __init__(self, config: BotConfig, api_client: SupercellAPIClient, db_manager: DatabaseManager = None):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(intents=intents, command_prefix="!")

        self.config = config
        self.api_client = api_client
        self.db_manager = db_manager
        self.cwl_service = CwlService(api_client, db_manager) if db_manager else None
        self.cw_service = CwService(api_client, db_manager) if db_manager else None
        self.raid_service = RaidService(api_client, db_manager) if db_manager else None
        self.clan_games_service = ClanGamesService(api_client, db_manager) if db_manager else None
        self.verification_service = VerificationService(api_client, db_manager) if db_manager else None
        self.contribution_service = ContributionService(db_manager) if db_manager else None
        self.dashboard_manager = DashboardManager(self, config.dashboard_channel_id, config.dashboard.leaderboard_top) if config.dashboard_channel_id else None
        self.ready_event = asyncio.Event()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _safe_respond(
        self,
        interaction: discord.Interaction,
        message: str = None,
        embed: discord.Embed = None,
        ephemeral: bool = False,
    ) -> bool:
        """Attempt to respond to an interaction, handling expired tokens.

        Returns True if the response was sent successfully, False if the
        interaction was already expired/invalid.
        """
        try:
            if embed:
                await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            else:
                await interaction.response.send_message(message, ephemeral=ephemeral)
            return True
        except discord.NotFound:
            logger.debug("Interaction %s already expired — skipping response", interaction.id)
            return False
        except discord.HTTPException as e:
            logger.warning("Failed to respond to interaction %s: %s", interaction.id, e)
            return False

    async def _safe_followup(
        self,
        interaction: discord.Interaction,
        message: str = None,
        embed: discord.Embed = None,
    ) -> bool:
        """Attempt to send a followup message, handling expired tokens.

        Returns True if the followup was sent successfully, False otherwise.
        """
        try:
            if embed:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(message)
            return True
        except discord.NotFound:
            logger.debug("Followup for interaction %s — interaction already expired", interaction.id)
            return False
        except discord.HTTPException as e:
            logger.warning("Failed to send followup for interaction %s: %s", interaction.id, e)
            return False

    async def setup_hook(self):
        """Called when the bot is setting up - before connecting to Discord."""
        # Register slash commands with the bot's tree
        self.tree.add_command(
            discord.app_commands.Command(
                name="ping",
                description="Ping the bot!",
                callback=self._ping_impl
            )
        )
        self.tree.add_command(
            discord.app_commands.Command(
                name="clan",
                description="Get clan information",
                callback=self._clan_impl
            )
        )
        self.tree.add_command(
            discord.app_commands.Command(
                name="player",
                description="Get player information",
                callback=self._player_impl
            )
        )
        self.tree.add_command(
            discord.app_commands.Command(
                name="config",
                description="Show current bot configuration",
                callback=self._config_impl
            )
        )
        if self.contribution_service:
            self.tree.add_command(
                discord.app_commands.Command(
                    name="contribution",
                    description="Show contribution rankings or a player's score breakdown",
                    callback=self._contribution_impl
                )
            )
        if self.cwl_service:
            self.tree.add_command(
                discord.app_commands.Command(
                    name="sync",
                    description="Sync data from Supercell API",
                    callback=self._sync_impl
                )
            )
            self.tree.add_command(
                discord.app_commands.Command(
                    name="sync_all",
                    description="Re-run full initial data sync (CWL, CW, Raids, Clan Games)",
                    callback=self._sync_all_impl
                )
            )
        if self.verification_service:
            self.tree.add_command(
                discord.app_commands.Command(
                    name="verify",
                    description="Verify your Discord account with a Clash tag",
                    callback=self._verify_impl
                )
            )
            self.tree.add_command(
                discord.app_commands.Command(
                    name="unverify",
                    description="Remove your Discord-to-Clash link",
                    callback=self._unverify_impl
                )
            )
            self.tree.add_command(
                discord.app_commands.Command(
                    name="myclan",
                    description="Show your clan info and verified status",
                    callback=self._myclan_impl
                )
            )
        if self.db_manager:
            self.tree.add_command(
                discord.app_commands.Command(
                    name="status",
                    description="Show bot status and database sync info",
                    callback=self._status_impl
                )
            )
            self.tree.add_command(
                discord.app_commands.Command(
                    name="sync_schema",
                    description="Check and fix database schema mismatches (ADMIN ONLY)",
                    callback=self._sync_schema_impl
                )
            )
        if self.dashboard_manager:
            # Create a dashboard group with subcommands
            self.dashboard_group = discord.app_commands.Group(
                name="dashboard",
                description="Manage persistent dashboard messages",
            )
            self.dashboard_group.add_command(
                discord.app_commands.Command(
                    name="update",
                    description="Update dashboard messages manually",
                    callback=self._dashboard_update_impl,
                )
            )
            self.dashboard_group.add_command(
                discord.app_commands.Command(
                    name="delete",
                    description="Delete dashboard messages",
                    callback=self._dashboard_delete_impl,
                )
            )
            self.dashboard_group.add_command(
                discord.app_commands.Command(
                    name="list",
                    description="List active dashboards",
                    callback=self._dashboard_list_impl,
                )
            )
            self.tree.add_command(self.dashboard_group)
            logger.info("Dashboard commands registered")
        logger.info("Slash commands registered with bot tree")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")
        self.ready_event.set()

        # Sync slash commands with Discord
        await self.tree.sync()
        logger.info("Synced slash commands with Discord")

        # Health check
        guilds = len(self.guilds)
        channels = sum(len(g.text_channels) for g in self.guilds)
        logger.info(f"Connected to {guilds} guilds with {channels} text channels")

        # Start dashboard updater if configured
        if self.dashboard_manager:
            await self.dashboard_manager.start()
            logger.info("Dashboard updater started")

        # Run initial data sync so dashboard has real numbers
        # Fix SSL certificate verification by using system certificate store
        await self.api_client._recreate_session_with_ssl()
        # Reset rate limit state and circuit breaker after restart
        self.api_client.reset_rate_limit_state()
        if self.dashboard_manager:
            self.dashboard_manager.reset_circuit_breaker()
        # Delay to let rate limiter reset after startup API calls
        await asyncio.sleep(5)
        await self._initial_data_sync()
        logger.info("Initial data sync completed")

    async def _initial_data_sync(self):
        """Fetch all event data from Supercell API and persist to database.

        Populates CWL, CW, Raid, and Clan Games tables so the dashboard
        displays real statistics instead of all zeros.

        Each sync is spaced by 3 seconds to respect Supercell's rate limit.
        A clan record is pre-created to avoid the expensive get_clan() API call.
        Syncs are retried with exponential backoff if they hit rate limits.
        """
        clean_tag = self.config.clan_tag.lstrip("#")
        logger.info("Starting initial data sync for clan #%s", clean_tag)

        # Pre-create clan record to avoid calling get_clan() API for each sync
        await self._ensure_clan_record(clean_tag)

        results = {}

        # List of (service, method_name) pairs to sync
        sync_tasks = [
            ("cwl", lambda: self.cwl_service.sync_cwl(clean_tag)),
            ("cw", lambda: self.cw_service.sync_cw(clean_tag)),
            ("raid", lambda: self.raid_service.sync_raids(clean_tag)),
            ("clan_games", lambda: self.clan_games_service.sync_clan_games(clean_tag)),
        ]

        for name, sync_func in sync_tasks:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await sync_func()
                    results[name] = result
                    logger.info("%s sync result (attempt %d): %s", name.upper(), attempt + 1, result)
                    break
                except Exception as exc:
                    logger.warning("%s sync attempt %d failed: %s", name.upper(), attempt + 1, exc)
                    results[name] = {"error": str(exc)}
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt  # 1s, 2s, 4s backoff
                        logger.info("Retrying %s in %ds...", name.upper(), wait)
                        await asyncio.sleep(wait)
                    else:
                        logger.error("%s sync permanently failed after %d attempts", name.upper(), max_retries)

            # Spacing between different sync types
            await asyncio.sleep(3)

        # Recalculate contribution scores now that event data is in the DB
        if self.contribution_service and self.db_manager:
            try:
                inserted = await self.contribution_service.recalculate_scores(clean_tag)
                logger.info("Contribution scores recalculated: %d records", inserted)
            except Exception as exc:
                logger.error("Contribution recalc failed: %s", exc, exc_info=True)

        logger.info(
            "Initial data sync complete: %s",
            {k: v.get("events_synced", v.get("participations_synced", "error")) for k, v in results.items()},
        )

    async def _ensure_clan_record(self, clan_tag: str):
        """Ensure the clan exists in the DB. Creates a local placeholder.

        Skips the API call entirely to avoid rate limit issues.
        """
        session = self.db_manager.session()
        if session is None:
            logger.warning("Cannot ensure clan record - no database session")
            return
        try:
            existing = session.query(Clan).filter(Clan.clan_tag == clan_tag).first()
            if existing:
                logger.info("Clan record already exists: #%s", clan_tag)
                return

            # Create a placeholder clan record locally - no API call needed
            clan = Clan(
                clan_tag=clan_tag,
                clan_name=f"#{clan_tag}",
                clan_level=0,
                trophies=0,
                war_frequency="Unknown",
                war_stage_frequency="Unknown",
                required_trophies=0,
                clan_points=0,
                clan_point_victories=0,
                region_name="Unknown",
                description="",
            )
            session.add(clan)
            session.commit()
            logger.info("Clan record created locally: #%s", clan_tag)
        except Exception as exc:
            session.rollback()
            logger.error("Failed to ensure clan record: %s", exc, exc_info=True)
        finally:
            session.close()

    async def on_member_join(self, member: discord.Member):
        """Called when a member joins the guild."""
        logger.info(f"Member joined: {member}")

    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        """Handle command errors."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(f"❌ Missing required argument: `{error.param.name}`. Use `{ctx.prefix}help` for usage.")
        elif isinstance(error, commands.BadArgument):
            await ctx.respond(f"❌ Could not parse that argument. Use `{ctx.prefix}help` for usage.")
        elif isinstance(error, commands.CommandNotFound):
            logger.warning(f"Unknown command: {ctx.command}")
        else:
            logger.error(f"Command error in {ctx.command}: {error}", exc_info=error)
            try:
                await ctx.respond(f"❌ An error occurred: {str(error)}")
            except Exception:
                pass

    async def on_application_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle slash command errors."""
        if isinstance(error, discord.app_commands.MissingPermissions):
            try:
                await interaction.response.send_message("❌ You don't have permission to use this command.")
            except discord.InteractionResponded:
                pass
        else:
            logger.error(f"Slash command error: {error}")
            try:
                await interaction.response.send_message(f"❌ An error occurred: {str(error)}")
            except (discord.InteractionResponded, discord.NotFound):
                pass

    # --- Command Implementations (used by setup_hook) ---

    async def _ping_impl(self, interaction: discord.Interaction):
        """Respond to ping with latency info."""
        latency = round(self.latency * 1000)
        await interaction.response.send_message(f"\U0001f3cc\ufe0f Pong! Latency: {latency}ms")

    async def _clan_impl(self, interaction: discord.Interaction, tag: str):
        """Get clan information from Supercell API."""
        responded = await self._safe_respond(interaction, "\u23f3 Fetching clan info...")
        if not responded:
            logger.warning("Clan interaction %s already expired", interaction.id)
            return

        try:
            clean_tag = tag.lstrip("#")
            clan_data = await self.api_client.get_clan(clean_tag)

            if clan_data is None:
                await self._safe_followup(interaction, f"\u274c Clan with tag #{clean_tag} not found.")
                return

            clan_name = clan_data.get("name", "Unknown")
            clan_level = clan_data.get("clanPointVictories", "N/A")
            members = clan_data.get("members", [])
            member_count = len(members)
            war_frequency = clan_data.get("warFrequency", "Unknown")

            embed = discord.Embed(
                title=f"\U0001f3f0 {clan_name}",
                description=f"Clan Tag: `#{clean_tag}`",
                color=discord.Color.blue()
            )
            embed.add_field(name="Level", value=str(clan_level), inline=True)
            embed.add_field(name="Members", value=str(member_count), inline=True)
            embed.add_field(name="War Frequency", value=war_frequency, inline=True)

            if members:
                top_members = sorted(members, key=lambda m: m.get("trophies", 0), reverse=True)[:5]
                top_text = "\n".join(
                    f"`#{m.get('tags', '?')}` - {m.get('name', '?')}: {m.get('trophies', 0)} trophies"
                    for m in top_members
                )
                embed.add_field(name="Top Members", value=top_text, inline=False)

            await self._safe_followup(interaction, embed=embed)

        except APIError as e:
            logger.error(f"API error fetching clan {clean_tag}: {e}")
            await self._safe_followup(interaction, f"\u274c API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in /clan command: {e}")
            await self._safe_followup(interaction, "\u274c An unexpected error occurred.")

    async def _player_impl(self, interaction: discord.Interaction, tag: str):
        """Get player information from Supercell API."""
        responded = await self._safe_respond(interaction, "\u23f3 Fetching player info...")
        if not responded:
            logger.warning("Player interaction %s already expired", interaction.id)
            return

        try:
            clean_tag = tag.lstrip("#")
            player_data = await self.api_client.get_player(clean_tag)

            if player_data is None:
                await self._safe_followup(interaction, f"\u274c Player with tag #{clean_tag} not found.")
                return

            name = player_data.get("name", "Unknown")
            trophies = player_data.get("trophies", 0)
            league = player_data.get("league", {}).get("name", "Unranked")
            role = player_data.get("role", "Member")
            donations = player_data.get("donations", 0)
            donations_received = player_data.get("donationsReceived", 0)
            war_days = player_data.get("warDays", 0)

            embed = discord.Embed(
                title=f"\U0001f464 {name}",
                description=f"Player Tag: `{clean_tag}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Trophies", value=str(trophies), inline=True)
            embed.add_field(name="League", value=league, inline=True)
            embed.add_field(name="Role", value=role, inline=True)
            embed.add_field(name="Donations", value=str(donations), inline=True)
            embed.add_field(name="Donations Received", value=str(donations_received), inline=True)
            embed.add_field(name="War Days", value=str(war_days), inline=True)

            await self._safe_followup(interaction, embed=embed)

        except APIError as e:
            logger.error(f"API error fetching player {clean_tag}: {e}")
            await self._safe_followup(interaction, f"\u274c API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in /player command: {e}")
            await self._safe_followup(interaction, "\u274c An unexpected error occurred.")
            await interaction.followup.send("\u274c An unexpected error occurred.")

    async def _config_impl(self, interaction: discord.Interaction):
        """Show current bot configuration (without sensitive data)."""
        embed = discord.Embed(
            title="\U0001f527 Bot Configuration",
            color=discord.Color.orange()
        )
        embed.add_field(name="Clan Tag", value=f"`#{self.config.clan_tag}`", inline=True)
        embed.add_field(name="API Region", value=self.config.api_region, inline=True)
        embed.add_field(name="Log Level", value=self.config.log_level, inline=True)
        embed.add_field(
            name="API Key",
            value=f"`{self.config.api_key[:8]}****` (configured)" if self.config.api_key else "Not configured",
            inline=True
        )
        embed.add_field(
            name="Bot Token",
            value="Configured \u2713" if self.config.bot_token else "Not configured",
            inline=True
        )
        # Database status: check both config URL and actual connection
        db_status = "Not configured (optional)"
        if self.db_manager:
            if self.db_manager.is_skeleton_mode():
                db_status = "Configured, but temporarily unavailable"
            else:
                db_status = "Configured \u2713"
        elif self.config.database_url:
            db_status = "Configured (manager not initialized)"
        embed.add_field(
            name="Database",
            value=db_status,
            inline=True
        )
        await self._safe_respond(interaction, embed=embed, ephemeral=True)

    async def _sync_all_impl(self, interaction: discord.Interaction):
        """Re-run full initial data sync (CWL, CW, Raids, Clan Games).

        Runs as a background task so the interaction responds immediately
        instead of timing out after the 15-minute Discord limit.
        """
        try:
            if not self.cwl_service or not self.db_manager:
                await interaction.response.send_message(
                    "\u274c Sync services not available \u2014 database must be configured."
                )
                return

            await interaction.response.send_message(
                "\u23f3 Full data sync started \u2014 this runs in the background. "
                "I'll post results when complete."
            )

            clean_tag = self.config.clan_tag.lstrip("#")
            logger.info("Manual full data sync triggered for clan #%s", clean_tag)

            # Run the actual sync in the background, catching errors so
            # the background task doesn't silently fail.
            try:
                await self._run_sync_all(interaction, clean_tag)
            except Exception as exc:
                logger.error("Background sync-all task failed: %s", exc, exc_info=True)
                await interaction.followup.send(
                    f"\u274c Sync task failed: {str(exc)}"
                )

        except Exception as e:
            logger.error(f"Sync-all command error: {e}", exc_info=True)
            await interaction.followup.send(f"\u274c Failed to start sync: {str(e)}")

    async def _run_sync_all(self, interaction: discord.Interaction, clan_tag: str):
        """Background task that performs the actual sync operations.

        Each service is run sequentially with retry logic and spacing.
        Results are posted as a followup message when complete.
        """
        results = {}
        sync_tasks = [
            ("CWL", lambda: self.cwl_service.sync_cwl(clan_tag)),
            ("Clan War", lambda: self.cw_service.sync_cw(clan_tag)),
            ("Raids", lambda: self.raid_service.sync_raids(clan_tag)),
            ("Clan Games", lambda: self.clan_games_service.sync_clan_games(clan_tag)),
        ]

        for name, sync_func in sync_tasks:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await sync_func()
                    results[name] = result
                    logger.info("%s sync result (attempt %d): %s", name, attempt + 1, result)
                    break
                except Exception as exc:
                    logger.warning("%s sync attempt %d failed: %s", name, attempt + 1, exc)
                    results[name] = {"error": str(exc)}
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.info("Retrying %s in %ds...", name, wait)
                        await asyncio.sleep(wait)
                    else:
                        logger.error("%s sync permanently failed after %d attempts", name, max_retries)

            # Spacing between different sync types to respect rate limits
            await asyncio.sleep(3)

        # Recalculate contribution scores
        if self.contribution_service and self.db_manager:
            try:
                inserted = await self.contribution_service.recalculate_scores(clan_tag)
                logger.info("Contribution scores recalculated: %d records", inserted)
                results["contributions"] = {"records": inserted}
            except Exception as exc:
                logger.error("Contribution recalc failed: %s", exc, exc_info=True)
                results["contributions"] = {"error": str(exc)}

        # Build result summary
        parts = []
        for name, result in results.items():
            if "error" in result:
                error_msg = result["error"]
                # CWL data is only available at month boundaries
                if name == "CWL" and "no active war season" in error_msg.lower():
                    error_msg += " (CWL data only available at month boundaries)"
                parts.append(f"{name}: \u274c {error_msg}")
            else:
                events = result.get("events_synced", result.get("participations_synced", result.get("records", "N/A")))
                parts.append(f"{name}: \u2705 {events}")

        embed = discord.Embed(
            title="\u2705 Full Data Sync Complete",
            description="\n".join(parts),
            color=discord.Color.green(),
        )

        try:
            await self._safe_followup(interaction, embed=embed)
        except Exception as e:
            logger.warning("Could not send sync result followup: %s", e)

        logger.info(
            "Full data sync completed: %s",
            {k: v.get("events_synced", v.get("participations_synced", "error")) for k, v in results.items()},
        )


    async def _sync_impl(
        self,
        interaction: discord.Interaction,
        entity: str = "cwl",
        tag: str = None,
    ):
        """Sync data from Supercell API (CWL, clan, etc.)."""
        responded = await self._safe_respond(interaction, "\u23f3 Syncing data...")
        if not responded:
            logger.warning("Sync interaction %s already expired — skipping", interaction.id)
            return

        try:
            if entity == "cwl":
                target_tag = tag or self.config.clan_tag
                result = await self.cwl_service.sync_cwl(target_tag)

                if "error" in result:
                    await self._safe_followup(interaction, f"\u274c {result['error']}")
                    return

                embed = discord.Embed(
                    title="\u2705 CWL Sync Complete",
                    description=f"Successfully synced CWL data for {result['clan_tag']}",
                    color=discord.Color.green(),
                )
                embed.add_field(name="Events", value=str(result["events_synced"]), inline=True)
                embed.add_field(
                    name="Participations", value=str(result["participations_synced"]), inline=True
                )
                await self._safe_followup(interaction, embed=embed)
            else:
                await self._safe_followup(interaction, f"\u274c Unknown entity: {entity}")

        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
            await self._safe_followup(interaction, f"\u274c Sync failed: {str(e)}")


    # -----------------------------------------------------------------------
    # Contribution scoring commands (Work Item #13)
    # -----------------------------------------------------------------------

    async def _contribution_impl(
        self,
        interaction: discord.Interaction,
        player: str = None,
    ):
        """Show contribution rankings or a player's score breakdown."""
        if not self.contribution_service:
            await interaction.response.send_message(
                "\u274c Contribution scoring is not available (no database configured)"
            )
            return

        try:
            if player:
                # Individual breakdown
                result = await self.contribution_service.get_player_breakdown(
                    player_tag=player,
                    clan_tag=self.config.clan_tag,
                )

                if not result:
                    await interaction.response.send_message(
                        f"\u274c No contribution data found for player `{player}`."
                    )
                    return

                embed = discord.Embed(
                    title=f"\U0001f3c6 {result['player_tag']}",
                    description="**Contribution Breakdown**",
                    color=discord.Color.gold(),
                )
                embed.add_field(
                    name="\U0001f4c6 Total Score",
                    value=f"**{int(result['total_score']):,}**",
                    inline=True,
                )
                embed.add_field(
                    name="\U0001f3f5\ufe0f CWL (x4)",
                    value=f"{int(result['cwl_score']):,}",
                    inline=True,
                )
                embed.add_field(
                    name="\U0001f94a CW (x3)",
                    value=f"{int(result['cw_score']):,}",
                    inline=True,
                )
                embed.add_field(
                    name="\U0001f94e Raid (x2)",
                    value=f"{int(result['raid_score']):,}",
                    inline=True,
                )
                embed.add_field(
                    name="\U0001f3af CG (x2)",
                    value=f"{int(result['clan_games_score']):,}",
                    inline=True,
                )
                embed.set_footer(text=f"As of {result['event_date'][:10]}")
                await interaction.response.send_message(embed=embed)
                return

            # Default: show leaderboard
            leaderboard = await self.contribution_service.get_leaderboard(
                clan_tag=self.config.clan_tag, top=10
            )

            if not leaderboard:
                await interaction.response.send_message(
                    "\u26a0\ufe0f No contribution scores found. Run `/sync` first to populate data."
                )
                return

            embed = discord.Embed(
                title="\U0001f3c6 Clan Contribution Ranking",
                color=discord.Color.gold(),
            )
            lines = []
            for entry in leaderboard:
                cw = int(entry["cw_score"])
                cwl = int(entry["cwl_score"])
                raid = int(entry["raid_score"])
                cg = int(entry["clan_games_score"])
                total = int(entry["total_score"])
                lines.append(
                    f"{entry['rank']}. `{entry['player_tag']}` \u2014 {total:,} pts  "
                    f"(CWL: {cwl:,}, CW: {cw:,}, Raid: {raid:,}, CG: {cg:,})"
                )
            embed.description = "\n".join(lines)
            embed.set_footer(text=f"Showing top 10 of {len(leaderboard)} players")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Contribution command error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Failed to fetch contribution data: {str(e)}"
            )

    # -----------------------------------------------------------------------
    # Verification commands (Work Item #12)
    # -----------------------------------------------------------------------

    async def _verify_impl(self, interaction: discord.Interaction, tag: str):
        """Verify Discord user with a Clash of Clans player tag."""
        await interaction.response.send_message("\u23f3 Verifying account...")

        try:
            clean_tag = tag.lstrip("#")
            result = await self.verification_service.verify_player(
                interaction.user.id, clean_tag
            )

            if result.get("success"):
                embed = discord.Embed(
                    title="\u2705 Verification Successful",
                    description=f"Linked Discord {interaction.user} to **{result['player_tag']}**",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name="Clan Role", value=result["role"], inline=True
                )
                role_name = self.verification_service.get_discord_role_name(
                    result["role"]
                )
                embed.add_field(name="Discord Role", value=role_name, inline=True)
                await interaction.followup.send(embed=embed)
            else:
                error_msg = result.get("error", "Unknown error")
                await interaction.followup.send(
                    f"\u274c Verification failed: {error_msg}"
                )

        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            await interaction.followup.send(
                f"\u274c Verification failed: {str(e)}"
            )

    async def _unverify_impl(self, interaction: discord.Interaction):
        """Remove Discord-to-Clash verification link."""
        session = self.db_manager.session()
        if session is None:
            await interaction.response.send_message(
                "\u274c Database unavailable. Try again later."
            )
            return
        try:
            member = session.query(Members).filter(
                Members.discord_id == str(interaction.user.id)
            ).first()

            if member:
                session.delete(member)
                session.commit()
                await interaction.response.send_message(
                    f"\u2705 Unverified. Your link to **{member.player_tag}** has been removed."
                )
            else:
                await interaction.response.send_message(
                    "\u274c You are not currently verified."
                )
        except Exception as e:
            session.rollback()
            logger.error(f"Unverify error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Unverify failed: {str(e)}"
            )
        finally:
            session.close()

    async def _myclan_impl(self, interaction: discord.Interaction):
        """Show your clan info and verified status."""
        session = self.db_manager.session()
        if session is None:
            await interaction.response.send_message(
                "\u274c Database unavailable. Try again later."
            )
            return
        try:
            member = session.query(Members).filter(
                Members.discord_id == str(interaction.user.id)
            ).first()

            if not member:
                embed = discord.Embed(
                    title="\U0001f464 Your Status",
                    description="You are not verified for this clan.",
                    color=discord.Color.red(),
                )
                embed.add_field(
                    name="What is verification?",
                    value="Use `/verify #YourPlayerTag` to link your Discord account to your Clash of Clans account.",
                )
                await interaction.response.send_message(embed=embed)
                return

            clan_data = await self.api_client.get_clan(self.config.clan_tag)
            if clan_data is None:
                await interaction.response.send_message("\u274c Could not fetch clan data.")
                return

            embed = discord.Embed(
                title=f"\U0001f464 Your Status in #{self.config.clan_tag}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Player Tag", value=f"`{member.player_tag}`", inline=True)
            embed.add_field(name="Clan Role", value=member.role, inline=True)
            embed.add_field(name="Discord", value=interaction.user.name, inline=True)
            embed.add_field(
                name="Verified Since",
                value=member.verified_at.strftime("%Y-%m-%d") if member.verified_at else "Unknown",
                inline=True,
            )

            player_data = await self.api_client.get_player(
                member.player_tag.lstrip("#")
            )
            if player_data:
                trophies = player_data.get("trophies", 0)
                league = player_data.get("league", {}).get("name", "Unranked")
                embed.add_field(name="Trophies", value=str(trophies), inline=True)
                embed.add_field(name="League", value=league, inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"MyClan error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Failed to fetch your status: {str(e)}"
            )
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Status / Query commands (Work Item #14)
    # -----------------------------------------------------------------------

    async def _status_impl(self, interaction: discord.Interaction):
        """Show bot status and database sync info."""
        from database import Clan, CwlEvents, CwEvents, RaidEvents, ClanGamesEvents, Members, ContributionScores

        session = self.db_manager.session()
        if session is None:
            embed = discord.Embed(
                title="\U0001f916 Bot Status",
                description="\u26a0\ufe0f Database unavailable — showing bot-only stats.",
                color=discord.Color.yellow(),
            )
            embed.add_field(
                name="\U0001f916 Bot Info",
                value=(
                    f"**Guilds**: {len(self.guilds)}\n"
                    f"**Latency**: {round(self.latency * 1000)} ms"
                ),
                inline=True,
            )
            embed.set_footer(
                text="Database-dependent stats (CWL, CW, Raids, Members) unavailable."
            )
            await interaction.response.send_message(embed=embed)
            return
        try:
            clan_count = session.query(Clan).count()
            cwl_events = session.query(CwlEvents).count()
            cw_events = session.query(CwEvents).count()
            raid_events = session.query(RaidEvents).count()
            cg_events = session.query(ClanGamesEvents).count()
            verified_members = session.query(Members).count()
            contribution_records = session.query(ContributionScores).count()

            embed = discord.Embed(
                title="\U0001f916 Bot Status",
                description="Current bot and database statistics",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="\U0001f916 Bot Info",
                value=(
                    f"**Guilds**: {len(self.guilds)}\n"
                    f"**Latency**: {round(self.latency * 1000)} ms"
                ),
                inline=True,
            )
            embed.add_field(
                name="\U0001f4be Database",
                value=(
                    f"**Clans**: {clan_count}\n"
                    f"**CWL Events**: {cwl_events}\n"
                    f"**CW Events**: {cw_events}\n"
                    f"**Raid Events**: {raid_events}\n"
                    f"**Clan Games Events**: {cg_events}\n"
                    f"**Verified Members**: {verified_members}\n"
                    f"**Contribution Scores**: {contribution_records}"
                ),
                inline=True,
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Status error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Failed to fetch status: {str(e)}"
            )
        finally:
            session.close()

    async def _sync_schema_impl(self, interaction: discord.Interaction):
        """Check and fix database schema mismatches (ADMIN ONLY)."""
        await interaction.response.send_message("\u23f3 Checking and fixing database schema...")

        try:
            migrations = self.db_manager.sync_schema()
            if migrations:
                embed = discord.Embed(
                    title="\u2705 Schema Migration Complete",
                    description=f"Added {len(migrations)} missing column(s).",
                    color=discord.Color.green(),
                )
                for i, stmt in enumerate(migrations[:10], 1):
                    embed.add_field(
                        name=f"Migration {i}",
                        value=f"``{stmt[:100]}``",
                        inline=False,
                    )
                if len(migrations) > 10:
                    embed.add_field(
                        name="More",
                        value=f"... and {len(migrations) - 10} more migrations",
                        inline=False,
                    )
                embed.set_footer(text="Restart the bot to apply schema changes.")
            else:
                embed = discord.Embed(
                    title="\u2705 Schema Up to Date",
                    description="No schema changes were needed.",
                    color=discord.Color.blue(),
                )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Schema sync error: {e}", exc_info=True)
            await interaction.followup.send(
                f"\u274c Schema sync failed: {str(e)}"
            )

    # -----------------------------------------------------------------------
    # Dashboard management commands (Work Item #14)
    # -----------------------------------------------------------------------

    async def _dashboard_update_impl(self, interaction: discord.Interaction):
        """Manually trigger dashboard update."""
        if not self.dashboard_manager:
            await interaction.response.send_message(
                "\u274c Dashboard is not configured. Set `DASHBOARD_CHANNEL_ID` in your environment."
            )
            return

        try:
            await self.dashboard_manager.update_all_dashboards()
            await interaction.response.send_message(
                "\U0001f4cb All dashboards updated successfully."
            )
        except Exception as e:
            logger.error(f"Dashboard update error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Dashboard error: {str(e)}"
            )

    async def _dashboard_delete_impl(self, interaction: discord.Interaction):
        """Delete dashboard messages."""
        if not self.dashboard_manager:
            await interaction.response.send_message(
                "\u274c Dashboard is not configured. Set `DASHBOARD_CHANNEL_ID` in your environment."
            )
            return

        try:
            # Stop the updater and delete all dashboards
            await self.dashboard_manager.stop()
            await interaction.response.send_message(
                "\u274c All dashboards stopped and removed."
            )
        except Exception as e:
            logger.error(f"Dashboard delete error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Dashboard error: {str(e)}"
            )

    async def _dashboard_list_impl(self, interaction: discord.Interaction):
        """List active dashboards."""
        if not self.dashboard_manager:
            await interaction.response.send_message(
                "\u274c Dashboard is not configured. Set `DASHBOARD_CHANNEL_ID` in your environment."
            )
            return

        try:
            active = list(self.dashboard_manager._messages.keys())
            if active:
                status = "\n".join(
                    f"- `{d}`: {msg.id}"
                    for d, msg in self.dashboard_manager._messages.items()
                )
                embed = discord.Embed(
                    title="\U0001f4cb Active Dashboards",
                    description=status,
                    color=discord.Color.green(),
                )
                interval = self.config.dashboard.update_interval_seconds
                embed.set_footer(text=f"Updates every {interval}s")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "No active dashboards. Use `/dashboard update` to create one."
                )
        except Exception as e:
            logger.error(f"Dashboard list error: {e}", exc_info=True)
            await interaction.response.send_message(
                f"\u274c Dashboard error: {str(e)}"
            )


async def create_bot(config: BotConfig, db_manager: DatabaseManager = None) -> AliceIsBoredBot:
    """Create and configure the bot instance."""
    session = aiohttp.ClientSession()
    api_client = SupercellAPIClient(
        api_key=config.api_key,
        session=session,
    )
    bot = AliceIsBoredBot(config=config, api_client=api_client, db_manager=db_manager)
    bot.session = session
    return bot


async def health_check(bot: AliceIsBoredBot) -> dict:
    """Perform a health check on the bot."""
    await bot.ready_event.wait()
    return {
        "status": "healthy",
        "user": str(bot.user),
        "guilds": len(bot.guilds),
    }


async def main():
    """Main entry point."""
    config = BotConfig()
    logger.info(f"Starting AliceIsBored bot for clan '#{config.clan_tag}'")

    # Initialize database — Azure SQL with pause-resume retry
    database_url = get_default_database_url(environment="azure")
    db_manager = DatabaseManager(config=config)
    logger.info(f"Database URL: {DatabaseManager._sanitize_url(database_url)}")
    db_manager._initialize(database_url)
    if db_manager.is_skeleton_mode():
        logger.warning(
            "Azure SQL is unavailable — starting in skeleton mode. "
            "Database-dependent features (CWL, CW, Raid, Clan Games, verification, "
            "contribution scoring, leaderboard) are disabled. "
            "Ping/basic commands still work. "
            "The bot will automatically attempt to reconnect when Azure SQL resumes — "
            "the first database-dependent command after resume will trigger reconnection."
        )
    else:
        db_manager.create_tables()
        db_manager.sync_schema()
        logger.info("Azure SQL database connected and tables initialized")

    bot = await create_bot(config, db_manager)

    def handle_sigint():
        logger.info("Received shutdown signal. Cleaning up...")
        bot.loop.stop()

    loop = asyncio.get_event_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_sigint)
            except NotImplementedError:
                pass  # Windows doesn't support add_signal_handler

        await bot.start(config.bot_token)
    except discord.PrivilegedIntentsRequired:
        logger.error("Privileged intents are required. Enable them in Discord Developer Portal.")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        raise
    finally:
        # Clean up the session
        if bot.session:
            await bot.session.close()
        # Stop dashboard updater
        if bot.dashboard_manager:
            await bot.dashboard_manager.stop()
        await bot.api_client.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())