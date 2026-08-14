# Research: Free Discord Bots for Clash of Clans

This document evaluates freely available Discord bots that could cover the functional requirements
of Work Item #7 before building a custom bot.

## Functional Requirements (from WI #7)

1. Clan member data queries
2. War data (CWL) tracking
3. Raid data (Clan Capital) tracking
4. Clan Games data
5. Player details
6. Scoreboards/leaderboards

---

## Open-Source Bots Available

### 1. ClashKing (ClashKingInc/ClashKingBot)
- **GitHub:** https://github.com/ClashKingInc/ClashKingBot
- **Language:** Python (discord.py)
- **Stars:** 70 | **Forks:** 26 | **Issues:** 40
- **License:** Open Source
- **Description:** "An Open Source Clash Of Clans Discord Bot aiming to cover all possible features & do the heavy lifting so others don't have to."

#### Features (from documentation):
| Feature | Status |
|---------|--------|
| Clan commands & member data | ✅ |
| War & CWL tracking | ✅ |
| Clan Capital (Raid) tracking | ✅ |
| Clan Games | ✅ |
| Player details & stats | ✅ |
| Leaderboards | ✅ |
| Role automation | ✅ |
| Family (multi-clan) commands | ✅ |
| Graphs/Analytics | ✅ |
| Boosted Super Troops | ✅ |
| Ticket system | ✅ |
| Account linking (Discord ↔ Supercell) | ✅ |
| Auto-greeting members | ✅ |
| Ban alerts | ✅ |
| Reminders (war, CWL, inactivity) | ✅ |
| Webhook logging (clan, war, capital, clan games) | ✅ |
| Custom bot branding (name/picture) | ✅ |
| Category-based clan organization | ✅ |

#### Documentation Structure:
- `clan-and-family-commands/` - Clan commands, family commands, war & CWL, leaderboards, graphs
- `clan-setups/` - Add clan, setup clan, log setup
- `player-commands/` - Player details, accounts check
- `server-setups/` - Setup server, reminders, others
- `ticketing/` - Ticket system documentation
- `faq.md` - Frequently asked questions

#### Compatibility with Project:
- **Language:** Python (discord.py) - matches project tech stack
- **API Integration:** Uses Supercell API directly
- **Architecture:** Modular command structure, extensible
- **Setup:** Self-hosted, no external service dependency
- **Customization:** Full control over code

---

### 2. ClashPerk (clashperk/clashperk)
- **GitHub:** https://github.com/clashperk/clashperk
- **Language:** TypeScript
- **Stars:** 26 | **Forks:** 10 | **Issues:** 4
- **License:** Open Source
- **Description:** "Feature-Rich and Powerful Clash of Clans Discord bot with everything you will ever need."

#### Features (from source code analysis):
| Feature | Status |
|---------|--------|
| Clan data & embed logs | ✅ |
| War logging | ✅ |
| CWL tracking | ✅ |
| Clan Capital (Raid) logging | ✅ |
| Clan Games logging | ✅ |
| Player details | ✅ |
| Legend league logging | ✅ |
| Ranked battle logging | ✅ |
| Auto board logging | ✅ |
| Flag alerts | ✅ |
| Last seen tracking | ✅ |
| Ticket system | ✅ |
| Setup commands | ✅ |
| Event setup | ✅ |

#### Source Code Structure:
- `src/commands/` - Command implementations
- `src/core/` - Log handlers (clan-log, clan-war-log, capital-log, clan-games-log, etc.)
- Uses GitBook documentation structure

#### Compatibility with Project:
- **Language:** TypeScript - different from Python stack
- **API Integration:** Uses Supercell API via feeds
- **Setup:** Self-hosted
- **Customization:** Full control, but requires TypeScript knowledge

---

## Previously Evaluated (Closed-Source/Hosted Bots)

### 3. ClashTag (clashtag.app)
- **Website:** https://clashtag.app
- **Free Tier:** Yes (limited)
- **Discord Bot:** Yes
- **Features:** Clan tracking, wars, CWL, raids, Clan Games, player stats, dashboards
- **Coverage:** ✅ All requirements
- **Limitations:** Free tier has limited clan slots, rate limits
- **Verdict:** Strong candidate but not self-hosted

### 4. StatClash (statclash.com)
- **Website:** https://statclash.com
- **Free Tier:** Yes
- **Discord Bot:** Yes
- **Coverage:** ✅ Players, Clan, Wars, CWL | ❌ Raids, Clan Games
- **Verdict:** Good but less comprehensive

---

## Summary Comparison

| Feature | ClashKing (Open Source) | ClashPerk (Open Source) | ClashTag (Hosted) | Custom Bot |
|---------|------------------------|------------------------|-------------------|------------|
| Clan member data | ✅ | ✅ | ✅ | ✅ |
| War/CWL tracking | ✅ | ✅ | ✅ | ✅ |
| Raid/Capital tracking | ✅ | ✅ | ✅ | ✅ |
| Clan Games | ✅ | ✅ | ✅ | ✅ |
| Player details | ✅ | ✅ | ✅ | ✅ |
| Leaderboards | ✅ | ✅ | ✅ | ❌ (not in WI#7) |
| Discord integration | ✅ | ✅ | ✅ | ✅ |
| Self-hosted | ✅ | ✅ | ❌ | ✅ |
| Language match (Python) | ✅ | ❌ (TypeScript) | N/A | ✅ |
| Free tier limits | None | None | Yes | None |
| Customization | Full | Full | Low | Full |
| Setup effort | Medium | Medium | Low | Medium |
| External dependency | None | None | Yes (ClashTag API) | None |

---

## Recommendation

**ClashKing (ClashKingInc/ClashKingBot) is the best option** for this project:

### Why ClashKing?
1. **Language Match:** Built with Python + discord.py - exactly the project's tech stack
2. **Complete Feature Coverage:** Covers ALL requirements from WI #7 (clan data, wars, CWL, raids, Clan Games, player details)
3. **Open Source & Self-Hosted:** No external service dependency, no rate limits, no free tier restrictions
4. **Modular Architecture:** Well-organized command structure that can be used as a reference or starting point
5. **Active Community:** 70 stars, 26 forks, regular updates
6. **Comprehensive Documentation:** GitBook-style docs with detailed setup guides

### Comparison with Building from Scratch:
| Aspect | ClashKing as Base | Custom Bot from Scratch |
|--------|-------------------|------------------------|
| Development time | Weeks (adaptation) | Months (full implementation) |
| Feature coverage | Complete | Partial (WI #7 only) |
| Maintenance | Can fork and maintain | Full responsibility |
| Learning value | Study existing patterns | Learn from scratch |
| Alignment with WI #7 | Can be adapted | Perfect fit |

### Recommended Approach:
1. **Evaluate ClashKing** by forking and running locally
2. **Test** if it meets AliceIsBored clan needs
3. **Adapt** the codebase if it fits (Python/discord.py makes this easier)
4. **Fall back to custom implementation** if ClashKing doesn't meet specific requirements

### Next Steps:
1. Fork ClashKingInc/ClashKingBot
2. Set up local development environment
3. Test with Supercell API (free developer key)
4. Evaluate feature coverage against WI #7 requirements
5. Decide: adapt ClashKing or build custom bot