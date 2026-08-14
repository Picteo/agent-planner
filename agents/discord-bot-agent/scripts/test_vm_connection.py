#!/usr/bin/env python3
"""Test Azure SQL connection from VM using pypyodbc (pure Python, no native ODBC driver)."""
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool

wsman = WSMan(
    server="WIN-2HBN30ECLV2.fritz.box",
    port=5985,
    username="administrator",
    password="Sunsh!n30!",
    auth="ntlm",
    ssl=False,
)

# Test connection using pypyodbc which is pure Python
ps_script = r"""
# Test pypyodbc connection
$code = @'
import sys
import pypyodbc as pyodbc

# Connection parameters for Azure SQL
server = "discordcoc.database.windows.net"
database = "discordcoc"
username = "twan"
password = "Sunsh!n30!"  # masked in output

try:
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;ConnectionTimeout=30;"
    print(f"Connection string pattern: DRIVER={{...}};SERVER={server};...")
    conn = pyodbc.connect(conn_str)
    print("CONNECTION SUCCESS with ODBC Driver 18!")
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()
    print(f"Server version: {version[0][:100]}...")
    cursor.close()
    conn.close()
except pyodbc.Error as e:
    print(f"ODBC Driver 18 failed: {e}")
    # Try legacy SQL Server driver
    try:
        conn_str2 = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;ConnectionTimeout=30;"
        print(f"Trying legacy SQL Server driver...")
        conn = pyodbc.connect(conn_str2)
        print("CONNECTION SUCCESS with legacy SQL Server driver!")
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        print(f"Server version: {version[0][:100]}...")
        cursor.close()
        conn.close()
    except pyodbc.Error as e2:
        print(f"Legacy driver also failed: {e2}")

except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")
'@

$result = py -c $code 2>&1
Write-Output $result
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