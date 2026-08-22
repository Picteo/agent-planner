"""Unit tests for raid_service module."""

import asyncio
import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from raid_service import RaidService


class TestRaidServiceParseDatetime(unittest.TestCase):
    """Test _parse_iso_datetime static method."""

    def test_valid_iso_datetime(self):
        result = RaidService._parse_iso_datetime("2024-03-10T08:00:00.000Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertTrue(result.tzinfo is not None)

    def test_empty_string_returns_epoch(self):
        result = RaidService._parse_iso_datetime("")
        self.assertEqual(result.year, 1970)

    def test_invalid_string_returns_epoch(self):
        result = RaidService._parse_iso_datetime("bad-date")
        self.assertEqual(result.year, 1970)


class TestRaidServiceInit(unittest.TestCase):
    """Test RaidService initialization."""

    def test_init_stores_references(self):
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = RaidService(mock_api, mock_db)
        self.assertEqual(service._api_client, mock_api)
        self.assertEqual(service._db, mock_db)


class TestRaidServiceSyncRaid(unittest.IsolatedAsyncioTestCase):
    """Test sync_raids async method."""

    def setUp(self):
        self.mock_api = AsyncMock()
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.service = RaidService(self.mock_api, self.mock_db)

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

        self.mock_api.get_clan_raid.return_value = {
            "challenges": [
                {
                    "id": "challenge-1",
                    "startTime": "2024-03-10T08:00:00.000Z",
                    "endTime": "2024-03-17T20:00:00.000Z",
                    "playerGroups": [
                        {
                            "player": {"tags": "#Player1"},
                            "attacksUsed": 3,
                            "pointsReached": 85,
                        },
                        {
                            "player": {"tags": "#Player2"},
                            "attacksUsed": 2,
                            "pointsReached": 60,
                        },
                    ],
                }
            ]
        }

        result = await self.service.sync_raids("AliceIsBored")

        self.assertIn("events_synced", result)
        self.assertIn("participations_synced", result)
        self.assertEqual(result["events_synced"], 1)
        self.assertEqual(result["participations_synced"], 2)

    async def test_sync_clan_not_found(self):
        self._setup_query_mock(None)
        self.mock_api.get_clan.return_value = None

        result = await self.service.sync_raids("NonExistent")

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    async def test_sync_no_raid_data(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_raid.return_value = None

        result = await self.service.sync_raids("AliceIsBored")

        self.assertIn("error", result)
        self.assertIn("No Raid data", result["error"])

    async def test_sync_empty_challenges(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_raid.return_value = {"challenges": []}

        result = await self.service.sync_raids("AliceIsBored")

        self.assertEqual(result["events_synced"], 0)
        self.assertEqual(result["participations_synced"], 0)


if __name__ == "__main__":
    unittest.main()
