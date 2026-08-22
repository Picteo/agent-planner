"""Unit tests for contribution_service module."""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from contribution_service import (
    ContributionService,
    CWL_WEIGHT,
    CW_WEIGHT,
    RAID_WEIGHT,
    CG_WEIGHT,
)


class TestScoringConstants(unittest.TestCase):
    """Test that scoring constants are defined correctly."""

    def test_cwl_weight(self):
        self.assertEqual(CWL_WEIGHT, 4)

    def test_cw_weight(self):
        self.assertEqual(CW_WEIGHT, 3)

    def test_raid_weight(self):
        self.assertEqual(RAID_WEIGHT, 2)

    def test_cg_weight(self):
        self.assertEqual(CG_WEIGHT, 2)


class TestContributionServiceInit(unittest.TestCase):
    """Test ContributionService initialization."""

    def test_init_stores_db_manager(self):
        mock_db = MagicMock()
        service = ContributionService(mock_db)
        self.assertEqual(service._db, mock_db)


class TestApplyScoring(unittest.TestCase):
    """Test the scoring formula."""

    def test_empty_scores(self):
        raw = {"cwl": 0.0, "cw": 0.0, "raid": 0.0, "cg": 0.0}
        result = ContributionService._apply_scoring(raw)
        self.assertEqual(result["total"], 0.0)
        self.assertEqual(result["cwl"], 0.0)

    def test_cwl_only(self):
        raw = {"cwl": 100.0, "cw": 0.0, "raid": 0.0, "cg": 0.0}
        result = ContributionService._apply_scoring(raw)
        self.assertEqual(result["cwl"], 400.0)
        self.assertEqual(result["total"], 400.0)

    def test_cw_only(self):
        raw = {"cwl": 0.0, "cw": 100.0, "raid": 0.0, "cg": 0.0}
        result = ContributionService._apply_scoring(raw)
        self.assertEqual(result["cw"], 300.0)
        self.assertEqual(result["total"], 300.0)

    def test_raid_only(self):
        raw = {"cwl": 0.0, "cw": 0.0, "raid": 100.0, "cg": 0.0}
        result = ContributionService._apply_scoring(raw)
        self.assertEqual(result["raid"], 200.0)
        self.assertEqual(result["total"], 200.0)

    def test_cg_only(self):
        raw = {"cwl": 0.0, "cw": 0.0, "raid": 0.0, "cg": 100.0}
        result = ContributionService._apply_scoring(raw)
        self.assertEqual(result["cg"], 200.0)
        self.assertEqual(result["total"], 200.0)

    def test_all_event_types(self):
        raw = {"cwl": 100.0, "cw": 200.0, "raid": 50.0, "cg": 30.0}
        result = ContributionService._apply_scoring(raw)
        # CWL: 100 * 4 = 400, CW: 200 * 3 = 600, Raid: 50 * 2 = 100, CG: 30 * 2 = 60
        self.assertEqual(result["cwl"], 400.0)
        self.assertEqual(result["cw"], 600.0)
        self.assertEqual(result["raid"], 100.0)
        self.assertEqual(result["cg"], 60.0)
        self.assertEqual(result["total"], 1160.0)


class TestGetLeaderboardEmpty(unittest.TestCase):
    """Test leaderboard returns empty list when no scores exist."""

    def test_empty_leaderboard(self):
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.order_by.return_value.first.return_value = None
        mock_db.session.return_value = mock_session

        service = ContributionService(mock_db)

        import asyncio

        async def run():
            result = await service.get_leaderboard(clan_tag="AliceIsBored", top=10)
            self.assertEqual(result, [])

        asyncio.run(run())


class TestGetPlayerBreakdownEmpty(unittest.TestCase):
    """Test player breakdown returns None when no data exists."""

    def test_empty_breakdown(self):
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.session.return_value = mock_session

        service = ContributionService(mock_db)

        import asyncio

        async def run():
            result = await service.get_player_breakdown(player_tag="Player1")
            self.assertIsNone(result)

        asyncio.run(run())


class TestGetPlayerBreakdownWithData(unittest.TestCase):
    """Test player breakdown with actual data."""

    def test_breakdown_with_data(self):
        mock_db = MagicMock()
        mock_score = MagicMock()
        mock_score.player_tag = "#Player1"
        mock_score.event_date.isoformat.return_value = "2024-01-15T10:00:00+00:00"
        mock_score.total_score = 500.0
        mock_score.cwl_score = 400.0
        mock_score.cw_score = 50.0
        mock_score.raid_score = 30.0
        mock_score.clan_games_score = 20.0

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_score
        mock_db.session.return_value = mock_session

        service = ContributionService(mock_db)

        import asyncio

        async def run():
            result = await service.get_player_breakdown(player_tag="#Player1")
            self.assertIsNotNone(result)
            self.assertEqual(result["total_score"], 500.0)
            self.assertEqual(result["cwl_score"], 400.0)
            self.assertEqual(result["raid_score"], 30.0)

        asyncio.run(run())


