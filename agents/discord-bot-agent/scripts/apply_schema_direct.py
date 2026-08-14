#!/usr/bin/env python3
"""
Apply database schema to Azure SQL database directly from this machine.
Uses az CLI AccessToken authentication with pyodbc ODBC Driver 18.
"""
import subprocess
import sys
import pyodbc


def main():
    # Get Azure AD access token
    print("Step 1: Obtaining Azure AD token...")
    result = subprocess.run(
        ["az", "account", "get-access-token",
         "--resource", "https://database.windows.net",
         "--query", "accessToken",
         "--output", "tsv"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  [ERROR] az CLI failed: {result.stderr.strip()}")
        return 1
    azure_token = result.stdout.strip()
    if not azure_token:
        print("  [ERROR] Empty token from az CLI")
        return 1
    print(f"  Token: {azure_token[:40]}...")

    # Read schema file
    from pathlib import Path
    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    print(f"  Schema: {len(schema_sql)} bytes")
    print()

    # Connect to Azure SQL
    server = "picteoinst1.database.windows.net"
    database = "discordcoc"
    port = 1433

    print(f"Step 2: Connecting to Azure SQL Database...")
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Authentication=AccessToken;"
        f"AccessToken={azure_token}"
    )
    print(f"  Server: {server},{port}")
    print(f"  Database: {database}")
    print(f"  Auth: Azure AD Access Token")
    print()

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        print("  SUCCESS: Connected!")
        cursor = conn.cursor()

        # Show current user
        cursor.execute("SELECT SYSTEM_USER, USER_NAME()")
        row = cursor.fetchone()
        print(f"  Current user: {row[0]} (db user: {row[1]})")
        print()

        # Execute schema
        print("Step 3: Executing schema...")
        print("-" * 70)

        batches = []
        current_batch = []
        for line in schema_sql.split("\n"):
            if line.strip().upper() == "GO":
                if current_batch:
                    batches.append("\n".join(current_batch).strip())
                    current_batch = []
            else:
                current_batch.append(line)
        if current_batch:
            batches.append("\n".join(current_batch).strip())

        print(f"  Total batches: {len(batches)}")
        print()

        executed = 0
        errors = 0
        warnings_list = []
        skipped = 0
        for i, batch in enumerate(batches):
            if not batch:
                skipped += 1
                continue
            try:
                cursor.execute(batch)
                executed += 1
                if executed % 10 == 0:
                    print(f"  Progress: {executed} executed, {errors} errors...")
            except Exception as e:
                errors += 1
                first_word = None
                for word in batch.split():
                    if word and not word.startswith("--") and len(word) > 2:
                        first_word = word[:50]
                        break
                msg = str(e)[:200]
                warnings_list.append(f"Batch {i+1} ({first_word}): {msg}")
                if errors <= 10:
                    print(f"  [WARN] Batch {i+1} ({first_word}): {msg}")

        conn.commit()
        print("-" * 70)
        print(f"\n  Executed: {executed} batches")
        print(f"  Errors:   {errors}")
        if skipped:
            print(f"  Skipped:  {skipped} empty batches")

        if warnings_list:
            print(f"\n  Warnings (first {min(10, len(warnings_list))}):")
            for w in warnings_list[:10]:
                print(f"    - {w}")

        # Verify tables
        print("\nStep 4: Verifying created tables...")
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo' ORDER BY TABLE_NAME"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  Tables in discordcoc: {len(tables)}")
        for t in tables:
            print(f"    - {t}")

        cursor.close()
        conn.close()
        print("\n" + "=" * 70)
        print("Schema deployment completed successfully!")
        print("=" * 70)
        return 0

    except pyodbc.Error as e:
        print(f"\n  [ERROR] pyodbc.Error: {e}")
        print("\n  Troubleshooting:")
        print("  1. Verify SQL Azure firewall allows your IP")
        print("  2. Check Azure SQL server admin configuration")
        print("  3. Ensure user has db_owner or create table permission")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())