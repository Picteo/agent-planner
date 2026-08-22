const {
    Client,
    GatewayIntentBits,
    ChannelType,
    PermissionsBitField,
} = require('discord.js');

/**
 * Finalize Server Script
 * Cleans up duplicate categories and organizes remaining channels
 */
class ServerFinalize {
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
            console.log('✅ Finalize Bot is ready!\n');
            await this.finalizeServer();
        });

        this.client.on('error', (error) => {
            console.error('❌ Finalize error:', error);
        });
    }

    async finalizeServer() {
        const guild = this.client.guilds.cache.first();

        if (!guild) {
            console.error('❌ Bot is not connected to any guild!');
            process.exit(1);
        }

        console.log(`📡 Connected to server: ${guild.name}\n`);

        // Fetch all channels
        const allChannels = await guild.channels.fetch();
        const categories = allChannels.filter(ch => ch.type === ChannelType.GuildCategory);
        const textChannels = allChannels.filter(ch => ch.type === ChannelType.GuildText);

        console.log('Current categories:');
        for (const cat of categories.values()) {
            const channels = [...textChannels.values()].filter(ch => ch.parentId === cat.id);
            console.log(`   📁 "${cat.name}" (${channels.length} channels)`);
        }

        // Duplicate categories to delete (keep the emoji ones: 📢 Information, 🎮 Clan Activity, etc.)
        const categoriesToDelete = [
            'Information',    // Old duplicate (keep 📢 Information)
            'Bot Commands',   // Old duplicate (keep 🤖 Bot Commands)
        ];

        console.log('\n' + '='.repeat(50));
        console.log('REORGANIZING SERVER:');
        console.log('='.repeat(50));

        // Get role references for permission overwrites
        const memberRole = guild.roles.cache.find(r => r.name === 'Member');
        const leaderRole = guild.roles.cache.find(r => r.name === 'Leader');
        const unverifiedRole = guild.roles.cache.find(r => r.name === 'Unverified');
        const aliceIsBoredRole = guild.roles.cache.find(r => r.name === 'AliceIsBored');

        // Build permission overwrites for verify channel (visible to all authenticated)
        const verifyOverwrites = [];
        if (unverifiedRole) {
            verifyOverwrites.push({
                id: unverifiedRole.id,
                type: 0,
                allow: [PermissionsBitField.Flags.ViewChannel],
                deny: [],
            });
        }
        if (memberRole) {
            verifyOverwrites.push({
                id: memberRole.id,
                type: 0,
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            });
        }
        if (leaderRole) {
            verifyOverwrites.push({
                id: leaderRole.id,
                type: 0,
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            });
        }
        if (aliceIsBoredRole) {
            verifyOverwrites.push({
                id: aliceIsBoredRole.id,
                type: 0,
                allow: [PermissionsBitField.Flags.Administrator],
                deny: [],
            });
        }

        // Build admin channel overwrites (Leader and Owner only)
        const adminOverwrites = [];
        if (aliceIsBoredRole) {
            adminOverwrites.push({
                id: aliceIsBoredRole.id,
                type: 0,
                allow: [PermissionsBitField.Flags.Administrator],
                deny: [],
            });
        }
        if (leaderRole) {
            adminOverwrites.push({
                id: leaderRole.id,
                type: 0,
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            });
        }
        if (memberRole) {
            adminOverwrites.push({
                id: memberRole.id,
                type: 0,
                allow: [],
                deny: [PermissionsBitField.Flags.ViewChannel],
            });
        }
        if (unverifiedRole) {
            adminOverwrites.push({
                id: unverifiedRole.id,
                type: 0,
                allow: [],
                deny: [PermissionsBitField.Flags.ViewChannel],
            });
        }

        // Find the 📢 Information category
        const infoCategory = [...categories.values()].find(c => c.name === '📢 Information');

        // Move verify channel to 📢 Information category
        const verifyChannel = [...textChannels.values()].find(ch => ch.name === 'verify');
        if (verifyChannel && infoCategory) {
            try {
                await verifyChannel.edit({
                    parent: infoCategory.id,
                    permissionOverwrites: verifyOverwrites,
                });
                console.log(`   ✅ Moved #verify to 📢 Information`);
            } catch (error) {
                console.error(`   ❌ Failed to move #verify:`, error.message);
            }
        } else if (verifyChannel && !infoCategory) {
            // Create 📢 Information if it doesn't exist
            try {
                const newInfoCategory = await guild.channels.create({
                    name: '📢 Information',
                    type: ChannelType.GuildCategory,
                });
                await verifyChannel.edit({
                    parent: newInfoCategory.id,
                    permissionOverwrites: verifyOverwrites,
                });
                console.log(`   ✅ Created 📢 Information and moved #verify`);
            } catch (error) {
                console.error(`   ❌ Failed to create category:`, error.message);
            }
        }

        // Move admin-log and admin-settings to a new Admin category or 📢 Information
        const adminChannels = [...textChannels.values()].filter(ch => ch.name === 'admin-log' || ch.name === 'admin-settings');
        for (const adminChannel of adminChannels) {
            try {
                await adminChannel.edit({
                    parent: infoCategory?.id,
                    permissionOverwrites: adminOverwrites,
                });
                console.log(`   ✅ Moved #${adminChannel.name} to 📢 Information`);
            } catch (error) {
                console.error(`   ❌ Failed to move #${adminChannel.name}:`, error.message);
            }
        }

        // Delete duplicate categories
        console.log('\n' + '='.repeat(50));
        console.log('DELETING DUPLICATE CATEGORIES:');
        console.log('='.repeat(50));

        for (const catName of categoriesToDelete) {
            const cat = [...categories.values()].find(c => c.name === catName);
            if (cat) {
                try {
                    await cat.delete();
                    console.log(`   ✅ Deleted category: "${catName}"`);
                } catch (error) {
                    console.error(`   ❌ Failed to delete category "${catName}":`, error.message);
                }
            }
        }

        // Verify final state
        const finalChannels = await guild.channels.fetch();
        const finalCategories = finalChannels.filter(ch => ch.type === ChannelType.GuildCategory);
        const finalTextChannels = finalChannels.filter(ch => ch.type === ChannelType.GuildText);

        console.log('\n' + '='.repeat(50));
        console.log('FINAL SERVER STATE:');
        console.log('='.repeat(50));
        console.log(`Categories: ${finalCategories.size}`);
        console.log(`Text channels: ${finalTextChannels.size}`);

        for (const category of finalCategories.values()) {
            console.log(`\n   📁 ${category.name}:`);
            const channels = [...finalTextChannels.values()].filter(ch => ch.parentId === category.id);
            for (const ch of channels) {
                console.log(`      # ${ch.name}`);
            }
        }

        const uncategorized = [...finalTextChannels.values()].filter(ch => !ch.parentId);
        if (uncategorized.length > 0) {
            console.log('\n   Uncategorized channels:');
            for (const ch of uncategorized) {
                console.log(`      # ${ch.name}`);
            }
        }

        setTimeout(() => {
            console.log('\n👋 Finalize bot shutting down...');
            this.client.destroy();
            process.exit(0);
        }, 3000);
    }
}

function main() {
    const token = process.env.DISCORD_TOKEN;

    if (!token) {
        console.error('❌ DISCORD_TOKEN environment variable is required');
        process.exit(1);
    }

    const finalize = new ServerFinalize(token);
    finalize.client.login(token);
}

module.exports = ServerFinalize;

if (require.main === module) {
    main();
}