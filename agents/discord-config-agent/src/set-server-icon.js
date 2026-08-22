const { Client, GatewayIntentBits } = require('discord.js');
const { createCanvas } = require('canvas');

const DISCORD_TOKEN = process.env.DISCORD_TOKEN;

if (!DISCORD_TOKEN) {
  console.error('DISCORD_TOKEN not found in .env file');
  process.exit(1);
}

const client = new Client({});

function generateServerIcon() {
  const size = 512; // Discord requires 512x512 for best quality
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background - dark green (Clash of Clans theme)
  ctx.fillStyle = '#2d5a27';
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
  ctx.fill();

  // Inner border - gold ring
  ctx.strokeStyle = '#f0c848';
  ctx.lineWidth = 12;
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2 - 8, 0, Math.PI * 2);
  ctx.stroke();

  // Castle tower - base
  ctx.fillStyle = '#8b7355';
  ctx.fillRect(size / 2 - 60, size / 2 - 20, 120, 160);

  // Castle tower - top (battlement)
  ctx.fillStyle = '#8b7355';
  for (let i = 0; i < 5; i++) {
    ctx.fillRect(size / 2 - 65 + i * 30, size / 2 - 70, 20, 30);
  }

  // Castle tower - door
  ctx.fillStyle = '#4a3728';
  ctx.beginPath();
  ctx.arc(size / 2, size / 2 + 110, 25, Math.PI, 0);
  ctx.fillRect(size / 2 - 25, size / 2 + 110, 50, 35);
  ctx.fill();

  // Flag on top
  ctx.strokeStyle = '#555';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(size / 2, size / 2 - 70);
  ctx.lineTo(size / 2, size / 2 - 110);
  ctx.stroke();

  // Flag - red
  ctx.fillStyle = '#e74c3c';
  ctx.beginPath();
  ctx.moveTo(size / 2, size / 2 - 110);
  ctx.lineTo(size / 2 + 40, size / 2 - 95);
  ctx.lineTo(size / 2, size / 2 - 80);
  ctx.fill();

  // Text - "AliceIsBored"
  ctx.fillStyle = '#f0c848';
  ctx.font = 'bold 36px Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.strokeStyle = '#1a1a1a';
  ctx.lineWidth = 4;
  ctx.strokeText('AliceIsBored', size / 2, size / 2 + 180);
  ctx.fillText('AliceIsBored', size / 2, size / 2 + 180);

  // Subtitle - "Clash of Clans"
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 22px Arial, sans-serif';
  ctx.strokeStyle = '#1a1a1a';
  ctx.lineWidth = 3;
  ctx.strokeText('Clash of Clans', size / 2, size / 2 + 215);
  ctx.fillText('Clash of Clans', size / 2, size / 2 + 215);

  return canvas.toBuffer('image/png');
}

async function setServerIcon() {
  try {
    await client.login(DISCORD_TOKEN);

    // Wait for ready
    await new Promise((resolve) => {
      client.once('clientReady', (c) => {
        console.log(`Logged in as ${c.user.tag}`);
        resolve();
      });
    });

    // Get the AliceIsBored server
    const targetGuildId = '1528452897564655636';
    let guild = client.guilds.cache.get(targetGuildId);

    if (!guild) {
      console.log(`Guild ${targetGuildId} not cached, fetching...`);
      try {
        guild = await client.guilds.fetch(targetGuildId);
      } catch (error) {
        console.error(`Failed to fetch guild ${targetGuildId}:`, error.message);
        process.exit(1);
      }
    }

    console.log(`Using guild: ${guild.name} (${guild.id})`);
    await setIconOnGuild(guild);
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

async function setIconOnGuild(guild) {
  console.log(`Setting icon for server: ${guild.name}`);

  const iconBuffer = generateServerIcon();

  try {
    await guild.setIcon(iconBuffer, 'AliceIsBored clan icon');
    console.log('✅ Server icon set successfully!');
  } catch (error) {
    console.error('Failed to set server icon:', error.message);
  }

  client.destroy();
}

setServerIcon();