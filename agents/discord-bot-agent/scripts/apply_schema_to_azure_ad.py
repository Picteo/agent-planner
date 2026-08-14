#!/usr/bin/env python3
"""Apply the DiscordCoC database schema to Azure SQL using Azure AD authentication."""

import os
import sys
import subprocess

# Use pyodbc if available, otherwise fall back to pypsrp
try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    from pypsrp.wsman import WSMan
    from pypsrp.powershell import PowerShell, RunspacePool
    from pypsrp.complex_objects import Command
    HAS_PS = True
except ImportError:
    HAS_PS = False

from azure.identity import DefaultAzureCredential

# Azure SQL Configuration
SQL_SERVER = "picteoinst1.database.windows.net"
SQL_DATABASE = "discordcoc"
SQL_DRIVER = "{ODBC Driver 18 for SQL Server}"

# VM Configuration
VM_HOST = "WIN-2HBN30ECLV2.fritz.box"
VM_PORT = 5985
VM_USERNAME = "administrator"
VM_PASSWORD = "Sunsh!n30!"

# SQL Schema
SCHEMA_SQL = r"""
CREATE TABLE CwlEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL,
    league_name NVARCHAR(50) NULL,
    division NVARCHAR(50) NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);
CREATE INDEX IX_CwlEvents_clan_tag ON CwlEvents(clan_tag);

CREATE TABLE CwlParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    day_number INT NOT NULL,
    participated BIT NOT NULL CONSTRAINT DF_CwlParticipations_participated DEFAULT 0,
    attacks_used INT NOT NULL CONSTRAINT DF_CwlParticipations_attacks_used DEFAULT 0,
    attack_targets INT NOT NULL CONSTRAINT DF_CwlParticipations_attack_targets DEFAULT 0,
    war_count_comparison INT NOT NULL CONSTRAINT DF_CwlParticipations_wcc DEFAULT 0,
    stars_collected INT NOT NULL CONSTRAINT DF_CwlParticipations_stars DEFAULT 0,
    damage_percentage DECIMAL(5,2) NOT NULL CONSTRAINT DF_CwlParticipations_damage DEFAULT 0.00,
    bonuses_assigned INT NOT NULL CONSTRAINT DF_CwlParticipations_bonuses DEFAULT 0,
    CONSTRAINT FK_CwlParticipations_CwlEvents FOREIGN KEY (event_id) REFERENCES CwlEvents(id)
);
CREATE INDEX IX_CwlParticipations_player_tag ON CwlParticipations(player_tag);
CREATE INDEX IX_CwlParticipations_event_id ON CwlParticipations(event_id);

CREATE TABLE CwEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    attack_days INT NOT NULL CONSTRAINT DF_CwEvents_attack_days DEFAULT 1
);
CREATE INDEX IX_CwEvents_clan_tag ON CwEvents(clan_tag);

CREATE TABLE CwParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    day_number INT NOT NULL,
    attacks_used INT NOT NULL CONSTRAINT DF_CwParticipations_attacks_used DEFAULT 0,
    attack_targets INT NOT NULL CONSTRAINT DF_CwParticipations_attack_targets DEFAULT 0,
    war_count_comparison INT NOT NULL CONSTRAINT DF_CwParticipations_wcc DEFAULT 0,
    stars_collected INT NOT NULL CONSTRAINT DF_CwParticipations_stars DEFAULT 0,
    CONSTRAINT FK_CwParticipations_CwEvents FOREIGN KEY (event_id) REFERENCES CwEvents(id)
);
CREATE INDEX IX_CwParticipations_player_tag ON CwParticipations(player_tag);
CREATE INDEX IX_CwParticipations_event_id ON CwParticipations(event_id);

CREATE TABLE RaidEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);

CREATE TABLE RaidParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    attacks_used INT NOT NULL CONSTRAINT DF_RaidParticipations_attacks_used DEFAULT 0,
    points_reached INT NOT NULL CONSTRAINT DF_RaidParticipations_points DEFAULT 0,
    CONSTRAINT FK_RaidParticipations_RaidEvents FOREIGN KEY (event_id) REFERENCES RaidEvents(id)
);
CREATE INDEX IX_RaidParticipations_player_tag ON RaidParticipations(player_tag);
CREATE INDEX IX_RaidParticipations_event_id ON RaidParticipations(event_id);

CREATE TABLE ClanGamesEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);

CREATE TABLE ClanGamesParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    points_contributed INT NOT NULL CONSTRAINT DF_ClanGamesParticipations_points DEFAULT 0,
    milestone_reached NVARCHAR(20) NULL,
    CONSTRAINT FK_ClanGamesParticipations_ClanGamesEvents FOREIGN KEY (event_id) REFERENCES ClanGamesEvents(id)
);
CREATE INDEX IX_ClanGamesParticipations_player_tag ON ClanGamesParticipations(player_tag);
CREATE INDEX IX_ClanGamesParticipations_event_id ON ClanGamesParticipations(event_id);

CREATE TABLE Members (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL UNIQUE,
    discord_id NVARCHAR(20) NULL,
    role NVARCHAR(20) NOT NULL CONSTRAINT DF_Members_role DEFAULT N'Member',
    verified_at DATETIME2 NOT NULL CONSTRAINT DF_Members_verified_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_Members_updated_at DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_Members_discord_id ON Members(discord_id);

CREATE TABLE ContributionScores (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL,
    event_date DATETIME2 NOT NULL,
    cwl_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cwl DEFAULT 0.00,
    cw_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cw DEFAULT 0.00,
    raid_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_raid DEFAULT 0.00,
    clan_games_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cg DEFAULT 0.00,
    total_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_total DEFAULT 0.00
);
CREATE INDEX IX_ContributionScores_player_tag ON ContributionScores(player_tag);
CREATE INDEX IX_ContributionScores_event_date ON ContributionScores(event_date);
"""


