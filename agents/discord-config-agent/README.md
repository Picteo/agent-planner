# Agent Workspace: Discord Config Agent

## Purpose
This workspace is dedicated to the agent executing **Work Item #6** from Azure DevOps.

## Work Item
- **ID:** 6
- **Title:** Configure Discord server channels and roles for AliceIsBored clan
- **State:** Doing
- **Project:** DiscordCoC (Azure DevOps)

## Context
See `workitem-6-context.md` for the complete work item specification including:
- Server configuration details
- Channel structure (13 channels across 4 categories)
- Role hierarchy and permissions (4 roles)
- Bot token setup requirements
- 11 acceptance criteria

## Project Structure
```
discord-config-agent/
├── src/
│   ├── bot.js              # Main Discord bot with commands and verification
│   ├── config.js           # Server configuration (channels, roles, permissions)
│   └── setup-server.js     # Server setup script (creates categories, channels, roles)
├── .env.example            # Environment variable template
├── .gitignore
├── package.json
├── README.md
└── workitem-6-context.md
```

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Bot Token
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Then edit `.env` and add your Discord bot token:
```
DISCORD_TOKEN=your_actual_bot_token_here
```

**How to get a bot token:**
1. Go to https://discord.com/developers/applications
2. Click "New Application" and name it (e.g., "AliceIsBored")
3. Go to the "Bot" section in the left sidebar
4. Click "Reset Token" and copy the token
5. Paste it into your `.env` file

**Important permissions to enable for the bot:**
- Send Messages
- Embed Links
- Manage Roles
- Manage Channels
- Read Message History
- Use Slash Commands

### 3. Invite the Bot to Your Server
Generate an invite URL with the `bot` scope and `Administrator` permission (or at minimum `Manage Roles` and `Manage Channels`):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274877965824&scope=bot
```

Replace `YOUR_CLIENT_ID` with your application's client ID (found in the Application overview page).

### 4. Run Server Setup
This will create all categories, channels, roles, and permission overwrites:

```bash
npm run setup
```

Or directly:
```bash
node src/setup-server.js
```

The setup script will:
1. Configure server settings (name, verification level)
2. Create 4 roles: Unverified, Member, Leader, AliceIsBored
3. Create 4 categories: Information, Clan Activity, Statistics, Bot Commands
4. Create 13 text channels across the categories
5. Create the `#verify` channel with an embed message and verification button
6. Create 2 hidden admin channels: `#admin-log`, `#admin-settings`
7. Display an acceptance criteria checklist for manual verification

### 5. Start the Bot
After setup is complete, start the interactive bot:

```bash
npm start
```

Or directly:
```bash
node src/bot.js
```

## Bot Commands
Once running, the bot responds to these slash commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available bot commands |
| `/status` | Show server and bot status information |
| `/roles` | Show role hierarchy and permissions |

## Verification Flow
New members joining the server will:
1. See only the `#announcements` channel (Unverified role)
2. Go to `#verify` channel
3. Click the "✅ Verify" button in the verification embed
4. Receive the Member role and access to all clan channels

## Server Configuration Summary

### Categories & Channels
| Category | Channels |
|----------|----------|
| 📢 Information | `#announcements`, `#rules` |
| 🎮 Clan Activity | `#general`, `#war-chat`, `#war-updates`, `#raid-chat`, `#raid-updates`, `#clan-games`, `#clan-games-updates`, `#capital-raids`, `#capital-updates` |
| 📊 Statistics | `#leaderboards`, `#scores` |
| 🤖 Bot Commands | `#bot-commands` |
| 🔐 Verification | `#verify` |
| 🔒 Admin (hidden) | `#admin-log`, `#admin-settings` |

### Role Hierarchy
| Role | Access Level |
|------|-------------|
| 👑 @AliceIsBored (Owner) | All permissions, all channels |
| ⚔️ @Leader | All channels + hidden admin channels |
| 🛡️ @Member | 13 public channels |
| ⏳ @Unverified | `#announcements` only |

## Acceptance Criteria
Verify each criterion manually after running setup:

- [ ] Discord server exists with name 'AliceIsBored'
- [ ] Server description set to 'Clash of Clans clan — AliceIsBored'
- [ ] Server icon set (bored Alice illustration)
- [ ] 4 categories created: Information, Clan Activity, Statistics, Bot Commands
- [ ] 13 text channels created across categories
- [ ] 4 roles created with proper hierarchy
- [ ] #announcements visible to all authenticated members
- [ ] #general, #war-chat, #raid-chat, #clan-games hidden from Unverified
- [ ] #admin-log and #admin-settings hidden from Member and Unverified
- [ ] #verify channel has bot verification embed
- [ ] Bot token configured with proper permissions

## Troubleshooting

### "Bot not connected to any guild"
- Make sure the bot is invited to your server (see step 3 above)
- Check that the bot has the `Manage Roles` and `Manage Channels` permissions

### "Failed to create role/channel"
- Ensure the bot has sufficient permissions
- Check that the bot's role is higher in the hierarchy than the roles it's trying to create
- The bot needs `Administrator` or at least `Manage Roles` and `Manage Channels` permissions

### "DISCORD_TOKEN environment variable is required"
- Make sure you created a `.env` file with your bot token
- Verify the token is valid and hasn't been reset in the Discord Developer Portal

## Constraints
- Use Discord.js v14 framework for server configuration
- Bot token must be stored securely (environment variable, never commit to git)
- Follow the exact channel structure and role hierarchy specified in workitem-6-context.md

## Next Steps After Setup
1. Manually verify each acceptance criterion in the Discord server
2. Set the server icon (bored Alice illustration) via Discord client
3. Set the server description via Discord client (Discord API doesn't expose this)
4. Update Azure DevOps work item #6 with completion status
5. Mark all acceptance criteria as complete in Azure DevOps