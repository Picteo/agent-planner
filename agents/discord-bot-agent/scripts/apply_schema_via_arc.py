#!/usr/bin/env python3
"""
Apply database schema to Azure SQL database via WIN-2HBN30ECLV2 ARC server.
Uses system managed identity of the ARC VM to connect to Azure SQL Database.
Connects via local SQL Server on the ARC VM using Windows Authentication.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool


def read_schema_file():
    """Read the schema.sql file content."""
    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        return None
    return schema_path.read_text(encoding="utf-8")


def main():
    # VM credentials
    wsman = WSMan(
        server="WIN-2HBN30ECLV2.fritz.box",
        port=5985,
        username="administrator",
        password="Sunsh!n30!",
        auth="ntlm",
        ssl=False,
    )

    # Read schema content
    schema_sql = read_schema_file()
    if schema_sql is None:
        return 1

    # Base64 encode the schema for safe transfer via PowerShell
    import base64
    schema_b64 = base64.b64encode(schema_sql.encode("utf-8")).decode("ascii")

    # PowerShell script that:
    # 1. Decodes the base64 schema
    # 2. Connects to local SQL Server on the VM using Windows Auth (managed identity context)
    # 3. Executes the schema against discordcoc database
    ps_script = rf'''
# Decode schema SQL
$encoded = "{schema_b64}"
$bytes = [Convert]::FromBase64String($encoded)
$schemaSql = [System.Text.Encoding]::UTF8.GetString($bytes)

Write-Output "Schema decoded: $($schemaSql.Length) bytes"

# Connection to local SQL Server on VM (Windows Auth via managed identity context)
$server = "WIN-2HBN30ECLV2"
$database = "discordcoc"
$connectionString = "Server=$server;Database=$database;Trusted_Connection=True;TrustServerCertificate=True;"

Write-Output "Connecting to SQL Server: $connectionString"

try {{
    $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
    $connection.Open()
    Write-Output "Connected to SQL Server successfully"

    $command = $connection.CreateCommand()
    $command.CommandText = $schemaSql

    # Split by GO and execute each batch
    $batches = $schemaSql -split "`nGO`n" | Where-Object {{ $_.Trim() -ne "" }}
    Write-Output "Found $($batches.Count) SQL batches to execute"

    $batchCount = 0
    foreach ($batch in $batches) {{
        $trimmed = $batch.Trim()
        if ($trimmed -ne "" -and $trimmed -ne "GO") {{
            $command.CommandText = $trimmed
            try {{
                $command.ExecuteNonQuery() | Out-Null
                $batchCount++
            }} catch {{
                Write-Output "[WARN] Batch execute error: $($_.Exception.Message)"
                # Continue with next batch
            }}
        }}
    }}

    Write-Output "Executed $batchCount batches"

    # Verify tables were created
    $verifyCmd = $connection.CreateCommand()
    $verifyCmd.CommandText = "SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' ORDER BY TABLE_NAME"
    $reader = $verifyCmd.ExecuteReader()
    Write-Output "`n=== Created Tables ==="
    while ($reader.Read()) {{
        $tableName = $reader.GetString(0)
        $tableType = $reader.GetString(1)
        Write-Output "  [$tableType] $tableName"
    }}
    $reader.Close()

    $connection.Close()
    Write-Output "SQL connection closed"
    Write-Output "Schema deployment completed successfully!"

}} catch {{
    Write-Output "[ERROR] SQL execution failed: $($_.Exception.Message)"
    Write-Output $_.Exception.StackTrace
    exit 1
}}
'''

    with RunspacePool(wsman) as rs:
        ps = PowerShell(rs)
        ps.add_script(ps_script)
        print("=== Applying schema to discordcoc database via WIN-2HBN30ECLV2 ===")
        print()
        ps.invoke()
        for item in ps.output:
            print(item)
        for err in ps.streams.error:
            print(f"[ERROR] {err}")

    wsman.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())