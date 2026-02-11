const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');

// --- Configuration ---
require('dotenv').config({ path: '../../.env' }); // Load from ClawBrain root
const PORT = 3000;
const AUTH_DIR = './.wwebjs_auth';
const OWNER_NUMBER = process.env.WHATSAPP_NUMBER;

// --- Web Server Setup ---
const app = express();
app.use(bodyParser.json());

// --- WhatsApp Client Setup ---
// Check for system chromium
const chromePaths = ['/usr/bin/chromium-browser', '/usr/bin/chromium'];
let executablePath = undefined;
for (const path of chromePaths) {
    if (fs.existsSync(path)) {
        executablePath = path;
        break;
    }
}

console.log('Initializing WhatsApp Client...');
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: AUTH_DIR }),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
        headless: true,
        executablePath: executablePath
    }
});

let isReady = false;
let qrCode = null;

client.on('qr', (qr) => {
    console.log('QR Received');
    // Generate QR file
    qrcode.toFile('./qr.png', qr, (err) => {
        if (err) console.error('Error generating QR file:', err);
        else console.log('QR file generated: qr.png');
    });
});

client.on('ready', () => {
    console.log('Client is ready!');
    isReady = true;
    qrCode = null;
});

client.on('disconnected', (reason) => {
    console.log('Client was disconnected', reason);
    isReady = false;
});

client.on('change_state', (state) => {
    console.log('Client state changed', state);
});

// Log unhandled rejections
process.on('unhandledRejection', (reason, p) => {
    console.error('Unhandled Rejection at:', p, 'reason:', reason);
});

// --- Message Handling ---
const axios = require('axios');
const BRAIN_API_URL = 'http://localhost:8000/api/chat';

// Shared logic for processing messages
async function processMessage(msg) {
    console.log(`[DEBUG] Processing message from ${msg.from}`);

    if (msg.from === 'status@broadcast') return;

    // Strict Filter: Only allow Owner
    if (!OWNER_NUMBER) {
        console.error('[ERROR] WHATSAPP_NUMBER not set in .env');
        return;
    }

    // Check if message is from Owner's number OR is self-sent (which might use @lid)
    const isOwner = msg.from.startsWith(OWNER_NUMBER) || msg.fromMe;
    const isGroup = msg.from.includes('@g.us');

    if (!isOwner || isGroup) {
        console.log(`[DEBUG] Ignoring message from non-owner/group: ${msg.from} (fromMe: ${msg.fromMe})`);
        return;
    }

    try {
        const messageBody = msg.body;
        console.log(`[DEBUG] Body: ${messageBody.substring(0, 20)}...`);

        if (!messageBody) {
            console.log('[DEBUG] Empty body, skipping');
            return;
        }

        // Call Brain API
        const senderName = msg.from;
        console.log(`[DEBUG] Calling API for ${senderName}...`);

        const response = await axios.post(BRAIN_API_URL, {
            message: messageBody,
            sender: senderName,
            complexity: 'simple'
        });

        console.log(`[DEBUG] API Response status: ${response.status}`);

        // Reply to user (with Robot prefix to avoid loops on Note to Self)
        if (response.data && response.data.response) {
            const replyText = `🤖 ${response.data.response}`;
            console.log(`[DEBUG] Replying: ${replyText.substring(0, 20)}...`);
            await msg.reply(replyText);
            console.log(`[DEBUG] Reply sent.`);
        } else {
            console.error('[ERROR] Empty response from Brain API');
        }

    } catch (err) {
        console.error('[ERROR] Message processing failed:', err);
    }
}

// 1. Handle messages from OTHERS (if any, though we filter them)
client.on('message', async (msg) => {
    // Standard inbound message
    await processMessage(msg);
});

// 2. Handle "Note to Self" (Messages sent by ME)
client.on('message_create', async (msg) => {
    // Only care if it IS from me
    if (!msg.fromMe) return;

    console.log(`[DEBUG] message_create fromMe. To: ${msg.to}, From: ${msg.from}, Body: ${msg.body}`);

    // Avoid infinite loops: Ignore if it starts with our bot prefix
    if (msg.body.startsWith('🤖')) return;

    // Check if it is "Note to Self"
    // Case 1: to === from (Primary device)
    // Case 2: to is Owner Number (Linked device sending to self)
    // Case 3: to is Client's LID (Bot's own ID)
    const botId = client.info && client.info.wid ? client.info.wid._serialized : '';
    const knownLid = '92998994014333@lid'; // Derived from logs

    console.log(`[DEBUG] NoteSelf Check. Match? ${msg.to === msg.from || msg.to.startsWith(OWNER_NUMBER) || msg.to === botId || msg.to === knownLid}. BotId: ${botId}`);

    if (msg.to === msg.from || msg.to.startsWith(OWNER_NUMBER) || (botId && msg.to === botId) || msg.to === knownLid) {
        console.log('[DEBUG] Detected Note to Self');
        await processMessage(msg);
    }
});

client.initialize();

// --- API Endpoints ---

// Status
app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        hasQr: !!qrCode,
        qr: qrCode
    });
});

// Send Message
app.post('/send', async (req, res) => {
    if (!isReady) return res.status(503).json({ error: 'Client not ready' });

    const { to, msg } = req.body;
    if (!to || !msg) return res.status(400).json({ error: 'Missing "to" or "msg"' });

    try {
        // Format number if needed (append @c.us if missing)
        let chatId = to;
        if (!chatId.includes('@')) {
            chatId = `${chatId}@c.us`;
        }

        const response = await client.sendMessage(chatId, msg);
        res.json({ success: true, id: response.id._serialized });
    } catch (err) {
        console.error('Send error:', err);
        res.status(500).json({ error: err.message });
    }
});

// Get History
app.get('/history', async (req, res) => {
    if (!isReady) return res.status(503).json({ error: 'Client not ready' });

    const { to, limit } = req.query;
    if (!to) return res.status(400).json({ error: 'Missing "to"' });

    try {
        let chatId = to;
        if (!chatId.includes('@')) {
            chatId = `${chatId}@c.us`;
        }

        const chat = await client.getChatById(chatId);
        const messages = await chat.fetchMessages({ limit: parseInt(limit) || 10 });

        const history = messages.map(m => ({
            from: m.from,
            body: m.body,
            timestamp: m.timestamp
        }));

        res.json({ success: true, history });
    } catch (err) {
        console.error('History error:', err);
        res.status(500).json({ error: err.message });
    }
});

// Start Server
app.listen(PORT, () => {
    console.log(`wacli-server running on port ${PORT}`);
});