class TestGetLeaderboardWithData(unittest.TestCase):
    """Test leaderboard with actual data."""

    def test_leaderboard_with_data(self):
        mock_db = MagicMock()
        mock_session = MagicMock()

        # latest score record
        mock_latest = MagicMock()
        mock_latest.event_date = "2024-01-15T10:00:00+00:00"

        # individual score records
        mock_r1 = MagicMock()
        mock_r1.player_tag = "#AliceIsBored"
        mock_r1.total_score = 500.0
        mock_r1.cwl_score = 400.0
        mock_r1.cw_score = 50.0
        mock_r1.raid_score = 30.0
        mock_r1.clan_games_score = 20.0

        mock_r2 = MagicMock()
        mock_r2.player_tag = "#Player2"
        mock_r2.total_score = 200.0
        mock_r2.cwl_score = 160.0
        mock_r2.cw_score = 20.0
        mock_r2.raid_score = 10.0
        mock_r2.clan_games_score = 10.0

        mock_session.query.return_value.order_by.return_value.first.return_value = mock_latest
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_r1, mock_r2]
        mock_db.session.return_value = mock_session

        service = ContributionService(mock_db)

        import asyncio

        async def run():
            result = await service.get_leaderboard(clan_tag="AliceIsBored", top=10)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["rank"], 1)
            self.assertEqual(result[0]["total_score"], 500.0)
            self.assertEqual(result[1]["rank"], 2)
            self.assertEqual(result[1]["total_score"], 200.0)

        asyncio.run(run())


class TestRecalculateScoresIntegration(unittest.TestCase):
    """Test recalculate_scores with mocked DB returns count of inserted records."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.mock_session.query = MagicMock()
        self.mock_session.add = MagicMock()
        self.mock_session.commit = MagicMock()
        self.mock_session.rollback = MagicMock()
        self.mock_session.close = MagicMock()
        self.mock_db.session.return_value = self.mock_session

    def test_recalculate_empty_data(self):
        """Test recalculate with no data in participation tables."""
        # Setup delete query
        delete_q = MagicMock()
        delete_q.filter.return_value.delete.return_value = 0
        self.mock_session.query.return_value = delete_q

        # Setup fetch queries - all return empty
        def mock_query(*args, **kwargs):
            q = MagicMock()
            q.join = MagicMock(return_value=q)
            q.filter = MagicMock(return_value=q)
            q.all.return_value = []
            return q
        self.mock_session.query.side_effect = mock_query

        service = ContributionService(self.mock_db)

        import asyncio

        async def run():
            result = await service.recalculate_scores(clan_tag="TestClan")
            self.assertEqual(result, 0)
            self.mock_session.commit.assert_called_once()

        asyncio.run(run())

    def test_recalculate_with_cwl_data(self):
        """Test recalculate with CWL data for one player."""
        delete_q = MagicMock()
        delete_q.filter.return_value.delete.return_value = 0
        self.mock_session.query.return_value = delete_q

        call_num = [0]

        def mock_query(*args, **kwargs):
            q = MagicMock()
            q.join = MagicMock(return_value=q)
            q.filter = MagicMock(return_value=q)
            call_num[0] += 1
            if call_num[0] == 1:
                # First query is CWL
                q.all.return_value = [
                    ("#Player1", 1, 10, 95.0),
                ]
            else:
                # All others are empty
                q.all.return_value = []
            return q
        self.mock_session.query.side_effect = mock_query

        service = ContributionService(self.mock_db)

        import asyncio

        async def run():
            result = await service.recalculate_scores(clan_tag="TestClan")
            self.assertEqual(result, 1)
            self.mock_session.commit.assert_called_once()
            self.assertEqual(self.mock_session.add.call_count, 1)

        asyncio.run(run())


class TestScoringFormulas(unittest.TestCase):
    """Test raw score calculations from individual event types."""

    def test_cwl_calculation(self):
        """Test CWL: base_per_day * days + stars * CWL_STARS + dmg * CWL_DAMAGE"""
        from contribution_service import (
            CWL_BASE_PER_DAY,
            CWL_DAMAGE,
            CWL_STARS,
        )
        # 2 days, 10 stars, 95% damage
        raw = 2 * CWL_BASE_PER_DAY + 10 * CWL_STARS + 95.0 * CWL_DAMAGE
        self.assertEqual(raw, 20 + 20 + 47.5)

    def test_cw_calculation(self):
        """Test CW: base_per_day * days + stars * CW_STARS"""
        from contribution_service import CW_BASE_PER_DAY, CW_STARS
        # 1 day, 8 stars
        raw = 1 * CW_BASE_PER_DAY + 8 * CW_STARS
        self.assertEqual(raw, 8 + 16)

    def test_raid_calculation(self):
        """Test Raid: attacks * PER_ATTACK + points * POINTS / 100"""
        from contribution_service import RAID_PER_ATTACK, RAID_POINTS
        # 3 attacks, 85 points
        raw = 3 * RAID_PER_ATTACK + 85 * RAID_POINTS / 100.0
        self.assertAlmostEqual(raw, 15.085)

    def test_cg_calculation(self):
        """Test Clan Games: points * CG_POINTS / 100"""
        from contribution_service import CG_POINTS
        # 400 points
        raw = 400 * CG_POINTS / 100.0
        self.assertEqual(raw, 20.0)


if __name__ == "__main__":
    unittest.main()
