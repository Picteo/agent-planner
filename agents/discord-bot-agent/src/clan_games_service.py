"""
Clan Games service for AliceIsBored Discord bot.

Handles fetching Clan Games data from Supercell API
and persisting it to the database via SQLAlchemy ORM models.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from database import Clan, ClanGamesEvents, ClanGamesParticipations, DatabaseManager

if TYPE_CHECKING:
    from api_client import SupercellAPIClient

logger = logging.getLogger(__name__)


class ClanGamesService:
    """Fetches Clan Games data from Supercell API and persists it to the database."""

    def __init__(self, api_client: "SupercellAPIClient", db_manager: DatabaseManager):
        self._api_client = api_client
        self._db = db_manager

    async def sync_clan_games(self, clan_tag: str, season_id: str = None) -> dict:
        """Fetch Clan Games data for a clan and persist to database.

        Args:
            clan_tag: Clan tag to fetch Clan Games data for (with or without '#').
            season_id: Optional season ID filter. If None, fetches active season.

        Returns:
            A summary dict with counts of events and participations synced.
        """
        clean_tag = clan_tag.lstrip("#")

        session = self._db.session()
        if session is None:
            return {"error": "Database unavailable"}
        try:
            clan = await self._fetch_and_upsert_clan(session, clean_tag)
            if clan is None:
                return {"error": f"Clan #{clean_tag} not found"}

            params = {"seasonId": season_id} if season_id else None
            cg_data = await self._api_client.get_clan_games(str(clan.id), season_id or "")
            if cg_data is None:
                return {"error": f"No Clan Games data available for clan #{clean_tag}"}

            challenges = cg_data.get("challenges", [])
            total_events = 0
            total_participations = 0

            for challenge in challenges:
                result = await self._process_challenge(session, challenge)
                total_events += 1
                total_participations += result.get("participations", 0)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        logger.info(
            "Clan Games sync complete for clan #%s: %d events, %d participations",
            clean_tag, total_events, total_participations,
        )
        return {
            "clan_tag": f"#{clean_tag}",
            "events_synced": total_events,
            "participations_synced": total_participations,
        }

    async def _fetch_and_upsert_clan(self, session, clan_tag: str):
        """Fetch clan from API and upsert to database."""
        existing = session.query(Clan).filter(Clan.clan_tag == clan_tag).first()
        if existing:
            return existing

        clan_data = await self._api_client.get_clan(clan_tag)
        if clan_data is None:
            logger.warning("Clan #%s not found in API", clan_tag)
            return None

        clan = Clan(
            clan_tag=clan_data.get("tags", f"#{clan_tag}"),
            clan_name=clan_data.get("name", "Unknown"),
            clan_level=clan_data.get("clanPointVictories", 0),
            trophies=clan_data.get("trophies", 0),
            war_frequency=clan_data.get("warFrequency", "Unknown"),
            war_stage_frequency=clan_data.get("warStageFrequency", "Unknown"),
            required_trophies=clan_data.get("requiredTrophies", 0),
            clan_points=clan_data.get("clanPoints", 0),
            clan_point_victories=clan_data.get("clanPointVictories", 0),
            region_name=clan_data.get("region", {}).get("name", "Unknown"),
            description=clan_data.get("description", ""),
        )
        session.add(clan)
        session.flush()
        logger.debug("Upserted clan #%s (id=%d)", clan_tag, clan.id)
        return clan

    async def _process_challenge(self, session, challenge: dict) -> dict:
        """Process a single Clan Games challenge and persist participation records."""
        start_raw = challenge.get("start", "")
        end_raw = challenge.get("end", "")

        start_time = self._parse_iso_datetime(start_raw)
        end_time = self._parse_iso_datetime(end_raw)

        event = ClanGamesEvents(
            start_time=start_time,
            end_time=end_time,
        )
        session.add(event)
        session.flush()

        player_groups = challenge.get("playerGroups", [])
        participation_count = 0

        for player_group in player_groups:
            player_tag = player_group.get("player", {}).get("tags", "")
            if not player_tag:
                continue

            participation = ClanGamesParticipations(
                event_id=event.id,
                player_tag=player_tag,
                points_contributed=player_group.get("pointsContributed", 0),
                milestone_reached=player_group.get("milestoneReached", ""),
            )
            session.add(participation)
            participation_count += 1

        session.flush()
        return {"participations": participation_count}

    @staticmethod
    def _parse_iso_datetime(dt_string: str) -> datetime:
        """Parse an ISO-8601 datetime string to a timezone-aware datetime."""
        if not dt_string:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            logger.warning("Could not parse datetime: %s", dt_string)
            return datetime(1970, 1, 1, tzinfo=timezone.utc)

