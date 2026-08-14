"""
Discord Bot for AliceIsBored Clan - Main Entry Point
Implements: Work Item #7 - Discord bot framework with Supercell API integration
"""

import asyncio
import logging
import os
import signal
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

from config import BotConfig
from api_client import SupercellAPIClient, APIError

# Load environment variables
_load_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_load_path)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AliceIsBoredBot(commands.Bot):
    """Main Discord bot client for AliceIsBored clan."""

    def __init__(self, config: BotConfig, api_client: SupercellAPIClient):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(intents=intents, command_prefix="!")

        self.config = config
        self.api_client = api_client
        self.ready_event = asyncio.Event()
        self.session: Optional[aiohttp.ClientSession] = None

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
        await interaction.response.send_message("\u23f3 Fetching clan info...")

        try:
            clean_tag = tag.lstrip("#")
            clan_data = await self.api_client.get_clan(clean_tag)

            if clan_data is None:
                await interaction.followup.send(f"\u274c Clan with tag #{clean_tag} not found.")
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

            await interaction.followup.send(embed=embed)

        except APIError as e:
            logger.error(f"API error fetching clan {clean_tag}: {e}")
            await interaction.followup.send(f"\u274c API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in /clan command: {e}")
            await interaction.followup.send("\u274c An unexpected error occurred.")

    async def _player_impl(self, interaction: discord.Interaction, tag: str):
        """Get player information from Supercell API."""
        await interaction.response.send_message("\u23f3 Fetching player info...")

        try:
            clean_tag = tag.lstrip("#")
            player_data = await self.api_client.get_player(clean_tag)

            if player_data is None:
                await interaction.followup.send(f"\u274c Player with tag #{clean_tag} not found.")
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

            await interaction.followup.send(embed=embed)

        except APIError as e:
            logger.error(f"API error fetching player {clean_tag}: {e}")
            await interaction.followup.send(f"\u274c API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in /player command: {e}")
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
        embed.add_field(
            name="Database",
            value="Configured \u2713" if self.config.database_url else "Not configured (optional)",
            inline=True
        )
        await interaction.response.send_message(embed=embed)


async def create_bot(config: BotConfig) -> AliceIsBoredBot:
    """Create and configure the bot instance."""
    session = aiohttp.ClientSession()
    api_client = SupercellAPIClient(
        api_key=config.api_key,
        session=session,
    )
    bot = AliceIsBoredBot(config=config, api_client=api_client)
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

    bot = await create_bot(config)

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
        await bot.api_client.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())