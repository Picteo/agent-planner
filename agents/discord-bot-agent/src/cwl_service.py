"""
CWL (Clan War League) service for AliceIsBored Discord bot.

Handles fetching CWL data from Supercell API and persisting it
to the database via SQLAlchemy ORM models.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from database import CwlEvents, CwlParticipations, Clan, DatabaseManager

if TYPE_CHECKING:
    from api_client import SupercellAPIClient

logger = logging.getLogger(__name__)


class CwlService:
    """Fetches CWL data from Supercell API and persists it to the database."""

    def __init__(self, api_client: "SupercellAPIClient", db_manager: DatabaseManager):
        self._api_client = api_client
        self._db = db_manager

    async def sync_cwl(self, clan_tag: str) -> dict:
        """Fetch CWL data for a clan and persist to database.

        Args:
            clan_tag: Clan tag to fetch CWL data for (with or without '#').

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

            cwl_data = await self._api_client.get_clan_warl_states(clan.clan_tag)
            if cwl_data is None:
                return {"error": f"No CWL data available for clan #{clean_tag}"}

            seasons = cwl_data.get("warSeasons", [])
            total_events = 0
            total_participations = 0

            for season in seasons:
                result = await self._process_season(session, clan, season)
                total_events += 1
                total_participations += result.get("participations", 0)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        logger.info(
            "CWL sync complete for clan #%s: %d events, %d participations",
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

    async def _process_season(self, session, clan, season: dict) -> dict:
        """Process a single CWL season and persist event + participations."""
        season_id = season.get("tags", "")
        start_raw = season.get("warStart", "")
        end_raw = season.get("warEnd", "")

        start_time = self._parse_iso_datetime(start_raw)
        end_time = self._parse_iso_datetime(end_raw)

        event = CwlEvents(
            clan_id=clan.id,
            clan_tag=clan.clan_tag,
            season_id=season_id,
            league_name=season.get("league", {}).get("name"),
            division=season.get("division"),
            war_count=season.get("warCount", 0),
            total_wins=season.get("totalWins", 0),
            start_time=start_time,
            end_time=end_time,
        )
        session.add(event)
        session.flush()

        day_groups = season.get("dayGroups", [])
        participation_count = 0

        for day_group in day_groups:
            day_number = day_group.get("dayNumber", 0)
            player_groups = day_group.get("playerGroups", [])

            for player_group in player_groups:
                player_tag = player_group.get("player", {}).get("tags", "")
                if not player_tag:
                    continue

                participation = CwlParticipations(
                    event_id=event.id,
                    player_tag=player_tag,
                    day_number=day_number,
                    attacks_used=player_group.get("attacksUsed", 0),
                    war_count_comparison=player_group.get("warCountComparison", 0),
                    stars_collected=player_group.get("starsCollected", 0),
                    damage_percentage=player_group.get("damagePercentage", 0.0),
                    clan_trophy_earned=player_group.get("clanTrophyEarned", 0),
                    bonus_bases_destroyed=player_group.get("bonusBasesDestroyed", 0),
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
