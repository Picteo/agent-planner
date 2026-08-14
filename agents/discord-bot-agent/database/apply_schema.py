#!/usr/bin/env python3
"""
Apply schema.sql to Azure SQL Database.

This script supports two authentication methods:
  1. Azure AD Access Token (Linux/macOS with pyodbc) - via AZURE_SQL_ACCESS_TOKEN env var
  2. ODBC Integrated Security (Windows with Azure Arc SQL tools) - via AZURE_SQL_SERVER env var

Usage:
  # Method 1: Azure AD Access Token (recommended for Linux)
  export AZURE_SQL_ACCESS_TOKEN="<token>"
  python database/apply_schema.py

  # Method 2: Use arc-enabled server (Windows with Azure Arc SQL tools)
  export AZURE_SQL_SERVER="WIN-2HBN30ECLV2.arc-dcc5e.9a6f-pd005016.centralus.arcsynapses.net"
  python database/apply_schema.py

  # Method 3: Custom server and database
  export AZURE_SQL_SERVER="picteoinst1.database.windows.net"
  export AZURE_SQL_DATABASE="discordcoc"
  python database/apply_schema.py
"""
import os
import sys


def main():
    # Get connection details from environment
    server = os.getenv("AZURE_SQL_SERVER", "picteoinst1.database.windows.net")
    database = os.getenv("AZURE_SQL_DATABASE", "discordcoc")
    schema_file = os.getenv("SCHEMA_FILE", "database/schema.sql")
    access_token = os.getenv("AZURE_SQL_ACCESS_TOKEN", "")

    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"Schema file: {schema_file}")
    print(f"Access token provided: {'Yes' if access_token else 'No'}")

    # Determine authentication method
    if access_token:
        print("\nAuth method: Azure AD Access Token")
    else:
        # Check if this is an Arc-enabled server
        if "arcsynapses" in server.lower():
            print("\nAuth method: Arc-enabled server (Integrated Security)")
        else:
            print("\nAuth method: Default (will use AccessToken or Integrated Security)")

    try:
        import pyodbc
    except ImportError:
        print("ERROR: pyodbc not installed. Install with: pip install pyodbc")
        sys.exit(1)

    # Build connection string
    if access_token:
        # Method 1: Access Token authentication
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"AccessToken={access_token};"
        )
    elif "arcsynapses" in server.lower():
        # Method 2: Arc-enabled server with Integrated Security
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Integrated Security=true;"
        )
    else:
        # Method 3: Try Azure AD Access Token from connection string
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Authentication=ActiveDirectoryDefault;"
        )

    print(f"Connecting to {server}...")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("Connection established successfully!")
    except pyodbc.Error as e:
        err = e.args[0]
        msg = err.msg if hasattr(err, 'msg') else str(err)
        print(f"\nERROR: Connection failed: {msg}")

        if "Login failed" in str(msg):
            print("\nTroubleshooting:")
            if access_token:
                print("  1. Token may have expired. Re-acquire token:")
                print('     az account get-access-token --resource-type "Microsoft SQL Server" --resource https://database.windows.net')
                print("  2. Ensure your identity has access to the Azure SQL DB:")
                print("     azure sql server admin-list --server picteoinst1 --resource-group <rg>")
            elif "arcsynapses" in server.lower():
                print("  1. Ensure Azure Arc SQL tools are installed and configured")
                print("  2. Run: arc sql db connect --server-connection-string ...")
            else:
                print("  1. Try setting AZURE_SQL_ACCESS_TOKEN environment variable")
                print("  2. Or run on the Arc-enabled server (WIN-2HBN30ECLV2)")
        sys.exit(1)

    # Test connection
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"Connection test: {result}")

    # Check existing tables
    cursor.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
    )
    existing = cursor.fetchall()
    if existing:
        print(f"\nExisting tables ({len(existing)}):")
        for t in existing:
            print(f"  - {str(t[0])}")
    else:
        print("\nNo existing tables found in database.")

    # Read schema file
    print(f"\nReading schema file: {schema_file}")
    if not os.path.exists(schema_file):
        print(f"ERROR: Schema file not found: {schema_file}")
        print("Set SCHEMA_FILE env var or ensure schema.sql is in the current directory.")
        sys.exit(1)

    with open(schema_file, "r") as f:
        schema_sql = f.read()

    print(f"Schema file: {len(schema_sql)} bytes, {len(schema_sql.splitlines())} lines")

    # Execute schema in batches (split on GO)
    batches = [b.strip() for b in schema_sql.split("GO") if b.strip()]
    print(f"Executing {len(batches)} SQL batches...")

    errors = []
    success_count = 0
    for i, batch in enumerate(batches):
        try:
            cursor.execute(batch)
            conn.commit()
            success_count += 1
            print(f"  Batch {i + 1}/{len(batches)}: OK")
        except Exception as e:
            err_msg = str(e).strip()
            print(f"  Batch {i + 1}/{len(batches)}: ERROR - {err_msg[:100]}")
            errors.append((i + 1, err_msg))
            conn.rollback()

    # Verify tables were created
    cursor.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
    )
    tables = cursor.fetchall()
    print(f"\nFinal tables ({len(tables)}):")
    for t in tables:
        print(f"  - {str(t[0])}")

    # Print column details for created tables
    print("\nTable column details:")
    for table in tables:
        table_name = str(table[0])
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            table_name,
        )
        cols = cursor.fetchall()
        if cols:
            print(f"\n  [{table_name}]:")
            for col in cols:
                name = str(col[0])
                dtype = str(col[1])
                nullable = str(col[2])
                length = str(col[3]) if col[3] else "MAX"
                print(f"    {name}: {dtype} ({length}), nullable={nullable}")

    if errors:
        print(f"\nWARNING: {len(errors)} batch(es) had errors:")
        for batch_num, err in errors:
            print(f"  Batch {batch_num}: {err[:200]}")
    else:
        print("\nAll batches executed successfully!")

    cursor.close()
    conn.close()
    print("\nDone! Schema application complete.")


if __name__ == "__main__":
    main()