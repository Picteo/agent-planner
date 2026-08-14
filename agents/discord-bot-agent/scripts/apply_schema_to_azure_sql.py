#!/usr/bin/env python3
"""Apply the DiscordCoC database schema to Azure SQL from the Windows VM."""

import base64
import sys
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.complex_objects import Command

# VM Configuration
HOST = "WIN-2HBN30ECLV2.fritz.box"
PORT = 5985
USERNAME = "administrator"
PASSWORD = "Sunsh!n30!"

# Azure SQL Configuration
SQL_SERVER = "picteoinst1.database.windows.net"
SQL_DATABASE = "discordcoc"
SQL_USER = "CloudSA3e4cb373"


def main():
    print(f"Connecting to {HOST}:{PORT} as {USERNAME}...")

    try:
        wsman = WSMan(
            server=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
            auth="ntlm",
            ssl=False,
        )

        print("Connection successful!")

        # Base64 encode the SQL to avoid escaping issues
        schema_sql = r"""
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

        sql_base64 = base64.b64encode(schema_sql.encode('utf-8')).decode('ascii')

        # PowerShell script using base64 decoded SQL
        ps_script = f"""
# Create temp directory if needed
if (-not (Test-Path "C:\\Temp")) {{
    New-Item -ItemType Directory -Path "C:\\Temp" -Force
}}

# Decode base64 SQL and write to file
$bytes = [Convert]::FromBase64String("{sql_base64}")
$encoded = [System.Text.Encoding]::UTF8.GetString($bytes)
[IO.File]::WriteAllText("C:\\Temp\\schema.sql", $encoded, [System.Text.Encoding]::UTF8)
Write-Output "Schema file written to C:\\Temp\\schema.sql"

# SQL Configuration
$SQLServer = "{SQL_SERVER}"
$SQLDatabase = "{SQL_DATABASE}"

Write-Output "Connecting to Azure SQL..."
Write-Output "Server: ${{SQLServer}}"
Write-Output "Database: ${{SQLDatabase}}"

# Install NuGet provider if needed
Write-Output "Installing NuGet provider..."
if (-not (Get-PackageProvider -Name NuGet -ListAvailable -ErrorAction SilentlyContinue)) {{
    Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Confirm:$false
    Write-Output "NuGet provider installed."
}} else {{
    Write-Output "NuGet provider already available."
}}

# Install Az.Accounts module (provides Connect-AzAccount)
Write-Output "Installing Az.Accounts module for Azure login..."
if (-not (Get-Module -ListAvailable -Name Az.Accounts)) {{
    Install-Module -Name Az.Accounts -Force -AllowClobber -Scope CurrentUser -Confirm:$false
    Write-Output "Az.Accounts module installed."
}} else {{
    Write-Output "Az.Accounts module already available."
}}

# Install az CLI for token acquisition
Write-Output "Installing Azure CLI (az)..."
try {{
    $azInstalled = Get-Command az -ErrorAction SilentlyContinue
    if ($azInstalled) {{
        Write-Output "az CLI already installed: $((az --version | Select-String 'azure-cli').ToString().Trim())"
    }} else {{
        Write-Output "Installing az CLI via winget..."
        winget install Microsoft.AzureCLI --silent --accept-package-agreements --accept-source-agreements
        Write-Output "az CLI installed."
    }}
}} catch {{
    Write-Output "az CLI not installed, will try Python method..."
}}

# Install SqlServer module if not present
if (-not (Get-Module -ListAvailable -Name SqlServer)) {{
    Write-Output "Installing SqlServer module..."
    Install-Module -Name SqlServer -Force -AllowClobber -Scope CurrentUser -Confirm:$false
    Write-Output "SqlServer module installed."
}} else {{
    Write-Output "SqlServer module already available."
}}

Import-Module SqlServer
Import-Module Az.Accounts

# Try to get Azure AD access token using Az module
$SqlAccessToken = $null

