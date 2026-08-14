#!/usr/bin/env python3
"""
Apply database schema to Azure SQL database via WIN-2HBN30ECLV2 ARC server.
Uses system managed identity of the ARC VM with Azure CLI to connect to Azure SQL Database.
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

    # PowerShell script that uses Azure CLI with managed identity to connect to Azure SQL
    ps_script = rf'''
# Decode schema SQL
$encoded = "{schema_b64}"
$bytes = [Convert]::FromBase64String($encoded)
$schemaSql = [System.Text.Encoding]::UTF8.GetString($bytes)

Write-Output "Schema decoded: $($schemaSql.Length) bytes"

# Write schema to temp file for sqlcmd
$schemaPath = "$env:TEMP\apply_schema.sql"
[System.IO.File]::WriteAllText($schemaPath, $schemaSql, [System.Text.UTF8Encoding]::new($false))
Write-Output "Schema written to: $schemaPath"

# Try to use Azure CLI with managed identity to get access token and connect
$azureSqlServer = "picteoinst1.database.windows.net"
$azureSqlDatabase = "discordcoc"
$azureSqlUser = "twan"

Write-Output "Attempting to connect via Azure SQL with managed identity..."

# First check if we can login with managed identity
try {{
    $tokenResult = az account get-access-resource --resource https://database.windows.net/ --query 'accessToken' -o tsv 2>&1
    if ($tokenResult -and $tokenResult.Trim() -ne "") {{
        Write-Output "Got access token via Azure CLI"

        # Use sqlcmd with Azure AD Managed Identity
        # sqlcmd -S $azureSqlServer -U $azureSqlUser@$azureSqlServer -d $azureSqlDatabase -G -i $schemaPath
        $sqlcmdArgs = "-S", "$azureSqlServer", "-U", "$azureSqlUser@$azureSqlServer",
                      "-d", "$azureSqlDatabase", "-G", "-i", $schemaPath, "-o", "$env:TEMP\apply_schema.log", "-h-1", "-W"

        Write-Output "Running: sqlcmd $($sqlcmdArgs -join ' ')"
        $sqlcmdOutput = & sqlcmd $sqlcmdArgs 2>&1
        Write-Output $sqlcmdOutput

        # Check results
        if (Test-Path "$env:TEMP\apply_schema.log") {{
            Write-Output "`n=== sqlcmd Output ==="
            Get-Content "$env:TEMP\apply_schema.log"
        }}
    }} else {{
        Write-Output "Failed to get access token, trying alternative methods..."
    }}
}} catch {{
    Write-Output "[ERROR] Azure CLI token failed: $($_.Exception.Message)"
}}

# List available SQL tools
Write-Output "`n=== Checking SQL tools ==="
$tools = @("sqlcmd", "SQLPS", "Microsoft.SqlServer.Management.Sdk.Sfc")
foreach ($tool in $tools) {{
    $found = Get-Command $tool -ErrorAction SilentlyContinue
    if ($found) {{
        Write-Output "Found: $($found.Source)"
    }} else {{
        Write-Output "Not found: $tool"
    }}
}}

# Check if SQL Server is running locally
Write-Output "`n=== Checking local SQL Server ==="
$services = Get-Service -Name "*SQL*" -ErrorAction SilentlyContinue
foreach ($svc in $services) {{
    Write-Output "  Service: $($svc.ServiceName) - Status: $($svc.Status)"
}}

# Check SQL instances
Write-Output "`n=== SQL Instances ==="
$instances = Get-CimInstance -ClassName Win32_Service -Filter "Name LIKE '%SQL%'" -ErrorAction SilentlyContinue
foreach ($inst in $instances) {{
    Write-Output "  $($inst.Name): $($inst.State)"
}}

# Cleanup
Remove-Item $schemaPath -ErrorAction SilentlyContinue

Write-Output "`n=== Diagnostics complete ==="
'''

    with RunspacePool(wsman) as rs:
        ps = PowerShell(rs)
        ps.add_script(ps_script)
        print("=== Diagnosing SQL connectivity on WIN-2HBN30ECLV2 ===")
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