def get_azure_token():
    """Get Azure AD access token for Azure SQL from the Linux host."""
    print("Getting Azure AD access token from Linux host...")
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        print("Got Azure AD token successfully.")
        return token.token
    except Exception as e:
        print(f"DefaultAzureCredential failed: {e}")
        # Fallback: try az cli
        print("Trying az cli as fallback...")
        try:
            result = subprocess.run(
                ["az", "account", "get-access-token", "--resource-type", "azure-database"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                print("Got token from az cli.")
                return data["accessToken"]
        except Exception as e2:
            print(f"Az CLI fallback also failed: {e2}")
        print("\nMake sure you're logged in with `az login` first.")
        sys.exit(1)


def apply_via_vm(access_token):
    """Apply schema by running Python on the Windows VM via pypsrp."""
    if not HAS_PS:
        print("ERROR: pypsrp is required but not installed.")
        print("Install with: pip install pypsrp")
        sys.exit(1)

    print(f"Connecting to VM {VM_HOST}:{VM_PORT} as {VM_USERNAME}...")
    wsman = WSMan(
        server=VM_HOST,
        port=VM_PORT,
        username=VM_USERNAME,
        password=VM_PASSWORD,
        auth="ntlm",
        ssl=False,
    )

    # Mask the token for logging
    masked_token = access_token[:20] + "..." if len(access_token) > 20 else "***"
    print(f"Using token: {masked_token}")

    # Write the Python script to the VM (with token pre-populated)
    python_script = r'''
import pyodbc

SQL_SERVER = "picteoinst1.database.windows.net"
SQL_DATABASE = "discordcoc"
ACCESS_TOKEN = r"""''' + access_token + r'''"""

with open("C:\\Temp\\schema.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

print(f"Connecting to {SQL_SERVER}/{SQL_DATABASE}...")
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"ACCESS_TOKEN={ACCESS_TOKEN};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
print("Connected!")

statements = [s.strip() for s in schema_sql.split(";") if s.strip() and not s.strip().startswith("--")]
for stmt in statements:
    if "CREATE TABLE" in stmt.upper():
        parts = stmt.split("(")[0].strip().split()
        table_name = parts[-1].strip()
        if table_name.startswith("["):
            table_name = table_name.strip("[]")
        print(f"  Creating table: {table_name}")
    try:
        cursor.execute(stmt)
    except Exception as e:
        if "already exists" in str(e).lower():
            pass
        else:
            print(f"  Error: {e}")

cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
print("\nTables in database:")
for table in cursor.fetchall():
    print(f"  - {table[0]}")

print("\nSchema applied successfully!")
cursor.close()
conn.close()
'''

    with RunspacePool(wsman) as rs:
        ps = PowerShell(rs)

        # Create temp directory and write files
        setup_script = """
if (-not (Test-Path "C:\\Temp")) {
    New-Item -ItemType Directory -Path "C:\\Temp" -Force | Out-Null
}

# Write SQL file
$sql = @'
""" + SCHEMA_SQL + """'@
[System.IO.File]::WriteAllText("C:\\Temp\\schema.sql", $sql, [System.Text.Encoding]::UTF8)
Write-Output "SQL file written."

# Write Python script (with access token)
$py = @'
""" + python_script + """'@
[System.IO.File]::WriteAllText("C:\\Temp\\apply_schema.py", $py, [System.Text.Encoding]::UTF8)
Write-Output "Python script written with access token."
"""

        ps.add_script(setup_script)
        print("Setting up files on VM...")
        result = ps.invoke()
        for item in ps.output:
            print(f"  {item}")

        for err in ps.streams.error:
            print(f"  [ERROR] {err}")

        # Run the Python script
        print("\nRunning schema application...")
        ps2 = PowerShell(rs)
        run_script = """
$env:PATH = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312;C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\Scripts;" + $env:PATH
$result = py C:\\Temp\\apply_schema.py 2>&1
Write-Output $result
"""
        ps2.add_script(run_script)
        ps2.invoke()
        for item in ps2.output:
            print(f"  {item}")

        for err in ps2.streams.error:
            print(f"  [ERROR] {err}")

    wsman.close()


def apply_locally():
    """Apply schema locally using pyodbc + Azure AD auth."""
    if pyodbc is None:
        print("ERROR: pyodbc is not available. Try running on the Windows VM.")
        sys.exit(1)

    print("=== DiscordCoC Azure SQL Schema Applied ===")
    print(f"Server: {SQL_SERVER}")
    print(f"Database: {SQL_DATABASE}\n")

    # Get Azure AD token
    access_token = get_azure_token()

    # Connect to Azure SQL
    connection_string = (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"ACCESS_TOKEN={access_token};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )

    print(f"Connecting to {SQL_SERVER}/{SQL_DATABASE}...")

    try:
        conn = pyodbc.connect(connection_string)
        print("Connected successfully!")
        cursor = conn.cursor()

        # Execute schema SQL (split by semicolons)
        print("\nApplying schema...")
        statements = [s.strip() for s in SCHEMA_SQL.split(";") if s.strip()]

        for stmt in statements:
            if stmt.startswith("--") or not stmt:
                continue
            try:
                cursor.execute(stmt)
                if "CREATE TABLE" in stmt.upper():
                    parts = stmt.split("(")[0].strip().split()
                    table_name = parts[-1].strip()
                    if table_name.startswith("["):
                        table_name = table_name.strip("[]")
                    print(f"  Created table: {table_name}")
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "object already exists" in error_msg.lower():
                    print(f"  (Table already exists)")
                else:
                    print(f"  Error: {e}")

        # Verify tables
        print("\nVerifying tables...")
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
        )
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

        print("\nSchema application completed successfully!")
        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=== DiscordCoC Azure SQL Schema Applied ===")

    if pyodbc is None:
        print("\nNo ODBC driver available locally. Falling back to VM execution...\n")
        access_token = get_azure_token()
        apply_via_vm(access_token)
    else:
        drivers = pyodbc.drivers()
        print(f"Available ODBC drivers: {drivers}")
        if drivers:
            print("Applying schema locally...\n")
            apply_locally()
        else:
            print("\nNo ODBC drivers available. Falling back to VM execution...\n")
            access_token = get_azure_token()
            apply_via_vm(access_token)