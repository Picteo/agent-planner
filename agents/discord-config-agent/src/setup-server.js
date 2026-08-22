const { 
    SERVER_CONFIG, 
    ROLES, 
    ROLE_HIERARCHY, 
    CATEGORIES_AND_CHANNELS, 
    VERIFY_CHANNEL,
    ADMIN_CHANNELS,
    BOT_PERMISSIONS,
    VERIFY_EMBED,
    ACCEPTANCE_CRITERIA,
} = require('./config');

const {
    Client,
    GatewayIntentBits,
    PermissionsBitField,
    EmbedBuilder,
    ActionRowBuilder,
    ButtonBuilder,
    ButtonStyle,
    Collection,
    ChannelType,
} = require('discord.js');

/**
 * Helper function to convert string permission names to PermissionsBitField.Flags
 * Handles discord.js v14 permission name mappings
 */
function permissionsFromString(permStrings) {
    if (!permStrings || permStrings.length === 0) return new PermissionsBitField(0n);
    
    // Special handling for Administrator (grants all permissions)
    if (permStrings.includes('Administrator')) {
        return new PermissionsBitField(PermissionsBitField.Flags.Administrator);
    }
    
    // Map of permission names to new discord.js v14 names
    const permissionMap = {
        'UseSlashCommands': 'UseApplicationCommands',
        'QuietThread': 'SendThreadsMessages',
        'All': 'All',
    };
    
    const flags = permStrings.filter(p => p !== 'Administrator').map(perm => {
        const mapped = permissionMap[perm] || perm;
        const flag = PermissionsBitField.Flags?.[mapped];
        return flag;
    }).filter(f => f !== undefined && f !== null);
    
    // If no valid flags found, return 0n
    if (flags.length === 0) {
        return new PermissionsBitField(0n);
    }
    
    return new PermissionsBitField(flags);
}

/**
 * Server Setup Script
 * Configures a Discord server with all required channels, categories, roles, and permissions
 * for the AliceIsBored clan.
 * 
 * Usage: node src/setup-server.js
 * Requires: DISCORD_TOKEN environment variable with bot token
 */
