"""Unit tests for verification_service module."""

import asyncio
import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from verification_service import VerificationService


class TestVerificationServiceInit(unittest.TestCase):
    """Test VerificationService initialization."""

    def test_init_stores_references(self):
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = VerificationService(mock_api, mock_db)
        self.assertEqual(service._api_client, mock_api)
        self.assertEqual(service._db, mock_db)

    def test_role_mapping(self):
        mock_api = AsyncMock()
        mock_db = MagicMock()
        service = VerificationService(mock_api, mock_db)
        self.assertEqual(service.get_discord_role_name("Leader"), "Clan Leader")
        self.assertEqual(service.get_discord_role_name("CoLeader"), "Co-Leader")
        self.assertEqual(service.get_discord_role_name("Elder"), "Elder")
        self.assertEqual(service.get_discord_role_name("Member"), "Member")
        self.assertEqual(service.get_discord_role_name("Unknown"), "Member")


class TestVerificationServiceVerifyPlayer(unittest.IsolatedAsyncioTestCase):
    """Test verify_player async method."""

    def setUp(self):
        self.mock_api = AsyncMock()
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.service = VerificationService(self.mock_api, self.mock_db)

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

    async def test_verify_success(self):
        self._setup_query_mock(None)  # No existing verification

        self.mock_api.get_player.return_value = {
            "tags": "#PlayerOne",
            "name": "PlayerOne",
            "trophies": 6400,
            "attackWins": 150,
            "role": "Member",
            "donations": 500,
            "donationsReceived": 300,
            "warDays": 20,
            "expLevel": 10,
            "league": {"id": 7, "name": "Gold"},
            "clan": {"tags": "#AliceIsBored", "name": "AliceIsBored"},
        }
        self.mock_api.get_clan.return_value = {
            "tags": "#AliceIsBored",
            "name": "AliceIsBored",
            "members": [
                {
                    "tags": "#PlayerOne",
                    "name": "PlayerOne",
                    "role": "Member",
                    "trophies": 6400,
                }
            ],
        }

        result = await self.service.verify_player(12345678, "#PlayerOne")

        self.assertTrue(result["success"])
        self.assertEqual(result["player_tag"], "#PlayerOne")
        self.assertEqual(result["role"], "Member")

    async def test_verify_already_verified(self):
        existing = MagicMock(player_tag="#PlayerOne")
        self._setup_query_mock(existing)

        result = await self.service.verify_player(12345678, "#PlayerOne")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Already verified")

    async def test_verify_player_not_found(self):
        self._setup_query_mock(None)
        self.mock_api.get_player.return_value = None

        result = await self.service.verify_player(12345678, "#NonExistent")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    async def test_verify_not_in_clan(self):
        self._setup_query_mock(None)
        self.mock_api.get_player.return_value = {
            "tags": "#PlayerOne",
            "name": "PlayerOne",
            "role": "Member",
            "clan": {"tags": "#OtherClan"},
        }
        self.mock_api.get_clan.return_value = {
            "tags": "#AliceIsBored",
            "members": [
                {"tags": "#OtherPlayer", "name": "OtherPlayer", "role": "Member"}
            ],
        }

        result = await self.service.verify_player(12345678, "#PlayerOne")

        self.assertFalse(result["success"])
        self.assertIn("not a member", result["error"])


if __name__ == "__main__":
    unittest.main()
