#!/usr/bin/env python3
"""
Apply database schema to Azure SQL database via WIN-2HBN30ECLV2 ARC server.
Uses Azure AD Access Token authentication via pyodbc AccessToken parameter.
"""
import sys
import base64
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

    # Azure AD token for oss-rdbms (SQL Database)
    azure_token = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6ImZFdHFyaEtUMWJYQUdhZlNk"
        "UW9OMXZYVFJwSSIsImtpZCI6ImZFdHFyaEtUMWJYQUdhZlNkUW9OMXZYVFJwSSJ9"
        ".eyJhdWQiOiJodHRwczovL29zc3JkYm1zLWFhZC5kYXRhYmFzZS53aW5kb3dzLm5l"
        "dCIsImlzcyI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0LzM1MDAyMDhiLTE3NDYt"
        "NGI3MC1hMTRkLTlmZDZiZGI1YTRhYy8iLCJpYXQiOjE3ODYyODc1NTIsIm5iZiI6"
        "MTc4NjI4NzU1MiwiZXhwIjoxNzg2MjkxOTgwLCJhY3IiOiIxIiwiYWNycyI6WyJw"
        "MSJdLCJhaW8iOiJBWFFBaS84Y0FBQUFvRHFoZVpoMnV6Y3NlNzIxa3pORS9wQ1N5"
        "a0prT1RsUjBUcDJyTlBzT0JIeHJyUlhNV2xYWnJpK3ptMng1VnZ6Rzh6K05waG5z"
        "a3NTdzdJdHhkanpYaHFXWmc3WjR5T0RQRDErR2VzQ2l3czdzV21WOUhIZEVXYkt4"
        "MGFNdksvdWdUd3FmWDQzRVlLMW9sTFhvTHhqemc9PSIsImFtciI6WyJwd2QiLCJt"
        "ZmEiXSwiYXBwaWQiOiIwNGIwNzc5NS04ZGRiLTQ2MWEtYmJlZS0wMmY5ZTFiZjdi"
        "NDYiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6IlBlbGttYW5zIiwiZ2l2"
        "ZW5fbmFtZSI6IlR3YW4iLCJncm91cHMiOlsiYjIxMDNmNzItZWJjMy00YTllLTkx"
        "OWQtYjM1ZmM2NjU0ZWVjIiwiN2NhZWExMTctYzQzYi00OWM2LTlmMTQtNGZiZGhm"
        "ZGJiMTc0IiwiMjgzYzc2YWItNDM0Ni00ZWZlLWE1YWYtOWQ5NzNmNDgxYzZjIiwi"
        "MDAxZjI3ZjgtNGM1MS00MWEyLWE4NjYtNzVhMzljNzc1NmU5Il0sImlkdHlwIjoi"
        "dXNlciIsImlwYWRkciI6IjE5NS4yNDAuMzIuMTM2IiwibmFtZSI6IlR3YW4gUGVs"
        "a21hbnMiLCJvaWQiOiIzOGJlZTk0Yy01ZGQ4LTRhN2UtYTU5MC0yYmYyZWVlZjNj"
        "MTkiLCJwdWlkIjoiMTAwMzIwMDI0NEQxQUU4RiIsInJoIjoiMS5BWG9BaXlBQU5V"
        "WVhjRXVoVFpfV3ZiV2tyRkRZUEJMZjJiMUFsTlhKOEh0X29nTjZBT0o2QUEuIiwv"
        "c2NwIjoidXNlcl9pbXBlcnNvbmF0aW9uIiwic2lkIjoiMDA1ZWEyYWEtZDU5YS02"
        "MjhmLTI4ZDEtNzU2NGJlMDNhN2FjIiwic3ViIjoiSVRXNVY0VHNhQzVoRndfVExv"
        "Ym1zVnZfck5HRmRtMk81TUMxajhwaUJmRSIsInRpZCI6IjM1MDAyMDhiLTE3NDYt"
        "NGI3MC1hMTRkLTlmZDZiZGI1YTRhYyIsInVuaXF1ZV9uYW1lIjoidHBlbGttYW5z"
        "QHBpY3Rlby5ubCIsInVwbiI6InRwZWxrbWFuc0BwaWN0ZW8ubmwiLCJ1dGkiOiI3"
        "ZTZZQm9xME1VR2l3aXFYMlpFa0FBIiwidmVyIjoiMS4wIiwieG1zX2FjdF9mY3Qi"
        "OiIzIDUiLCJ4bXNfZnRkIjoiQS1BWW1zVGpfdVR4RnJTTmpPQ0V5S0dNQVRJb2pR"
        "aThOOERBLXUwclJ3WUJaWFZ5YjNCbGQyVnpkQzFrYzIxeiIsInhtc19pZHJlbCI6"
        "IjEgMjAiLCJ4bXNfc3ViX2ZjdCI6IjMgMTYifQ"
        ".OrDPlHyM0OAodKstvTaA-9Ugy3daR3ZvlFynCYTaQQYfhATtlvYz6p9iA-ikIGyz2bmcIk8G_bhxNBvky1XZ3hD9gLQpG9zyfmAHXFoeQ5sJMLNqa3FMecBctQOkTy5PoswkjAcKnfH5aRVqGOuwIROYYAPLG2FeL4T65sxhoqS7oSNpkI1A6AzIl26ANBLer5CfuUWnetV1_Xgn4aXXHrKzpgIsW65kxyVSqJVHitIzpF05ks9CslWGyXdl1Va94UoSBLqTIGtnanXfeLxiG6uufOKCOjCVeAkpz8c7CR3Y_AHcEqcoj1-VLB36CKAoPBvW4NF5Tw2RuIjXmZ2DBA"
    )

    # Build the Python deployment script (base64 for safe transfer)
    # ODBC Driver 18 uses AccessToken= (not TOKEN=) and Authentication=ActiveDirectoryAccessToken
    py_script = (
        'import pyodbc, sys, base64\n'
        '\n'
        'server = "picteoinst1.database.windows.net"\n'
        'database = "discordcoc"\n'
        'user = "twan@picteoinst1.database.windows.net"\n'
        'port = 1433\n'
        '\n'
        'encoded = "' + schema_b64 + '"\n'
        'schema_sql = base64.b64decode(encoded).decode("utf-8")\n'
        '\n'
        'print("Connecting to: " + server + "/" + database + " as " + user)\n'
        'print("Schema size: " + str(len(schema_sql)) + " bytes")\n'
        '\n'
        '# Token from local Azure CLI\n'
        'token = "' + azure_token + '"\n'
        '\n'
        '# Build connection string with AccessToken authentication (ODBC Driver 18)\n'
        '# AccessToken parameter was added in Driver 17+ for Azure AD authentication\n'
        'conn_str = (\n'
        '    "DRIVER={ODBC Driver 18 for SQL Server};"\n'
        '    "SERVER=" + server + "," + str(port) + ";"\n'
        '    "DATABASE=" + database + ";"\n'
        '    "UID=" + user + ";"\n'
        '    "Encrypt=yes;"\n'
        '    "TrustServerCertificate=no;"\n'
        '    "AccessToken=" + token\n'
        ')\n'
        '\n'
        'print("Connection string built with AccessToken auth")\n'
        '\n'
        'try:\n'
        '    conn = pyodbc.connect(conn_str)\n'
        '    print("Connected to Azure SQL Database successfully!")\n'
        '    cursor = conn.cursor()\n'
        '\n'
        '    # Split on GO statements (each line starting with GO)\n'
        '    batches = []\n'
        '    current_batch = []\n'
        '    for line in schema_sql.split("\\n"):\n'
        '        if line.strip().upper() == "GO":\n'
        '            if current_batch:\n'
        '                batches.append("\\n".join(current_batch).strip())\n'
        '                current_batch = []\n'
        '        else:\n'
        '            current_batch.append(line)\n'
        '    if current_batch:\n'
        '        batches.append("\\n".join(current_batch).strip())\n'
        '\n'
        '    print("Executing " + str(len(batches)) + " SQL batches...")\n'
        '\n'
        '    executed = 0\n'
        '    errors = 0\n'
        '    for i, batch in enumerate(batches):\n'
        '        if not batch:\n'
        '            continue\n'
        '        try:\n'
        '            cursor.execute(batch)\n'
        '            executed += 1\n'
        '        except Exception as e:\n'
        '            errors += 1\n'
        '            msg = str(e)[:200]\n'
        '            print("  [WARN] Batch " + str(i+1) + " error: " + msg)\n'
        '\n'
        '    conn.commit()\n'
        '    print("Executed " + str(executed) + " batches, " + str(errors) + " warnings")\n'
        '\n'
        '    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = \'dbo\' ORDER BY TABLE_NAME")\n'
        '    tables = [row[0] for row in cursor.fetchall()]\n'
        '    print("")\n'
        '    print("=== Tables in discordcoc database ===")\n'
        '    for t in tables:\n'
        '        print("  - " + t)\n'
        '\n'
        '    cursor.close()\n'
        '    conn.close()\n'
        '    print("Schema deployment completed successfully!")\n'
        'except Exception as e:\n'
        '    print("[ERROR] " + type(e).__name__ + ": " + str(e))\n'
        '    import traceback\n'
        '    traceback.print_exc()\n'
        '    sys.exit(1)\n'
    )
    py_b64 = base64.b64encode(py_script.encode("utf-8")).decode("ascii")

    # PowerShell: decode+save Python script, then run
    ps_script = (
        '$pyB64 = "' + py_b64 + '"\n'
        '$pyBytes = [Convert]::FromBase64String($pyB64)\n'
        '$pyText = [System.Text.Encoding]::UTF8.GetString($pyBytes)\n'
        '\n'
        '$pyPath = "$env:TEMP\\deploy_schema.py"\n'
        '[System.IO.File]::WriteAllText($pyPath, $pyText, [System.Text.UTF8Encoding]::new($false))\n'
        'Write-Output "Python script written to: $pyPath"\n'
        'Write-Output "Python script size: $($pyText.Length) bytes"\n'
        '\n'
        '# Check ODBC drivers\n'
        '& py -c "import pyodbc; print([d for d in pyodbc.drivers()])" 2>&1\n'
        '\n'
        'Write-Output ""\n'
        'Write-Output "=== Deploying schema ==="\n'
        '& py -u "$pyPath" 2>&1\n'
        '$result = $LASTEXITCODE\n'
        '\n'
        'Remove-Item $pyPath -ErrorAction SilentlyContinue\n'
        'exit $result\n'
    )

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