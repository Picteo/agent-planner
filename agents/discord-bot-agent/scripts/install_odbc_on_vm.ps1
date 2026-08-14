# Download and install ODBC Driver 18 on the Windows VM
Write-Output 'Downloading ODBC Driver 18...'
$url = 'https://go.microsoft.com/fwlink/?linkid=2213075'
$outFile = 'C:\Temp\msodbcsql18.msi'
try {
    Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing -TimeoutSec 120
    Write-Output 'Download complete'
} catch {
    Write-Output "Download failed: $($_.Exception.Message)"
    $url = 'https://aka.ms/odbc18'
    Write-Output "Trying alternate URL: $url"
    Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing -TimeoutSec 120
    Write-Output 'Download complete (alternate URL)'
}

# Install silently
Write-Output 'Installing ODBC Driver 18...'
$installArgs = '/i "C:\Temp\msodbcsql18.msi" /quiet /qn ADDLOCAL=All ACCEPT_SHA=1 EULA_ACCEPT=YES'
& msiexec.exe $installArgs
$exitCode = $LASTEXITCODE
Write-Output "Install exit code: $exitCode"

# Verify installation
Write-Output 'Verifying installation...'
$drivers = [System.Data.Odbc.OdbcDriver]::InstalledDrivers()
Write-Output 'Installed drivers:'
$drivers.GetEnumerator() | ForEach-Object { Write-Output "  $($_.Key) = $($_.Value)" }