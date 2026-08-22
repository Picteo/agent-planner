const { Client, GatewayIntentBits } = require('discord.js');
const { createCanvas } = require('canvas');

const DISCORD_TOKEN = process.env.DISCORD_TOKEN;

if (!DISCORD_TOKEN) {
  console.error('DISCORD_TOKEN not found in .env file');
  process.exit(1);
}

const TARGET_GUILD_ID = '1528452897564655636';

const client = new Client({
  intents: [GatewayIntentBits.Guilds]
});

function generateBanner() {
  const width = 1024;
  const height = 256;
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');

  // === BACKGROUND - Wonderland Forest Scene ===
  const skyGrad = ctx.createLinearGradient(0, 0, 0, height);
  skyGrad.addColorStop(0, '#1a0a2e'); // Dark purple sky
  skyGrad.addColorStop(0.3, '#2d1b69');
  skyGrad.addColorStop(0.6, '#4a2c8a');
  skyGrad.addColorStop(0.8, '#6b8fbf'); // Horizon light
  skyGrad.addColorStop(1, '#87CEEB');
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, width, height);

  // Stars
  const starPositions = [
    [50, 20], [120, 45], [180, 15], [250, 55], [320, 30],
    [400, 10], [480, 50], [550, 25], [620, 60], [700, 15],
    [780, 40], [850, 20], [920, 55], [980, 35], [100, 70],
    [300, 75], [500, 65], [700, 70], [870, 60], [150, 85],
    [650, 80], [800, 90], [220, 95], [440, 85], [950, 75]
  ];
  ctx.fillStyle = '#fff';
  starPositions.forEach(([x, y]) => {
    ctx.beginPath();
    ctx.arc(x, y, Math.random() * 1.5 + 0.5, 0, Math.PI * 2);
    ctx.fill();
  });

  // Moon
  ctx.fillStyle = '#FFF8DC';
  ctx.beginPath();
  ctx.arc(850, 50, 35, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#1a0a2e';
  ctx.beginPath();
  ctx.arc(862, 42, 30, 0, Math.PI * 2);
  ctx.fill();

  // Moon glow
  const moonGlow = ctx.createRadialGradient(850, 50, 20, 850, 50, 80);
  moonGlow.addColorStop(0, 'rgba(255, 248, 220, 0.3)');
  moonGlow.addColorStop(1, 'rgba(255, 248, 220, 0)');
  ctx.fillStyle = moonGlow;
  ctx.beginPath();
  ctx.arc(850, 50, 80, 0, Math.PI * 2);
  ctx.fill();

  // Ground/hills
  const groundGrad = ctx.createLinearGradient(0, 160, 0, height);
  groundGrad.addColorStop(0, '#2d5a27');
  groundGrad.addColorStop(1, '#1a3a15');
  ctx.fillStyle = groundGrad;
  ctx.beginPath();
  ctx.moveTo(0, 180);
  ctx.quadraticCurveTo(200, 150, 400, 170);
  ctx.quadraticCurveTo(600, 190, 800, 165);
  ctx.quadraticCurveTo(950, 155, 1024, 175);
  ctx.lineTo(1024, height);
  ctx.lineTo(0, height);
  ctx.closePath();
  ctx.fill();

  // Grass details
  ctx.strokeStyle = '#3d7a32';
  ctx.lineWidth = 2;
  for (let i = 0; i < 1024; i += 8) {
    const grassH = Math.random() * 10 + 5;
    ctx.beginPath();
    ctx.moveTo(i, 190 + Math.sin(i * 0.02) * 10);
    ctx.quadraticCurveTo(i + 2, 190 - grassH + Math.sin(i * 0.02) * 10, i + 4, 190 + Math.sin(i * 0.02) * 10);
    ctx.stroke();
  }

  // Mushrooms
  function drawMushroom(x, y, size, color) {
    // Stem
    ctx.fillStyle = '#F5F5DC';
    ctx.fillRect(x - size * 0.15, y - size * 0.5, size * 0.3, size * 0.5);
    // Cap
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.ellipse(x, y - size * 0.5, size * 0.4, size * 0.25, 0, Math.PI, 0);
    ctx.fill();
    // Spots
    ctx.fillStyle = '#FFF';
    ctx.beginPath();
    ctx.arc(x - size * 0.1, y - size * 0.6, size * 0.06, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x + size * 0.12, y - size * 0.55, size * 0.05, 0, Math.PI * 2);
    ctx.fill();
  }
  drawMushroom(150, 195, 20, '#DC143C');
  drawMushroom(180, 200, 15, '#DC143C');
  drawMushroom(850, 190, 18, '#8B0000');
  drawMushroom(880, 195, 14, '#8B0000');

  // Trees in background
  function drawTree(x, y, trunkH, crownR, crownColor) {
    // Trunk
    ctx.fillStyle = '#4a3728';
    ctx.fillRect(x - 8, y - trunkH, 16, trunkH);
    // Crown
    ctx.fillStyle = crownColor;
    ctx.beginPath();
    ctx.moveTo(x, y - trunkH - crownR);
    ctx.lineTo(x - crownR, y - trunkH + crownR * 0.3);
    ctx.lineTo(x + crownR, y - trunkH + crownR * 0.3);
    ctx.closePath();
    ctx.fill();
  }
  drawTree(80, 180, 60, 35, '#1a4a1a');
  drawTree(960, 175, 50, 30, '#1a4a1a');
  drawTree(60, 170, 45, 28, '#2a5a2a');
  drawTree(980, 170, 55, 32, '#2a5a2a');

  // === MAD HATTER (Left side, yawning) ===
  function drawMadHatter(cx, cy) {
    const s = 1.0; // scale

    // Body - purple coat
    ctx.fillStyle = '#6B3FA0';
    ctx.beginPath();
    ctx.moveTo(cx - 35 * s, cy + 70 * s);
    ctx.lineTo(cx - 25 * s, cy + 20 * s);
    ctx.lineTo(cx + 25 * s, cy + 20 * s);
    ctx.lineTo(cx + 35 * s, cy + 70 * s);
    ctx.closePath();
    ctx.fill();

    // Coat buttons
    ctx.fillStyle = '#FFD700';
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.arc(cx, cy + 30 * s + i * 15 * s, 3 * s, 0, Math.PI * 2);
      ctx.fill();
    }

    // White shirt front
    ctx.fillStyle = '#FFF8DC';
    ctx.beginPath();
    ctx.moveTo(cx - 12 * s, cy + 20 * s);
    ctx.lineTo(cx, cy + 50 * s);
    ctx.lineTo(cx + 12 * s, cy + 20 * s);
    ctx.closePath();
    ctx.fill();

    // Bow tie
    ctx.fillStyle = '#DC143C';
    ctx.beginPath();
    ctx.moveTo(cx, cy + 22 * s);
    ctx.lineTo(cx - 15 * s, cy + 17 * s);
    ctx.lineTo(cx - 15 * s, cy + 27 * s);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx, cy + 22 * s);
    ctx.lineTo(cx + 15 * s, cy + 17 * s);
    ctx.lineTo(cx + 15 * s, cy + 27 * s);
    ctx.closePath();
    ctx.fill();

    // Head
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.ellipse(cx, cy, 22 * s, 25 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Hair - wild and grey
    ctx.fillStyle = '#C0C0C0';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 10 * s, 24 * s, 15 * s, 0, Math.PI, 0);
    ctx.fill();
    // Wild hair tufts
    ctx.beginPath();
    ctx.moveTo(cx - 20 * s, cy - 15 * s);
    ctx.quadraticCurveTo(cx - 35 * s, cy - 30 * s, cx - 28 * s, cy - 20 * s);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx + 18 * s, cy - 18 * s);
    ctx.quadraticCurveTo(cx + 35 * s, cy - 28 * s, cx + 30 * s, cy - 15 * s);
    ctx.fill();

    // Eyes - half-closed, tired
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.ellipse(cx - 9 * s, cy - 2 * s, 8 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 9 * s, cy - 2 * s, 8 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#4682B4';
    ctx.beginPath();
    ctx.arc(cx - 9 * s, cy - 1 * s, 4 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 9 * s, cy - 1 * s, 4 * s, 0, Math.PI * 2);
    ctx.fill();
    // Pupils
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx - 9 * s, cy - 1 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 9 * s, cy - 1 * s, 2 * s, 0, Math.PI * 2);
    ctx.fill();

    // Eyelids (bored/tired)
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.ellipse(cx - 9 * s, cy - 5 * s, 9 * s, 6 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 9 * s, cy - 5 * s, 9 * s, 6 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Eyebrows - raised in tiredness
    ctx.strokeStyle = '#C0C0C0';
    ctx.lineWidth = 2 * s;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(cx - 16 * s, cy - 12 * s);
    ctx.quadraticCurveTo(cx - 9 * s, cy - 16 * s, cx - 2 * s, cy - 11 * s);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx + 2 * s, cy - 11 * s);
    ctx.quadraticCurveTo(cx + 9 * s, cy - 16 * s, cx + 16 * s, cy - 12 * s);
    ctx.stroke();

    // Mustache
    ctx.fillStyle = '#C0C0C0';
    ctx.beginPath();
    ctx.moveTo(cx, cy + 5 * s);
    ctx.quadraticCurveTo(cx - 12 * s, cy + 10 * s, cx - 18 * s, cy + 5 * s);
    ctx.quadraticCurveTo(cx - 8 * s, cy + 8 * s, cx, cy + 8 * s);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx, cy + 5 * s);
    ctx.quadraticCurveTo(cx + 12 * s, cy + 10 * s, cx + 18 * s, cy + 5 * s);
    ctx.quadraticCurveTo(cx + 8 * s, cy + 8 * s, cx, cy + 8 * s);
    ctx.fill();

    // Yawning mouth - open wide
    ctx.fillStyle = '#8B0000';
    ctx.beginPath();
    ctx.ellipse(cx, cy + 14 * s, 10 * s, 8 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    // Tongue
    ctx.fillStyle = '#FF6B6B';
    ctx.beginPath();
    ctx.ellipse(cx, cy + 17 * s, 6 * s, 4 * s, 0, 0, Math.PI);
    ctx.fill();

    // === THE HAT (iconic oversized top hat) ===
    // Hat band
    ctx.fillStyle = '#DC143C';
    ctx.fillRect(cx - 28 * s, cy - 45 * s, 56 * s, 8 * s);

    // Hat brim
    ctx.fillStyle = '#2F1810';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 35 * s, 35 * s, 6 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Hat crown
    ctx.fillStyle = '#1a1a2e';
    ctx.beginPath();
    ctx.moveTo(cx - 22 * s, cy - 35 * s);
    ctx.lineTo(cx - 18 * s, cy - 70 * s);
    ctx.lineTo(cx + 18 * s, cy - 70 * s);
    ctx.lineTo(cx + 22 * s, cy - 35 * s);
    ctx.closePath();
    ctx.fill();

    // Hat top rim
    ctx.strokeStyle = '#FFD700';
    ctx.lineWidth = 2 * s;
    ctx.beginPath();
    ctx.ellipse(cx, cy - 70 * s, 18 * s, 4 * s, 0, 0, Math.PI * 2);
    ctx.stroke();

    // "10/10" on hat band
    ctx.fillStyle = '#FFF';
    ctx.font = `bold ${7 * s}px Arial`;
    ctx.textAlign = 'center';
    ctx.fillText('10/10', cx, cy - 39 * s);

    // Arms
    ctx.fillStyle = '#6B3FA0';
    // Left arm raised (yawning gesture)
    ctx.beginPath();
    ctx.moveTo(cx - 25 * s, cy + 25 * s);
    ctx.quadraticCurveTo(cx - 45 * s, cy + 10 * s, cx - 40 * s, cy - 10 * s);
    ctx.lineTo(cx - 32 * s, cy - 8 * s);
    ctx.quadraticCurveTo(cx - 38 * s, cy + 5 * s, cx - 22 * s, cy + 20 * s);
    ctx.fill();
    // Hand
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.arc(cx - 38 * s, cy - 10 * s, 7 * s, 0, Math.PI * 2);
    ctx.fill();

    // Right arm by side
    ctx.fillStyle = '#6B3FA0';
    ctx.beginPath();
    ctx.moveTo(cx + 25 * s, cy + 25 * s);
    ctx.quadraticCurveTo(cx + 42 * s, cy + 40 * s, cx + 38 * s, cy + 65 * s);
    ctx.lineTo(cx + 30 * s, cy + 65 * s);
    ctx.quadraticCurveTo(cx + 35 * s, cy + 40 * s, cx + 22 * s, cy + 20 * s);
    ctx.fill();
    // Hand
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.arc(cx + 36 * s, cy + 65 * s, 7 * s, 0, Math.PI * 2);
    ctx.fill();

    // Legs
    ctx.fillStyle = '#2F1810';
    ctx.fillRect(cx - 18 * s, cy + 65 * s, 12 * s, 20 * s);
    ctx.fillRect(cx + 6 * s, cy + 65 * s, 12 * s, 20 * s);

    // Shoes (one slightly off)
    ctx.fillStyle = '#1a1a1a';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy + 88 * s, 12 * s, 5 * s, -0.1, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy + 88 * s, 12 * s, 5 * s, 0.15, 0, Math.PI * 2);
    ctx.fill();
  }

  drawMadHatter(280, 100);

  // === WHITE RABBIT (Center-left, impatient, checking watch) ===
  function drawWhiteRabbit(cx, cy) {
    const s = 1.0;

    // Body - white fur
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(cx, cy + 15 * s, 30 * s, 45 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Fur texture
    ctx.strokeStyle = '#E0E0E0';
    ctx.lineWidth = 1;
    for (let i = 0; i < 15; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = Math.random() * 20 * s;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(angle) * dist, cy + 15 * s + Math.sin(angle) * dist);
      ctx.lineTo(cx + Math.cos(angle) * (dist + 5), cy + 15 * s + Math.sin(angle) * (dist + 5));
      ctx.stroke();
    }

    // Blue vest
    ctx.fillStyle = '#4169E1';
    ctx.beginPath();
    ctx.moveTo(cx - 22 * s, cy - 10 * s);
    ctx.lineTo(cx - 18 * s, cy + 35 * s);
    ctx.lineTo(cx + 18 * s, cy + 35 * s);
    ctx.lineTo(cx + 22 * s, cy - 10 * s);
    ctx.closePath();
    ctx.fill();

    // Vest buttons
    ctx.fillStyle = '#FFD700';
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.arc(cx, cy + 5 * s + i * 12 * s, 2.5 * s, 0, Math.PI * 2);
      ctx.fill();
    }

    // Head
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 45 * s, 22 * s, 25 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Ears - long and drooping (anxious)
    ctx.fillStyle = '#F5F5F5';
    // Left ear - drooping forward
    ctx.beginPath();
    ctx.ellipse(cx - 10 * s, cy - 90 * s, 7 * s, 30 * s, 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFB6C1';
    ctx.beginPath();
    ctx.ellipse(cx - 10 * s, cy - 88 * s, 4 * s, 22 * s, 0.3, 0, Math.PI * 2);
    ctx.fill();
    // Right ear - up but tense
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 95 * s, 6 * s, 32 * s, -0.15, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFB6C1';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 92 * s, 3.5 * s, 24 * s, -0.15, 0, Math.PI * 2);
    ctx.fill();

    // Eyes - wide and panicked
    ctx.fillStyle = '#FFF';
    ctx.beginPath();
    ctx.ellipse(cx - 9 * s, cy - 48 * s, 8 * s, 10 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 9 * s, cy - 48 * s, 8 * s, 10 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Irises - orange
    ctx.fillStyle = '#FF8C00';
    ctx.beginPath();
    ctx.arc(cx - 9 * s, cy - 47 * s, 5 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 9 * s, cy - 47 * s, 5 * s, 0, Math.PI * 2);
    ctx.fill();

    // Pupils - small and worried
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx - 9 * s, cy - 47 * s, 2.5 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 9 * s, cy - 47 * s, 2.5 * s, 0, Math.PI * 2);
    ctx.fill();

    // Panic lines around eyes
    ctx.strokeStyle = '#C0C0C0';
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {
      ctx.beginPath();
      ctx.moveTo(cx - 18 * s - i * 3 * s, cy - 52 * s + i * 3 * s);
      ctx.lineTo(cx - 16 * s - i * 3 * s, cy - 50 * s + i * 3 * s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx + 18 * s + i * 3 * s, cy - 52 * s + i * 3 * s);
      ctx.lineTo(cx + 16 * s + i * 3 * s, cy - 50 * s + i * 3 * s);
      ctx.stroke();
    }

    // Nose
    ctx.fillStyle = '#FFB6C1';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 38 * s, 4 * s, 3 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Whiskers
    ctx.strokeStyle = '#808080';
    ctx.lineWidth = 1;
    for (let i = -2; i <= 2; i++) {
      ctx.beginPath();
      ctx.moveTo(cx - 5 * s, cy - 36 * s + i * 3 * s);
      ctx.lineTo(cx - 30 * s, cy - 40 * s + i * 5 * s);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx + 5 * s, cy - 36 * s + i * 3 * s);
      ctx.lineTo(cx + 30 * s, cy - 40 * s + i * 5 * s);
      ctx.stroke();
    }

    // Mouth - tense line
    ctx.strokeStyle = '#808080';
    ctx.lineWidth = 1.5 * s;
    ctx.beginPath();
    ctx.moveTo(cx - 8 * s, cy - 33 * s);
    ctx.lineTo(cx + 8 * s, cy - 33 * s);
    ctx.stroke();

    // Feet - one slightly forward (ready to run)
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy + 60 * s, 12 * s, 6 * s, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 15 * s, cy + 58 * s, 13 * s, 6 * s, 0.1, 0, Math.PI * 2);
    ctx.fill();

    // === GOLDEN POCKET WATCH (Right paw) ===
    ctx.fillStyle = '#FFD700';
    ctx.beginPath();
    ctx.arc(cx + 35 * s, cy + 5 * s, 10 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFF';
    ctx.beginPath();
    ctx.arc(cx + 35 * s, cy + 5 * s, 7 * s, 0, Math.PI * 2);
    ctx.fill();
    // Watch hands - showing late time!
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1.5 * s;
    // Hour hand
    ctx.beginPath();
    ctx.moveTo(cx + 35 * s, cy + 5 * s);
    ctx.lineTo(cx + 35 * s, cy - 1 * s);
    ctx.stroke();
    // Minute hand
    ctx.beginPath();
    ctx.moveTo(cx + 35 * s, cy + 5 * s);
    ctx.lineTo(cx + 40 * s, cy + 8 * s);
    ctx.stroke();
    // Watch chain
    ctx.strokeStyle = '#FFD700';
    ctx.lineWidth = 1.5 * s;
    ctx.beginPath();
    ctx.moveTo(cx + 35 * s, cy - 5 * s);
    ctx.quadraticCurveTo(cx + 45 * s, cy - 10 * s, cx + 48 * s, cy);
    ctx.stroke();

    // Left paw waving in panic
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(cx - 32 * s, cy - 5 * s, 8 * s, 15 * s, -0.5, 0, Math.PI * 2);
    ctx.fill();

    // Sweat drops (impatient)
    ctx.fillStyle = 'rgba(135, 206, 250, 0.7)';
    ctx.beginPath();
    ctx.moveTo(cx + 22 * s, cy - 60 * s);
    ctx.quadraticCurveTo(cx + 26 * s, cy - 50 * s, cx + 22 * s, cy - 48 * s);
    ctx.quadraticCurveTo(cx + 18 * s, cy - 50 * s, cx + 22 * s, cy - 60 * s);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx + 15 * s, cy - 68 * s);
    ctx.quadraticCurveTo(cx + 18 * s, cy - 60 * s, cx + 15 * s, cy - 58 * s);
    ctx.quadraticCurveTo(cx + 12 * s, cy - 60 * s, cx + 15 * s, cy - 68 * s);
    ctx.fill();

    // "LATE!" text bubble
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.beginPath();
    ctx.roundRect(cx + 15 * s, cy - 105 * s, 50 * s, 20 * s, 5 * s);
    ctx.fill();
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = '#DC143C';
    ctx.font = `bold ${10 * s}px Arial`;
    ctx.textAlign = 'center';
    ctx.fillText('LATE!', cx + 40 * s, cy - 92 * s);
  }

  drawWhiteRabbit(500, 95);

  // === CHESHIRE CAT (Right side, bored, floating) ===
  function drawCheshireCat(cx, cy) {
    const s = 1.0;

    // Floating body - semi-transparent, striped
    ctx.globalAlpha = 0.7;

    // Body outline (fading)
    ctx.strokeStyle = '#9370DB';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);

    // Torso - floating, relaxed pose
    ctx.fillStyle = '#9370DB';
    ctx.beginPath();
    ctx.ellipse(cx, cy + 15 * s, 35 * s, 50 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Stripes
    ctx.fillStyle = '#4B0082';
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.ellipse(cx, cy - 20 * s + i * 20 * s, 30 * s, 8 * s, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.setLineDash([]);
    ctx.globalAlpha = 1.0;

    // Head
    ctx.fillStyle = '#9370DB';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 50 * s, 30 * s, 28 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Ears - pointed cat ears
    ctx.fillStyle = '#9370DB';
    // Left ear
    ctx.beginPath();
    ctx.moveTo(cx - 20 * s, cy - 70 * s);
    ctx.lineTo(cx - 30 * s, cy - 100 * s);
    ctx.lineTo(cx - 5 * s, cy - 75 * s);
    ctx.closePath();
    ctx.fill();
    // Right ear
    ctx.beginPath();
    ctx.moveTo(cx + 20 * s, cy - 70 * s);
    ctx.lineTo(cx + 30 * s, cy - 100 * s);
    ctx.lineTo(cx + 5 * s, cy - 75 * s);
    ctx.closePath();
    ctx.fill();

    // Inner ears
    ctx.fillStyle = '#FFB6C1';
    ctx.beginPath();
    ctx.moveTo(cx - 18 * s, cy - 72 * s);
    ctx.lineTo(cx - 26 * s, cy - 94 * s);
    ctx.lineTo(cx - 10 * s, cy - 76 * s);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx + 18 * s, cy - 72 * s);
    ctx.lineTo(cx + 26 * s, cy - 94 * s);
    ctx.lineTo(cx + 10 * s, cy - 76 * s);
    ctx.closePath();
    ctx.fill();

    // Eyes - half-closed, extremely bored
    // Left eye
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy - 52 * s, 10 * s, 6 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFD700';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy - 52 * s, 7 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#228B22';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy - 52 * s, 3 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy - 52 * s, 1.5 * s, 3 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Left eyelid (droopy)
    ctx.fillStyle = '#9370DB';
    ctx.beginPath();
    ctx.ellipse(cx - 12 * s, cy - 55 * s, 11 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Right eye
    ctx.fillStyle = '#FFE4C4';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 52 * s, 10 * s, 6 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFD700';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 52 * s, 7 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#228B22';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 52 * s, 3 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 52 * s, 1.5 * s, 3 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Right eyelid (droopy)
    ctx.fillStyle = '#9370DB';
    ctx.beginPath();
    ctx.ellipse(cx + 12 * s, cy - 55 * s, 11 * s, 5 * s, 0, 0, Math.PI * 2);
    ctx.fill();

    // Nose
    ctx.fillStyle = '#FF69B4';
    ctx.beginPath();
    ctx.moveTo(cx, cy - 42 * s);
    ctx.lineTo(cx - 4 * s, cy - 38 * s);
    ctx.lineTo(cx + 4 * s, cy - 38 * s);
    ctx.closePath();
    ctx.fill();

    // === THE GRIN (signature Cheshire Cat grin) ===
    ctx.fillStyle = '#FFF';
    ctx.beginPath();
    ctx.ellipse(cx, cy - 30 * s, 22 * s, 10 * s, 0, 0, Math.PI);
    ctx.fill();

    // Teeth
    ctx.fillStyle = '#FFF';
    for (let i = 0; i < 7; i++) {
      const tx = cx - 18 * s + i * 6 * s;
      ctx.fillRect(tx - 2 * s, cy - 30 * s, 4 * s, 5 * s);
    }

    // Smile line
    ctx.strokeStyle = '#4B0082';
    ctx.lineWidth = 2 * s;
    ctx.beginPath();
    ctx.ellipse(cx, cy - 30 * s, 22 * s, 10 * s, 0, 0, Math.PI);
    ctx.stroke();

    // Floating paws - relaxed
    ctx.fillStyle = '#9370DB';
    // Left paw
    ctx.beginPath();
    ctx.ellipse(cx - 38 * s, cy + 5 * s, 10 * s, 6 * s, -0.3, 0, Math.PI * 2);
    ctx.fill();
    // Right paw
    ctx.beginPath();
    ctx.ellipse(cx + 38 * s, cy + 5 * s, 10 * s, 6 * s, 0.3, 0, Math.PI * 2);
    ctx.fill();

    // Floating tail - curving
    ctx.strokeStyle = '#9370DB';
    ctx.lineWidth = 8 * s;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(cx + 35 * s, cy + 45 * s);
    ctx.quadraticCurveTo(cx + 55 * s, cy + 60 * s, cx + 50 * s, cy + 30 * s);
    ctx.stroke();
    ctx.strokeStyle = '#4B0082';
    ctx.lineWidth = 5 * s;
    ctx.beginPath();
    ctx.moveTo(cx + 35 * s, cy + 45 * s);
    ctx.quadraticCurveTo(cx + 55 * s, cy + 60 * s, cx + 50 * s, cy + 30 * s);
    ctx.stroke();

    // Fading effect at edges (floating/bored ghost)
    const fadeGrad = ctx.createRadialGradient(cx, cy, 30 * s, cx, cy, 80 * s);
    fadeGrad.addColorStop(0, 'rgba(147, 112, 219, 0)');
    fadeGrad.addColorStop(1, 'rgba(147, 112, 219, 0.3)');
  }

  drawCheshireCat(750, 100);

  // === FOREGROUND ELEMENTS ===
  // Flowers
  function drawFlower(x, y, size, petals, color, centerColor) {
    for (let i = 0; i < petals; i++) {
      ctx.fillStyle = color;
      ctx.beginPath();
      const angle = (i * 2 * Math.PI) / petals;
      ctx.ellipse(
        x + Math.cos(angle) * size * 0.5,
        y + Math.sin(angle) * size * 0.5,
        size * 0.4,
        size * 0.2,
        angle,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
    ctx.fillStyle = centerColor;
    ctx.beginPath();
    ctx.arc(x, y, size * 0.2, 0, Math.PI * 2);
    ctx.fill();
  }

  drawFlower(100, 220, 12, 5, '#FF69B4', '#FFD700');
  drawFlower(200, 230, 10, 6, '#DDA0DD', '#FFD700');
  drawFlower(350, 225, 14, 5, '#FF6347', '#FFD700');
  drawFlower(600, 228, 11, 5, '#FF69B4', '#FFD700');
  drawFlower(700, 235, 10, 6, '#DDA0DD', '#FFD700');
  drawFlower(900, 222, 13, 5, '#FF6347', '#FFD700');

  // Teacup on ground (left)
  ctx.save();
  ctx.translate(420, 210);
  ctx.fillStyle = '#FFF8DC';
  ctx.beginPath();
  ctx.ellipse(0, 0, 15, 18, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#8B4513';
  ctx.beginPath();
  ctx.ellipse(0, -3, 12, 6, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // === FOREGROUND GRASS ===
  ctx.fillStyle = '#2d5a27';
  ctx.beginPath();
  ctx.moveTo(0, height);
  for (let x = 0; x <= 1024; x += 20) {
    ctx.lineTo(x, 230 + Math.sin(x * 0.03) * 10);
  }
  ctx.lineTo(1024, height);
  ctx.closePath();
  ctx.fill();

  // === TITLE TEXT ===
  ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.font = 'bold 28px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('AliceIsBored', 512, 220);

  ctx.fillStyle = '#FFF8DC';
  ctx.strokeStyle = '#4B0082';
  ctx.lineWidth = 4;
  ctx.strokeText('AliceIsBored', 512, 220);
  ctx.fillText('AliceIsBored', 512, 220);

  return canvas.toBuffer('image/png');
}

async function setBanner() {
  try {
    await client.login(DISCORD_TOKEN);

    await new Promise((resolve, reject) => {
      client.once('clientReady', (c) => {
        console.log(`Logged in as ${c.user.tag}`);
        resolve();
      });
      client.once('error', reject);
    });

    let guild = client.guilds.cache.get(TARGET_GUILD_ID);
    if (!guild) {
      console.log(`Fetching guild ${TARGET_GUILD_ID}...`);
      guild = await client.guilds.fetch(TARGET_GUILD_ID);
    }

    console.log(`\nServer: ${guild.name} (${guild.id})`);

    // Set banner
    console.log('\n--- Setting Server Banner ---');
    const bannerBuffer = generateBanner();
    await guild.setBanner(bannerBuffer, 'image/png');
    console.log('✅ Server banner set successfully!');
    console.log('\n✅ Banner: Alice in Wonderland scene with yawning Mad Hatter, impatient White Rabbit, and bored Cheshire Cat');
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  } finally {
    client.destroy();
  }
}

setBanner();