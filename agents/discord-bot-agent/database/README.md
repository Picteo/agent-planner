# SQL Schema Application for Azure SQL Database

## Overview
This directory contains the SQL schema for the DiscordCoC database. The schema defines the data model for managing Discord user profiles, clan information, and bot interactions.

## Schema Files
- `schema.sql` - Complete DDL including tables, indexes, views, and stored procedures

## Tables Created
1. `discord_user` - Discord user profile with guild, clan, and role mappings
2. `clan` - Clan information linked to Supercell API
3. `clan_member` - Clan membership with role, status, and join tracking
4. `bot_interaction` - Bot command audit log with usage metrics

## Authentication Methods

### Method 1: Via Azure Arc SQL Tools (Recommended - Windows Server)

The recommended way to apply the schema is from the Azure Arc-enabled server **WIN-2HBN30ECLV2** where Azure Arc SQL tools are already configured.

```powershell
# On the Arc-enabled Windows server (WIN-2HBN30ECLV2)

# 1. Clone or copy the project to the server
# 2. Install Python dependencies
pip install pyodbc azure-identity

# 3. Apply the schema using Azure Arc SQL tools connection string
$connection_string = arc sql db connect --database discordcoc --server "picteoinst1.database.windows.net" --print-odbc-connection-string
# Use the output connection string to set AZURE_SQL_SERVER

# Or directly use the Arc-enabled server name
$env:AZURE_SQL_SERVER = "WIN-2HBN30ECLV2.arc-dcc5e.9a6f-pd005016.centralus.arcsynapses.net"
$env:AZURE_SQL_DATABASE = "discordcoc"
python apply_schema.py
```

### Method 2: Via Azure AD Access Token (Linux/macOS)

```bash
# 1. Install dependencies
pip install pyodbc azure-identity

# 2. Acquire Azure AD token for SQL Database
TOKEN=$(az account get-access-token --resource-type "Microsoft SQL" --resource "https://database.windows.net" --query accessToken -o tsv)

# 3. Set environment variable
export AZURE_SQL_ACCESS_TOKEN="$TOKEN"
export AZURE_SQL_SERVER="picteoinst1.database.windows.net"
export AZURE_SQL_DATABASE="discordcoc"

# 4. Apply the schema
python apply_schema.py
```

### Method 3: Via Azure CLI (Quick Test)

```bash
# Test connectivity first
az sql db show --name discordcoc --resource-group <your-resource-group> --server picteoinst1

# Use sql-mgmt tool if installed
az sql db sql-script execute --file database/schema.sql --path discordcoc --server picteoinst1
```

## Troubleshooting

### "Login failed for user ''" with AccessToken
This indicates the ODBC driver isn't parsing the AccessToken connection string parameter. Solutions:
1. Use pyodbc >= 4.0.39 with ODBC Driver 17+
2. Try setting AccessToken via connection handle: `conn.set_attr(1256, token)`
3. Use Method 1 (Arc-enabled server) which uses Integrated Security

### "Azure Arc SQL tools not found"
Install Azure Arc SQL tools on the Windows server:
```powershell
az extension add --name azure-arc-sql-mgmt
az extension add --name sql-mgmt
```

### Permission Denied
Ensure your Azure identity has `db_owner` or `db_ddladmin` role on the `discordcoc` database:
```sql
-- In the master database
CREATE USER [your-identity] FROM EXTERNAL PROVIDER;
ALTER ROLE db_ddladmin ADD MEMBER [your-identity];

-- In the discordcoc database
CREATE USER [your-identity] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [your-identity];
```

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_SQL_SERVER` | `picteoinst1.database.windows.net` | Azure SQL Server hostname |
| `AZURE_SQL_DATABASE` | `discordcoc` | Target database name |
| `AZURE_SQL_ACCESS_TOKEN` | (none) | Azure AD Access Token |
| `SCHEMA_FILE` | `database/schema.sql` | Path to schema file |