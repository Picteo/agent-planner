# COC Discord Bot Comparison Research

## Overview

This document compares three public open-source Clash of Clans Discord bots to help determine the best fork candidate for the AliceIsBored custom bot.

---

## 1. ClashKingBot (ClashKingInc/ClashKingBot) ⭐ RECOMMENDED

| Attribute | Details |
|-----------|---------|
| **URL** | https://github.com/ClashKingInc/ClashKingBot |
| **License** | MIT |
| **Language** | Python |
| **Stars** | 70 |
| **Forks** | 26 |
| **Last Push** | July 2026 (active) |
| **Website** | https://clashk.ing |

### Directory Structure
```
.github/workflows/
assets/
background/         # Background tasks, schedulers, war timers
classes/           # Data models, clan models, player models
commands/          # Command modules (CWL, wars, events, player info)
discord/           # Discord integration, event handlers, bot core
exceptions/        # Custom exceptions
```

### Key Features
- **CWL Tracking**: Full Clan War League tracking with history and predictions
- **War Logs**: Real-time war tracking with attack progress
- **Clan Capital**: Capital raids tracking
- **Player Stats**: Player profiles, seasons, donations, attacks
- **Auto-Role**: Role assignment based on clan activity, donations
- **Dashboard**: Web dashboard integration
- **Multi-Clan Support**: Track multiple clans in one server
- **Notifications**: War reminders, CWL start/end alerts
- **Roster Management**: Track clan members and their contributions
- **API Integration**: Uses Supercell API (Clash of Clans API)

### Why It's Recommended
1. **Python + discord.py** - Same stack as planned AliceIsBored bot
2. **MIT License** - Fully permissive for commercial/custom use
3. **Most feature-complete** - 70 stars, 26 forks, active development
4. **Clan-centric** - Built specifically for clan management, not player stats
5. **Large community** - Established user base and community
6. **Active development** - Last push July 2026

### Forkability
- **High** - Well-structured modular code
- Clean separation of commands, classes, and background tasks
- MIT license allows forking and customization
- Large community means good documentation

---

## 2. ClashPerk (clashperk/clashperk)

| Attribute | Details |
|-----------|---------|
| **URL** | https://github.com/clashperk/clashperk |
| **License** | MIT |
| **Language** | TypeScript (discord.js v14) |
| **Stars** | 26 |
| **Forks** | 10 |
| **Last Push** | July 2026 (active) |

### Directory Structure
```
.claude/skills/
.github/
.vscode/
docs/
locales/          # 32+ language translations (git submodule)
scripts/
src/             # Main bot source code
```

### Key Features
- **Clan Management**: CWL, Clan Games, Capital Raids tracking
- **Player Tracking**: Player stats, ranks, seasons, attacks
- **Legend League**: Legend attacks tracking
- **Roster System**: Player roster CRUD
- **Auto-Role**: Automated role assignment
- **Tickets**: Built-in support ticket system
- **Multi-language**: 32+ translations
- **AI Integration**: AI-SDK for enhanced features
- **Leaderboards**: Global and server-specific
- **Custom Commands**: Alias system
- **Logging**: Clan logs, war logs, donation logs, capital logs

### Considerations
- **TypeScript/d discord.js** - Different stack than planned Python bot
- Requires Node.js runtime instead of Python
- More modern architecture but harder to port to Python

---

## 3. ClashBaseDeveloper (rutger901/clashbasedeveloper)

| Attribute | Details |
|-----------|---------|
| **URL** | https://github.com/rutger901/clashbasedeveloper |
| **License** | MIT |
| **Language** | Python (discord.py v2+) |
| **Stars** | 0 |
| **Forks** | 0 |
| **Last Push** | Last year (less active) |

### Directory Structure
```
.cogs/           # Cog-based modular commands
.commands/       # Command modules
.events/         # Discord event handlers
.utils/          # Utility functions
```

### Key Features
- **Onboarding System**: Multi-step role-based onboarding
- **Base Tracking**: Custom base sharing/tracking
- **Supabase Integration**: Database layer via Supabase
- **Emoji-based UI**: Custom emojis with Discord UI components
- **Role Management**: Auto role assignment by Town Hall level
- **ArmyLink**: Add/remove army link functionality
- **Rate Limiting**: Built-in rate limiting

### Considerations
- **Small codebase** - Less comprehensive than ClashKingBot
- **No active community** - 0 stars, 0 forks
- **Less tested** - Not battle-tested in production
- **Supabase dependency** - Tight coupling to Supabase

---

## Comparison Matrix

| Feature | ClashKingBot | ClashPerk | ClashBaseDev |
|---------|-------------|-----------|-------------|
| **Language** | Python | TypeScript | Python |
| **Framework** | discord.py | discord.js v14 | discord.py v2+ |
| **License** | MIT | MIT | MIT |
| **Stars/Forks** | 70/26 | 26/10 | 0/0 |
| **CWL Tracking** | ✅ Full | ✅ Full | ❌ Partial |
| **War Logs** | ✅ Real-time | ✅ Real-time | ❌ |
| **Clan Capital** | ✅ | ✅ | ❌ |
| **Clan Games** | ✅ | ✅ | ❌ |
| **Player Stats** | ✅ | ✅ | ✅ |
| **Base Sharing** | ❌ | ❌ | ✅ |
| **Auto-Role** | ✅ | ✅ | ✅ |
| **Dashboard** | ✅ Web | ❌ | ❌ |
| **Multi-Clan** | ✅ | ❌ | ❌ |
| **AI Integration** | ❌ | ✅ | ❌ |
| **Multi-language** | ❌ | ✅ 32+ | ❌ |
| **Active Dev** | ✅ | ✅ | ❌ |
| **Maturity** | High | Medium | Low |
| **Fork Ease** | High | Medium | High |

---

## Recommendation

### Best Fork Candidate: **ClashKingBot**

**Reasons:**
1. **Same tech stack** (Python + discord.py) - minimal migration needed
2. **MIT License** - fully permissive
3. **Most mature** - 70 stars, 26 forks, established community
4. **Clan-centric features** - exactly what AliceIsBored needs
5. **Active development** - ongoing improvements and bug fixes
6. **Modular architecture** - easy to customize and extend

### Customization Plan for AliceIsBored
Starting from ClashKingBot, we would need to:
1. **Remove**: Player stats-only features, base sharing (not needed)
2. **Add**: Weekend raid tracking, verification system, custom scoring
3. **Modify**: CWL tracking to match AliceIsBored's specific requirements
4. **Brand**: Rebrand from ClashKing to AliceIsBored
5. **Database**: Replace Supabase with chosen database (PostgreSQL/SQLite)

### Alternative Approach
If ClashKingBot doesn't have all needed features:
- **Combine** features from all three bots
- Use ClashKingBot as base (Python, mature)
- Add base sharing concept from ClashBaseDeveloper
- Consider AI features from ClashPerk (if porting to TypeScript)

---

## Next Steps
1. Fork ClashKingInc/ClashKingBot
2. Audit existing code against AliceIsBored requirements
3. Create detailed implementation plan for custom features
4. Set up development environment
5. Begin customizing for AliceIsBored