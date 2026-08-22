const {
    Client,
    GatewayIntentBits,
    ChannelType,
} = require('discord.js');

class FixOrphans {
    constructor(token) {
        this.token = token;
        this.client = new Client({
            intents: [GatewayIntentBits.Guilds],
        });
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.client.once('ready', async () => {
            console.log('✅ Fix Orphans Bot is ready!\n');
            await this.fixOrphans();
        });
        this.client.on('error', (error) => {
            console.error('❌ Error:', error);
        });
    }

    async fixOrphans() {
        const guild = this.client.guilds.cache.first();
        if (!guild) {
            console.error('❌ Not connected to any guild!');
            process.exit(1);
        }

        console.log(`Server: ${guild.name}\n`);

        // Known good channels that should exist
        const goodChannels = new Set([
            'announcements', 'rules', 'verify', 'admin-log', 'admin-settings',
            'general', 'war-chat', 'war-updates', 'raid-chat', 'raid-updates',
            'clan-games', 'clan-games-updates', 'capital-raids', 'capital-updates',
            'leaderboards', 'scores', 'bot-commands'
        ]);

        // Fetch all channels
        const allChannels = await guild.channels.fetch();
        const textChannels = allChannels.filter(ch => ch.type === ChannelType.GuildText);
        const categories = allChannels.filter(ch => ch.type === ChannelType.GuildCategory);

        console.log(`Found ${textChannels.size} text channels, ${categories.size} categories\n`);

        // Find orphaned channels (not in a category)
        const orphanedChannels = [...textChannels.values()].filter(ch => !ch.parentId);
        console.log(`Orphaned channels (${orphanedChannels.length}):`);
        for (const ch of orphanedChannels) {
            console.log(`   #${ch.name} (ID: ${ch.id})`);
        }

        // Find categories without any channels
        const emptyCategories = [];
        for (const cat of categories.values()) {
            const channelsInCat = [...textChannels.values()].filter(ch => ch.parentId === cat.id);
            if (channelsInCat.length === 0) {
                emptyCategories.push(cat);
                console.log(`\nEmpty category: "${cat.name}"`);
            }
        }

        // Delete orphaned channels
        console.log('\n--- DELETING ORPHANED CHANNELS ---');
        for (const ch of orphanedChannels) {
            try {
                await ch.delete();
                console.log(`   ✅ Deleted #${ch.name}`);
            } catch (error) {
                console.error(`   ❌ Failed to delete #${ch.name}:`, error.message);
            }
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Delete empty categories
        console.log('\n--- DELETING EMPTY CATEGORIES ---');
        for (const cat of emptyCategories) {
            try {
                await cat.delete();
                console.log(`   ✅ Deleted category: "${cat.name}"`);
            } catch (error) {
                console.error(`   ❌ Failed to delete "${cat.name}":`, error.message);
            }
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Final verification
        console.log('\n--- FINAL STATE ---');
        const finalChannels = await guild.channels.fetch();
        const finalCategories = finalChannels.filter(ch => ch.type === ChannelType.GuildCategory);
        const finalTextChannels = finalChannels.filter(ch => ch.type === ChannelType.GuildText);

        console.log(`Categories: ${finalCategories.size}`);
        console.log(`Text channels: ${finalTextChannels.size}`);

        for (const cat of finalCategories.values()) {
            console.log(`\n   📁 ${cat.name}:`);
            const channels = [...finalTextChannels.values()].filter(ch => ch.parentId === cat.id);
            for (const ch of channels) {
                console.log(`      # ${ch.name}`);
            }
        }

        const remainingOrphans = [...finalTextChannels.values()].filter(ch => !ch.parentId);
        if (remainingOrphans.length > 0) {
            console.log('\n   Remaining orphans:');
            for (const ch of remainingOrphans) {
                console.log(`      # ${ch.name}`);
            }
        } else {
            console.log('\n   ✅ All channels are categorized!');
        }

        setTimeout(() => {
            console.log('\n👋 Shutting down...');
            this.client.destroy();
            process.exit(0);
        }, 2000);
    }
}

function main() {
    const token = process.env.DISCORD_TOKEN;
    if (!token) {
        console.error('❌ DISCORD_TOKEN required');
        process.exit(1);
    }
    const fix = new FixOrphans(token);
    fix.client.login(token);
}

module.exports = FixOrphans;
if (require.main === module) main();