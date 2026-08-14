"""
Database models and session management for DiscordCoC bot.

Provides SQLAlchemy ORM models for all bot data tables and session management
for both Azure SQL (production) and SQLite (development) backends.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# ---------------------------------------------------------------------------
# Model base with common fields
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Mixin that adds created_at / updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# ---------------------------------------------------------------------------
# Event models
# ---------------------------------------------------------------------------

class CwlEvents(Base):
    """Clan War League events."""

    __tablename__ = "CwlEvents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    league_name: Mapped[str] = mapped_column(String(50), nullable=True)
    division: Mapped[str] = mapped_column(String(50), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    participations = relationship("CwlParticipations", back_populates="event")

    def __repr__(self) -> str:
        return f"<CwlEvents(id={self.id}, clan={self.clan_tag}, league={self.league_name})>"


class CwlParticipations(Base):
    """CWL participation records per player per day."""

    __tablename__ = "CwlParticipations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("CwlEvents.id"), nullable=False)
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    participated: Mapped[bool] = mapped_column(Integer, default=0)
    attacks_used: Mapped[int] = mapped_column(Integer, default=0)
    attack_targets: Mapped[int] = mapped_column(Integer, default=0)
    war_count_comparison: Mapped[int] = mapped_column(Integer, default=0)
    stars_collected: Mapped[int] = mapped_column(Integer, default=0)
    damage_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    bonuses_assigned: Mapped[int] = mapped_column(Integer, default=0)

    event = relationship("CwlEvents", back_populates="participations")

    def __repr__(self) -> str:
        return f"<CwlParticipations(id={self.id}, player={self.player_tag}, day={self.day_number})>"


class CwEvents(Base):
    """Clan War events (non-CWL)."""

    __tablename__ = "CwEvents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attack_days: Mapped[int] = mapped_column(Integer, default=1)

    participations = relationship("CwParticipations", back_populates="event")

    def __repr__(self) -> str:
        return f"<CwEvents(id={self.id}, clan={self.clan_tag})>"


class CwParticipations(Base):
    """Clan War participation records per player per day."""

    __tablename__ = "CwParticipations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("CwEvents.id"), nullable=False)
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attacks_used: Mapped[int] = mapped_column(Integer, default=0)
    attack_targets: Mapped[int] = mapped_column(Integer, default=0)
    war_count_comparison: Mapped[int] = mapped_column(Integer, default=0)
    stars_collected: Mapped[int] = mapped_column(Integer, default=0)

    event = relationship("CwEvents", back_populates="participations")

    def __repr__(self) -> str:
        return f"<CwParticipations(id={self.id}, player={self.player_tag}, day={self.day_number})>"


class RaidEvents(Base):
    """Challenges (Raid) events."""

    __tablename__ = "RaidEvents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    participations = relationship("RaidParticipations", back_populates="event")

    def __repr__(self) -> str:
        return f"<RaidEvents(id={self.id})>"


class RaidParticipations(Base):
    """Challenge (Raid) participation records."""

    __tablename__ = "RaidParticipations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("RaidEvents.id"), nullable=False)
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    attacks_used: Mapped[int] = mapped_column(Integer, default=0)
    points_reached: Mapped[int] = mapped_column(Integer, default=0)

    event = relationship("RaidEvents", back_populates="participations")

    def __repr__(self) -> str:
        return f"<RaidParticipations(id={self.id}, player={self.player_tag})>"


class ClanGamesEvents(Base):
    """Clan Games events."""

    __tablename__ = "ClanGamesEvents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    participations = relationship("ClanGamesParticipations", back_populates="event")

    def __repr__(self) -> str:
        return f"<ClanGamesEvents(id={self.id})>"


class ClanGamesParticipations(Base):
    """Clan Games participation records."""

    __tablename__ = "ClanGamesParticipations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ClanGamesEvents.id"), nullable=False
    )
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    points_contributed: Mapped[int] = mapped_column(Integer, default=0)
    milestone_reached: Mapped[str] = mapped_column(String(20), nullable=True)  # "4000" or "10000"

    event = relationship("ClanGamesEvents", back_populates="participations")

    def __repr__(self) -> str:
        return f"<ClanGamesParticipations(id={self.id}, player={self.player_tag})>"


# ---------------------------------------------------------------------------
# Member and scoring models
# ---------------------------------------------------------------------------

class Members(Base):
    """Clan members — one row per verified player."""

    __tablename__ = "Members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_tag: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    discord_id: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="Member")
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    participations = relationship("CwlParticipations", back_populates="player", foreign_keys="[CwlParticipations.player_tag]")

    def __repr__(self) -> str:
        return f"<Members(id={self.id}, tag={self.player_tag}, role={self.role})>"


class ContributionScores(Base):
    """Aggregated contribution scores per player per event date."""

    __tablename__ = "ContributionScores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    cwl_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    cw_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    raid_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    clan_games_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    total_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    def __repr__(self) -> str:
        return f"<ContributionScores(player={self.player_tag}, date={self.event_date}, total={self.total_score})>"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

class DatabaseManager:
    """Manages database engine, session, and schema creation."""

    def __init__(self, database_url: str = ""):
        self._engine = None
        self._session_factory: sessionmaker = None
        if database_url:
            self._initialize(database_url)

    def _initialize(self, database_url: str) -> None:
        """Create engine and session factory."""
        self._engine = create_engine(database_url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine)
        logger.info("Database engine created for: %s", self._sanitize_url(database_url))

    def create_tables(self) -> None:
        """Create all tables defined in the ORM models."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init() first.")
        Base.metadata.create_all(self._engine)
        logger.info("All tables created successfully.")

    def drop_tables(self) -> None:
        """Drop all tables (DEV/TEST ONLY)."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init() first.")
        Base.metadata.drop_all(self._engine)
        logger.warning("All tables dropped.")

    def session(self):
        """Return a new session scoped to the current thread."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory()

    def get_engine(self):
        """Return the SQLAlchemy engine."""
        return self._engine

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """Return a URL with password hidden for logging."""
        if "://" not in url:
            return url
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            path = rest.split("@", 1)[1]
            return f"{scheme}://****@{path}"
        return url


# ---------------------------------------------------------------------------
# Convenience: known database URLs
# ---------------------------------------------------------------------------

def get_default_database_url(environment: str = "auto") -> str:
    """Return the DATABASE_URL for the given environment.

    Args:
        environment: "azure" for Azure SQL, "sqlite" for local development,
                     or "auto" to use DATABASE_URL env var.

    Returns:
        A SQLAlchemy-compatible database URL string.
    """
    import os

    url = os.getenv("DATABASE_URL", "")
    if url:
        return url

    if environment == "azure":
        # Placeholder — fill in actual Azure SQL connection string
        # Format: mssql+pyodbc://@<server>.database.windows.net/<db>?driver=ODBC+Driver+17+for+SQL+Server
        raise ValueError(
            "DATABASE_URL not set. For Azure SQL, set the connection string "
            "in environment or use 'sqlite' for local development."
        )

    # Default to SQLite for local development
    db_path = "bot_data.db"
    return f"sqlite:///{db_path}"