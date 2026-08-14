#!/usr/bin/env python3
"""
Apply database schema to Azure SQL database via WIN-2HBN30ECLV2 ARC server.
Uses PowerShell WinRM with az CLI token acquisition + pyodbc AccessToken auth.

This approach:
1. Runs 'az account get-access-token --resource-type az-api' on the ARC server
2. Parses the token
3. Uses pyodbc with AccessToken= parameter to connect to Azure SQL
"""
import sys
import base64
import json
from pathlib import Path
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool


def main():
    wsman = WSMan(
        server="WIN-2HBN30ECLV2.fritz.box",
        port=5985,
        username="administrator",
        password="Sunsh!n30!",
        auth="ntlm",
        ssl=False,
    )

    # Read schema file
    schema_path_local = Path(__file__).parent.parent / "database" / "schema.sql"
    schema_sql = schema_path_local.read_text(encoding="utf-8")
    schema_b64 = base64.b64encode(schema_sql.encode("utf-8")).decode("ascii")

    # Build the Python script - no IMDS, just use az CLI token
    table_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' ORDER BY TABLE_NAME"

    py_script_lines = [
        'import pyodbc, sys, base64, json, subprocess',
        '',
        'server = "picteoinst1.database.windows.net"',
        'database = "discordcoc"',
        'port = 1433',
        '',
        'encoded = "' + schema_b64 + '"',
        'schema_sql = base64.b64decode(encoded).decode("utf-8")',
        '',
        'print("=" * 70)',
        'print("Azure SQL Schema Deployment via az CLI Token")',
        'print("=" * 70)',
        'print(f"Target: {server}/{database}")',
        'print(f"Schema size: {len(schema_sql)} bytes")',
        'print()',
        '',
        '# Step 1: Get Azure AD token via az CLI',
        'print("Step 1: Obtaining Azure AD token via az CLI...")',
        'try:',
        '    result = subprocess.run(',
        '        ["az", "account", "get-access-token",',
        '         "--resource-type", "az-api",',
        '         "--query", "accessToken",',
        '         "--output", "tsv"],',
        '        capture_output=True, text=True, timeout=30',
        '    )',
        '    if result.returncode != 0:',
        '        print(f"  [ERROR] az CLI failed: {result.stderr.strip()}")',
        '        print("  Hint: Run \'az login\' first or ensure managed identity is configured")',
        '        sys.exit(1)',
        '    azure_token = result.stdout.strip()',
        '    if not azure_token:',
        '        print("  [ERROR] Empty token from az CLI")',
        '        sys.exit(1)',
        '    print(f"  Token obtained: {azure_token[:40]}...")',
        'except FileNotFoundError:',
        '    print("  [ERROR] az CLI not found. Install Azure CLI or run az login first.")',
        '    sys.exit(1)',
        'except subprocess.TimeoutExpired:',
        '    print("  [ERROR] az CLI timed out. Check network connectivity.")',
        '    sys.exit(1)',
        'except Exception as e:',
        '    print(f"  [ERROR] Failed to get token: {e}")',
        '    sys.exit(1)',
        '',
        '# Step 2: Connect to Azure SQL using the token',
        'print("\\nStep 2: Connecting to Azure SQL Database...")',
        'conn_str = (',
        '    "DRIVER={ODBC Driver 18 for SQL Server};"',
        '    f"SERVER={server},{port};"',
        '    f"DATABASE={database};"',
        '    "Encrypt=yes;"',
        '    "TrustServerCertificate=no;"',
        '    "AccessToken=" + azure_token',
        ')',
        'print(f"  Server: {server},{port}")',
        'print(f"  Database: {database}")',
        'print(f"  Auth: Azure AD Access Token (via az CLI)")',
        'print(f"  Connection string: DRIVER=ODBC Driver 18; SERVER={server},{port}; DATABASE={database}; Encrypt=yes; AccessToken=****")',
        'print()',
        '',
        'try:',
        '    conn = pyodbc.connect(conn_str, timeout=30)',
        '    print("  SUCCESS: Connected to Azure SQL Database!")',
        '    cursor = conn.cursor()',
        '',
        '    # Show current user context',
        '    cursor.execute("SELECT SYSTEM_USER, USER_NAME()")',
        '    row = cursor.fetchone()',
        '    print(f"  Current user: {row[0]} (database user: {row[1]})")',
        '',
        '    # Step 3: Execute schema',
        '    print("\\nStep 3: Executing schema...")',
        '    print("-" * 70)',
        '',
        '    # Split on GO statements',
        '    batches = []',
        '    current_batch = []',
        '    for line in schema_sql.split("\\n"):',
        '        if line.strip().upper() == "GO":',
        '            if current_batch:',
        '                batches.append("\\n".join(current_batch).strip())',
        '                current_batch = []',
        '        else:',
        '            current_batch.append(line)',
        '    if current_batch:',
        '        batches.append("\\n".join(current_batch).strip())',
        '',
        '    print(f"  Total batches: {len(batches)}")',
        '    print()',
        '',
        '    executed = 0',
        '    errors = 0',
        '    warnings_list = []',
        '    skipped = 0',
        '    for i, batch in enumerate(batches):',
        '        if not batch:',
        '            skipped += 1',
        '            continue',
        '        try:',
        '            cursor.execute(batch)',
        '            executed += 1',
        '            if executed % 10 == 0:',
        '                print(f"  Progress: {executed} executed, {errors} errors...")',
        '        except Exception as e:',
        '            errors += 1',
        '            first_word = None',
        '            for word in batch.split():',
        '                if word and not word.startswith("--") and len(word) > 2:',
        '                    first_word = word[:50]',
        '                    break',
        '            msg = str(e)[:200]',
        '            warnings_list.append(f"Batch {i+1} ({first_word}): {msg}")',
        '            if errors <= 10:',
        '                print(f"  [WARN] Batch {i+1} ({first_word}): {msg}")',
        '',
        '    conn.commit()',
        '    print("-" * 70)',
        '    print(f"\\n  Executed: {executed} batches")',
        '    print(f"  Errors:   {errors}")',
        '    if skipped:',
        '        print(f"  Skipped:  {skipped} empty batches")',
        '',
        '    if warnings_list:',
        '        print(f"\\n  Warnings detail (first {min(10, len(warnings_list))}):")',
        '        for w in warnings_list[:10]:',
        '            print(f"    - {w}")',
        '        if len(warnings_list) > 10:',
        '            print(f"    ... and {len(warnings_list) - 10} more")',
        '',
        '    # Step 4: Verify tables',
        '    print("\\nStep 4: Verifying created tables...")',
        '    cursor.execute("' + table_query + '")',
        '    tables = [row[0] for row in cursor.fetchall()]',
        '    print(f"  Tables in discordcoc database: {len(tables)}")',
        '    for t in tables:',
        '        print(f"    - {t}")',
        '',
        '    cursor.close()',
        '    conn.close()',
        '    print("\\n" + "=" * 70)',
        '    print("Schema deployment completed successfully!")',
        '    print("=" * 70)',
        '    sys.exit(0)',
        'except pyodbc.Error as e:',
        '    print(f"\\n  [ERROR] pyodbc.Error: {e}")',
        '    print("\\n  Troubleshooting:")',
        '    print("  1. Verify az CLI is logged in (run \'az login\' on the server)")',
        '    print("  2. Check that the signed-in user has permission to discordcoc database")',
        '    print("  3. Verify SQL Azure firewall allows ARC server IP")',
        '    print("  4. Check Azure SQL server admin configuration")',
        '    import traceback',
        '    traceback.print_exc()',
        '    sys.exit(1)',
        'except Exception as e:',
        '    print(f"\\n  [ERROR] {type(e).__name__}: {e}")',
        '    import traceback',
        '    traceback.print_exc()',
        '    sys.exit(1)',
    ]
    py_script = "\n".join(py_script_lines) + "\n"
    py_b64 = base64.b64encode(py_script.encode("utf-8")).decode("ascii")

    # PowerShell: decode+save Python script, check az, then run
    ps_script = (
        '$pyB64 = "' + py_b64 + '"\n'
        '$pyBytes = [Convert]::FromBase64String($pyB64)\n'
        '$pyText = [System.Text.Encoding]::UTF8.GetString($pyBytes)\n'
        '\n'
        '$pyPath = "$env:TEMP\\deploy_schema_direct.py"\n'
        '[System.IO.File]::WriteAllText($pyPath, $pyText, [System.Text.UTF8Encoding]::new($false))\n'
        'Write-Output "Python script written to: $pyPath"\n'
        '\n'
        '# Check az CLI\n'
        'try {\n'
        '    $azVer = & az --version 2>&1 | Select-String "azure-cli" | Select-Object -First 1\n'
        '    Write-Output "az CLI version: $azVer"\n'
        '    $azLogin = & az account show --query "user.name" --output tsv 2>&1\n'
        '    if ($?) {\n'
        '        Write-Output "Currently logged in as: $azLogin"\n'
        '    } else {\n'
        '        Write-Output "az account show failed - run \'az login\' first"\n'
        '    }\n'
        '} catch {\n'
        '    Write-Output "az CLI not found or error: $_"\n'
        '}\n'
        '\n'
        '# Check ODBC drivers\n'
        '& py -c "import pyodbc; print(\'ODBC drivers: \' + str([d for d in pyodbc.drivers()]))" 2>&1\n'
        '\n'
        'Write-Output ""\n'
        'Write-Output "=== Deploying schema to discordcoc ==="\n'
        'Write-Output ""\n'
        '& py -u "$pyPath" 2>&1\n'
        '$result = $LASTEXITCODE\n'
        '\n'
        'Remove-Item $pyPath -ErrorAction SilentlyContinue\n'
        'exit $result\n'
    )

    with RunspacePool(wsman) as rs:
        ps = PowerShell(rs)
        ps.add_script(ps_script)
        print("=== Applying schema to discordcoc database via WIN-2HBN30ECLV2 (az CLI token) ===")
        print("Authentication: Azure AD Access Token via az CLI on ARC server")
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