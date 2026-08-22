const { Client, GatewayIntentBits, Events, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder } = require('discord.js');
const { 
    SERVER_CONFIG, 
    BOT_PERMISSIONS, 
    VERIFY_EMBED,
    ROLES 
} = require('./config');

/**
 * AliceIsBored Discord Bot
 * Main bot entry point for the Clash of Clans clan server
 */
class AliceIsBoredBot {
    constructor(token) {
        this.token = token;
        
        // Initialize Discord client with required intents
        this.client = new Client({
            intents: [
                GatewayIntentBits.Guilds,
                GatewayIntentBits.GuildMembers,
                GatewayIntentBits.GuildMessages,
                GatewayIntentBits.MessageContent,
                GatewayIntentBits.GuildMessages,
            ],
        });

        this.registerEventListeners();
    }

    /**
     * Register all event listeners
     */
    registerEventListeners() {
        // Ready event
        this.client.once(Events.ClientReady, (client) => {
            console.log(`✅ Logged in as ${client.user.tag}`);
            console.log(`📡 Connected to ${client.guilds.cache.size} guild(s)`);
            this.client.user.setPresence({
                status: 'online',
                activity: {
                    name: '!help | Clash of Clans',
                    type: 3, // Playing
                },
            });
        });

        // Slash command interaction
        this.client.on(Events.InteractionCreate, this.handleInteraction.bind(this));

        // Message creation for basic commands
        this.client.on(Events.MessageCreate, this.handleMessage.bind(this));

        // Guild join handler
        this.client.on(Events.GuildCreate, this.handleGuildCreate.bind(this));

        // Error handling
        this.client.on(Events.Error, (error) => {
            console.error('❌ Bot error:', error);
        });

        // Warning handling
        this.client.on(Events.Warn, (warning) => {
            console.warn('⚠️ Bot warning:', warning);
        });
    }

    /**
     * Handle interactions (slash commands, buttons)
     */
    async handleInteraction(interaction) {
        try {
            // Handle button clicks
            if (interaction.isButton()) {
                await this.handleButtonInteraction(interaction);
                return;
            }

            // Handle slash commands
            if (interaction.isChatInputCommand()) {
                await this.handleSlashCommand(interaction);
                return;
            }
        } catch (error) {
            console.error('❌ Interaction error:', error);
            if (!interaction.replied && !interaction.deferred) {
                await interaction.reply({ 
                    content: '❌ An error occurred while processing your request.',
                    ephemeral: true 
                }).catch(() => {});
            }
        }
    }

    /**
     * Handle button interactions
     */
    async handleButtonInteraction(interaction) {
        const customId = interaction.customId;

        switch (customId) {
            case 'verify-button':
                await this.handleVerifyButton(interaction);
                break;

            default:
                await interaction.reply({
                    content: '❓ This button is not configured yet.',
                    ephemeral: true
                }).catch(() => {});
                break;
        }
    }

    /**
     * Handle the verification button click
     */
    async handleVerifyButton(interaction) {
        const member = interaction.member;
        const guild = member.guild;

        try {
            // Get or create the Member role
            let memberRole = guild.roles.cache.find(r => r.name === ROLES.MEMBER.name);
            if (!memberRole) {
                memberRole = await guild.roles.create({
                    name: ROLES.MEMBER.name,
                    color: ROLES.MEMBER.color,
                    permissions: ROLES.MEMBER.permissions,
                    reason: 'Created by AliceIsBored bot during verification',
                });
            }

            // Remove Unverified role and add Member role
            const unverifiedRole = guild.roles.cache.find(r => r.name === ROLES.UNVERIFIED.name);
            if (unverifiedRole) {
                await member.roles.remove(unverifiedRole, 'Verification complete');
            }
            await member.roles.add(memberRole, 'Verification complete');

            // Send success message
            await interaction.reply({
                content: `✅ Welcome to **${guild.name}**, ${member.user}! You now have access to all channels.`,
                ephemeral: true
            });

            // Log to admin-log channel if available
            await this.logToAdminChannel(guild, `✅ ${member.user} (${member.id}) verified successfully`);

        } catch (error) {
            console.error('❌ Verification error:', error);
            await interaction.reply({
                content: '❌ Verification failed. Please check if the bot has proper permissions.',
                ephemeral: true
            });
        }
    }

    /**
     * Handle slash commands
     */
    async handleSlashCommand(interaction) {
        const { commandName, guild } = interaction;

        const commands = {
            help: this.handleHelp.bind(this),
            status: this.handleStatus.bind(this),
            roles: this.handleRoles.bind(this),
        };

        const handler = commands[commandName];
        if (handler) {
            await handler(interaction);
        } else {
            await interaction.reply({
                content: '❓ Unknown command. Use `/help` to see available commands.',
                ephemeral: true
            });
        }
    }

