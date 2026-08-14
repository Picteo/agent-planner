#!/usr/bin/env python3
"""Download the actual full ODBC Driver 18 MSI from GitHub releases."""
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

# The full MSI can be downloaded directly from the GitHub releases page
ps_script = r'''
# Try GitHub releases direct download for the full MSI
# Microsoft ODBC Driver 18 for SQL Server on GitHub
Write-Output 'Trying GitHub releases for full MSI...'

# Full MSI from GitHub releases
$urls = @(
    'https://github.com/microsoft/msodbcsql17/releases/download/v17.10.8.1/msodbcsql-17.10.8.1.msi',
    'https://github.com/microsoft/msodbcsql17/releases/download/v17.10.8.1/msodbcsql-17.10.8.1-x64.msi'
)

$outFile = 'C:\Temp\msodbcsql_full.msi'

foreach ($url in $urls) {
    try {
        Write-Output "Trying: $url"
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add('User-Agent', 'PowerShell')
        $wc.DownloadFile($url, $outFile)
        $size = (Get-Item $outFile).Length
        Write-Output "Downloaded: $size bytes"
        if ($size -gt 50000000) {
            Write-Output 'Full MSI downloaded successfully!'
            break
        } else {
            Write-Output "Too small, trying next URL..."
            Remove-Item $outFile -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Output "Failed: $($_.Exception.Message)"
    }
}

# Alternative: Use the SQL Server 2022 Shared Feature installer
if (-not (Test-Path $outFile) -or (Get-Item $outFile).Length -lt 50000000) {
    Write-Output 'Trying Azure Data Studio/SQL tools approach...'
    # Get the latest from NuGet package
    $nugetUrl = 'https://www.nuget.org/api/v2/package/Microsoft.SqlServer.SqlManagementObjects'
    Write-Output "Trying NuGet: $nugetUrl"
}

# Also try the direct CDN URL from Microsoft's download center
if (-not (Test-Path $outFile) -or (Get-Item $outFile).Length -lt 50000000) {
    Write-Output 'Trying direct download URL...'
    $directUrl = 'https://download.microsoft.com/download/7/f/d/7fd23816-c76d-4e06-8d97-5f2795a8a6a0/msodbcsql18.exe'
    try {
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add('User-Agent', 'PowerShell')
        $exeFile = 'C:\Temp\msodbcsql18.exe'
        $wc.DownloadFile($directUrl, $exeFile)
        $size = (Get-Item $exeFile).Length
        Write-Output "Downloaded exe: $size bytes"
        
        # Extract the MSI from the self-extracting exe
        if ($size -gt 50000000) {
            Write-Output 'Extracting MSI from self-extracting exe...'
            Start-Process "$exeFile" -ArgumentList "/x `"$outFile`" /quiet" -Wait
            if (Test-Path $outFile) {
                Write-Output "Extracted MSI: $((Get-Item $outFile).Length) bytes"
            }
        }
    } catch {
        Write-Output "Direct URL failed: $($_.Exception.Message)"
    }
}

if (Test-Path $outFile) {
    $size = (Get-Item $outFile).Length
    Write-Output "Final file: $outFile ($size bytes)"
    
    if ($size -gt 50000000) {
        Write-Output 'Installing full ODBC Driver...'
        $logFile = 'C:\Temp\odbc_full_install.log'
        & msiexec.exe /i "$outFile" /quiet /log "$logFile" /norestart
        Write-Output "Exit: $LASTEXITCODE"
        
        Start-Sleep -Seconds 15
        
        $key = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server'
        if (Test-Path $key) {
            Write-Output 'SUCCESS!'
        } else {
            Write-Output 'Checking log...'
            Get-Content $logFile -Tail 30 | ForEach-Object { Write-Output $_ }
        }
    }
}
'''

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Downloading full ODBC Driver from GitHub releases...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()