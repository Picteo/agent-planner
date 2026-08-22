"""
Verification service for AliceIsBored Discord bot.

Handles Discord user verification against Supercell API,
clan member verification, and Discord role assignment.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from database import Clan, DatabaseManager, Members, Player

if TYPE_CHECKING:
    from api_client import SupercellAPIClient

logger = logging.getLogger(__name__)

# Discord role names for different clan roles
ROLE_MAPPING = {
    "Leader": "Clan Leader",
    "CoLeader": "Co-Leader",
    "Elder": "Elder",
    "Member": "Member",
}


class VerificationService:
    """Handles Discord user verification and role assignment."""

    def __init__(self, api_client: "SupercellAPIClient", db_manager: DatabaseManager):
        self._api_client = api_client
        self._db = db_manager

    async def verify_player(self, discord_user_id: int, player_tag: str) -> dict:
        """Verify a Discord user against Supercell API and link to a clan player.

        Args:
            discord_user_id: Discord user ID to verify.
            player_tag: Clash of Clans player tag to verify against.

        Returns:
            A dict with verification result details.
        """
        clean_tag = player_tag.lstrip("#")

        session = self._db.session()
        if session is None:
            return {"success": False, "error": "Database unavailable"}
        try:
            # Check if already verified
            existing = session.query(Members).filter(
                Members.discord_id == str(discord_user_id)
            ).first()
            if existing:
                return {
                    "success": False,
                    "error": "Already verified",
                    "player_tag": existing.player_tag,
                }

            # Fetch player from Supercell API
            player_data = await self._api_client.get_player(clean_tag)
            if player_data is None:
                return {"success": False, "error": f"Player #{clean_tag} not found"}

            # Check if player is in our clan
            clan_data = await self._api_client.get_clan(self._db.config.clan_tag)
            if clan_data is None:
                return {"error": "Could not fetch clan data for verification"}

            clan_member = None
            for member in clan_data.get("members", []):
                if member.get("tags", "").lstrip("#") == clean_tag:
                    clan_member = member
                    break

            if clan_member is None:
                return {
                    "success": False,
                    "error": f"Player #{clean_tag} is not a member of #{self._db.config.clan_tag}",
                }

            # Upsert player data
            player = await self._upsert_player(session, player_data)

            # Create membership record
            member = Members(
                player_tag=player_data.get("tags", f"#{clean_tag}"),
                discord_id=str(discord_user_id),
                role=clan_member.get("role", "Member"),
                verified_at=datetime.now(timezone.utc),
            )
            session.add(member)
            session.commit()

            logger.info(
                "Verified player %s (Discord %d)", clean_tag, discord_user_id
            )
            return {
                "success": True,
                "player_tag": member.player_tag,
                "role": member.role,
            }

        except Exception as e:
            session.rollback()
            logger.error("Verification failed: %s", e, exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    async def _upsert_player(self, session, player_data: dict) -> Player:
        """Upsert player data from API response."""
        player_tag = player_data.get("tags", "")
        player = session.query(Player).filter(Player.player_tag == player_tag).first()

        if player:
            player.player_name = player_data.get("name", player.player_name)
            player.trophies = player_data.get("trophies", player.trophies)
            player.attack_wins = player_data.get("attackWins", player.attack_wins)
            player.donations = player_data.get("donations", player.donations)
            player.donations_received = player_data.get(
                "donationsReceived", player.donations_received
            )
            player.war_days = player_data.get("warDays", player.war_days)
            player.exp_level = player_data.get("expLevel", player.exp_level)
            league = player_data.get("league", {})
            if league:
                player.league_id = league.get("id", player.league_id)
                player.league_name = league.get("name", player.league_name)
        else:
            league = player_data.get("league", {})
            player = Player(
                player_tag=player_tag,
                player_name=player_data.get("name", "Unknown"),
                trophies=player_data.get("trophies", 0),
                attack_wins=player_data.get("attackWins", 0),
                role=player_data.get("role", "Member"),
                donations=player_data.get("donations", 0),
                donations_received=player_data.get("donationsReceived", 0),
                war_days=player_data.get("warDays", 0),
                exp_level=player_data.get("expLevel", 0),
                league_id=league.get("id", 0),
                league_name=league.get("name", "Unranked"),
            )
            session.add(player)
        return player

    def get_discord_role_name(self, coc_role: str) -> str:
        """Map Clash of Clans role to Discord display name."""
        return ROLE_MAPPING.get(coc_role, "Member")
