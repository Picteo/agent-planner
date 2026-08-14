#!/usr/bin/env python3
"""Test Azure SQL connection from VM with multiple connection string variations."""
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool
import base64

wsman = WSMan(
    server="WIN-2HBN30ECLV2.fritz.box",
    port=5985,
    username="administrator",
    password="Sunsh!n30!",
    auth="ntlm",
    ssl=False,
)

test_script = r"""
import sys

try:
    import pypyodbc as pyodbc
    print("pypyodbc version: " + pyodbc.version)
    print("")
    print("Available drivers:")
    drivers = pyodbc.drivers()
    for d in drivers:
        print("  - " + d)
except ImportError as e:
    print("pypyodbc import failed: " + str(e))
    sys.exit(1)

server = "discordcoc.database.windows.net"
database = "discordcoc"
username = "twan"
password = "Sunsh" + chr(33) + "n30" + chr(33)

print("")
print("Testing Azure SQL connection with multiple strategies...")
print("Server: " + server)
print("Database: " + database)
print("")

# Strategy 1: ODBC Driver 18 (if available)
print("=== Strategy 1: ODBC Driver 18 for SQL Server ===")
try:
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=" + server + ";"
        "DATABASE=" + database + ";UID=" + username + ";PWD=" + password + ";"
        "Encrypt=yes;TrustServerCertificate=no;"
        "ConnectionTimeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    print("SUCCESS with ODBC Driver 18!")
    conn.close()
except pyodbc.Error as e:
    print("FAILED: " + str(e))

# Strategy 2: Legacy SQL Server with TCP
print("")
print("=== Strategy 2: SQL Server driver with TCP ===")
try:
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=tcp:" + server + ",1433;"
        "DATABASE=" + database + ";UID=" + username + ";PWD=" + password + ";"
        "Encrypt=yes;TrustServerCertificate=no;"
        "ConnectionTimeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    print("SUCCESS with SQL Server driver + TCP!")
    conn.close()
except pyodbc.Error as e:
    print("FAILED: " + str(e))

# Strategy 3: No encryption (for debugging)
print("")
print("=== Strategy 3: No encryption ===")
try:
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=tcp:" + server + ",1433;"
        "DATABASE=" + database + ";UID=" + username + ";PWD=" + password + ";"
        "Encrypt=no;"
        "ConnectionTimeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    print("SUCCESS without encryption (debug mode)!")
    conn.close()
except pyodbc.Error as e:
    print("FAILED: " + str(e))

# Strategy 4: mssql package (pure Python TDS)
print("")
print("=== Strategy 4: mssql pure Python package ===")
try:
    import mssql
    print("mssql package loaded")
except ImportError:
    print("mssql package not available")
except Exception as e:
    print("mssql import error: " + str(e))

# Strategy 5: mssql package (pure Python TDS) - try pymssql
print("")
print("=== Strategy 5: pymssql package ===")
try:
    import pymssql
    print("pymssql package loaded")
except ImportError:
    print("pymssql package not available")
except Exception as e:
    print("pymssql import error: " + str(e))
"""

encoded = base64.b64encode(test_script.encode('utf-8')).decode('utf-8')

ps_script = f"""
$bytes = [Convert]::FromBase64String('{encoded}')
$script = [System.Text.Encoding]::UTF8.GetString($bytes)
[System.IO.File]::WriteAllText('C:\\Temp\\test_connection_v4.py', $script, [System.Text.Encoding]::UTF8)
Write-Output 'Script written'
py C:\\Temp\\test_connection_v4.py 2>&1
"""

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Running comprehensive connection test...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()