"""Unit tests for database module."""

import sys
import os
import unittest
import warnings
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database import (
    Base,
    Clan,
    CwlEvents,
    CwlParticipations,
    Player,
    Members,
    ContributionScores,
    DatabaseManager,
    get_default_database_url,
)


class TestClanModel(unittest.TestCase):
    """Test Clan ORM model."""

    def test_clan_repr(self):
        """Test __repr__ method."""
        clan = Clan()
        clan.id = 1
        clan.clan_tag = "#AliceIsBored"
        clan.clan_name = "AliceIsBored"
        self.assertEqual(
            repr(clan),
            "<Clan(id=1, tag=#AliceIsBored, name=AliceIsBored)>",
        )

    def test_clan_table_name(self):
        """Test Clan table name."""
        self.assertEqual(Clan.__tablename__, "clan")


class TestCwlEventsModel(unittest.TestCase):
    """Test CwlEvents ORM model."""

    def test_cwl_events_repr(self):
        """Test __repr__ method."""
        event = CwlEvents()
        event.id = 1
        event.clan_tag = "#AliceIsBored"
        event.season_id = "cwl-2024-01"
        self.assertEqual(
            repr(event),
            "<CwlEvents(id=1, clan=#AliceIsBored, season=cwl-2024-01)>",
        )

    def test_cwl_events_table_name(self):
        """Test CwlEvents table name."""
        self.assertEqual(CwlEvents.__tablename__, "CwlEvents")


class TestCwlParticipationsModel(unittest.TestCase):
    """Test CwlParticipations ORM model."""

    def test_cwl_participations_repr(self):
        """Test __repr__ method."""
        participation = CwlParticipations()
        participation.id = 1
        participation.player_tag = "#Player1"
        participation.day_number = 1
        self.assertEqual(
            repr(participation),
            "<CwlParticipations(id=1, player=#Player1, day=1)>",
        )

    def test_cwl_participations_table_name(self):
        """Test CwlParticipations table name."""
        self.assertEqual(CwlParticipations.__tablename__, "CwlParticipations")


class TestPlayerModel(unittest.TestCase):
    """Test Player ORM model."""

    def test_player_repr(self):
        """Test __repr__ method."""
        player = Player()
        player.id = 1
        player.player_tag = "#Player1"
        player.player_name = "TestPlayer"
        self.assertEqual(
            repr(player),
            "<Player(id=1, tag=#Player1, name=TestPlayer)>",
        )

    def test_player_table_name(self):
        """Test Player table name."""
        self.assertEqual(Player.__tablename__, "player")


class TestMembersModel(unittest.TestCase):
    """Test Members ORM model."""

    def test_members_repr(self):
        """Test __repr__ method."""
        member = Members()
        member.id = 1
        member.player_tag = "#Player1"
        member.role = "Leader"
        self.assertEqual(
            repr(member),
            "<Members(id=1, tag=#Player1, role=Leader)>",
        )


class TestContributionScoresModel(unittest.TestCase):
    """Test ContributionScores ORM model."""

    def test_contribution_scores_repr(self):
        """Test __repr__ method."""
        scores = ContributionScores()
        scores.id = 1
        scores.player_tag = "#Player1"
        scores.event_date = datetime.now(timezone.utc)
        scores.total_score = 150.5
        self.assertIn(
            "total=150.5", repr(scores),
        )


class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager class."""

    def test_init_without_url(self):
        """Test initialization without database URL."""
        db = DatabaseManager()
        self.assertIsNone(db._engine)

    def test_sanitize_url_with_password(self):
        """Test URL sanitization with password."""
        url = "mssql+pyodbc://user:password@server/db"
        result = DatabaseManager._sanitize_url(url)
        self.assertNotIn("password", result)
        self.assertIn("****", result)

    def test_sanitize_url_without_password(self):
        """Test URL sanitization without password."""
        url = "sqlite:///test.db"
        result = DatabaseManager._sanitize_url(url)
        self.assertEqual(result, url)

    def test_get_default_database_url_sqlite(self):
        """Test getting default SQLite database URL."""
        url = get_default_database_url(environment="sqlite")
        self.assertIn("sqlite", url)

    def test_get_default_database_url_auto_no_env(self):
        """Test auto mode with no DATABASE_URL env var."""
        old = os.environ.pop("DATABASE_URL", None)
        try:
            url = get_default_database_url(environment="auto")
            self.assertIn("sqlite", url)
        finally:
            if old:
                os.environ["DATABASE_URL"] = old


class TestTableMetadata(unittest.TestCase):
    """Test that all table names match between ORM and schema."""

    def test_clan_table_name(self):
        """Test Clan table name is 'clan' (lowercase, matches SQL Server)."""
        self.assertEqual(Clan.__tablename__, "clan")

    def test_cwl_events_table_name(self):
        """Test CwlEvents table name matches SQL Server."""
        self.assertEqual(CwlEvents.__tablename__, "CwlEvents")

    def test_cwl_participations_table_name(self):
        """Test CwlParticipations table name matches SQL Server."""
        self.assertEqual(CwlParticipations.__tablename__, "CwlParticipations")

    def test_player_table_name(self):
        """Test Player table name is 'player' (lowercase, matches SQL Server)."""
        self.assertEqual(Player.__tablename__, "player")

    def test_base_metadata_has_all_tables(self):
        """Test that Base.metadata contains all expected tables."""
        expected_tables = {
            "clan", "player", "CwlEvents", "CwlParticipations",
            "Members", "ContributionScores",
        }
        actual_tables = set(Base.metadata.tables.keys())
        self.assertTrue(expected_tables.issubset(actual_tables),
                        f"Missing tables: {expected_tables - actual_tables}")


if __name__ == "__main__":
    # Suppress SQLAlchemy relationship warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        unittest.main()
