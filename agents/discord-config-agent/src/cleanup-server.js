const { 
    CATEGORIES_AND_CHANNELS, 
    VERIFY_CHANNEL,
    ADMIN_CHANNELS,
} = require('./config');

const {
    Client,
    GatewayIntentBits,
    ChannelType,
} = require('discord.js');

/**
 * Channel Cleanup Script
 * Removes all channels and categories that are not in the configuration
 * Usage: node src/cleanup-server.js
 * Requires: DISCORD_TOKEN environment variable with bot token
 */
class ServerCleanup {
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
            console.log('✅ Cleanup Bot is ready!\n');
            await this.cleanupServer();
        });

        this.client.on('error', (error) => {
            console.error('❌ Cleanup error:', error);
        });
    }

    async cleanupServer() {
        const guild = this.client.guilds.cache.first();

        if (!guild) {
            console.error('❌ Bot is not connected to any guild!');
            process.exit(1);
        }

        console.log(`📡 Connected to server: ${guild.name}`);
        console.log(`🆔 Server ID: ${guild.id}\n`);

        // Get all channels and categories
        const allChannels = guild.channels.cache;
        const categories = allChannels.filter(ch => ch.type === ChannelType.GuildCategory);
        const textChannels = allChannels.filter(ch => ch.type === ChannelType.GuildText);

        console.log(`Found ${categories.size} categories and ${textChannels.size} text channels\n`);

        // Build set of channels to KEEP
        const keepChannelNames = new Set();

        // Add configured category channel names
        for (const category of CATEGORIES_AND_CHANNELS) {
            for (const channel of category.channels) {
                keepChannelNames.add(channel.name);
            }
        }

        // Add verify channel
        keepChannelNames.add(VERIFY_CHANNEL.name);

        // Add admin channels
        for (const channel of ADMIN_CHANNELS) {
            keepChannelNames.add(channel.name);
        }

        console.log('═══════════════════════════════════════════════');
        console.log('CHANNELS TO KEEP:');
        console.log('═══════════════════════════════════════════════');
        for (const name of keepChannelNames) {
            console.log(`   ✅ #${name}`);
        }

        // Find channels to delete
        const channelsToDelete = [...textChannels.values()].filter(ch => !keepChannelNames.has(ch.name));

        console.log('\n' + '='.repeat(50));
        console.log(`CHANNELS TO DELETE (${channelsToDelete.length}):`);
        console.log('='.repeat(50));

        for (const channel of channelsToDelete) {
            console.log(`   ❌ #${channel.name} (ID: ${channel.id})${channel.parent ? ` in ${channel.parent.name}` : ' (uncategorized)'}`);
        }

        // Confirm before deletion
        console.log('\n⚠️  This will permanently delete the above channels!');
        console.log('Proceeding with deletion...\n');

        // Delete unwanted channels
        let deletedCount = 0;
        let errorCount = 0;

        for (const channel of channelsToDelete) {
            try {
                await channel.delete();
                console.log(`   ✅ Deleted #${channel.name}`);
                deletedCount++;
            } catch (error) {
                console.error(`   ❌ Failed to delete #${channel.name}:`, error.message);
                errorCount++;
            }
            // Small delay to avoid rate limits
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Find categories to delete (those without remaining channels)
        console.log('\n' + '='.repeat(50));
        console.log('CHECKING CATEGORIES FOR DELETION:');
        console.log('='.repeat(50));

        // Re-fetch channels after deletion
        const updatedChannels = await guild.channels.fetch();
        const updatedTextChannels = updatedChannels.filter(ch => ch.type === ChannelType.GuildText);
        const updatedCategories = updatedChannels.filter(ch => ch.type === ChannelType.GuildCategory);

        const categoriesToDelete = [];
        for (const category of updatedCategories.values()) {
            const channelsInCategory = [...updatedTextChannels.values()].filter(ch => ch.parentId === category.id);
            if (channelsInCategory.length === 0) {
                categoriesToDelete.push(category);
                console.log(`   📁 Will delete empty category: "${category.name}"`);
            } else {
                console.log(`   📁 Keeping category "${category.name}" (${channelsInCategory.length} channels remaining)`);
            }
        }

        // Delete empty categories
        console.log('\n' + '='.repeat(50));
        console.log(`DELETING EMPTY CATEGORIES (${categoriesToDelete.length}):`);
        console.log('='.repeat(50));

        for (const category of categoriesToDelete) {
            try {
                await category.delete();
                console.log(`   ✅ Deleted category: "${category.name}"`);
            } catch (error) {
                console.error(`   ❌ Failed to delete category "${category.name}":`, error.message);
            }
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Summary
        console.log('\n' + '='.repeat(50));
        console.log('CLEANUP SUMMARY:');
        console.log('='.repeat(50));
        console.log(`   Channels deleted: ${deletedCount}`);
        console.log(`   Delete errors: ${errorCount}`);
        console.log(`   Empty categories deleted: ${categoriesToDelete.length}`);

        // Verify final state
        const finalChannels = await guild.channels.fetch();
        const finalTextChannels = finalChannels.filter(ch => ch.type === ChannelType.GuildText);
        const finalCategories = finalChannels.filter(ch => ch.type === ChannelType.GuildCategory);

        console.log('\n' + '='.repeat(50));
        console.log('FINAL SERVER STATE:');
        console.log('='.repeat(50));
        console.log(`   Categories: ${finalCategories.size}`);
        console.log(`   Text channels: ${finalTextChannels.size}`);

        for (const category of finalCategories.values()) {
            console.log(`   📁 ${category.name}:`);
            const channels = [...finalTextChannels.values()].filter(ch => ch.parentId === category.id);
            for (const ch of channels) {
                console.log(`      # ${ch.name}`);
            }
        }

        // Uncategorized channels
        const uncategorized = [...finalTextChannels.values()].filter(ch => !ch.parentId);
        if (uncategorized.length > 0) {
            console.log('   Uncategorized channels:');
            for (const ch of uncategorized) {
                console.log(`      # ${ch.name}`);
            }
        }

        // Shutdown
        setTimeout(() => {
            console.log('\n👋 Cleanup bot shutting down...');
            this.client.destroy();
            process.exit(errorCount > 0 ? 1 : 0);
        }, 3000);
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
        console.error('Usage:');
        console.error('  export DISCORD_TOKEN=your_bot_token_here');
        console.error('  node src/cleanup-server.js');
        console.error('');
        console.error('Or create a .env file with:');
        console.error('  DISCORD_TOKEN=your_bot_token_here');
        process.exit(1);
    }

    const cleanup = new ServerCleanup(token);
    cleanup.client.login(token);
}

module.exports = ServerCleanup;

if (require.main === module) {
    main();
}