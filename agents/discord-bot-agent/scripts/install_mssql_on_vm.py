#!/usr/bin/env python3
"""Install mssql and pypyodbc Python packages on VM and test connection."""
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

ps_script = r"""
Write-Output 'Installing mssql Python package (pure TDS, no ODBC driver needed)...'
py -m pip install mssql --quiet --disable-pip-version-check
Write-Output 'pip install mssql done'

# Test mssql
try {
    $code = @'
import sys
try:
    import mssql
    print("mssql loaded OK")
except Exception as e:
    print(f"mssql import failed: {e}")
'@
    $result = py -c $code 2>&1
    Write-Output $result
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}

# Also try pypyodbc which is pure Python (no native ODBC needed)
Write-Output 'Trying pypyodbc as alternative...'
py -m pip install pypyodbc --quiet --disable-pip-version-check
Write-Output 'pip install pypyodbc done'

try {
    $code = @'
import sys
try:
    import pypyodbc
    print(f"pypyodbc loaded: {pypyodbc.version}")
except Exception as e:
    print(f"pypyodbc import failed: {e}")
'@
    $result = py -c $code 2>&1
    Write-Output $result
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}
"""

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Installing pure Python TDS packages on VM...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()