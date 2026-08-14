#!/usr/bin/env python3
"""Download and install the FULL ODBC Driver 18 on the VM."""
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

# The direct full MSI download URL (64-bit)
ps_script = r'''
# Remove the small bootstrapper MSI
$msiPath = 'C:\Temp\msodbcsql18.msi'
if (Test-Path $msiPath) {
    $size = (Get-Item $msiPath).Length
    Write-Output "Current MSI size: $size bytes (likely bootstrapper)"
    Remove-Item $msiPath -Force
    Write-Output 'Removed bootstrapper MSI'
}

# Download the FULL ODBC Driver 18 MSI (64-bit, x64)
# Direct URL from Microsoft CDN
Write-Output 'Downloading full ODBC Driver 18 MSI...'
$url = 'https://go.microsoft.com/fwlink/?linkid=2213076&clouddriveGuid=6725c29f-5691-4d29-991-0dde53176fab'
# x64 version has linkid=2213076, x86 has linkid=2213075
# Try the aka.ms redirect which always gives latest
$url2 = 'https://aka.ms/odbc'
$outFile = 'C:\Temp\msodbcsql18_x64.msi'

try {
    Write-Output "Trying URL: $url"
    Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing -TimeoutSec 300
    $size = (Get-Item $outFile).Length
    Write-Output "Downloaded: $size bytes"
    if ($size -gt 10000000) {
        Write-Output 'Looks like full MSI (>10MB)'
    }
} catch {
    Write-Output "First URL failed: $($_.Exception.Message)"
    try {
        Write-Output "Trying URL: $url2"
        Invoke-WebRequest -Uri $url2 -OutFile $outFile -UseBasicParsing -TimeoutSec 300
        $size = (Get-Item $outFile).Length
        Write-Output "Downloaded from aka.ms: $size bytes"
    } catch {
        Write-Output "Second URL also failed: $($_.Exception.Message)"
    }
}

# If download failed or too small, try PowerShell WebClient
if (-not (Test-Path $outFile) -or (Get-Item $outFile).Length -lt 10000000) {
    Write-Output 'WebClient fallback...'
    $wc = New-Object System.Net.WebClient
    try {
        $wc.DownloadFile('https://go.microsoft.com/fwlink/?linkid=2213076', $outFile)
        Write-Output "WebClient downloaded: $((Get-Item $outFile).Length) bytes"
    } catch {
        Write-Output "WebClient failed: $($_.Exception.Message)"
    }
}

if (Test-Path $outFile) {
    $size = (Get-Item $outFile).Length
    Write-Output "Final MSI: $outFile ($size bytes)"
    
    if ($size -gt 10000000) {
        # Install the full MSI
        Write-Output 'Installing ODBC Driver 18...'
        $logFile = 'C:\Temp\odbc_install_full.log'
        & msiexec.exe /i "$outFile" /quiet /log "$logFile" /norestart
        Write-Output "msiexec exit: $LASTEXITCODE"
        
        Start-Sleep -Seconds 10
        
        # Verify
        $key = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server'
        if (Test-Path $key) {
            Write-Output 'SUCCESS: ODBC Driver 18 installed!'
        } else {
            Write-Output 'Install may have failed. Checking log...'
            if (Test-Path $logFile) {
                Get-Content $logFile -Tail 30 | ForEach-Object { Write-Output $_ }
            }
        }
    } else {
        Write-Output 'MSI too small - still a bootstrapper. Need different URL.'
    }
} else {
    Write-Output 'Download failed completely'
}
'''

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Downloading full ODBC Driver 18 MSI...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()