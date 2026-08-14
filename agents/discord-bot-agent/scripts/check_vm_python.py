#!/usr/bin/env python3
"""Check Python packages on the VM."""
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

# Write a check script to the VM
check_script = '''
if (-not (Test-Path "C:\\Temp\\check_packages.py")) {
    $content = @"
import sys
print(f"Python path: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import pyodbc
    print(f"pyodbc version: {pyodbc.version}")
except ImportError:
    print("pyodbc NOT installed")
except Exception as e:
    print(f"pyodbc error: {e}")

try:
    import azure.identity
    print("azure.identity installed")
except ImportError:
    print("azure.identity NOT installed")
except Exception as e:
    print(f"azure.identity error: {e}")
"@
    [System.IO.File]::WriteAllText("C:\\Temp\\check_packages.py", $content, [System.Text.Encoding]::UTF8)
    Write-Output "check_packages.py written"
}

Write-Output "Running check..."
$result = py C:\\Temp\\check_packages.py 2>&1
Write-Output $result
'''

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(check_script)
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()