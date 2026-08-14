#!/usr/bin/env python3
"""
Database initialization script for DiscordCoC bot.

Creates all tables in the database using SQLAlchemy ORM models.
Supports both SQLite (development) and Azure SQL (production).

Usage:
    # SQLite (default, for development)
    python scripts/init_database.py

    # Azure SQL (production)
    DATABASE_URL=mssql+pyodbc://user:pass@server/db?driver=Driver+17 python scripts/init_database.py

    # Force drop and recreate (DANGEROUS - destroys data)
    python scripts/init_database.py --force-recreate
"""

import argparse
import sys
import os

# Add project root to path so we can import src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import DatabaseManager, get_default_database_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize DiscordCoC bot database schema.")
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Drop all tables first (WARNING: destroys existing data).",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default="",
        help="Override DATABASE_URL environment variable with explicit connection string.",
    )
    args = parser.parse_args()

    # Determine database URL
    database_url = args.database_url or get_default_database_url()
    print(f"Database URL: {DatabaseManager._sanitize_url(database_url)}")

    # Initialize manager
    db = DatabaseManager(database_url)

    if args.force_recreate:
        print("[!] Dropping all tables (data will be lost)...")
        db.drop_tables()

    print("Creating tables...")
    db.create_tables()

    # List created tables
    engine = db.get_engine()
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTables created ({len(tables)}):")
    for table in sorted(tables):
        columns = inspector.get_columns(table)
        col_info = ", ".join(f"{c['name']}({c['type']})" for c in columns[:4])
        print(f"  - {table}: {col_info}...")

    print("\nDatabase initialization complete.")


if __name__ == "__main__":
    main()