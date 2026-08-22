"""Unit tests for clan_games_service module."""

import asyncio
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clan_games_service import ClanGamesService


class TestClanGamesServiceParseDatetime(unittest.TestCase):
    """Test _parse_iso_datetime static method."""

    def test_valid_iso_datetime(self):
        result = ClanGamesService._parse_iso_datetime("2024-04-01T10:00:00.000Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertTrue(result.tzinfo is not None)

    def test_empty_string_returns_epoch(self):
        result = ClanGamesService._parse_iso_datetime("")
        self.assertEqual(result.year, 1970)


class TestClanGamesServiceInit(unittest.TestCase):
    """Test ClanGamesService initialization."""

    def test_init_stores_references(self):
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = ClanGamesService(mock_api, mock_db)
        self.assertEqual(service._api_client, mock_api)
        self.assertEqual(service._db, mock_db)


class TestClanGamesServiceSync(unittest.IsolatedAsyncioTestCase):
    """Test sync_clan_games async method."""

    def setUp(self):
        self.mock_api = AsyncMock()
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.service = ClanGamesService(self.mock_api, self.mock_db)

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

        self.mock_api.get_clan_games.return_value = {
            "challenges": [
                {
                    "id": "cg-2024-01",
                    "start": "2024-04-01T10:00:00.000Z",
                    "end": "2024-04-08T20:00:00.000Z",
                    "name": "Destroying Buildings",
                    "category": "Destruction",
                    "totalPoints": 5000,
                    "playerGroups": [
                        {
                            "player": {"tags": "#Player1"},
                            "pointsContributed": 3000,
                            "milestoneReached": "4000",
                        }
                    ],
                }
            ]
        }

        result = await self.service.sync_clan_games("AliceIsBored", "cg-2024-01")

        self.assertIn("events_synced", result)
        self.assertIn("participations_synced", result)
        self.assertEqual(result["events_synced"], 1)
        self.assertEqual(result["participations_synced"], 1)

    async def test_sync_clan_not_found(self):
        self._setup_query_mock(None)
        self.mock_api.get_clan.return_value = None

        result = await self.service.sync_clan_games("NonExistent")

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    async def test_sync_no_cg_data(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_games.return_value = None

        result = await self.service.sync_clan_games("AliceIsBored")

        self.assertIn("error", result)
        self.assertIn("No Clan Games data", result["error"])

    async def test_sync_empty_challenges(self):
        mock_clan = MagicMock(id=1, clan_tag="#AliceIsBored")
        self._setup_query_mock(mock_clan)
        self.mock_api.get_clan_games.return_value = {"challenges": []}

        result = await self.service.sync_clan_games("AliceIsBored")

        self.assertEqual(result["events_synced"], 0)
        self.assertEqual(result["participations_synced"], 0)


if __name__ == "__main__":
    unittest.main()
