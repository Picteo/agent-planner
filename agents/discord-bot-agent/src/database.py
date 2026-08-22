"""
Database models and session management for DiscordCoC bot.

Provides SQLAlchemy ORM models for all bot data tables and session management
for Azure SQL (production) with pause-resume retry and skeleton mode fallback.
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    foreign,
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

class Clan(Base):
    """Clan information."""

    __tablename__ = "clan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_tag: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    clan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    clan_level: Mapped[int] = mapped_column(Integer, default=0)
    trophies: Mapped[int] = mapped_column(Integer, default=0)
    war_frequency: Mapped[str] = mapped_column(String(50), default="Unknown")
    war_stage_frequency: Mapped[str] = mapped_column(String(50), default="Unknown")
    required_trophies: Mapped[int] = mapped_column(Integer, default=0)
    clan_points: Mapped[int] = mapped_column(Integer, default=0)
    clan_point_victories: Mapped[int] = mapped_column(Integer, default=0)
    region_name: Mapped[str] = mapped_column(String(50), default="Unknown")
    description: Mapped[str] = mapped_column(String(500), default="")

    cwl_events = relationship("CwlEvents", back_populates="clan")

    def __repr__(self) -> str:
        return f"<Clan(id={self.id}, tag={self.clan_tag}, name={self.clan_name})>"


class CwlEvents(Base):
    """Clan War League (CWL) events."""

    __tablename__ = "CwlEvents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_id: Mapped[int] = mapped_column(Integer, ForeignKey("clan.id"), nullable=False)
    clan_tag: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    season_id: Mapped[str] = mapped_column(String(50), nullable=True)
    league_name: Mapped[str] = mapped_column(String(50), nullable=True)
    division: Mapped[str] = mapped_column(String(50), nullable=True)
    war_count: Mapped[int] = mapped_column(Integer, default=0)
    total_wins: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    clan = relationship("Clan", back_populates="cwl_events")
    participations = relationship("CwlParticipations", back_populates="event")

    def __repr__(self) -> str:
        return f"<CwlEvents(id={self.id}, clan={self.clan_tag}, season={self.season_id})>"


class CwlParticipations(Base):
    """CWL participation records per player per day."""

    __tablename__ = "CwlParticipations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("CwlEvents.id"), nullable=False)
    player_tag: Mapped[str] = mapped_column(String(20), ForeignKey("player.player_tag"), nullable=False, index=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attacks_used: Mapped[int] = mapped_column(Integer, default=0)
    war_count_comparison: Mapped[int] = mapped_column(Integer, default=0)
    stars_collected: Mapped[int] = mapped_column(Integer, default=0)
    damage_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    clan_trophy_earned: Mapped[int] = mapped_column(Integer, default=0)
    bonus_bases_destroyed: Mapped[int] = mapped_column(Integer, default=0)

    event = relationship("CwlEvents", back_populates="participations")
    player = relationship("Player", back_populates="cwl_participations")

    def __repr__(self) -> str:
        return f"<CwlParticipations(id={self.id}, player={self.player_tag}, day={self.day_number})>"


class Player(Base):
    """Player information with back-references to participation records."""

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_tag: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    player_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trophies: Mapped[int] = mapped_column(Integer, default=0)
    attack_wins: Mapped[int] = mapped_column(Integer, default=0)
    role: Mapped[str] = mapped_column(String(20), default="Member")
    donations: Mapped[int] = mapped_column(Integer, default=0)
    donations_received: Mapped[int] = mapped_column(Integer, default=0)
    war_days: Mapped[int] = mapped_column(Integer, default=0)
    exp_level: Mapped[int] = mapped_column(Integer, default=0)
    league_id: Mapped[int] = mapped_column(Integer, default=0)
    league_name: Mapped[str] = mapped_column(String(50), default="Unranked")

    cwl_participations = relationship("CwlParticipations", back_populates="player")

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, tag={self.player_tag}, name={self.player_name})>"


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

    # CwlParticipations are linked via player_tag, but the back_populates="player"
    # relationship on CwlParticipations references Player (not Members).
    # So we use a one-way relationship here instead of back_populates.
    participations = relationship(
        "CwlParticipations",
        primaryjoin="Members.player_tag == foreign(CwlParticipations.player_tag)",
        foreign_keys="[CwlParticipations.player_tag]",
        overlaps="cwl_participations,player",
    )

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

    def __init__(self, database_url: str = "", config=None):
        self._engine = None
        self._session_factory: sessionmaker = None
        self.config = config
        self._skeleton_mode = False
        if database_url:
            self._initialize(database_url)

    def _initialize(self, database_url: str) -> None:
        """Create engine and session factory.

        For Azure SQL (ActiveDirectoryMsi), retries on pause errors (40613, 40501)
        with exponential back-up.  Falls back to skeleton mode if ultimately
        unreachable.
        """
        self._skeleton_mode = False

        def _create_azure_conn():
            import pyodbc
            # Hardcoded production server to avoid env var hostname parsing issues
            server = "tcp:picteoinst1.database.windows.net,1433"
            database = "discordcoc"
            driver = "ODBC Driver 18 for SQL Server"
            conn_str = (
                f"DRIVER={{{driver}}};SERVER={{{server}}};DATABASE={database};"
                f"Authentication=ActiveDirectoryMsi;"
                f"Encrypt=yes;TrustServerCertificate=no;"
            )
            logger.debug("Azure SQL connection string (password hidden): %s",
                         conn_str.replace("ODBC Driver 18", "***"))
            return pyodbc.connect(conn_str)

        creator = _create_azure_conn if "ActiveDirectoryMsi" in database_url else None

        # --- Azure SQL pause-resume retry loop ---
        if creator is not None:
            max_retries = 10  # ~5 minutes total with exponential back-off
            delay = 5.0  # start with 5 seconds

            for attempt in range(1, max_retries + 1):
                try:
                    self._engine = create_engine(
                        database_url, echo=False, creator=creator,
                        pool_pre_ping=True,
                    )
                    self._session_factory = sessionmaker(bind=self._engine)
                    # Force a test connection
                    with self._engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.info("Azure SQL connected on attempt %d.", attempt)
                    return

                except (OperationalError, DBAPIError) as exc:
                    error_str = str(exc).lower()
                    # 40613 = SQL Server Free Tier paused
                    # 40501 = Authentication required (transient)
                    if "40613" in error_str or "40501" in error_str:
                        logger.warning(
                            "Azure SQL paused / not ready (attempt %d/%d): %s — "
                            "retrying in %.1fs …",
                            attempt, max_retries, exc, delay,
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, 60.0)  # exponential back-off, cap at 60s
                        continue
                    else:
                        logger.error(
                            "Azure SQL failure (non-pause): %s — "
                            "entering skeleton mode", exc, exc_info=True
                        )
                        self._skeleton_mode = True
                        return
                except Exception:
                    logger.error(
                        "Azure SQL unexpected failure (attempt %d): %s — "
                        "entering skeleton mode", attempt, exc, exc_info=True
                    )
                    self._skeleton_mode = True
                    return

            # Exhausted retries
            logger.warning(
                "Azure SQL did not resume after %d retries — entering skeleton mode",
                max_retries,
            )
            self._skeleton_mode = True
            # Still create the engine so sessionmaker doesn't raise
            self._engine = create_engine(
                database_url, echo=False, creator=creator,
                pool_pre_ping=True,
            )
            self._session_factory = sessionmaker(bind=self._engine)
            return

        # --- Non-Azure-SQL path (should not happen in production) ---
        self._engine = create_engine(
            database_url, echo=False, creator=creator,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(bind=self._engine)
        logger.info("Database engine created for: %s", self._sanitize_url(database_url))

    def create_tables(self) -> None:
        """Create all tables defined in the ORM models."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init() first.")
        Base.metadata.create_all(self._engine)
        logger.info("All tables created successfully.")

    def sync_schema(self) -> list[str]:
        """Ensure the database schema matches the ORM models.

        For each table defined in the models, checks whether all expected
        columns exist in the physical database and adds missing columns
        via ``ALTER TABLE``.

        Returns a list of migration statements executed.
        """
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init() first.")

        migrations: list[str] = []

        # Collect model metadata
        table_defs: dict[str, dict[str, dict]] = {}
        for table_name, table_obj in Base.metadata.tables.items():
            cols = {}
            for col in table_obj.columns:
                cols[col.name] = {
                    "type": col.type,
                    "nullable": col.nullable,
                    "default": col.default,
                    "foreign_key": (
                        str(fk.target)
                        for fk in col.foreign_keys
                    ),
                }
            # Fix: foreign_keys is a set, not a generator
            for col in table_obj.columns:
                fks = list(col.foreign_keys)
                cols[col.name]["foreign_keys"] = fks
            table_defs[table_name] = cols

        with self._engine.connect() as conn:
            for table_name, model_cols in table_defs.items():
                # Query existing columns for this table
                result = conn.execute(
                    text(
                        "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
                        "FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :tbl "
                        "ORDER BY ORDINAL_POSITION"
                    ),
                    {"tbl": table_name},
                )
                existing = {row[0] for row in result}
                for col_name, col_info in model_cols.items():
                    if col_name not in existing:
                        sql_type = self._sql_type(col_info["type"])
                        default_val = ""
                        if col_info["default"]:
                            default_str = self._default_literal(col_info["default"])
                            if default_str:
                                default_val = f" DEFAULT{default_str}"
                        nullable = "NULL" if col_info["nullable"] else "NOT NULL"
                        alter_sql = (
                            f"ALTER TABLE [{table_name}] "
                            f"ADD [{col_name}] {sql_type} {nullable}{default_val}"
                        )
                        migrations.append(alter_sql)
                        logger.info("Adding column [%s] to [%s]", col_name, table_name)
                        try:
                            conn.execute(text(alter_sql))
                            conn.commit()
                        except Exception as exc:
                            conn.rollback()
                            logger.error(
                                "Failed to add column [%s] to [%s]: %s",
                                col_name,
                                table_name,
                                exc,
                            )
        if migrations:
            logger.info(
                "Schema sync complete: %d column(s) added.", len(migrations)
            )
        else:
            logger.info("Schema already up to date — no migrations needed.")
        return migrations

    def _sql_type(self, sa_type) -> str:
        """Map SQLAlchemy type objects to SQL Server types."""
        if isinstance(sa_type, Integer):
            return "INT"
        if isinstance(sa_type, Numeric):
            return f"NUMERIC({sa_type.precision or 10}, {sa_type.scale or 2})"
        if isinstance(sa_type, String):
            max_len = sa_type.length or 255
            return f"NVARCHAR({max_len})"
        if isinstance(sa_type, Text):
            return "NVARCHAR(MAX)"
        if isinstance(sa_type, DateTime):
            return "DATETIME2"
        if isinstance(sa_type, Boolean):
            return "BIT"
        # Fallback
        return "NVARCHAR(255)"

    def _default_literal(self, default) -> str:
        """Convert a SQLAlchemy ColumnDefault to a SQL literal."""
        from sqlalchemy import ColumnDefault, DefaultClause

        # Handle ColumnDefault (used by mapped_column default=...)
        if isinstance(default, (ColumnDefault, DefaultClause)):
            arg = default.arg
            if arg is None:
                return ""
            if isinstance(arg, int):
                return f"({arg})"
            if isinstance(arg, float):
                return f"({arg})"
            if isinstance(arg, bool):
                return f"({int(arg)})"
            if isinstance(arg, str):
                escaped = arg.replace("'", "''")
                return f"('{escaped}')"
            return f"({arg})"
        return ""

    def drop_tables(self) -> None:
        """Drop all tables (DEV/TEST ONLY)."""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init() first.")
        Base.metadata.drop_all(self._engine)
        logger.warning("All tables dropped.")

    def session(self):
        """Return a new session scoped to the current thread.

        In skeleton mode, automatically attempts to reconnect to Azure SQL.
        If reconnection succeeds, skeleton mode is cleared and a session is returned.
        If reconnection fails, returns None so callers can show an error message.
        """
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")
        if self._skeleton_mode:
            if not self._attempt_reconnect():
                return None
        return self._session_factory()

    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to Azure SQL.

        Returns True and clears skeleton mode if reconnection succeeds,
        otherwise returns False and keeps skeleton mode active.
        """
        try:
            def _azure_connect():
                import pyodbc
                server = "tcp:picteoinst1.database.windows.net,1433"
                database = "discordcoc"
                conn_str = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={{{server}}};DATABASE={database};"
                    f"Authentication=ActiveDirectoryMsi;Encrypt=yes;TrustServerCertificate=no;"
                )
                return pyodbc.connect(conn_str)

            if not self._engine:
                self._engine = create_engine(
                    get_default_database_url(), echo=False,
                    creator=_azure_connect, pool_pre_ping=True,
                )
            else:
                try:
                    self._engine.dispose()
                except Exception:
                    pass
                self._engine = create_engine(
                    get_default_database_url(), echo=False,
                    creator=_azure_connect, pool_pre_ping=True,
                )
            self._session_factory = sessionmaker(bind=self._engine)
            self._skeleton_mode = False
            logger.info(
                "Reconnected to Azure SQL database — full functionality restored"
            )
            return True
        except Exception as exc:
            logger.debug(
                "Reconnection attempt failed: %s", exc
            )
            return False

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

    def is_skeleton_mode(self) -> bool:
        """Return True if the database is unavailable (skeleton mode)."""
        return self._skeleton_mode


# ---------------------------------------------------------------------------
# Convenience: known database URLs
# ---------------------------------------------------------------------------

def get_default_database_url(environment: str = "auto") -> str:
    """Return the DATABASE_URL for the given environment.

    Args:
        environment: "azure" for Azure SQL, or "auto" to use DATABASE_URL env var.

    Returns:
        A SQLAlchemy-compatible database URL string.
    """
    url = os.getenv("DATABASE_URL", "")
    if url:
        return url

    server = os.getenv("AZURE_SQL_SERVER", "picteoinst1.database.windows.net")
    database = os.getenv("AZURE_SQL_DATABASE", "discordcoc")
    url = (
        f"mssql+pyodbc://@{server}/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&Authentication=ActiveDirectoryMsi"
        f"&Encrypt=yes"
        f"&TrustServerCertificate=no"
    )
    return url