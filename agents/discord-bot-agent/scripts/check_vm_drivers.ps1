# Check ODBC drivers
$drivers = [System.Data.Odbc.OdbcDriver]::InstalledDrivers()
Write-Output "ODBC Drivers:"
$drivers.GetEnumerator() | ForEach-Object { Write-Output "  $($_.Key) = $($_.Value)" }

# Check if SqlClient is available
try {
    $t = [System.Data.SqlClient.SqlConnection]
    Write-Output 'System.Data.SqlClient is available'
} catch {
    Write-Output 'System.Data.SqlClient NOT available'
}
try {
    $t = [Microsoft.Data.SqlClient.SqlConnection]
    Write-Output 'Microsoft.Data.SqlClient is available'
} catch {
    Write-Output 'Microsoft.Data.SqlClient NOT available'
}

# Check installed Python packages
Write-Output ""
Write-Output "Python packages:"
py -m pip list 2>&1 | Select-String -Pattern "pyodbc|azure|sqlclient|tds"