-- ============================================================
-- DiscordCoC Bot Database Schema
-- Target: Azure SQL Database (SQL Server 2019+)
-- Run with: sqlcmd -S <server> -d <db> -U <user> -i create_schema.sql
-- ============================================================

-- -------------------------------------------------------------------
-- Event tables
-- -------------------------------------------------------------------

CREATE TABLE CwlEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL,
    league_name NVARCHAR(50) NULL,
    division NVARCHAR(50) NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);
GO

CREATE INDEX IX_CwlEvents_clan_tag ON CwlEvents(clan_tag);
GO

CREATE TABLE CwlParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    day_number INT NOT NULL,
    participated BIT NOT NULL CONSTRAINT DF_CwlParticipations_participated DEFAULT 0,
    attacks_used INT NOT NULL CONSTRAINT DF_CwlParticipations_attacks_used DEFAULT 0,
    attack_targets INT NOT NULL CONSTRAINT DF_CwlParticipations_attack_targets DEFAULT 0,
    war_count_comparison INT NOT NULL CONSTRAINT DF_CwlParticipations_wcc DEFAULT 0,
    stars_collected INT NOT NULL CONSTRAINT DF_CwlParticipations_stars DEFAULT 0,
    damage_percentage DECIMAL(5,2) NOT NULL CONSTRAINT DF_CwlParticipations_damage DEFAULT 0.00,
    bonuses_assigned INT NOT NULL CONSTRAINT DF_CwlParticipations_bonuses DEFAULT 0,
    CONSTRAINT FK_CwlParticipations_CwlEvents FOREIGN KEY (event_id) REFERENCES CwlEvents(id)
);
GO

CREATE INDEX IX_CwlParticipations_player_tag ON CwlParticipations(player_tag);
CREATE INDEX IX_CwlParticipations_event_id ON CwlParticipations(event_id);
GO

CREATE TABLE CwEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    attack_days INT NOT NULL CONSTRAINT DF_CwEvents_attack_days DEFAULT 1
);
GO

CREATE INDEX IX_CwEvents_clan_tag ON CwEvents(clan_tag);
GO

CREATE TABLE CwParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    day_number INT NOT NULL,
    attacks_used INT NOT NULL CONSTRAINT DF_CwParticipations_attacks_used DEFAULT 0,
    attack_targets INT NOT NULL CONSTRAINT DF_CwParticipations_attack_targets DEFAULT 0,
    war_count_comparison INT NOT NULL CONSTRAINT DF_CwParticipations_wcc DEFAULT 0,
    stars_collected INT NOT NULL CONSTRAINT DF_CwParticipations_stars DEFAULT 0,
    CONSTRAINT FK_CwParticipations_CwEvents FOREIGN KEY (event_id) REFERENCES CwEvents(id)
);
GO

CREATE INDEX IX_CwParticipations_player_tag ON CwParticipations(player_tag);
CREATE INDEX IX_CwParticipations_event_id ON CwParticipations(event_id);
GO

CREATE TABLE RaidEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);
GO

CREATE TABLE RaidParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    attacks_used INT NOT NULL CONSTRAINT DF_RaidParticipations_attacks_used DEFAULT 0,
    points_reached INT NOT NULL CONSTRAINT DF_RaidParticipations_points DEFAULT 0,
    CONSTRAINT FK_RaidParticipations_RaidEvents FOREIGN KEY (event_id) REFERENCES RaidEvents(id)
);
GO

CREATE INDEX IX_RaidParticipations_player_tag ON RaidParticipations(player_tag);
CREATE INDEX IX_RaidParticipations_event_id ON RaidParticipations(event_id);
GO

CREATE TABLE ClanGamesEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL
);
GO

CREATE TABLE ClanGamesParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    player_tag NVARCHAR(20) NOT NULL,
    points_contributed INT NOT NULL CONSTRAINT DF_ClanGamesParticipations_points DEFAULT 0,
    milestone_reached NVARCHAR(20) NULL,
    CONSTRAINT FK_ClanGamesParticipations_ClanGamesEvents FOREIGN KEY (event_id) REFERENCES ClanGamesEvents(id)
);
GO

CREATE INDEX IX_ClanGamesParticipations_player_tag ON ClanGamesParticipations(player_tag);
CREATE INDEX IX_ClanGamesParticipations_event_id ON ClanGamesParticipations(event_id);
GO

-- -------------------------------------------------------------------
-- Member and scoring tables
-- -------------------------------------------------------------------

CREATE TABLE Members (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL UNIQUE,
    discord_id NVARCHAR(20) NULL,
    role NVARCHAR(20) NOT NULL CONSTRAINT DF_Members_role DEFAULT N'Member',
    verified_at DATETIME2 NOT NULL CONSTRAINT DF_Members_verified_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_Members_updated_at DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX IX_Members_discord_id ON Members(discord_id);
GO

CREATE TABLE ContributionScores (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL,
    event_date DATETIME2 NOT NULL,
    cwl_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cwl DEFAULT 0.00,
    cw_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cw DEFAULT 0.00,
    raid_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_raid DEFAULT 0.00,
    clan_games_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_cg DEFAULT 0.00,
    total_score DECIMAL(10,2) NOT NULL CONSTRAINT DF_ContributionScores_total DEFAULT 0.00
);
GO

CREATE INDEX IX_ContributionScores_player_tag ON ContributionScores(player_tag);
CREATE INDEX IX_ContributionScores_event_date ON ContributionScores(event_date);
GO

-- -------------------------------------------------------------------
-- Summary
-- -------------------------------------------------------------------
PRINT 'All tables and indexes created successfully.'
GO