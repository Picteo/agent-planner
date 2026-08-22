-- =====================================================
-- AliceIsBored Discord Bot - Database Schema
-- Database: discordcoc
-- Server: picteoinst1.database.windows.net
-- Purpose: Store clan data, player data, and Discord mappings
-- =====================================================

-- 1. Clan table - stores clan information
CREATE TABLE dbo.clan (
    clan_id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL UNIQUE,
    clan_name NVARCHAR(100) NOT NULL,
    clan_level INT DEFAULT 0,
    trophies INT DEFAULT 0,
    war_frequency NVARCHAR(50) DEFAULT 'Unknown',
    war_stage_frequency NVARCHAR(50) DEFAULT 'Unknown',
    required_trophies INT DEFAULT 0,
    clan_points INT DEFAULT 0,
    clan_point_victories INT DEFAULT 0,
    region_name NVARCHAR(50) DEFAULT 'Unknown',
    description NVARCHAR(500) DEFAULT '',
    last_synced DATETIME2 DEFAULT SYSUTCDATETIME(),
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- 2. Player table - stores player details
CREATE TABLE dbo.player (
    player_id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL UNIQUE,
    player_name NVARCHAR(100) NOT NULL,
    trophies INT DEFAULT 0,
    attack_wins INT DEFAULT 0,
    role NVARCHAR(20) DEFAULT 'Member',
    donations INT DEFAULT 0,
    donations_received INT DEFAULT 0,
    war_days INT DEFAULT 0,
    exp_level INT DEFAULT 0,
    league_id INT DEFAULT 0,
    league_name NVARCHAR(50) DEFAULT 'Unranked',
    flood_protection_until DATETIME2 DEFAULT NULL,
    clan_id INT NULL REFERENCES dbo.clan(clan_id),
    last_synced DATETIME2 DEFAULT SYSUTCDATETIME(),
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- 3. Clan member table - stores clan membership
CREATE TABLE dbo.clan_member (
    member_id INT IDENTITY(1,1) PRIMARY KEY,
    player_id INT NOT NULL REFERENCES dbo.player(player_id),
    clan_id INT NOT NULL REFERENCES dbo.clan(clan_id),
    role NVARCHAR(20) DEFAULT 'Member',
    donations INT DEFAULT 0,
    donations_received INT DEFAULT 0,
    trophies INT DEFAULT 0,
    joined_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    last_synced DATETIME2 DEFAULT SYSUTCDATETIME(),
    UNIQUE (player_id, clan_id)
);
GO

-- 4. Discord user table - maps Discord users to clan players
CREATE TABLE dbo.discord_user (
    discord_user_id BIGINT PRIMARY KEY,  -- Discord user ID
    discord_username NVARCHAR(100) NOT NULL,
    discord_discriminator NVARCHAR(10) DEFAULT '0000',  -- For legacy bot display names
    discord_global_name NVARCHAR(100) NULL,
    player_id INT NULL REFERENCES dbo.player(player_id),
    clan_tag NVARCHAR(20) NULL,  -- User's preferred clan tag
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- 5. Clan war table - stores Clan War League data
CREATE TABLE dbo.clan_war (
    war_id INT IDENTITY(1,1) PRIMARY KEY,
    clan_id INT NOT NULL REFERENCES dbo.clan(clan_id),
    season_id NVARCHAR(50) NOT NULL,
    season_name NVARCHAR(100) NULL,
    war_state NVARCHAR(20) DEFAULT 'prepared',  -- prepared, fighting, results
    clan_placement INT NULL,
    clan_wins INT DEFAULT 0,
    clan_losses INT DEFAULT 0,
    clan_draws INT DEFAULT 0,
    clan_medals_earned INT DEFAULT 0,
    war_members NVARCHAR(MAX) NULL,  -- JSON array of member war data
    started_at DATETIME2 NULL,
    ended_at DATETIME2 NULL,
    synced_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    UNIQUE (clan_id, season_id)
);
GO

-- 6. Player clan history - tracks member changes over time
CREATE TABLE dbo.player_clan_history (
    history_id INT IDENTITY(1,1) PRIMARY KEY,
    player_id INT NOT NULL REFERENCES dbo.player(player_id),
    clan_id INT NOT NULL REFERENCES dbo.clan(clan_id),
    previous_role NVARCHAR(20) NULL,
    new_role NVARCHAR(20) NOT NULL,
    action NVARCHAR(20) NOT NULL,  -- joined, left, promoted, kicked, demoted
    recorded_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- =====================================================
-- Indexes for performance
-- =====================================================

-- Indexes on clan_tag for quick clan lookups
CREATE INDEX IX_clan_tag ON dbo.clan(clan_tag);
GO

-- Indexes on player_tag for quick player lookups
CREATE INDEX IX_player_tag ON dbo.player(player_tag);
GO

-- Index on discord_user for Discord user lookups
CREATE INDEX IX_discord_user_id ON dbo.discord_user(discord_user_id);
GO

-- Index on player_id for clan_member lookups
CREATE INDEX IX_clan_member_player_id ON dbo.clan_member(player_id);
GO

-- Index on clan_id for clan_member lookups
CREATE INDEX IX_clan_member_clan_id ON dbo.clan_member(clan_id);
GO

-- Index on clan_id for war lookups
CREATE INDEX IX_clan_war_clan_id ON dbo.clan_war(clan_id);
GO

-- Index on player_id for history lookups
CREATE INDEX IX_player_clan_history_player_id ON dbo.player_clan_history(player_id);
GO

-- =====================================================
-- Helper Stored Procedures
-- =====================================================

-- Upsert clan data
CREATE OR ALTER PROCEDURE dbo.upsert_clan
    @clan_tag NVARCHAR(20),
    @clan_name NVARCHAR(100),
    @clan_level INT,
    @trophies INT,
    @war_frequency NVARCHAR(50),
    @war_stage_frequency NVARCHAR(50),
    @required_trophies INT,
    @clan_points INT,
    @clan_point_victories INT,
    @region_name NVARCHAR(50),
    @description NVARCHAR(500)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @clan_id INT;
    
    SELECT @clan_id = clan_id FROM dbo.clan WHERE clan_tag = @clan_tag;
    
    IF @clan_id IS NOT NULL
    BEGIN
        UPDATE dbo.clan
        SET clan_name = @clan_name,
            clan_level = @clan_level,
            trophies = @trophies,
            war_frequency = @war_frequency,
            war_stage_frequency = @war_stage_frequency,
            required_trophies = @required_trophies,
            clan_points = @clan_points,
            clan_point_victories = @clan_point_victories,
            region_name = @region_name,
            description = @description,
            updated_at = SYSUTCDATETIME()
        WHERE clan_id = @clan_id;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.clan (clan_tag, clan_name, clan_level, trophies, war_frequency,
                              war_stage_frequency, required_trophies, clan_points,
                              clan_point_victories, region_name, description)
        VALUES (@clan_tag, @clan_name, @clan_level, @trophies, @war_frequency,
                @war_stage_frequency, @required_trophies, @clan_points,
                @clan_point_victories, @region_name, @description);
    END
END
GO

-- Upsert player data
CREATE OR ALTER PROCEDURE dbo.upsert_player
    @player_tag NVARCHAR(20),
    @player_name NVARCHAR(100),
    @trophies INT,
    @attack_wins INT,
    @role NVARCHAR(20),
    @donations INT,
    @donations_received INT,
    @war_days INT,
    @exp_level INT,
    @league_id INT,
    @league_name NVARCHAR(50),
    @flood_protection_until DATETIME2,
    @clan_id INT,
    @player_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @player_id = player_id FROM dbo.player WHERE player_tag = @player_tag;
    
    IF @player_id IS NOT NULL
    BEGIN
        UPDATE dbo.player
        SET player_name = @player_name,
            trophies = @trophies,
            attack_wins = @attack_wins,
            role = @role,
            donations = @donations,
            donations_received = @donations_received,
            war_days = @war_days,
            exp_level = @exp_level,
            league_id = @league_id,
            league_name = @league_name,
            flood_protection_until = @flood_protection_until,
            clan_id = @clan_id,
            updated_at = SYSUTCDATETIME()
        WHERE player_id = @player_id;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.player (player_tag, player_name, trophies, attack_wins, role,
                                donations, donations_received, war_days, exp_level,
                                league_id, league_name, flood_protection_until, clan_id)
        VALUES (@player_tag, @player_name, @trophies, @attack_wins, @role,
                @donations, @donations_received, @war_days, @exp_level,
                @league_id, @league_name, @flood_protection_until, @clan_id);
        
        SET @player_id = SCOPE_IDENTITY();
    END
END
GO

-- Upsert Discord user mapping
CREATE OR ALTER PROCEDURE dbo.upsert_discord_user
    @discord_user_id BIGINT,
    @discord_username NVARCHAR(100),
    @discord_discriminator NVARCHAR(10),
    @discord_global_name NVARCHAR(100),
    @player_id INT,
    @clan_tag NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (SELECT 1 FROM dbo.discord_user WHERE discord_user_id = @discord_user_id)
    BEGIN
        UPDATE dbo.discord_user
        SET discord_username = @discord_username,
            discord_discriminator = @discord_discriminator,
            discord_global_name = @discord_global_name,
            player_id = @player_id,
            clan_tag = @clan_tag,
            updated_at = SYSUTCDATETIME()
        WHERE discord_user_id = @discord_user_id;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.discord_user (discord_user_id, discord_username, discord_discriminator,
                                       discord_global_name, player_id, clan_tag)
        VALUES (@discord_user_id, @discord_username, @discord_discriminator,
                @discord_global_name, @player_id, @clan_tag);
    END
END
GO

-- Upsert clan war data
CREATE OR ALTER PROCEDURE dbo.upsert_clan_war
    @clan_id INT,
    @season_id NVARCHAR(50),
    @season_name NVARCHAR(100),
    @war_state NVARCHAR(20),
    @clan_placement INT,
    @clan_wins INT,
    @clan_losses INT,
    @clan_draws INT,
    @clan_medals_earned INT,
    @war_members NVARCHAR(MAX),
    @started_at DATETIME2,
    @ended_at DATETIME2
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (SELECT 1 FROM dbo.clan_war WHERE clan_id = @clan_id AND season_id = @season_id)
    BEGIN
        UPDATE dbo.clan_war
        SET season_name = @season_name,
            war_state = @war_state,
            clan_placement = @clan_placement,
            clan_wins = @clan_wins,
            clan_losses = @clan_losses,
            clan_draws = @clan_draws,
            clan_medals_earned = @clan_medals_earned,
            war_members = @war_members,
            started_at = @started_at,
            ended_at = @ended_at,
            synced_at = SYSUTCDATETIME()
        WHERE clan_id = @clan_id AND season_id = @season_id;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.clan_war (clan_id, season_id, season_name, war_state, clan_placement,
                                   clan_wins, clan_losses, clan_draws, clan_medals_earned,
                                   war_members, started_at, ended_at)
        VALUES (@clan_id, @season_id, @season_name, @war_state, @clan_placement,
                @clan_wins, @clan_losses, @clan_draws, @clan_medals_earned,
                @war_members, @started_at, @ended_at);
    END
END
GO

-- =====================================================
-- Sample Data (for testing)
-- =====================================================

-- Insert sample clan
IF NOT EXISTS (SELECT 1 FROM dbo.clan WHERE clan_tag = '#AliceIsBored')
BEGIN
    INSERT INTO dbo.clan (clan_tag, clan_name, clan_level, trophies, war_frequency,
                          required_trophies, clan_points, clan_point_victories, region_name)
    VALUES ('#AliceIsBored', 'AliceIsBored', 10, 4500, 'often', 5000, 1500, 200, 'Europe');
END
GO

-- Create default schema migration tracking table
CREATE TABLE IF NOT EXISTS dbo.schema_migration (
    migration_id INT IDENTITY(1,1) PRIMARY KEY,
    migration_name NVARCHAR(100) NOT NULL,
    applied_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    UNIQUE (migration_name)
);
GO

-- Record this schema version
IF NOT EXISTS (SELECT 1 FROM dbo.schema_migration WHERE migration_name = 'v1.0-initial-schema')
BEGIN
    INSERT INTO dbo.schema_migration (migration_name) VALUES ('v1.0-initial-schema');
END
GO
-- =====================================================
-- 6. CWL Events table - stores Clan War League season data
-- =====================================================
CREATE TABLE dbo.CwlEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_id INT NOT NULL REFERENCES dbo.clan(clan_id),
    clan_tag NVARCHAR(20) NOT NULL,
    season_id NVARCHAR(50) NULL,
    league_name NVARCHAR(50) NULL,
    division NVARCHAR(50) NULL,
    war_count INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_CwlEvents_clan_tag ON dbo.CwlEvents(clan_tag);
GO

-- =====================================================
-- 7. CWL Participations table - per-player per-day CWL stats
-- =====================================================
CREATE TABLE dbo.CwlParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL REFERENCES dbo.CwlEvents(id),
    player_tag NVARCHAR(20) NOT NULL REFERENCES dbo.player(player_tag),
    day_number INT NOT NULL,
    attacks_used INT DEFAULT 0,
    war_count_comparison INT DEFAULT 0,
    stars_collected INT DEFAULT 0,
    damage_percentage DECIMAL(5,2) DEFAULT 0.00,
    clan_trophy_earned INT DEFAULT 0,
    bonus_bases_destroyed INT DEFAULT 0,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    UNIQUE (event_id, player_tag, day_number)
);
GO

CREATE INDEX idx_CwlParticipations_player_tag ON dbo.CwlParticipations(player_tag);
GO

-- =====================================================
-- 8. CW Events table - non-CWL Clan War data
-- =====================================================
CREATE TABLE dbo.CwEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    clan_tag NVARCHAR(20) NOT NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    attack_days INT DEFAULT 1,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_CwEvents_clan_tag ON dbo.CwEvents(clan_tag);
GO

-- =====================================================
-- 9. CW Participations table
-- =====================================================
CREATE TABLE dbo.CwParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL REFERENCES dbo.CwEvents(id),
    player_tag NVARCHAR(20) NOT NULL,
    day_number INT NOT NULL,
    attacks_used INT DEFAULT 0,
    attack_targets INT DEFAULT 0,
    war_count_comparison INT DEFAULT 0,
    stars_collected INT DEFAULT 0,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    UNIQUE (event_id, player_tag, day_number)
);
GO

-- =====================================================
-- 10. Raid Events table
-- =====================================================
CREATE TABLE dbo.RaidEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- =====================================================
-- 11. Raid Participations table
-- =====================================================
CREATE TABLE dbo.RaidParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL REFERENCES dbo.RaidEvents(id),
    player_tag NVARCHAR(20) NOT NULL,
    attacks_used INT DEFAULT 0,
    points_reached INT DEFAULT 0,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_RaidParticipations_player_tag ON dbo.RaidParticipations(player_tag);
GO

-- =====================================================
-- 12. Clan Games Events table
-- =====================================================
CREATE TABLE dbo.ClanGamesEvents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- =====================================================
-- 13. Clan Games Participations table
-- =====================================================
CREATE TABLE dbo.ClanGamesParticipations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    event_id INT NOT NULL REFERENCES dbo.ClanGamesEvents(id),
    player_tag NVARCHAR(20) NOT NULL,
    attacks_used INT DEFAULT 0,
    points_contributed INT DEFAULT 0,
    milestone_reached NVARCHAR(20) NULL,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_ClanGamesParticipations_player_tag ON dbo.ClanGamesParticipations(player_tag);
GO

-- =====================================================
-- 14. Members table - verified clan members
-- =====================================================
CREATE TABLE dbo.Members (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL UNIQUE,
    discord_id NVARCHAR(20) NULL,
    role NVARCHAR(20) DEFAULT 'Member',
    verified_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_Members_player_tag ON dbo.Members(player_tag);
CREATE INDEX idx_Members_discord_id ON dbo.Members(discord_id);
GO

-- =====================================================
-- 15. Contribution Scores table
-- =====================================================
CREATE TABLE dbo.ContributionScores (
    id INT IDENTITY(1,1) PRIMARY KEY,
    player_tag NVARCHAR(20) NOT NULL,
    event_date DATETIME2 NOT NULL,
    cwl_score DECIMAL(10,2) DEFAULT 0.00,
    cw_score DECIMAL(10,2) DEFAULT 0.00,
    raid_score DECIMAL(10,2) DEFAULT 0.00,
    clan_games_score DECIMAL(10,2) DEFAULT 0.00,
    total_score DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX idx_ContributionScores_player_tag ON dbo.ContributionScores(player_tag);
CREATE INDEX idx_ContributionScores_event_date ON dbo.ContributionScores(event_date);
GO

-- =====================================================
-- Stored procedures for CWL data
-- =====================================================

-- Upsert CWL event
CREATE OR ALTER PROCEDURE dbo.upsert_cwl_event
    @clan_id INT,
    @clan_tag NVARCHAR(20),
    @season_id NVARCHAR(50),
    @league_name NVARCHAR(50),
    @division NVARCHAR(50),
    @war_count INT,
    @total_wins INT,
    @start_time DATETIME2,
    @end_time DATETIME2,
    @event_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT @event_id = id FROM dbo.CwlEvents WHERE season_id = @season_id AND clan_tag = @clan_tag;

    IF @event_id IS NOT NULL
    BEGIN
        UPDATE dbo.CwlEvents
        SET clan_id = @clan_id,
            league_name = @league_name,
            division = @division,
            war_count = @war_count,
            total_wins = @total_wins,
            start_time = @start_time,
            end_time = @end_time,
            updated_at = SYSUTCDATETIME()
        WHERE id = @event_id;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.CwlEvents (clan_id, clan_tag, season_id, league_name, division,
                                   war_count, total_wins, start_time, end_time)
        VALUES (@clan_id, @clan_tag, @season_id, @league_name, @division,
                @war_count, @total_wins, @start_time, @end_time);

        SET @event_id = SCOPE_IDENTITY();
    END
END
GO

-- Upsert CWL participation
CREATE OR ALTER PROCEDURE dbo.upsert_cwl_participation
    @event_id INT,
    @player_tag NVARCHAR(20),
    @day_number INT,
    @attacks_used INT,
    @war_count_comparison INT,
    @stars_collected INT,
    @damage_percentage DECIMAL(5,2),
    @clan_trophy_earned INT,
    @bonus_bases_destroyed INT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (SELECT 1 FROM dbo.CwlParticipations
               WHERE event_id = @event_id AND player_tag = @player_tag AND day_number = @day_number)
    BEGIN
        UPDATE dbo.CwlParticipations
        SET attacks_used = @attacks_used,
            war_count_comparison = @war_count_comparison,
            stars_collected = @stars_collected,
            damage_percentage = @damage_percentage,
            clan_trophy_earned = @clan_trophy_earned,
            bonus_bases_destroyed = @bonus_bases_destroyed,
            updated_at = SYSUTCDATETIME()
        WHERE event_id = @event_id AND player_tag = @player_tag AND day_number = @day_number;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.CwlParticipations (event_id, player_tag, day_number, attacks_used,
                                           war_count_comparison, stars_collected, damage_percentage,
                                           clan_trophy_earned, bonus_bases_destroyed)
        VALUES (@event_id, @player_tag, @day_number, @attacks_used,
                @war_count_comparison, @stars_collected, @damage_percentage,
                @clan_trophy_earned, @bonus_bases_destroyed);
    END
END
GO

-- =====================================================
-- Update schema version
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM dbo.schema_migration WHERE migration_name = 'v1.1-cwl-models')
BEGIN
    INSERT INTO dbo.schema_migration (migration_name) VALUES ('v1.1-cwl-models');
END
GO
