# Product Requirements Document — DiscordCoC

**Project**: DiscordCoC  
**Clan**: AliceIsBored (Clash of Clans)  
**Version**: 1.0  
**Date**: 2026-07-18  
**Status**: Draft for Review

---

## 1. Product Vision

DiscordCoC is a Discord server setup and management system for the Clash of Clans clan **"AliceIsBored"**. The primary product is a well-configured Discord server with an integrated bot that tracks clan member participation and contribution across multiple game events (CWL, CW, Weekend Raids, Clan Games). Data is persisted in Azure SQL for long-term analysis.

**Target Users:**
- Clan Leaders/Co-Leaders (admin access, view all analytics)
- Clan Members (read access, personal stats)

---

## 2. Scope

### In Scope (MVP)
- Discord server setup with minimal channels and roles
- Discord bot that queries Supercell API
- Azure SQL database for data persistence
- Participation tracking for 4 event types: CWL, CW, Weekend Raids, Clan Games
- Member contribution scoring and reporting
- Commands for querying stored data

### Out of Scope (Future)
- Music bot or entertainment bots
- Complex custom emojis or server branding
- Multi-clan support (single clan focus)
- Mobile app or web dashboard (Discord commands only)

---

## 3. Discord Server Setup

### 3.1 Channels

| Category | Channel Name | Type | Purpose |
|----------|-------------|------|---------|
| 📋 Information | #announcements | Text | Leader announcements |
| 💬 General | #general | Text | Main clan chat |
| ⚔️ Warfare | #war-chat | Text | War coordination |

### 3.2 Roles

| Role | Permissions | Assignment |
|------|------------|------------|
| Leader | Full admin | Manual |
| Member | Read channels, send messages | Auto (verified via Supercell API clan membership) |
| Unverified | Limited access | Default (before verification) |

### 3.3 Verification Flow
- New members join → assigned "Unverified" role
- Bot checks Supercell API for clan membership
- If found in clan → assigned "Member" role
- If not found → remains "Unverified" (limited access)

---

## 4. Bot Requirements

### 4.1 Data Source
- **Supercell API** (requires API token)
- Bot queries API on command trigger or scheduled interval

### 4.2 Commands (MVP)

| Command | Description |
|---------|-------------|
| `!verify` | Check clan membership and assign role |
| `!cwl-stats` | Display CWL participation data |
| `!cw-stats` | Display CW participation data |
| `!raid-stats` | Display Weekend Raid participation data |
| `!cg-stats` | Display Clan Games participation data |
| `!contribution` | Display overall member contribution score |

### 4.3 Data Storage
- **Azure SQL Database**
- Separate tables for each event type
- Historical data preserved for trend analysis

---

## 5. Event Tracking Specifications

### 5.1 Clan War League (CWL)

**Per CWL Event:**
- League name and division
- Start/end dates

**Per Player Per Day:**
- Participated (yes/no)
- Number of attacks
- Attack targets (adversary player number)
- War count comparison with attacked adversary
- Stars collected
- Damage percentage

**Per Player Per Event:**
- Total days participated
- Total attacks across all days
- Total stars collected
- Rewards earned
- Bonuses assigned (from Co-Leaders)

### 5.2 Clan War (CW)

**Per CW Event:**
- League name
- Start/end dates
- Number of attack days (2 per day)

**Per Player Per Event:**
- Number of attacks used (out of available)
- Attack targets (adversary player number)
- War count comparison with attacked adversary
- Total stars collected

*Note: Rewards are NOT tracked for CW (less important).*

### 5.3 Weekend Raids

**Per Raid Event:**
- Event name and dates

**Per Player Per Event:**
- Number of attacks used
- Total points reached

### 5.4 Clan Games

**Per Clan Games Event:**
- Event name and dates

**Per Player Per Event:**
- Points contributed
- Milestone reached (4000 points / 10000 points)

---

## 6. Contribution Scoring

An overall member contribution score calculated from all event types. This enables leaders to identify:
- Most active/valuable members
- Members needing engagement
- Participation trends over time

**Scoring Formula (TBD in design phase):**
- CWL participation: weighted highest (competitive)
- CW participation: weighted high
- Weekend Raids: weighted medium
- Clan Games: weighted medium

---

## 7. Technical Requirements

### 7.1 Technology Stack (TBD)
- Bot framework: To be determined during task creation
- Database: Azure SQL
- API: Supercell API

### 7.2 Security
- Supercell API token stored securely (environment variables / Azure Key Vault)
- Database access restricted to bot service identity

### 7.3 Deployment
- Bot runs in a containerized environment
- Scheduled tasks for periodic data sync

---

## 8. Success Criteria

1. ✅ Discord server configured with channels and roles
2. ✅ Bot verifies clan membership via Supercell API
3. ✅ Bot stores CWL, CW, Raid, and Clan Games data
4. ✅ Commands return accurate participation data
5. ✅ Contribution scores accurately reflect member activity
6. ✅ Historical data preserved for trend analysis

---

## 9. Assumptions

- Supercell API token is available
- Azure SQL database can be provisioned
- Clan "AliceIsBored" has a public Supercell tag for API lookup
- Current members have Supercell accounts linked to the clan