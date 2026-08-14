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