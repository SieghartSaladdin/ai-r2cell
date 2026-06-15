const { 
    makeWASocket, 
    useMultiFileAuthState, 
    DisconnectReason,
    fetchLatestBaileysVersion // Dynamically fetch latest version to avoid 405 errors
} = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const path = require('path');
const dotenv = require('dotenv');

// Load configurations
dotenv.config();

// ── Intercept Console Logs to Write to logs/baileys.log ────────────────
const fs = require('fs');
const logDir = path.resolve(__dirname, '../../../logs');
const logFile = path.join(logDir, 'baileys.log');
try {
    fs.mkdirSync(logDir, { recursive: true });
} catch (err) {}
const logStream = fs.createWriteStream(logFile, { flags: 'a' });

const originalLog = console.log;
const originalError = console.error;

console.log = function(...args) {
    originalLog.apply(console, args);
    try {
        logStream.write(`[${new Date().toISOString()}] ${args.join(' ')}\n`);
    } catch (err) {}
};

console.error = function(...args) {
    originalError.apply(console, args);
    try {
        logStream.write(`[${new Date().toISOString()}] ERROR: ${args.join(' ')}\n`);
    } catch (err) {}
};

const BACKEND_URL = process.env.CHATBOT_BACKEND_URL || 'http://127.0.0.1:8000/chat';
const KEEP_ALIVE_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
let lastActivityTime = Date.now();
let socketInstance = null;

/**
 * Splits a long AI chatbot response into multiple logical messages (bubbles)
 * to simulate a real human typing separate messages on WhatsApp.
 * 
 * Splits strictly by double newlines (\n\n) to keep lists/paragraphs coherent.
 * Filters out empty bubbles.
 */
function splitIntoHumanMessages(text) {
    if (!text) return [];
    
    // Split by double newlines (one or more blank lines)
    const paragraphs = text.split(/\n\n+/);
    
    return paragraphs
        .map(p => p.trim())
        .filter(p => p.length > 0);
}

const INTERNAL_STATUS_URL = 'http://127.0.0.1:8000/api/internal/status';

async function pushStatusToIPC(state, qr = "", phone = "", error = "") {
    try {
        await axios.post(INTERNAL_STATUS_URL, {
            state: state,
            qr: qr,
            phone: phone,
            pid: process.pid,
            error: error
        });
    } catch (err) {
        // Silently fail if IPC is not yet up
    }
}

