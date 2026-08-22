// Discord Bot Configuration for AliceIsBored Clan
// This file defines all server configuration constants

/**
 * Server configuration settings
 */
const SERVER_CONFIG = {
    serverName: 'AliceIsBored',
    serverDescription: 'Clash of Clans clan — AliceIsBored',
    verificationLevel: 'Medium', // None, Low, Medium, High, Very high
    defaultRole: 'Unverified',
};

/**
 * Role definitions with their permissions and hierarchy
 * Note: Roles are created bottom-to-top in hierarchy
 */
const ROLES = {
    UNVERIFIED: {
        name: 'Unverified',
        color: '#8095A5', // Grey
        permissions: [],
        isDefault: true,
    },
    MEMBER: {
        name: 'Member',
        color: '#344703', // Blue
        permissions: [
            'SendMessages',
            'EmbedLinks',
            'AttachFiles',
            'ReadMessageHistory',
            'AddReactions',
        ],
    },
    LEADER: {
        name: 'Leader',
        color: '#F0B232', // Gold
        permissions: [
            'KickMembers',
            'BanMembers',
            'ManageChannels',
            'ManageRoles',
            'ManageMessages',
            'SendMessages',
            'EmbedLinks',
            'AttachFiles',
            'ReadMessageHistory',
            'AddReactions',
            'UseApplicationCommands',
        ],
    },
    OWNER: {
        name: 'AliceIsBored',
        color: '#E74C3C', // Red
        permissions: [], // Will be set to all
    },
};

/**
 * Role hierarchy order (highest to lowest)
 */
const ROLE_HIERARCHY = ['OWNER', 'LEADER', 'MEMBER', 'UNVERIFIED'];

/**
 * Channel type constants
 */
const CHANNEL_TYPES = {
    TEXT: 'GuildText',
};

/**
 * Permission overwrite structure for channels
 */
const PERMISSION_OVERWRITES = {
    VIEW_CHANNEL: 'ViewChannel',
    SEND_MESSAGES: 'SendMessages',
    EMBED_LINKS: 'EmbedLinks',
};

/**
 * Categories and their channels
 * Each category contains an array of channel definitions
 */
const CATEGORIES_AND_CHANNELS = [
    {
        name: '📢 Information',
        channels: [
            {
                name: 'announcements',
                type: CHANNEL_TYPES.TEXT,
                description: 'Leader announcements, bot updates',
                visibility: 'all-authenticated', // visible to all authenticated
            },
            {
                name: 'rules',
                type: CHANNEL_TYPES.TEXT,
                description: 'Server rules and guidelines',
                visibility: 'all-authenticated',
            },
        ],
    },
    {
        name: '🎮 Clan Activity',
        channels: [
            {
                name: 'general',
                type: CHANNEL_TYPES.TEXT,
                description: 'Main clan chat',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'war-chat',
                type: CHANNEL_TYPES.TEXT,
                description: 'CWL war coordination and discussion',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'war-updates',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: CWL war starts, results, predictions',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'raid-chat',
                type: CHANNEL_TYPES.TEXT,
                description: 'Weekend raid coordination',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'raid-updates',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: raid starts, contributions, results',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'clan-games',
                type: CHANNEL_TYPES.TEXT,
                description: 'Clan Games choices and coordination',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'clan-games-updates',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: Clan Games start, progress, points',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'capital-raids',
                type: CHANNEL_TYPES.TEXT,
                description: 'Clan Capital coordination',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'capital-updates',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: Capital raid nights, contributions',
                visibility: ['Leader', 'Member'],
            },
        ],
    },
    {
        name: '📊 Statistics',
        channels: [
            {
                name: 'leaderboards',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: weekly top attackers, donors',
                visibility: ['Leader', 'Member'],
            },
            {
                name: 'scores',
                type: CHANNEL_TYPES.TEXT,
                description: 'Bot auto-postings: member scoring updates',
                visibility: ['Leader', 'Member'],
            },
        ],
    },
    {
        name: '🤖 Bot Commands',
        channels: [
            {
                name: 'bot-commands',
                type: CHANNEL_TYPES.TEXT,
                description: 'Dedicated channel for bot slash commands',
                visibility: ['Leader', 'Member'],
            },
        ],
    },
];

/**
 * Verification channel configuration
 */
const VERIFY_CHANNEL = {
    name: 'verify',
    type: CHANNEL_TYPES.TEXT,
    description: 'Bot verification flow (embed with buttons)',
    visibility: 'all-authenticated',
};

/**
 * Hidden admin channels (Leader and Owner only)
 */
const ADMIN_CHANNELS = [
    {
        name: 'admin-log',
        type: CHANNEL_TYPES.TEXT,
        description: 'Bot admin log (war changes, member joins/leaves, verification events)',
    },
    {
        name: 'admin-settings',
        type: CHANNEL_TYPES.TEXT,
        description: 'Bot configuration commands',
    },
];

/**
 * Bot permissions required
 */
const BOT_PERMISSIONS = [
    'SendMessages',
    'EmbedLinks',
    'ManageRoles',
    'ReadMessageHistory',
    'ManageChannels',
    'UseSlashCommands',
    'AddReactions',
    'AttachFiles',
    'QuietThread',
];

/**
 * Verification embed message configuration
 */
const VERIFY_EMBED = {
    title: '🔐 Verify Yourself',
    description: 'Welcome to **AliceIsBored**! To access all channels, please verify your membership by clicking the button below.',
    color: 'Blue',
    footer: 'AliceIsBored Clan Discord Bot',
    buttons: [
        { label: '✅ Verify', style: 'Success' },
    ],
};

/**
 * Acceptance criteria checklist
 */
const ACCEPTANCE_CRITERIA = [
    'Discord server exists with name "AliceIsBored"',
    'Server description set to "Clash of Clans clan — AliceIsBored"',
    'Server icon set (bored Alice illustration)',
    '4 categories created: Information, Clan Activity, Statistics, Bot Commands',
    '13 text channels created across categories',
    '4 roles created with proper hierarchy',
    '#announcements visible to all authenticated members',
    '#general, #war-chat, #raid-chat, #clan-games hidden from Unverified',
    '#admin-log and #admin-settings hidden from Member and Unverified',
    '#verify channel has bot verification embed',
    'Bot token configured with proper permissions',
];

module.exports = {
    SERVER_CONFIG,
    ROLES,
    ROLE_HIERARCHY,
    CHANNEL_TYPES,
    PERMISSION_OVERWRITES,
    CATEGORIES_AND_CHANNELS,
    VERIFY_CHANNEL,
    ADMIN_CHANNELS,
    BOT_PERMISSIONS,
    VERIFY_EMBED,
    ACCEPTANCE_CRITERIA,
};