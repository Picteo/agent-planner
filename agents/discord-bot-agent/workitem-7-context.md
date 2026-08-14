# Work Item #7: Implement Discord bot framework with Supercell API integration

## State
**Current State:** To Do

## Azure DevOps
- **Project:** DiscordCoC
- **Type:** Task
- **Parent:** Work Item #4 (Epic: DiscordCoC — Clash of Clans Clan Discord Server & Bot)
- **URL:** https://dev.azure.com/Picteo/_workitems/edit/7

## Summary
Create the Discord bot framework with Supercell API client for querying clan and player data.

## Motivation
The bot needs a foundation framework that connects to Discord and the Supercell API to fetch clan member data, war data, raid data, and Clan Games data.

## Requirements

### Bot Framework
- Use discord.py (or similar Python framework) for Discord bot
- Bot token stored as environment variable
- Connect to Discord gateway
- Handle bot events (on_ready, on_member_join)
- Health check endpoint

### Supercell API Client
- Create API client with rate limiting (max 5 requests per second per Supercell ID)
- API key stored as environment variable
- Endpoints to implement:
  - GET /v1/clans?tag={clanTag} — get clan details and members
  - GET /v1/clans/{clanId}/warstates — get current/past war states (CWL)
  - GET /v1/clans/{clanId}/cwallstates — get CWL history
  - GET /v1/clans/{clanId}/raidstates — get raid states
  - GET /v1/clans/{clanId}/clanGames?seasonId={seasonId} — get Clan Games data
  - GET /v1/players/{playerTag} — get player details

### Configuration
- Clan tag: AliceIsBored (configurable)
- API region (default: eu)
- Database connection string

## Acceptance Criteria
- [ ] Bot starts and connects to Discord successfully
- [ ] Bot responds to ping command
- [ ] Supercell API client can fetch clan info by clan tag
- [ ] Supercell API client handles rate limiting correctly
- [ ] API key and bot token are stored securely (env vars)
- [ ] Bot logs API requests and responses (debug level)
- [ ] Code is in repository with README for setup