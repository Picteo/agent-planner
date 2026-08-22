const { Client, GatewayIntentBits } = require('discord.js');

/**
 * Server Inspection Script
 * Connects to an existing Discord server and reports its current configuration state
 * Usage: node src/check-server.js
 * Requires: DISCORD_TOKEN environment variable with bot token
 */
class ServerChecker {
    constructor(token) {
        this.token = token;
        this.client = new Client({
            intents: [
                GatewayIntentBits.Guilds,
            ],
        });
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.client.once('ready', async () => {
            console.log('✅ Server Checker Bot is ready!\n');
            await this.checkServer();
        });

        this.client.on('error', (error) => {
            console.error('❌ Checker error:', error);
        });
    }

    async checkServer() {
        const guild = this.client.guilds.cache.first();

        if (!guild) {
            console.error('❌ Bot is not connected to any guild!');
            console.error('Make sure the bot is invited to your server.');
            process.exit(1);
        }

        console.log('═══════════════════════════════════════════════');
        console.log(`SERVER: ${guild.name}`);
        console.log(`ID: ${guild.id}`);
        console.log(`Owner: ${guild.ownerId}`);
        console.log(`Created: ${new Date(guild.createdTimestamp).toLocaleString()}`);
        console.log(`Region: ${guild.region || 'auto'}`);
        console.log(`Verification Level: ${guild.verificationLevel}`);
        console.log(`Default Notification: ${guild.defaultMessageNotifications}`);
        console.log('═══════════════════════════════════════════════\n');

        // Check roles
        await this.checkRoles(guild);

        // Check categories and channels
        await this.checkChannels(guild);

        // Compare with expected configuration
        await this.compareWithExpected(guild);

        // Shutdown after reporting
        setTimeout(() => {
            this.client.destroy();
            process.exit(0);
        }, 3000);
    }

    async checkRoles(guild) {
        console.log('═══════════════════════════════════════════════');
        console.log('ROLES (Total: ' + guild.roles.cache.size + ')');
        console.log('═══════════════════════════════════════════════\n');

        const roles = [...guild.roles.cache.sort((a, b) => b.position - a.position).values()];

        for (const role of roles) {
            const isEveryone = role.id === guild.roles.everyone.id;
            const icon = isEveryone ? '👤' : '🎭';
            console.log(`${icon} @${role.name}`);
            console.log(`   ID: ${role.id}`);
            console.log(`   Color: ${role.color || 'Default (Grey)'}`);
            console.log(`   Hoisted: ${role.hoist ? 'Yes' : 'No'}`);
            console.log(`   Permissions: ${role.permissions.toArray().slice(0, 10).join(', ')}${role.permissions.toArray().length > 10 ? ` (+${role.permissions.toArray().length - 10} more)` : ''}`);
            console.log(`   Members: ${role.members.size}`);
            console.log('');
        }
    }

    async checkChannels(guild) {
        console.log('═══════════════════════════════════════════════');
        console.log('CATEGORIES & CHANNELS (Total: ' + guild.channels.cache.size + ')');
        console.log('═══════════════════════════════════════════════\n');

        const categories = guild.channels.cache.filter(ch => ch.type === 15); // GuildCategory
        const textChannels = guild.channels.cache.filter(ch => ch.type === 0); // GuildText

        console.log(`Categories: ${categories.size}`);
        console.log(`Text Channels: ${textChannels.size}`);
        console.log('');

        // List categories and their channels
        for (const category of categories.values()) {
            console.log(`📁 ${category.name}`);
            console.log(`   ID: ${category.id}`);
            
            const channelsArr = [...textChannels.filter(ch => ch.parentId === category.id)
                .sort((a, b) => a.position - b.position).values()];

            if (channelsArr.length === 0) {
                console.log('   (no channels)');
            }

            for (const channel of channelsArr) {
                console.log(`   # ${channel.name}`);
                console.log(`      ID: ${channel.id}`);
                
                // Show permission overwrites
                const overwrites = channel.permissionOverwrites.cache;
                if (overwrites.size > 0) {
                    console.log(`      Overwrites: ${overwrites.size}`);
                    overwrites.forEach((overwrite, targetId) => {
                        const target = guild.roles.cache.get(targetId) || guild.members.cache.get(targetId);
                        const targetName = target ? target.name : targetId;
                        const allow = overwrite.allow.toArray();
                        const deny = overwrite.deny.toArray();
                        
                        if (deny.includes('ViewChannel')) {
                            console.log(`         🔒 ${targetName}: DENY ViewChannel`);
                        } else if (allow.includes('ViewChannel')) {
                            console.log(`         ✅ ${targetName}: ALLOW ViewChannel`);
                        }
                    });
                }
            }
            console.log('');
        }

        // Channels without categories
        const uncategorized = textChannels.filter(ch => !ch.parentId);
        if (uncategorized.size > 0) {
            console.log('📋 Uncategorized Channels:');
            for (const channel of uncategorized.values()) {
                console.log(`   # ${channel.name} (ID: ${channel.id})`);
            }
            console.log('');
        }
    }

