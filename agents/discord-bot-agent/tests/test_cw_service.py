"""Unit tests for cw_service module."""

import asyncio
import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cw_service import CwService


class TestCwServiceParseDatetime(unittest.TestCase):
    """Test _parse_iso_datetime static method."""

    def test_valid_iso_datetime(self):
        result = CwService._parse_iso_datetime("2024-01-15T10:00:00.000Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertTrue(result.tzinfo is not None)

    def test_empty_string_returns_epoch(self):
        result = CwService._parse_iso_datetime("")
        self.assertEqual(result.year, 1970)

    def test_none_returns_epoch(self):
        result = CwService._parse_iso_datetime(None)  # type: ignore
        self.assertEqual(result.year, 1970)

    def test_invalid_string_returns_epoch(self):
        result = CwService._parse_iso_datetime("not-a-date")
        self.assertEqual(result.year, 1970)


class TestCwServiceInit(unittest.TestCase):
    """Test CwService initialization."""

    def test_init_stores_references(self):
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = CwService(mock_api, mock_db)
        self.assertEqual(service._api_client, mock_api)
        self.assertEqual(service._db, mock_db)


class TestCwServiceSyncCw(unittest.IsolatedAsyncioTestCase):
    """Test sync_cw async method."""

    def setUp(self):
        self.mock_api = AsyncMock()
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.service = CwService(self.mock_api, self.mock_db)

    async def asyncSetUp(self):
        self.mock_session.add = MagicMock()
        self.mock_session.flush = MagicMock()
        self.mock_session.commit = MagicMock()
        self.mock_session.rollback = MagicMock()
        self.mock_session.close = MagicMock()
        self.mock_db.session.return_value = self.mock_session

    def _setup_query_mock(self, return_value):
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = return_value
        self.mock_session.query.return_value = query_mock

    async def test_sync_success(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)

        self.mock_api.get_clan_wars.return_value = {
            "war": [
                {
                    "state": "fighting",
                    "start": "2024-02-01T10:00:00.000Z",
                    "end": "2024-02-01T22:00:00.000Z",
                    "attackDays": 1,
                    "dayGroups": [
                        {
                            "dayNumber": 1,
                            "playerGroups": [
                                {
                                    "player": {"tags": "#Player1"},
                                    "attacksUsed": 2,
                                    "attackTargets": 5,
                                    "warCountComparison": 1,
                                    "starsCollected": 8,
                                }
                            ],
                        }
                    ],
                }
            ],
            "pastWars": [],
        }

        result = await self.service.sync_cw("AliceIsBored")

        self.assertIn("events_synced", result)
        self.assertIn("participations_synced", result)
        self.assertEqual(result["events_synced"], 1)
        self.assertEqual(result["participations_synced"], 1)

    async def test_sync_clan_not_found(self):
        self._setup_query_mock(None)
        self.mock_api.get_clan.return_value = None

        result = await self.service.sync_cw("NonExistent")

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    async def test_sync_no_war_data(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_wars.return_value = None

        result = await self.service.sync_cw("AliceIsBored")

        self.assertIn("error", result)
        self.assertIn("No CW data", result["error"])

    async def test_sync_empty_wars(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_wars.return_value = {"war": [], "pastWars": []}

        result = await self.service.sync_cw("AliceIsBored")

        self.assertEqual(result["events_synced"], 0)
        self.assertEqual(result["participations_synced"], 0)


if __name__ == "__main__":
    unittest.main()
