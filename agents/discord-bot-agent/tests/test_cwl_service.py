"""Unit tests for cwl_service module."""

import asyncio
import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cwl_service import CwlService


class TestCwlServiceParseDatetime(unittest.TestCase):
    """Test _parse_iso_datetime static method."""

    def test_valid_iso_datetime(self):
        """Test parsing a valid ISO-8601 datetime string."""
        result = CwlService._parse_iso_datetime("2024-01-15T10:00:00.000Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 10)
        self.assertTrue(result.tzinfo is not None)

    def test_empty_string_returns_epoch(self):
        """Test that empty string returns epoch datetime."""
        result = CwlService._parse_iso_datetime("")
        self.assertEqual(result.year, 1970)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_none_returns_epoch(self):
        """Test that None returns epoch datetime."""
        result = CwlService._parse_iso_datetime(None)  # type: ignore
        self.assertEqual(result.year, 1970)

    def test_invalid_string_returns_epoch(self):
        """Test that invalid strings return epoch datetime."""
        result = CwlService._parse_iso_datetime("not-a-date")
        self.assertEqual(result.year, 1970)

    def test_datetime_without_z(self):
        """Test parsing without trailing Z."""
        result = CwlService._parse_iso_datetime("2024-06-20T14:30:00+00:00")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 6)


class TestCwlServiceInit(unittest.TestCase):
    """Test CwlService initialization."""

    def test_init_stores_references(self):
        """Test that init stores api_client and db_manager."""
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = CwlService(mock_api, mock_db)
        self.assertEqual(service._api_client, mock_api)
        self.assertEqual(service._db, mock_db)


class TestCwlServiceSyncCwl(unittest.IsolatedAsyncioTestCase):
    """Test sync_cwl async method."""

    def setUp(self):
        self.mock_api = AsyncMock()
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.service = CwlService(self.mock_api, self.mock_db)

    async def asyncSetUp(self):
        # Set up the session mock methods
        self.mock_session.add = MagicMock()
        self.mock_session.flush = MagicMock()
        self.mock_session.commit = MagicMock()
        self.mock_session.rollback = MagicMock()
        self.mock_session.close = MagicMock()
        self.mock_db.session.return_value = self.mock_session

    def _setup_query_mock(self, return_value):
        """Properly configure the query.filter().first() mock chain."""
        # Configure the top-level query mock so the entire chain returns the expected value
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = return_value
        self.mock_session.query.return_value = query_mock

    async def test_sync_success(self):
        """Test successful CWL sync."""
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(None)  # No existing clan

        self.mock_api.get_clan.return_value = {
            "tags": "#AliceIsBored",
            "name": "AliceIsBored",
            "clanPointVictories": 200,
            "trophies": 4500,
            "warFrequency": "often",
            "warStageFrequency": "often",
            "requiredTrophies": 5000,
            "clanPoints": 1500,
            "region": {"name": "Europe"},
            "description": "Test clan",
        }

        self.mock_api.get_clan_warl_states.return_value = {
            "warSeasons": [
                {
                    "tags": "cwl-2024-01",
                    "warStart": "2024-01-15T10:00:00.000Z",
                    "warEnd": "2024-01-22T10:00:00.000Z",
                    "league": {"name": "Gold I"},
                    "warCount": 7,
                    "totalWins": 5,
                    "dayGroups": [
                        {
                            "dayNumber": 1,
                            "playerGroups": [
                                {
                                    "player": {"tags": "#Player1"},
                                    "attacksUsed": 2,
                                    "warCountComparison": 1,
                                    "starsCollected": 6,
                                    "damagePercentage": 95.5,
                                    "clanTrophyEarned": 10,
                                    "bonusBasesDestroyed": 2,
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        result = await self.service.sync_cwl("AliceIsBored")

        self.assertIn("events_synced", result)
        self.assertIn("participations_synced", result)
        self.assertEqual(result["events_synced"], 1)
        self.assertEqual(result["participations_synced"], 1)

    async def test_sync_clan_not_found(self):
        """Test sync when clan is not found in API."""
        self._setup_query_mock(None)
        self.mock_api.get_clan.return_value = None

        result = await self.service.sync_cwl("NonExistent")

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    async def test_sync_no_cwl_data(self):
        """Test sync when API returns no CWL data."""
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_warl_states.return_value = None

        result = await self.service.sync_cwl("AliceIsBored")

        self.assertIn("error", result)
        self.assertIn("No CWL data", result["error"])

    async def test_sync_empty_seasons(self):
        """Test sync when API returns no war seasons."""
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_warl_states.return_value = {"warSeasons": []}

        result = await self.service.sync_cwl("AliceIsBored")

        self.assertEqual(result["events_synced"], 0)
        self.assertEqual(result["participations_synced"], 0)


if __name__ == "__main__":
    unittest.main()
