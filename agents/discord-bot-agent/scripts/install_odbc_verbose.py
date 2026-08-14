#!/usr/bin/env python3
"""Install ODBC Driver 18 with verbose logging on the VM."""
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

ps_script = r'''
# Check the MSI file exists
$msiPath = 'C:\Temp\msodbcsql18.msi'
if (Test-Path $msiPath) {
    $file = Get-Item $msiPath
    Write-Output "MSI file size: $($file.Length) bytes"
    Write-Output "MSI file exists: $msiPath"
} else {
    Write-Output 'MSI file NOT found'
    exit 1
}

# Install with verbose logging
Write-Output 'Installing ODBC Driver 18 with logging...'
$logFile = 'C:\Temp\odbc_install.log'
$exitCode = Start-Process msiexec.exe -ArgumentList "/i `"$msiPath`" /qn /log `"$logFile`" /norestart" -Wait -NoNewWindow -PassThru | Select-Object -ExpandProperty ExitCode

Write-Output "Install exit code: $exitCode"

# Also try the direct msiexec approach
Write-Output 'Trying direct install...'
$exitCode2 = msiexec.exe /i "$msiPath" /quiet /log "C:\Temp\odbc_install2.log" /norestart
Write-Output "Direct install exit code: $exitCode2"

# Check registry again
$key = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server'
if (Test-Path $key) {
    Write-Output 'SUCCESS: ODBC Driver 18 is now installed!'
} else {
    Write-Output 'FAILED: ODBC Driver 18 still not in registry'
    Write-Output 'Checking log for errors...'
    if (Test-Path $logFile) {
        $lines = Get-Content $logFile -Tail 50
        $lines | Where-Object { $_ -match 'error|fail|cost|return value' } | ForEach-Object { Write-Output $_ }
    }
}
'''

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Installing ODBC Driver 18 with verbose logging...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()