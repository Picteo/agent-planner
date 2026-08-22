# DiscordCoC - Clash of Clans Clan Discord Bot

Discord bot for the AliceIsBored Clan with Supercell API integration.

## Getting Your Discord Bot Token

### Step 1: Create a Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** in the top right
3. Give it a name (e.g., "AliceIsBored Bot") and click **Create**

### Step 2: Create the Bot
1. In your application, click **"Bot"** in the left sidebar
2. Click **"Add Bot"** if shown (confirm by clicking "Yes, do it!")
3. Under **"PRESENCE INTENT"** and **"SERVER MEMBERS INTENT"**, toggle both **ON**
   - These are required for the bot to see servers and members

### Step 3: Get the Token
1. On the Bot page, click **"Reset Token"** (or "Copy" if already has one)
2. Copy the token — it starts with `MT` (e.g., `MTIzNDU2Nzg5...`)
3. **Keep this token secret!** Anyone with your token can control your bot

### Step 4: Invite the Bot to Your Server
1. Go to **"OAuth2" → "URL Generator"** in the left sidebar
2. Under **"SCOPES"**, select **"bot"**
3. Under **"BOT PERMISSIONS"**, select:
   - `Send Messages`
   - `Read Message History`
   - `Embed Links`
   - `Use Slash Commands`
4. Copy the generated URL at the bottom
5. Paste the URL in your browser and select your Discord server to invite the bot

## Getting Your Supercell API Key

1. Go to [Supercell Developer Portal](https://developer.supercell.com/retrieve)
2. Enter your email address
3. You'll receive an API key via email
4. The key is rate-limited to 5 requests per second per Supercell ID

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
SUPERCELL_API_KEY=your_supercell_api_key_here
CLAN_TAG=AliceIsBored
REGION=eu
```

**Security Note:** The `.env` file is in `.gitignore` — never commit it.

You can also store tokens in your system keyring:

```bash
# Store Discord token
echo -n "your_token" | secret-tool store --label="Discord Bot Token" service discord application bot username your_username

# Retrieve it later
secret-tool lookup service discord
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Bot

```bash
python src/main.py
```

## Available Commands

### General
- `/ping` — Check bot latency
- `/config` — Show current bot configuration

### Clan & Player Info
- `/clan <tag>` — Display clan info (members, trophies, wars frequency)
- `/player <tag>` — Display player profile (trophies, league, role, donations)

### Data Sync
- `/sync entity:cwl|cw|raid|clan_games [tag:#ClanTag]` — Sync data from Supercell API

### Verification
- `/verify <tag>` — Link your Discord account to a Clash of Clans player tag
- `/unverify` — Remove your Discord-to-Clash verification link
- `/myclan` — Show your clan status and verification details

### Status
- `/status` — Show bot status and database statistics

## Windows VM Deployment

The bot is deployed to a Windows VM (`WIN-2HBN30ECLV2.fritz.box`) at `C:\ClashKing\`.

### VM Setup Details
- **Python:** 3.12.9 at `C:\ClashKing\venv\Scripts\python.exe`
- **Virtual Environment:** `C:\ClashKing\venv\`
- **Environment File:** `C:\ClashKing\.env` (DISCORD_BOT_TOKEN, SUPERCELL_API_KEY)

### Deployment Files
- `C:\ClashKing\src\` — Bot source files (main.py, api_client.py, config.py)
- `C:\ClashKing\run_bot.py` — Bootstrap script that starts the bot via asyncio
- `C:\ClashKing\launch_bot.bat` — Windows scheduled task entry point
- `C:\ClashKing\.env` — Environment variables with tokens
- `C:\ClashKing\restart_bot.bat` — Monitor script that checks/restarts bot
- `C:\ClashKing\logs\` — Log directory

### Windows Scheduled Tasks

**Bot Task: `AliceIsBored Bot`**
- Runs `C:\ClashKing\launch_bot.bat` at logon (Interactive session)
- Status: Running (PID visible in `tasklist`)

**Monitor Task: `AliceIsBored Bot Monitor`**
- Runs `C:\ClashKing\restart_bot.bat` every 15 minutes
- Checks if bot process exists; restarts if not found
- Runs as Administrator with highest privileges

### Log Files
- `C:\ClashKing\logs\bot_wrapper.log` — Bot startup, imports, connection logs
- `C:\ClashKing\logs\bot_stdout.log` — Bot stdout output (Discord events)
- `C:\ClashKing\logs\bot_launch.log` — Launch task execution log
- `C:\ClashKing\logs\restart_monitor.log` — Monitor restart checks

### Running the Bot on VM
- **Managed by scheduled tasks** — No manual intervention needed
- **Auto-start on reboot:** Bot task runs at Windows logon
- **Auto-restart:** Monitor checks every 15 minutes and restarts if needed

### Updating Files on VM
Use the deployment Python script via WinRM:
```bash
./deploy_to_vm.py [--target=prod]
```
Or deploy manually via RDP/file share.

### Troubleshooting VM
```cmd
REM Check bot status
tasklist /FI "IMAGENAME eq python.exe"

REM Check scheduled tasks
schtasks /query /tn "AliceIsBored Bot" /v
schtasks /query /tn "AliceIsBored Bot Monitor" /v

REM Manually start bot task
schtasks /run /tn "AliceIsBored Bot"

REM Manually run monitor
schtasks /run /tn "AliceIsBored Bot Monitor"

REM View logs (PowerShell/CMD)
type C:\ClashKing\logs\bot_wrapper.log
type C:\ClashKing\logs\restart_monitor.log
```

## Project Structure

```
src/
├── main.py              # Bot entry point with slash commands
├── api_client.py        # Supercell API client with rate limiting
├── config.py            # Configuration (clan tag, API key, region)
├── database.py          # SQLAlchemy ORM models & session management
├── cwl_service.py       # CWL sync service
├── cw_service.py        # Clan War sync service
├── raid_service.py      # Raid/Challenge sync service
├── clan_games_service.py # Clan Games sync service
├── verification_service.py # Discord verification & role mapping
└── __init__.py          # Package init
```

## Architecture

```
launch_bot.bat
    └── run_bot.py (asyncio.run(main()))
            └── AliceIsBoredBot(commands.Bot)
                    ├── Slash commands: /ping, /clan, /player, /config
                    ├── /sync (entity: cwl, cw, raid, clan_games)
                    ├── /verify, /unverify, /myclan
                    ├── /status
                    ├── SupercellAPIClient (aiohttp session)
                    ├── CwlService, CwService, RaidService, ClanGamesService
                    ├── VerificationService
                    └── BotConfig (.env + environment variables)
```

## Rate Limiting

- Supercell API allows max 5 requests per second per Supercell ID
- The API client implements automatic rate limiting with delays
- Rate limit errors are handled gracefully with retry delays

## Development

### Running Locally
```bash
# Create virtual environment
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your tokens

# Run the bot
python src/main.py
```

### Testing Commands
After the bot connects, test in your Discord server:
- `/ping` — Bot responds with latency
- `/clan #AliceIsBored` — Fetch clan info from Supercell API
- `/player #PlayerTag` — Fetch player profile

## Security

- **Never commit `.env` files or token values**
- `.env` is in `.gitignore`
- On production VM, `.env` is stored at `C:\ClashKing\.env`
- When referencing tokens in logs/chat, always mask them (e.g., `MT****`)