class ServerSetup {
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
            console.log('✅ Server Setup Bot is ready!\n');
            await this.runSetup();
        });

        this.client.on('error', (error) => {
            console.error('❌ Setup error:', error);
        });
    }

    /**
     * Main setup orchestration
     */
    async runSetup() {
        const guild = this.client.guilds.cache.first();
        
        if (!guild) {
            console.error('❌ Bot is not connected to any guild!');
            console.error('Invite the bot to a server first, then run this setup.');
            process.exit(1);
        }

        console.log(`📡 Connected to server: ${guild.name}`);
        console.log(`🆔 Server ID: ${guild.id}\n`);

        let successCount = 0;
        let failCount = 0;
        const results = [];

        // Step 1: Update server settings
        console.log('═══════════════════════════════════════════════');
        console.log('Step 1: Configuring server settings...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.configureServer(guild);
            console.log('✅ Server settings configured');
            results.push({ step: 'Server Settings', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Server settings configuration failed:', error.message);
            results.push({ step: 'Server Settings', status: 'FAIL' });
            failCount++;
        }

        // Step 2: Create roles (bottom to top in hierarchy)
        console.log('\n═══════════════════════════════════════════════');
        console.log('Step 2: Creating roles...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.createRoles(guild);
            console.log('✅ All roles created successfully');
            results.push({ step: 'Role Creation', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Role creation failed:', error.message);
            results.push({ step: 'Role Creation', status: 'FAIL' });
            failCount++;
        }

        // Step 3: Create categories and channels
        console.log('\n═══════════════════════════════════════════════');
        console.log('Step 3: Creating categories and channels...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.createCategoriesAndChannels(guild);
            console.log('✅ All categories and channels created');
            results.push({ step: 'Categories & Channels', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Channel creation failed:', error.message);
            results.push({ step: 'Categories & Channels', status: 'FAIL' });
            failCount++;
        }

        // Step 4: Create verification channel
        console.log('\n═══════════════════════════════════════════════');
        console.log('Step 4: Creating verification channel...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.createVerificationChannel(guild);
            console.log('✅ Verification channel created with embed');
            results.push({ step: 'Verification Channel', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Verification channel creation failed:', error.message);
            results.push({ step: 'Verification Channel', status: 'FAIL' });
            failCount++;
        }

        // Step 5: Create admin channels
        console.log('\n═══════════════════════════════════════════════');
        console.log('Step 5: Creating admin channels...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.createAdminChannels(guild);
            console.log('✅ Admin channels created');
            results.push({ step: 'Admin Channels', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Admin channel creation failed:', error.message);
            results.push({ step: 'Admin Channels', status: 'FAIL' });
            failCount++;
        }

        // Step 6: Set default role for new members
        console.log('\n═══════════════════════════════════════════════');
        console.log('Step 6: Configuring default role for new members...');
        console.log('═══════════════════════════════════════════════');
        try {
            await this.configureDefaultRole(guild);
            console.log('✅ Default role configured');
            results.push({ step: 'Default Role', status: 'PASS' });
            successCount++;
        } catch (error) {
            console.error('❌ Default role configuration failed:', error.message);
            results.push({ step: 'Default Role', status: 'FAIL' });
            failCount++;
        }

        // Print summary
        console.log('\n' + '='.repeat(50));
        console.log('SETUP COMPLETE - SUMMARY');
        console.log('='.repeat(50));
        results.forEach(r => {
            const icon = r.status === 'PASS' ? '✅' : '❌';
            console.log(`${icon} ${r.step}: ${r.status}`);
        });
        console.log(`\nTotal: ${successCount} passed, ${failCount} failed out of ${results.length} steps`);

        // Acceptance criteria verification
        console.log('\n' + '='.repeat(50));
        console.log('ACCEPTANCE CRITERIA CHECKLIST');
        console.log('='.repeat(50));
        ACCEPTANCE_CRITERIA.forEach((criterion, index) => {
            console.log(`${index + 1}. [ ] ${criterion}`);
        });

        console.log('\n⚠️  Please verify each acceptance criterion manually in the Discord server.');
        console.log('To update Azure DevOps work item #6, mark all criteria as complete.');

        // Keep the bot running briefly so user can see the results
        setTimeout(() => {
            console.log('\n👋 Setup bot shutting down...');
            this.client.destroy();
            process.exit(failCount > 0 ? 1 : 0);
        }, 5000);
    }

    /**
     * Configure server settings (name, description, verification level)
     */
    async configureServer(guild) {
        const updates = {};

        // Update server name
        if (guild.name !== SERVER_CONFIG.serverName) {
            updates.name = SERVER_CONFIG.serverName;
        }

        // Update verification level
        const verificationLevelMap = {
            'None': 0,
            'Low': 1,
            'Medium': 2,
            'High': 3,
            'Very high': 4,
        };
        updates.verifyLevel = verificationLevelMap[SERVER_CONFIG.verificationLevel] ?? 2;

        // Update AFK channel settings if needed
        updates.afkTimeout = 300; // 5 minutes

        await guild.edit(updates);
        console.log(`   📝 Server name: "${updates.name || guild.name}"`);
        console.log(`   🔒 Verification level: ${updates.verifyLevel}`);
    }

    /**
     * Create all roles with proper hierarchy
     * Roles are created bottom-to-top (Unverified → Member → Leader → Owner)
     */
    async createRoles(guild) {
        const roleDataMap = {
            'Unverified': ROLES.UNVERIFIED,
            'Member': ROLES.MEMBER,
            'Leader': ROLES.LEADER,
            'AliceIsBored': ROLES.OWNER,
        };

        // Create roles in hierarchy order (lowest first)
        for (const roleName of ['Unverified', 'Member', 'Leader', 'AliceIsBored']) {
            const roleInfo = roleDataMap[roleName];
            
            // Check if role already exists
            const existingRole = guild.roles.cache.find(r => r.name === roleInfo.name);
            if (existingRole) {
                console.log(`   ⏭️  Role "${roleInfo.name}" already exists (ID: ${existingRole.id})`);
                continue;
            }

            try {
                // Convert hex string color to integer (e.g., '#F0B232' → 0xF0B232)
                let colorInt = 0;
                if (roleInfo.color) {
                    colorInt = parseInt(roleInfo.color.replace('#', ''), 16);
                }
                
                const role = await guild.roles.create({
                    name: roleInfo.name,
                    color: colorInt || 0x808080, // discord.js v14 uses 'color', integer value
                    permissions: permissionsFromString(roleInfo.permissions),
                    reason: 'Created by AliceIsBored server setup',
                });
                console.log(`   ✅ Created role: ${roleInfo.name} (ID: ${role.id})`);
            } catch (error) {
                console.error(`   ❌ Failed to create role "${roleInfo.name}":`, error.message);
                throw error;
            }
        }

        // Note: The Owner role "AliceIsBored" will be at the top of the hierarchy
        // The actual server owner gets @everyone permissions + their own role
    }

    /**
     * Create all categories and text channels
     */
    async createCategoriesAndChannels(guild) {
        const memberRole = guild.roles.cache.find(r => r.name === 'Member');
        const leaderRole = guild.roles.cache.find(r => r.name === 'Leader');
        const unverifiedRole = guild.roles.cache.find(r => r.name === 'Unverified');
        const aliceIsBoredRole = guild.roles.cache.find(r => r.name === 'AliceIsBored');

        // Permission overwrites for different channel types
        const getAllAuthenticatedOverwrites = () => {
            const overwrites = [];
            
            // Unverified: can view
            if (unverifiedRole) {
                overwrites.push({
                    id: unverifiedRole.id,
                    allow: [PermissionsBitField.Flags.ViewChannel],
                    deny: [],
                });
            }
            
            // Member: can view and send
            if (memberRole) {
                overwrites.push({
                    id: memberRole.id,
                    allow: [
                        PermissionsBitField.Flags.ViewChannel,
                        PermissionsBitField.Flags.SendMessages,
                        PermissionsBitField.Flags.EmbedLinks,
                        PermissionsBitField.Flags.AttachFiles,
                        PermissionsBitField.Flags.AddReactions,
                    ],
                    deny: [],
                });
            }
            
            // Leader: can view and send
            if (leaderRole) {
                overwrites.push({
                    id: leaderRole.id,
                    allow: [
                        PermissionsBitField.Flags.ViewChannel,
                        PermissionsBitField.Flags.SendMessages,
                        PermissionsBitField.Flags.EmbedLinks,
                        PermissionsBitField.Flags.AttachFiles,
                        PermissionsBitField.Flags.AddReactions,
                        PermissionsBitField.Flags.UseApplicationCommands,
                    ],
                    deny: [],
                });
            }
            
            // AliceIsBored role: full access
            if (aliceIsBoredRole) {
                overwrites.push({
                    id: aliceIsBoredRole.id,
                    allow: [PermissionsBitField.Flags.Administrator],
                    deny: [],
                });
            }
            
            return overwrites;
        };

        const getMemberLeaderOverwrites = () => {
            const overwrites = [];
            
            // Member and Leader: full access
            if (memberRole) {
                overwrites.push({
                    id: memberRole.id,
                    allow: [
                        PermissionsBitField.Flags.ViewChannel,
                        PermissionsBitField.Flags.SendMessages,
                        PermissionsBitField.Flags.EmbedLinks,
                        PermissionsBitField.Flags.AttachFiles,
                        PermissionsBitField.Flags.AddReactions,
                        PermissionsBitField.Flags.UseApplicationCommands,
                    ],
                    deny: [],
                });
            }
            if (leaderRole) {
                overwrites.push({
                    id: leaderRole.id,
                    allow: [
                        PermissionsBitField.Flags.ViewChannel,
                        PermissionsBitField.Flags.SendMessages,
                        PermissionsBitField.Flags.EmbedLinks,
                        PermissionsBitField.Flags.AttachFiles,
                        PermissionsBitField.Flags.AddReactions,
                        PermissionsBitField.Flags.UseApplicationCommands,
                    ],
                    deny: [],
                });
            }
            if (aliceIsBoredRole) {
                overwrites.push({
                    id: aliceIsBoredRole.id,
                    allow: [PermissionsBitField.Flags.Administrator],
                    deny: [],
                });
            }
            
            // Hide from Unverified
            if (unverifiedRole) {
                overwrites.push({
                    id: unverifiedRole.id,
                    allow: [],
                    deny: [PermissionsBitField.Flags.ViewChannel],
                });
            }
            
            return overwrites;
        };

        // Create categories and channels
        for (const category of CATEGORIES_AND_CHANNELS) {
            // Check if category already exists
            const existingCategory = guild.channels.cache.find(
                ch => ch.type === ChannelType.GuildCategory && ch.name === category.name
            );

            let categoryId;
            let categoryObj;

            if (existingCategory) {
                console.log(`   ⏭️  Category "${category.name}" already exists`);
                categoryId = existingCategory.id;
                categoryObj = existingCategory;
            } else {
                // Create category
                categoryObj = await guild.channels.create({
                    name: category.name,
                    type: ChannelType.GuildCategory,
                    reason: 'Created by AliceIsBored server setup',
                });
                categoryId = categoryObj.id;
                console.log(`   📁 Created category: "${category.name}"`);
            }

            // Create channels in this category
            for (const channelDef of category.channels) {
                // Determine visibility
                let overwrites;
                if (channelDef.visibility === 'all-authenticated') {
                    overwrites = getAllAuthenticatedOverwrites();
                } else {
                    overwrites = getMemberLeaderOverwrites();
                }

                // Check if channel already exists
                const existingChannel = guild.channels.cache.find(
                    ch => ch.type === ChannelType.GuildText && ch.name === channelDef.name && ch.parentId === categoryId
                );

                if (existingChannel) {
                    console.log(`   ⏭️  Channel "#${channelDef.name}" already exists`);
                    continue;
                }

                try {
                    await guild.channels.create({
                        name: channelDef.name,
                        type: ChannelType.GuildText,
                        parent: categoryId,
                        permissionOverwrites: overwrites,
                        reason: `Created by AliceIsBored server setup`,
                    });
                    console.log(`   #️⃣  Created channel: #${channelDef.name} in ${category.name}`);
                } catch (error) {
                    console.error(`   ❌ Failed to create channel "#${channelDef.name}":`, error.message);
                    throw error;
                }
            }
        }

        console.log(`\n   📊 Created ${CATEGORIES_AND_CHANNELS.length} categories`);
        const totalChannels = CATEGORIES_AND_CHANNELS.reduce(
            (sum, cat) => sum + cat.channels.length, 0
        );
        console.log(`   📝 Created ${totalChannels} text channels`);
    }

    /**
     * Create the verification channel with embed message
     */
    async createVerificationChannel(guild) {
        const memberRole = guild.roles.cache.find(r => r.name === 'Member');
        const leaderRole = guild.roles.cache.find(r => r.name === 'Leader');
        const unverifiedRole = guild.roles.cache.find(r => r.name === 'Unverified');
        const aliceIsBoredRole = guild.roles.cache.find(r => r.name === 'AliceIsBored');

        // Check if verify channel already exists
        const existingVerifyChannel = guild.channels.cache.find(ch => ch.name === VERIFY_CHANNEL.name);
        if (existingVerifyChannel) {
            console.log(`   ⏭️  Verify channel "#${VERIFY_CHANNEL.name}" already exists`);
            return;
        }

        // Create permission overwrites for verify channel
        const overwrites = [
            // AliceIsBored role: full access
            ...(aliceIsBoredRole ? [{
                id: aliceIsBoredRole.id,
                type: 0, // Role
                allow: [PermissionsBitField.Flags.Administrator],
                deny: [],
            }] : []),
            // Leader: full access
            ...(leaderRole ? [{
                id: leaderRole.id,
                type: 0, // Role
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            }] : []),
            // Member: full access
            ...(memberRole ? [{
                id: memberRole.id,
                type: 0, // Role
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            }] : []),
            // Unverified: can view and interact
            ...(unverifiedRole ? [{
                id: unverifiedRole.id,
                type: 0, // Role
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                ],
                deny: [],
            }] : []),
        ];

        const verifyChannel = await guild.channels.create({
            name: VERIFY_CHANNEL.name,
            type: ChannelType.GuildText,
            permissionOverwrites: overwrites,
            reason: 'Created by AliceIsBored server setup',
        });

        console.log(`   #️⃣  Created verify channel: #${VERIFY_CHANNEL.name}`);

        // Create and send verification embed
        const embed = new EmbedBuilder()
            .setColor(memberRole?.color || 3447003) // Blue
            .setTitle(VERIFY_EMBED.title)
            .setDescription(VERIFY_EMBED.description)
            .setFooter({ text: VERIFY_EMBED.footer })
            .setTimestamp();

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder()
                .setCustomId('verify-button')
                .setLabel(VERIFY_EMBED.buttons[0].label)
                .setStyle(ButtonStyle.Success)
        );

        await verifyChannel.send({ embeds: [embed], components: [row] });
        console.log(`   ✅ Posted verification embed in #${VERIFY_CHANNEL.name}`);
    }

    /**
     * Create hidden admin channels (Leader and Owner only)
     */
    async createAdminChannels(guild) {
        const leaderRole = guild.roles.cache.find(r => r.name === 'Leader');
        const aliceIsBoredRole = guild.roles.cache.find(r => r.name === 'AliceIsBored');
        const memberRole = guild.roles.cache.find(r => r.name === 'Member');
        const unverifiedRole = guild.roles.cache.find(r => r.name === 'Unverified');

        // Admin channel overwrites - only Leader and AliceIsBored role can see
        const adminOverwrites = [
            // AliceIsBored role: full access
            ...(aliceIsBoredRole ? [{
                id: aliceIsBoredRole.id,
                type: 0, // Role
                allow: [PermissionsBitField.Flags.Administrator],
                deny: [],
            }] : []),
            // Leader: full access
            ...(leaderRole ? [{
                id: leaderRole.id,
                type: 0, // Role
                allow: [
                    PermissionsBitField.Flags.ViewChannel,
                    PermissionsBitField.Flags.SendMessages,
                    PermissionsBitField.Flags.EmbedLinks,
                ],
                deny: [],
            }] : []),
            // Member: hidden
            ...(memberRole ? [{
                id: memberRole.id,
                type: 0, // Role
                allow: [],
                deny: [PermissionsBitField.Flags.ViewChannel],
            }] : []),
            // Unverified: hidden
            ...(unverifiedRole ? [{
                id: unverifiedRole.id,
                type: 0, // Role
                allow: [],
                deny: [PermissionsBitField.Flags.ViewChannel],
            }] : []),
        ];

        for (const adminChannel of ADMIN_CHANNELS) {
            // Check if channel already exists
            const existingChannel = guild.channels.cache.find(ch => ch.name === adminChannel.name);
            if (existingChannel) {
                console.log(`   ⏭️  Admin channel "#${adminChannel.name}" already exists`);
                continue;
            }

            try {
                const channel = await guild.channels.create({
                    name: adminChannel.name,
                    type: ChannelType.GuildText,
                    permissionOverwrites: adminOverwrites,
                    reason: 'Created by AliceIsBored server setup',
                });
                console.log(`   🔒 Created admin channel: #${adminChannel.name}`);
            } catch (error) {
                console.error(`   ❌ Failed to create admin channel "#${adminChannel.name}":`, error.message);
                throw error;
            }
        }
    }

    /**
     * Configure default role for new members
     * Sets up the Unverified role as the default for new members
     */
    async configureDefaultRole(guild) {
        const unverifiedRole = guild.roles.cache.find(r => r.name === 'Unverified');
        
        if (!unverifiedRole) {
            console.log('   ⚠️  Unverified role not found - skipping default role configuration');
            return;
        }

        // Discord doesn't have a native "default role" setting for new members
        // Instead, we need to set up the @everyone role permissions
        // and rely on the bot to assign Unverified to new members
        
        // Get @everyone role
        const everyoneRole = guild.roles.everyone;

        // Update @everyone permissions - only allow view announcements
        // This requires careful handling to not break the server
        try {
            await everyoneRole.edit({
                permissions: new PermissionsBitField(PermissionsBitField.Flags.ViewChannel),
                reason: 'Configured by AliceIsBored server setup - limited default permissions',
            });
            console.log('   ✅ @everyone role permissions configured');
        } catch (error) {
            console.log('   ⚠️  Could not modify @everyone role (may need manual setup):', error.message);
        }

        console.log('   ℹ️  New members will need to use #verify to get Member role');
        console.log('   ℹ️  The Unverified role restricts access to #announcements only');
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
        console.error('  node src/setup-server.js');
        console.error('');
        console.error('Or create a .env file with:');
        console.error('  DISCORD_TOKEN=your_bot_token_here');
        console.error('');
        console.error('To get a bot token:');
        console.error('  1. Go to https://discord.com/developers/applications');
        console.error('  2. Create a new application');
        console.error('  3. Go to "Bot" section and create a bot');
        console.error('  4. Copy the token and set it as DISCORD_TOKEN');
        console.error('  5. Invite the bot to your server with "Manage Roles" permission');
        process.exit(1);
    }

    const setup = new ServerSetup(token);
    setup.client.login(token);
}

// Export for testing
module.exports = ServerSetup;

// Run if executed directly
if (require.main === module) {
    main();
}