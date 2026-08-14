#!/usr/bin/env python3
"""Check if ODBC Driver 18 was installed on the VM."""
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

# Write the PS1 script to the VM
ps_script = r'''
# Check registry for ODBC Driver 18
$key = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server'
if (Test-Path $key) {
    Write-Output 'ODBC Driver 18 is installed!'
    Get-ItemProperty $key | Format-List
} else {
    Write-Output 'ODBC Driver 18 NOT found in registry'
}

# Also check Wow6432Node for 32-bit
$key32 = 'HKLM:\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server'
if (Test-Path $key32) {
    Write-Output 'ODBC Driver 18 (32-bit) is installed!'
    Get-ItemProperty $key32 | Format-List
} else {
    Write-Output 'ODBC Driver 18 (32-bit) NOT found'
}

# List all ODBC driver registry entries
Write-Output ''
Write-Output 'All ODBC drivers in registry:'
Get-ChildItem 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ('  ' + $_.PSChildName) }
Get-ChildItem 'HKLM:\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ('  (32-bit) ' + $_.PSChildName) }

# Check if MSI was installed
if (Test-Path 'C:\Temp\msodbcsql18.msi') {
    Write-Output 'MSI file still exists at C:\Temp\msodbcsql18.msi'
}

# Check if pyodbc can see the driver now
$result = py -c "import pyodbc; print(pyodbc.drivers())" 2>&1
Write-Output $result
'''

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Checking ODBC driver installation on VM...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()