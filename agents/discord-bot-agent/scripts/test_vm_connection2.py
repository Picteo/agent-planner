#!/usr/bin/env python3
"""Test Azure SQL connection from VM using pypyodbc (pure Python, no native ODBC driver)."""
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

# Write the Python test script to the VM as a file, avoiding shell escaping issues
ps_script = r"""
# Create the test Python script on the VM
$testScript = @'
import sys

# Try pypyodbc first
try:
    import pypyodbc as pyodbc
    print(f"pypyodbc version: {pyodbc.version}")
except ImportError as e:
    print(f"pypyodbc import failed: {e}")
    sys.exit(1)

# Connection parameters for Azure SQL
server = "discordcoc.database.windows.net"
database = "discordcoc"
username = "twan"
password = "Sunsh" + "!n30" + "!"

print("Testing Azure SQL connection...")
print(f"Server: {server}")
print(f"Database: {database}")

# Try ODBC Driver 18
try:
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};PORT=1433;"
        f"DATABASE={database};UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;TrustServerCertificate=no;"
        f"ConnectionTimeout=30;"
    )
    print(f"Trying ODBC Driver 18...")
    conn = pyodbc.connect(conn_str)
    print("SUCCESS with ODBC Driver 18!")
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()
    print(f"Server version: {version[0][:100]}")
    cursor.close()
    conn.close()
except pyodbc.Error as e:
    print(f"ODBC Driver 18 failed: {e}")
    # Try legacy SQL Server driver
    try:
        conn_str2 = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"ConnectionTimeout=30;"
        )
        print("Trying legacy SQL Server driver...")
        conn = pyodbc.connect(conn_str2)
        print("SUCCESS with legacy SQL Server driver!")
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        print(f"Server version: {version[0][:100]}")
        cursor.close()
        conn.close()
    except pyodbc.Error as e2:
        print(f"Legacy driver also failed: {e2}")
except Exception as e:
    print(f"Unexpected error with Driver 18: {type(e).__name__}: {e}")
'@

# Write to file on VM
[System.IO.File]::WriteAllText('C:\Temp\test_connection.py', $testScript, [System.Text.Encoding]::UTF8)
Write-Output 'Script written to C:\Temp\test_connection.py'

# Run the test script
Write-Output 'Running connection test...'
py C:\Temp\test_connection.py 2>&1
"""

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Testing Azure SQL connection from VM...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()