    /**
     * Help command handler
     */
    async handleHelp(interaction) {
        const embed = new EmbedBuilder()
            .setColor('Blue')
            .setTitle('🤖 AliceIsBored Bot Commands')
            .setDescription('Available commands for the clan server:')
            .addFields(
                { name: '/help', value: 'Show this help message', inline: false },
                { name: '/status', value: 'Show bot and server status', inline: false },
                { name: '/roles', value: 'Show available roles and permissions', inline: false },
            )
            .setFooter({ text: 'AliceIsBored Clan • Clash of Clans' });

        await interaction.reply({ embeds: [embed] });
    }

    /**
     * Status command handler
     */
    async handleStatus(interaction) {
        const guild = interaction.guild;
        const botMember = guild.members.cache.get(this.client.user.id);
        
        const embed = new EmbedBuilder()
            .setColor('Green')
            .setTitle(`📊 ${guild.name} Status`)
            .addFields(
                { name: '👥 Members', value: `${guild.memberCount.toLocaleString()}`, inline: true },
                { name: '📝 Channels', value: `${guild.channels.cache.size}`, inline: true },
                { name: '🎭 Roles', value: `${guild.roles.cache.size}`, inline: true },
                { name: '🤖 Bot Latency', value: `${this.client.ws.ping}ms`, inline: true },
                { name: '📅 Server Created', value: `<t:${Math.floor(guild.createdTimestamp / 1000)}:R>`, inline: true },
                { name: '🔗 Verification Level', value: SERVER_CONFIG.verificationLevel, inline: true },
            )
            .setThumbnail(guild.iconURL())
            .setFooter({ text: 'AliceIsBored Clan • Clash of Clans' });

        await interaction.reply({ embeds: [embed] });
    }

    /**
     * Roles command handler
     */
    async handleRoles(interaction) {
        const embed = new EmbedBuilder()
            .setColor('Purple')
            .setTitle('🎭 AliceIsBored Server Roles')
            .setDescription('Role hierarchy and permissions:')
            .addFields(
                { 
                    name: `👑 ${ROLES.OWNER.name}`, 
                    value: 'Server Owner — Full administrative access to all channels and features', 
                    inline: false 
                },
                { 
                    name: `⚔️ ${ROLES.LEADER.name}`, 
                    value: `Leader — Manage server, kick/ban members, manage channels\nPermissions: ${ROLES.LEADER.permissions.slice(0, 5).join(', ')}${ROLES.LEADER.permissions.length > 5 ? '...' : ''}`, 
                    inline: false 
                },
                { 
                    name: `🛡️ ${ROLES.MEMBER.name}`, 
                    value: `Member — Full access to clan activity channels\nPermissions: ${ROLES.MEMBER.permissions.join(', ')}`, 
                    inline: false 
                },
                { 
                    name: `⏳ ${ROLES.UNVERIFIED.name}`, 
                    value: 'Unverified — Limited to viewing announcements only. Complete verification to access more channels.', 
                    inline: false 
                },
            )
            .setFooter({ text: 'AliceIsBored Clan • Clash of Clans' });

        await interaction.reply({ embeds: [embed] });
    }

    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        // Bot shouldn't respond to its own messages
        if (message.author.bot) return;

        // Only process messages in guilds
        if (!message.guild) return;
    }

    /**
     * Handle new guild joins
     */
    async handleGuildCreate(guild) {
        console.log(`✅ Joined new guild: ${guild.name} (${guild.id})`);
    }

    /**
     * Log a message to the admin-log channel
     */
    async logToAdminChannel(guild, message) {
        try {
            const adminLogChannel = guild.channels.cache.find(
                ch => ch.name === 'admin-log' && ch.type === 0
            );
            if (adminLogChannel) {
                await adminLogChannel.send({
                    content: `📋 **Admin Log**\n${message}`,
                });
            }
        } catch (error) {
            console.error('Error logging to admin channel:', error);
        }
    }

    /**
     * Start the bot
     */
    async start() {
        try {
            if (!this.token) {
                throw new Error('Discord token is required. Set DISCORD_TOKEN environment variable.');
            }
            await this.client.login(this.token);
        } catch (error) {
            console.error('❌ Failed to start bot:', error.message);
            process.exit(1);
        }
    }
}

/**
 * Main entry point
 */
function main() {
    const token = process.env.DISCORD_TOKEN;
    
    if (!token) {
        console.error('❌ DISCORD_TOKEN environment variable is required');
        console.error('Please create a .env file with: DISCORD_TOKEN=your_bot_token_here');
        console.error('Or set it directly: export DISCORD_TOKEN=your_bot_token_here');
        process.exit(1);
    }

    const bot = new AliceIsBoredBot(token);
    bot.start();
}

// Export for testing
module.exports = AliceIsBoredBot;

// Run if executed directly
if (require.main === module) {
    main();
}