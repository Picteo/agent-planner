"""
Contribution scoring for AliceIsBored Discord bot.

Implements a unified contribution scoring engine that aggregates
participation data from CWL, CW, Raids, and Clan Games into per-member scores.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from database import (
    ClanGamesEvents,
    ClanGamesParticipations,
    ContributionScores,
    CwEvents,
    CwParticipations,
    CwlEvents,
    CwlParticipations,
    DatabaseManager,
    RaidEvents,
    RaidParticipations,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights and formulas
# ---------------------------------------------------------------------------

# Weight per event type (applied to the sum of that type's raw scores)
CWL_WEIGHT = 4
CW_WEIGHT = 3
RAID_WEIGHT = 2
CG_WEIGHT = 2

# CWL scoring
CWL_BASE_PER_DAY = 10.0      # pts per day of participation
CWL_STARS = 2.0             # pts per star
CWL_DAMAGE = 0.5            # pts per % damage

# CW scoring
CW_BASE_PER_DAY = 8.0       # pts per day of participation
CW_STARS = 2.0              # pts per star

# Raid scoring
RAID_PER_ATTACK = 5.0       # pts per attack
RAID_POINTS = 0.1           # pts per 100 points reached

# Clan Games scoring
CG_POINTS = 5.0             # pts per 100 points contributed


class ContributionService:
    """Calculates and persists contribution scores from all event types."""

    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def recalculate_scores(
        self,
        clan_tag: str = "AliceIsBored",
        as_of: Optional[datetime] = None,
    ) -> int:
        """Recalculate contribution scores for all players in the clan.

        Deletes existing scores for the given clan_tag and event_date,
        then computes and inserts new scores based on all event types.

        Args:
            clan_tag: The clan tag to calculate scores for.
            as_of: Optional datetime to cap the event_date (defaults to now).

        Returns:
            Number of score records inserted.
        """
        event_date = as_of or datetime.now(timezone.utc)
        clean_tag = clan_tag.lstrip("#")

        session = self._db.session()
        if session is None:
            raise RuntimeError("Database unavailable")
        try:
            # 1. Collect raw data
            cwl_data = self._fetch_cwl_scores(session, clean_tag)
            cw_data = self._fetch_cw_scores(session, clean_tag)
            raid_data = self._fetch_raid_scores(session)
            cg_data = self._fetch_cg_scores(session)

            # 2. Merge by player_tag
            all_player_tags = set(
                cwl_data.keys()
                | cw_data.keys()
                | raid_data.keys()
                | cg_data.keys()
            )

            # 3. Delete existing scores for this date
            session.query(ContributionScores).filter(
                ContributionScores.event_date == event_date
            ).delete()

            inserted = 0
            for player_tag in all_player_tags:
                raw = {
                    "cwl": cwl_data.get(player_tag, 0.0),
                    "cw": cw_data.get(player_tag, 0.0),
                    "raid": raid_data.get(player_tag, 0.0),
                    "cg": cg_data.get(player_tag, 0.0),
                }
                score = self._apply_scoring(raw)
                record = ContributionScores(
                    player_tag=player_tag,
                    event_date=event_date,
                    cwl_score=score["cwl"],
                    cw_score=score["cw"],
                    raid_score=score["raid"],
                    clan_games_score=score["cg"],
                    total_score=score["total"],
                )
                session.add(record)
                inserted += 1

            session.commit()
            logger.info(
                "Recalculated %d contribution scores for clan #%s (as_of=%s)",
                inserted, clean_tag, event_date.isoformat(),
            )
            return inserted

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_leaderboard(
        self,
        clan_tag: str = "AliceIsBored",
        top: int = 20,
    ) -> List[Dict]:
        """Return a ranked leaderboard of contribution scores.

        Returns the most recent scores (by event_date DESC), limited to ``top`` players.

        Returns:
            List of dicts with keys: rank, player_tag, total_score, cwl_score, cw_score,
            raid_score, clan_games_score.
        """
        session = self._db.session()
        if session is None:
            return []
        try:
            latest = (
                session.query(ContributionScores)
                .order_by(ContributionScores.event_date.desc())
                .first()
            )
            if not latest:
                return []

            records = (
                session.query(ContributionScores)
                .filter(
                    ContributionScores.event_date == latest.event_date
                )
                .order_by(ContributionScores.total_score.desc())
                .limit(top)
                .all()
            )
            return [
                {
                    "rank": i + 1,
                    "player_tag": r.player_tag,
                    "total_score": float(r.total_score),
                    "cwl_score": float(r.cwl_score),
                    "cw_score": float(r.cw_score),
                    "raid_score": float(r.raid_score),
                    "clan_games_score": float(r.clan_games_score),
                }
                for i, r in enumerate(records)
            ]

        finally:
            session.close()

    async def get_player_breakdown(
        self,
        player_tag: str,
        clan_tag: str = "AliceIsBored",
    ) -> Optional[Dict]:
        """Return the latest contribution score breakdown for a single player.

        Args:
            player_tag: The player tag to look up (with or without '#').
            clan_tag: Clan tag used to determine the date range for the latest score.

        Returns:
            Dict with player_tag, total_score, event_date, and per-event scores,
            or None if the player has no scores.
        """
        clean_tag = player_tag.lstrip("#")
        session = self._db.session()
        if session is None:
            return None
        try:
            latest = (
                session.query(ContributionScores)
                .filter(ContributionScores.player_tag == clean_tag)
                .order_by(ContributionScores.event_date.desc())
                .first()
            )
            if not latest:
                return None
            return {
                "player_tag": latest.player_tag,
                "event_date": latest.event_date.isoformat(),
                "total_score": float(latest.total_score),
                "cwl_score": float(latest.cwl_score),
                "cw_score": float(latest.cw_score),
                "raid_score": float(latest.raid_score),
                "clan_games_score": float(latest.clan_games_score),
            }

        finally:
            session.close()

    # ------------------------------------------------------------------
    # Raw score fetchers - query DB and return player_tag -> raw_score
    # ------------------------------------------------------------------

    def _fetch_cwl_scores(self, session, clan_tag: str) -> Dict[str, float]:
        """Aggregate raw CWL scores per player.

        Returns dict mapping player_tag -> sum of
        (base_per_day * unique_days + stars * CWL_STARS + damage% * CWL_DAMAGE)
        """
        result: Dict[str, float] = {}
        rows = session.query(
            CwlParticipations.player_tag,
            CwlParticipations.event_id,
            CwlParticipations.stars_collected,
            CwlParticipations.damage_percentage,
        ).join(
            CwlEvents, CwlParticipations.event_id == CwlEvents.id
        ).filter(
            CwlEvents.clan_tag == clan_tag,
        ).all()

        # group by player_tag + day to count unique days
        player_days: Dict[str, set] = {}
        player_stats: Dict[str, dict] = {}
        for player_tag, event_id, stars, dmg_pct in rows:
            if player_tag not in player_days:
                player_days[player_tag] = set()
                player_stats[player_tag] = {"stars": 0, "dmg_pct": 0.0}
            player_days[player_tag].add(event_id)  # rough day grouping
            player_stats[player_tag]["stars"] += stars
            player_stats[player_tag]["dmg_pct"] += dmg_pct or 0.0

        for player_tag, days in player_days.items():
            stats = player_stats[player_tag]
            raw = (
                len(days) * CWL_BASE_PER_DAY
                + stats["stars"] * CWL_STARS
                + stats["dmg_pct"] * CWL_DAMAGE
            )
            result[player_tag] = raw

        logger.debug("Fetched CWL raw scores for %d players", len(result))
        return result

    def _fetch_cw_scores(self, session, clan_tag: str) -> Dict[str, float]:
        """Aggregate raw CW scores per player.

        Returns dict mapping player_tag -> sum of
        (base_per_day * unique_days + stars * CW_STARS)
        """
        result: Dict[str, float] = {}
        rows = session.query(
            CwParticipations.player_tag,
            CwParticipations.event_id,
            CwParticipations.day_number,
            CwParticipations.stars_collected,
        ).join(
            CwEvents, CwParticipations.event_id == CwEvents.id
        ).filter(
            CwEvents.clan_tag == clan_tag,
        ).all()

        player_days: Dict[str, set] = {}
        player_stats: Dict[str, dict] = {}
        for player_tag, event_id, day, stars in rows:
            if player_tag not in player_days:
                player_days[player_tag] = set()
                player_stats[player_tag] = {"stars": 0}
            player_days[player_tag].add((event_id, day))
            player_stats[player_tag]["stars"] += stars

        for player_tag, days in player_days.items():
            stats = player_stats[player_tag]
            raw = (
                len(days) * CW_BASE_PER_DAY
                + stats["stars"] * CW_STARS
            )
            result[player_tag] = raw

        logger.debug("Fetched CW raw scores for %d players", len(result))
        return result

    def _fetch_raid_scores(self, session) -> Dict[str, float]:
        """Aggregate raw Raid scores per player.

        Returns dict mapping player_tag -> sum of
        (attacks_used * RAID_PER_ATTACK + points_reached * RAID_POINTS / 100)
        """
        result: Dict[str, float] = {}
        rows = session.query(
            RaidParticipations.player_tag,
            RaidParticipations.attacks_used,
            RaidParticipations.points_reached,
        ).all()

        for player_tag, attacks, points in rows:
            raw = (
                attacks * RAID_PER_ATTACK
                + points * RAID_POINTS / 100.0
            )
            result[player_tag] = result.get(player_tag, 0.0) + raw

        logger.debug("Fetched Raid raw scores for %d players", len(result))
        return result

    def _fetch_cg_scores(self, session) -> Dict[str, float]:
        """Aggregate raw Clan Games scores per player.

        Returns dict mapping player_tag -> sum of points_contributed * CG_POINTS / 100
        """
        result: Dict[str, float] = {}
        rows = session.query(
            ClanGamesParticipations.player_tag,
            ClanGamesParticipations.points_contributed,
        ).all()

        for player_tag, points in rows:
            raw = points * CG_POINTS / 100.0
            result[player_tag] = result.get(player_tag, 0.0) + raw

        logger.debug("Fetched Clan Games raw scores for %d players", len(result))
        return result

    # ------------------------------------------------------------------
    # Scoring formula
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_scoring(raw: Dict[str, float]) -> Dict[str, float]:
        """Apply weights and return weighted scores + total.

        Args:
            raw: Dict with keys 'cwl', 'cw', 'raid', 'cg' containing raw scores.

        Returns:
            Dict with weighted 'cwl_score', 'cw_score', 'raid_score',
            'clan_games_score', and 'total' (sum of weighted scores).
        """
        cwl_weighted = raw["cwl"] * CWL_WEIGHT
        cw_weighted = raw["cw"] * CW_WEIGHT
        raid_weighted = raw["raid"] * RAID_WEIGHT
        cg_weighted = raw["cg"] * CG_WEIGHT
        total = cwl_weighted + cw_weighted + raid_weighted + cg_weighted

        return {
            "cwl": cwl_weighted,
            "cw": cw_weighted,
            "raid": raid_weighted,
            "cg": cg_weighted,
            "total": total,
        }