async function connectToWhatsApp() {
    try {
        // 1. Setup multi-file auth credentials folder
        const authFolder = path.join(__dirname, 'auth_info_baileys');
        const { state, saveCreds } = await useMultiFileAuthState(authFolder);

        // Fetch the latest WhatsApp Web version to evade WebSocket 405 rejection errors
        const { version, isLatest } = await fetchLatestBaileysVersion();
        console.log(`Using WhatsApp Web v${version.join('.')}, isLatest: ${isLatest}`);
        console.log("Initializing WhatsApp Baileys client...");
        await pushStatusToIPC("CONNECTING");

        // 2. Create socket connection with low logging verbosity and dynamic version
        const sock = makeWASocket({
            version,
            auth: state,
            logger: pino({ level: 'warn' }),
            browser: ['Antigravity WhatsApp Client', 'Chrome', '1.0.0']
        });

        socketInstance = sock;

        // 3. Handle connection status updates
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log("\nScan this QR code in your WhatsApp app to log in:");
                // Generate QR code directly in the terminal console (using standard spacing)
                qrcode.generate(qr, { small: false });
                console.log("\n------------------------------------------------------------");
                console.log("If the terminal QR code looks distorted or shrunk, open this link:");
                console.log("👉 \x1b[36mhttp://localhost:8000/qr\x1b[0m");
                console.log("------------------------------------------------------------\n");
                await pushStatusToIPC("QR_PENDING", qr);
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                console.log(`Connection closed. Status code: ${statusCode}. Reconnecting: ${shouldReconnect}`);
                
                await pushStatusToIPC("DISCONNECTED", "", "", lastDisconnect?.error?.message || "");

                if (shouldReconnect) {
                    // Re-trigger connection loop
                    setTimeout(connectToWhatsApp, 5000);
                }
            } else if (connection === 'open') {
                console.log('\n======================================');
                console.log('  WhatsApp Bot Connection Established!');
                console.log('======================================\n');
                
                await pushStatusToIPC("AUTHENTICATED", "", sock.user.id.split(':')[0]);

                lastActivityTime = Date.now();
                
                // Delay presence update slightly to ensure WhatsApp profile is fully synced and avoid warning logs
                setTimeout(async () => {
                    try {
                        await sock.sendPresenceUpdate('available');
                    } catch (e) {
                        // Ignore transient presence registration errors on initial connection
                    }
                }, 3000);
            }
        });

        // 4. Save authentication credentials when updated
        sock.ev.on('creds.update', saveCreds);

        // 5. Listens for incoming WhatsApp messages
        sock.ev.on('messages.upsert', async (m) => {
            if (m.type !== 'notify') return;

            for (const msg of m.messages) {
                // Ignore messages sent by the bot itself or broadcast/status messages
                if (msg.key.fromMe) continue;
                const senderJid = msg.key.remoteJid;
                if (senderJid.endsWith('@broadcast') || senderJid.includes('g.us')) {
                    // Skip status broadcasts or group messages (unless configured otherwise)
                    continue;
                }

                // Extract message text content
                const textContent = msg.message?.conversation || 
                                    msg.message?.extendedTextMessage?.text || 
                                    msg.message?.imageMessage?.caption || 
                                    msg.message?.videoMessage?.caption || 
                                    '';

                const trimmedText = textContent.trim();
                if (!trimmedText) continue;

                console.log(`Received message from [${senderJid}]: "${trimmedText}"`);
                
                // Immediately mark message as read to trigger blue checkmarks/approval for the sender
                try {
                    await sock.readMessages([msg.key]);
                    console.log(`[Read-Receipt] Message marked as read (Blue checkmarks sent) to ${senderJid}`);
                } catch (err) {
                    console.error(`Failed to send read receipt: ${err.message}`);
                }

                // Set last active time immediately to refresh our presence loop
                lastActivityTime = Date.now();

                try {
                    // 1. Let sender know we are typing while we call the backend
                    await sock.sendPresenceUpdate('composing', senderJid);
                    console.log(`[Presence] Bot status set to 'composing' (typing indicator) for ${senderJid}`);

                    // 2. Send request to Python FastAPI LangGraph backend
                    // Map the WhatsApp sender JID to our session_id to maintain session continuity
                    const response = await axios.post(BACKEND_URL, {
                        message: trimmedText,
                        session_id: senderJid
                    });

                    const botResponse = response.data.response;
                    console.log(`FastAPI chatbot reply:\n"${botResponse}"`);

                    // 3. Stop initial composing presence
                    await sock.sendPresenceUpdate('paused', senderJid);

                    // 4. Split the response into natural, human-like bubbles
                    const messagesToSend = splitIntoHumanMessages(botResponse);
                    console.log(`Split response into ${messagesToSend.length} separate bubbles.`);

                    // 5. Send each bubble sequentially with a realistic typing delay
                    for (let i = 0; i < messagesToSend.length; i++) {
                        const currentBubble = messagesToSend[i];
                        
                        // Show typing indicator
                        await sock.sendPresenceUpdate('composing', senderJid);
                        
                        // Calculate a dynamic delay proportional to the character length:
                        // 20ms per character, clamped between 1000ms and 3500ms
                        const typingDelay = Math.min(3500, Math.max(1000, currentBubble.length * 20));
                        console.log(`[Bubble ${i+1}/${messagesToSend.length}] Typing duration: ${typingDelay}ms...`);
                        await new Promise(resolve => setTimeout(resolve, typingDelay));
                        
                        // Stop typing indicator and send the bubble
                        await sock.sendPresenceUpdate('paused', senderJid);
                        await sock.sendMessage(senderJid, { text: currentBubble });
                        console.log(`[Bubble ${i+1}/${messagesToSend.length}] Sent!`);
                        
                        // Add a natural pause between message bubbles to simulate standard human behavior
                        if (i < messagesToSend.length - 1) {
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                    }
                    
                    // 6. Update activity time and refresh available presence status
                    lastActivityTime = Date.now();
                    await sock.sendPresenceUpdate('available');

                } catch (err) {
                    console.error(`Error communicating with chatbot backend: ${err.message}`);
                    try {
                        await sock.sendPresenceUpdate('paused', senderJid);
                        await sock.sendMessage(senderJid, { 
                            text: "I apologize, but I am currently unable to process your request. Please try again shortly." 
                        });
                    } catch (sendErr) {
                        console.error("Failed to send error fallback message:", sendErr.message);
                    }
                }
            }
        });

        return sock;
    } catch (err) {
        console.error("Critical connection failure:", err);
        await pushStatusToIPC("ERROR", "", "", err.message || err.toString());
        // Reconnect after 10s if initial setup failed
        setTimeout(connectToWhatsApp, 10000);
    }
}

// 6. Keep-Alive / Presence retention engine
// Runs a check periodically every 30 seconds.
// If we have had active communication within the last 5 minutes, we actively refresh our status
// to 'available' to ensure that we do NOT go offline and the sender sees us as online.
// Even if we are fully idle (>5 minutes), we keep refreshing to maintain socket activity.
setInterval(async () => {
    if (!socketInstance) return;
    
    const idleDuration = Date.now() - lastActivityTime;
    
    if (idleDuration < KEEP_ALIVE_INTERVAL_MS) {
        // Active window (within 5 minutes of a message event): Refresh online status aggressively to stay active
        console.log(`[Presence-Retention] Active session (${Math.round(idleDuration / 1000)}s since last event). Maintaining 'online' presence.`);
        try {
            await socketInstance.sendPresenceUpdate('available');
        } catch (e) {
            console.error(`[Presence-Retention] Failed to send presence: ${e.message}`);
        }
    } else {
        // Idle window (longer than 5 minutes): Send normal background keep-alive ping
        console.log(`[Keep-Alive] Idle >5 mins. Refreshing backend socket presence registration.`);
        try {
            await socketInstance.sendPresenceUpdate('available');
        } catch (e) {
            console.error(`[Keep-Alive] Failed to send presence: ${e.message}`);
        }
    }
}, 30000); // Check and refresh presence state every 30 seconds

// Start connection
connectToWhatsApp().catch(err => console.error("Critical connection failure:", err));
