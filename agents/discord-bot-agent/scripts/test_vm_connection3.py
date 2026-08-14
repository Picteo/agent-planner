#!/usr/bin/env python3
"""Test Azure SQL connection from VM using pypyodbc with legacy SQL Server driver. Uses base64 to avoid escaping."""
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

# Base64 encoded Python test script
encoded_script = "aW1wb3J0IHN5cwp0cnk6CiAgICBpbXBvcnQgcHlweW9kYmMgYXMgcHlvZGJjCiAgICBwcmludCgncHlweW9kYmMgdmVyc2lvbjogJyArIHB5b2RiYy52ZXJzaW9uKQpleGNlcHQgSW1wb3J0RXJyb3IgYXMgZToKICAgIHByaW50KCdweXB5b2RiYyBpbXBvcnQgZmFpbGVkOiAnICsgc3RyKGUpKQogICAgc3lzLmV4aXQoMSkKCnNlcnZlciA9ICdkaXNjb3JkY29jLmRhdGFiYXNlLndpbmRvd3MubmV0JwpkYXRhYmFzZSA9ICdkaXNjb3JkY29jJwp1c2VybmFtZSA9ICd0d2FuJwpwYXNzd29yZCA9ICdTdW5zaCcgKyBjaHIoMzMpICsgJ24zMCcgKyBjaHIoMzMpCgpwcmludCgnVGVzdGluZyBBenVyZSBTUUwgY29ubmVjdGlvbi4uLicpCnByaW50KCdTZXJ2ZXI6ICcgKyBzZXJ2ZXIpCnByaW50KCdEYXRhYmFzZTogJyArIGRhdGFiYXNlKQoKdHJ5OgogICAgY29ubl9zdHIgPSAoJ0RSSVZFUj17U1FMIFNlcnZlcn07U0VSVkVSPScgKyBzZXJ2ZXIgKyAnO0RBVEFCQVNFPScgKyBkYXRhYmFzZSArICc7VUlEPScgKyB1c2VybmFtZSArICc7UFdEPScgKyBwYXNzd29yZCArICc7RW5jcnlwdD15ZXM7Q29ubmVjdGlvblRpbWVvdXQ9MzA7JykKICAgIHByaW50KCdUcnlpbmcgbGVnYWN5IFNRTCBTZXJ2ZXIgZHJpdmVyLi4uJykKICAgIGNvbm4gPSBweW9kYmMuY29ubmVjdChjb25uX3N0cikKICAgIHByaW50KCdTVUNDRVNTIHdpdGggbGVnYWN5IFNRTCBTZXJ2ZXIgZHJpdmVyIScpCiAgICBjdXJzb3IgPSBjb25uLmN1cnNvcigpCiAgICBjdXJzb3IuZXhlY3V0ZSgnU0VMRUNUIEBAVkVSU0lPTicpCiAgICB2ZXJzaW9uID0gY3Vyc29yLmZldGNob25lKCkKICAgIHByaW50KCdTZXJ2ZXIgdmVyc2lvbjogJyArIHN0cih2ZXJzaW9uWzBdKVs6MTAwXSkKICAgIGN1cnNvci5jbG9zZSgpCiAgICBjb25uLmNsb3NlKCkKZXhjZXB0IHB5b2RiYy5FcnJvciBhcyBlOgogICAgcHJpbnQoJ0xlZ2FjeSBkcml2ZXIgZmFpbGVkOiAnICsgc3RyKGUpKQpleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICBwcmludCgnVW5leHBlY3RlZCBlcnJvcjogJyArIHR5cGUoZSkuX19uYW1lX18gKyAnOiAnICsgc3RyKGUpKQo="

ps_script = f"""
$bytes = [Convert]::FromBase64String('{encoded_script}')
$script = [System.Text.Encoding]::UTF8.GetString($bytes)
[System.IO.File]::WriteAllText('C:\\Temp\\test_connection.py', $script, [System.Text.Encoding]::UTF8)
Write-Output 'Python script written to C:\\Temp\\test_connection.py'
Write-Output 'Running connection test...'
py C:\\Temp\\test_connection.py 2>&1
"""

with RunspacePool(wsman) as rs:
    ps = PowerShell(rs)
    ps.add_script(ps_script)
    print("Testing Azure SQL connection from VM (base64 approach)...")
    ps.invoke()
    for item in ps.output:
        print(item)
    for err in ps.streams.error:
        print(f"[ERROR] {err}")

wsman.close()