    async compareWithExpected(guild) {
        console.log('═══════════════════════════════════════════════');
        console.log('EXPECTED vs ACTUAL COMPARISON');
        console.log('═══════════════════════════════════════════════\n');

        const textChannels = guild.channels.cache.filter(ch => ch.type === 0);
        const categories = guild.channels.cache.filter(ch => ch.type === 15);
        const roles = guild.roles.cache;

        // Expected configuration
        const EXPECTED_CATEGORIES = ['📢 Information', '🎮 Clan Activity', '📊 Statistics', '🤖 Bot Commands'];
        const EXPECTED_CHANNELS = {
            '📢 Information': ['announcements', 'rules'],
            '🎮 Clan Activity': ['general', 'war-chat', 'war-updates', 'raid-chat', 'raid-updates', 'clan-games', 'clan-games-updates', 'capital-raids', 'capital-updates'],
            '📊 Statistics': ['leaderboards', 'scores'],
            '🤖 Bot Commands': ['bot-commands'],
        };
        const EXPECTED_SPECIAL_CHANNELS = ['verify'];
        const EXPECTED_ADMIN_CHANNELS = ['admin-log', 'admin-settings'];
        const EXPECTED_ROLES = ['AliceIsBored', 'Leader', 'Member', 'Unverified'];

        // Check categories
        console.log('📁 CATEGORIES:');
        for (const cat of EXPECTED_CATEGORIES) {
            const found = categories.find(c => c.name === cat);
            console.log(`   ${found ? '✅' : '❌'} ${cat}`);
        }

        // Check expected channels
        console.log('\n📝 EXPECTED CHANNELS:');
        for (const [category, channels] of Object.entries(EXPECTED_CHANNELS)) {
            const categoryObj = categories.find(c => c.name === category);
            console.log(`   📁 ${category}:`);
            for (const chName of channels) {
                const found = [...textChannels.values()].find(ch => ch.name === chName && ch.parentId === (categoryObj?.id));
                    console.log(`      ${found ? '✅' : '❌'} #${chName}`);
            }
        }

        // Check special channels
        console.log('\n🔐 SPECIAL CHANNELS:');
        for (const chName of EXPECTED_SPECIAL_CHANNELS) {
            const found = [...textChannels.values()].find(ch => ch.name === chName);
                console.log(`   ${found ? '✅' : '❌'} #${chName}`);
        }

        // Check admin channels
        console.log('\n🔒 ADMIN CHANNELS:');
        for (const chName of EXPECTED_ADMIN_CHANNELS) {
            const found = [...textChannels.values()].find(ch => ch.name === chName);
                console.log(`   ${found ? '✅' : '❌'} #${chName}`);
        }

        // Check roles
        console.log('\n🎭 ROLES:');
        for (const roleName of EXPECTED_ROLES) {
            const found = roles.find(r => r.name === roleName);
            console.log(`   ${found ? '✅' : '❌'} @${roleName}${found ? ` (ID: ${found.id})` : ''}`);
        }

        // Summary
        const totalExpectedChannels = Object.values(EXPECTED_CHANNELS).flat().length 
            + EXPECTED_SPECIAL_CHANNELS.length 
            + EXPECTED_ADMIN_CHANNELS.length;
        
        const actualTextChannels = textChannels.size;
        
        console.log('\n═══════════════════════════════════════════════');
        console.log('SUMMARY:');
        console.log(`   Expected categories: ${EXPECTED_CATEGORIES.length} | Found: ${categories.size}`);
        console.log(`   Expected text channels: ${totalExpectedChannels} | Found: ${actualTextChannels}`);
        console.log(`   Expected roles: ${EXPECTED_ROLES.length} | Found custom roles: ${[...roles.values()].filter(r => r.name !== '@everyone' && !EXPECTED_ROLES.includes(r.name)).length}`);
        console.log('═══════════════════════════════════════════════');

        console.log('\n⚠️  To configure the server, run: node src/setup-server.js');
    }
}

/**
 * Main entry point
 */
function main() {
    const token = process.env.DISCORD_TOKEN;

    if (!token) {
        console.error('❌ DISCORD_TOKEN environment variable is required');
        console.error('');
        console.error('Create a .env file with your bot token:');
        console.error('  DISCORD_TOKEN=your_bot_token_here');
        console.error('');
        console.error('Or set it directly:');
        console.error('  export DISCORD_TOKEN=your_bot_token_here');
        process.exit(1);
    }

    const checker = new ServerChecker(token);
    checker.client.login(token);
}

module.exports = ServerChecker;

if (require.main === module) {
    main();
}