# First try: Get-AzAccessToken (Az.Accounts 2.15+)
Write-Output "Trying Get-AzAccessToken..."
try {{
    $tokenResponse = Get-AzAccessToken -ResourceTypeName "SqlAzure" -ErrorAction SilentlyContinue
    if ($tokenResponse -and $tokenResponse.Token) {{
        $SqlAccessToken = $tokenResponse.Token
        Write-Output "Got token via Get-AzAccessToken."
    }}
}} catch {{
    Write-Output "Get-AzAccessToken failed: $($_.Exception.Message)"
}}

# Second try: Try az CLI cached token
if ($null -eq $SqlAccessToken) {{
    Write-Output "Trying az CLI for token..."
    try {{
        $azResult = az account get-access-token --resource-type aad-graph 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {{
            $json = $azResult | ConvertFrom-Json
            if ($json -and $json.accessToken) {{
                # Need Azure AD token for SQL, try database resource
            }}
        }}
    }} catch {{
        Write-Output "az CLI method failed: $($_.Exception.Message)"
    }}
}}

# Third try: Try az CLI with resource https://database.windows.net/
if ($null -eq $SqlAccessToken) {{
    Write-Output "Trying az CLI for SQL token..."
    try {{
        $azResult = (az account get-access-token --resource "https://database.windows.net/" 2>&1) | Out-String
        if ($LASTEXITCODE -eq 0 -and $azResult.Trim()) {{
            $json = $azResult | ConvertFrom-Json
            if ($json -and $json.accessToken) {{
                $SqlAccessToken = $json.accessToken
                Write-Output "Got token via az CLI."
            }}
        }}
    }} catch {{
        Write-Output "az CLI SQL token failed: $($_.Exception.Message)"
    }}
}}
        if ($SqlAccessToken) {{
            Write-Output "Token status: Available"
        }} else {{
            Write-Output "Token status: Missing"
        }}

Write-Output "Applying schema..."
try {{
    $SqlCommands = Get-Content -Path "C:\\Temp\\schema.sql" -Raw
    if ($SqlAccessToken) {{
        Invoke-Sqlcmd -ServerInstance $SQLServer -Database $SQLDatabase -AccessToken $SqlAccessToken -Query $SqlCommands -ErrorAction Stop
    }} else {{
        # Fallback to SQL auth
        $sqlConnStr = "Server=$SQLServer;Database=$SQLDatabase;User ID=CloudSA3e4cb373;Password=$env:SQL_ADMIN_PASSWORD;Encrypt=True;TrustServerCertificate=False;"
        Write-Output "Using SQL auth fallback"
        Invoke-Sqlcmd -ConnectionString $sqlConnStr -Query $SqlCommands -ErrorAction Stop
    }}
    Write-Output "SUCCESS: Schema applied!"

    Write-Output ""
    Write-Output "Verifying tables..."
    if ($SqlAccessToken) {{
        $Tables = Invoke-Sqlcmd -ServerInstance $SQLServer -Database $SQLDatabase -AccessToken $SqlAccessToken -Query "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME" -ErrorAction Stop
    }} else {{
        $sqlConnStr = "Server=$SQLServer;Database=$SQLDatabase;User ID=CloudSA3e4cb373;Password=$env:SQL_ADMIN_PASSWORD;Encrypt=True;TrustServerCertificate=False;"
        $Tables = Invoke-Sqlcmd -ConnectionString $sqlConnStr -Query "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME" -ErrorAction Stop
    }}
    Write-Output "Tables created:"
    $Tables | ForEach-Object {{ Write-Output "  - $($_.TABLE_NAME)" }}

    Write-Output ""
    Write-Output "Schema application completed successfully!"
}} catch {{
    Write-Output "ERROR: $($_.Exception.Message)"
    Write-Output $_.Exception.ToString()
}}
"""

        with RunspacePool(wsman) as rs:
            ps = PowerShell(rs)
            cmd = Command(cmd=ps_script, is_script=True)
            ps.add_command(cmd)

            print("\n--- Applying schema to Azure SQL ---")
            print(f"Server: {SQL_SERVER}")
            print(f"Database: {SQL_DATABASE}\n")

            # Invoke the script
            ps.invoke()

            # Print output
            for item in ps.output:
                print(f"  {item}")

            # Check for errors
            for err in ps.streams.error:
                print(f"  [ERROR] {err}")

            print("\n--- Script completed ---")

    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()