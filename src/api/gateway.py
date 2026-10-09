import sys
import os
import shutil
import time
import base64
import io
import qrcode
import subprocess
import signal
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from src.core.gateway_state import gateway_state
from src.core.metrics import metrics_state

router = APIRouter(tags=["gateway"])

class BaileysStatus(BaseModel):
    state: str
    qr: str = ""
    phone: str = ""
    pid: int = 0
    error: str = ""

def generate_qr_base64(qr_data: str) -> str:
    if not qr_data:
        return ""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, "PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR base64: {e}")
        return ""

@router.get("/qr", response_class=HTMLResponse)
async def qr_page():
    state = gateway_state.state.upper()
    qr = gateway_state.qr
    phone = gateway_state.phone
    error = gateway_state.error
    
    qr_img_src = ""
    if (state == "QR_PENDING" or state == "NEED SCAN") and qr:
        qr_img_src = generate_qr_base64(qr)

    # Inline HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>R2CELL WhatsApp Login</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient: radial-gradient(circle at top right, #141424, #0b0b11);
                --card-bg: rgba(22, 22, 38, 0.7);
                --card-border: rgba(255, 255, 255, 0.08);
                --text-primary: #f3f4f6;
                --text-secondary: #9ca3af;
                --accent-green: #10b981;
                --accent-blue: #3b82f6;
                --accent-orange: #f59e0b;
                --accent-red: #ef4444;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                background: var(--bg-gradient);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow-x: hidden;
            }}
            .container {{
                width: 100%;
                max-width: 440px;
                padding: 20px;
            }}
            .card {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 40px 30px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                transition: all 0.3s ease;
            }}
            .logo {{
                font-size: 2.2rem;
                font-weight: 800;
                background: linear-gradient(135deg, #7c8aff, #10b981);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 8px;
                letter-spacing: -0.5px;
            }}
            .subtitle {{
                color: var(--text-secondary);
                font-size: 0.95rem;
                margin-bottom: 30px;
                font-weight: 300;
            }}
            .qr-wrapper {{
                position: relative;
                width: 256px;
                height: 256px;
                margin: 0 auto 30px;
                background: #ffffff;
                border-radius: 16px;
                padding: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
                overflow: hidden;
            }}
            .qr-img {{
                max-width: 100%;
                max-height: 100%;
                display: block;
            }}
            .spinner {{
                width: 40px;
                height: 40px;
                border: 4px solid rgba(124, 138, 255, 0.1);
                border-top-color: var(--accent-blue);
                border-radius: 50%;
                animation: spin 1s infinite linear;
                margin-bottom: 12px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background: rgba(255, 255, 255, 0.05);
                margin-bottom: 25px;
            }}
            .status-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--text-secondary);
            }}
            .status-badge.connecting {{
                color: var(--accent-orange);
                background: rgba(245, 158, 11, 0.1);
            }}
            .status-badge.connecting .status-dot {{
                background: var(--accent-orange);
                animation: pulse 1.5s infinite alternate;
            }}
            .status-badge.need-scan {{
                color: var(--accent-blue);
                background: rgba(59, 130, 246, 0.1);
            }}
            .status-badge.need-scan .status-dot {{
                background: var(--accent-blue);
                animation: pulse 1s infinite alternate;
            }}
            .status-badge.connected {{
                color: var(--accent-green);
                background: rgba(16, 185, 129, 0.1);
            }}
            .status-badge.connected .status-dot {{
                background: var(--accent-green);
            }}
            .status-badge.error {{
                color: var(--accent-red);
                background: rgba(239, 68, 68, 0.1);
            }}
            .status-badge.error .status-dot {{
                background: var(--accent-red);
            }}
            @keyframes pulse {{
                0% {{ opacity: 0.4; }}
                100% {{ opacity: 1; }}
            }}
            .instructions {{
                font-size: 0.9rem;
                line-height: 1.5;
                color: var(--text-secondary);
                font-weight: 300;
            }}
            .instructions b {{
                color: var(--text-primary);
                font-weight: 600;
            }}
            .success-icon {{
                font-size: 3.5rem;
                color: var(--accent-green);
                margin-bottom: 10px;
            }}
            .timer {{
                font-size: 0.95rem;
                font-weight: 600;
                color: var(--accent-orange);
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card" id="card-content">
                <div class="logo">R2CELL</div>
                <div class="subtitle">WhatsApp Gateway Link</div>
    """
    
    # State-dependent markup
    if state in ("AUTHENTICATED", "CONNECTED"):
        html_content += f"""
                <div class="status-badge connected">
                    <div class="status-dot"></div>
                    <span>Connected</span>
                </div>
                <div class="qr-wrapper">
                    <div style="text-align: center;">
                        <div class="success-icon">✓</div>
                        <div style="font-weight: 600; font-size: 1.1rem; color: #10b981;">Device Connected</div>
                        <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Phone: {phone}</div>
                    </div>
                </div>
                <div class="instructions">
                    The chatbot is active and listening for WhatsApp messages.
                </div>
        """
    elif (state in ("QR_PENDING", "NEED SCAN")) and qr_img_src:
        html_content += f"""
                <div class="status-badge need-scan">
                    <div class="status-dot"></div>
                    <span>Scan Required</span>
                </div>
                <div class="timer">QR expires in: <span id="timer-countdown">60s</span></div>
                <div class="qr-wrapper">
                    <img id="qr-image" class="qr-img" src="{qr_img_src}" alt="Scan QR Code" />
                </div>
                <div class="instructions">
                    Open WhatsApp on your phone, go to <b>Linked Devices</b>, and scan the QR code.
                </div>
        """
    elif state == "CONNECTING":
        html_content += f"""
                <div class="status-badge connecting">
                    <div class="status-dot"></div>
                    <span>Connecting...</span>
                </div>
                <div class="qr-wrapper">
                    <div style="text-align: center;">
                        <div class="spinner"></div>
                        <div style="font-weight: 500; font-size: 0.9rem; color: #4b5563;">Initializing session...</div>
                    </div>
                </div>
                <div class="instructions">
                    Initializing WhatsApp web client session. Please wait.
                </div>
        """
    else:
        html_content += f"""
                <div class="status-badge error">
                    <div class="status-dot"></div>
                    <span>Offline / Disconnected</span>
                </div>
                <div class="qr-wrapper">
                    <div style="text-align: center; color: #ef4444; padding: 20px;">
                        <div style="font-size: 3rem; margin-bottom: 10px;">⚠</div>
                        <div style="font-weight: 500; font-size: 0.95rem;">Gateway is Offline</div>
                        <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">{error or 'Service is not running.'}</div>
                    </div>
                </div>
                <div class="instructions">
                    Make sure the WhatsApp Node.js backend is running.
                </div>
        """

    html_content += """
            </div>
        </div>
        
        <script>
            let countdown = 60;
            const timerVal = document.getElementById("timer-countdown");
            
            function runCountdown() {
                if (!timerVal) return;
                const interval = setInterval(() => {
                    countdown--;
                    if (countdown <= 0) {
                        clearInterval(interval);
                        window.location.reload();
                    } else {
                        timerVal.innerText = countdown + "s";
                    }
                }, 1000);
            }
            
            async function checkStatus() {
                try {
                    const response = await fetch("/wa/status");
                    if (response.ok) {
                        const data = await response.json();
                        const curState = data.state.toUpperCase();
                        
                        // If state transitioned from current view, reload
                        if (curState === "AUTHENTICATED" || curState === "CONNECTED") {
                            if (!document.querySelector(".status-badge.connected")) {
                                window.location.reload();
                            }
                        } else if (curState === "QR_PENDING" || curState === "NEED SCAN") {
                            if (!document.querySelector(".status-badge.need-scan")) {
                                window.location.reload();
                            } else if (data.qr_base64) {
                                const img = document.getElementById("qr-image");
                                if (img && img.src !== data.qr_base64) {
                                    img.src = data.qr_base64;
                                    countdown = 60; // reset
                                }
                            }
                        } else if (curState === "CONNECTING") {
                            if (!document.querySelector(".status-badge.connecting")) {
                                window.location.reload();
                            }
                        } else {
                            if (!document.querySelector(".status-badge.error")) {
                                window.location.reload();
                            }
                        }
                    }
                } catch (e) {}
            }
            
            runCountdown();
            setInterval(checkStatus, 2000);
            
            // Meta fallback refresh in 55s
            setTimeout(() => {
                window.location.reload();
            }, 55000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@router.post("/api/internal/status")
async def update_baileys_status(status: BaileysStatus):
    """
    Webhook for Baileys Node.js process to push its connection state,
    so the Python TUI can read it.
    """
    gateway_state.state = status.state
    if status.qr:
        gateway_state.qr = status.qr
    if status.phone:
        gateway_state.phone = status.phone
    if status.pid:
        gateway_state.pid = status.pid
    if status.error:
        gateway_state.error = status.error

    # Set start time for uptime when first authenticated
    if status.state == "AUTHENTICATED" and gateway_state.uptime_start == 0.0:
        gateway_state.uptime_start = time.time()
    elif status.state in ("DISCONNECTED", "ERROR"):
        gateway_state.uptime_start = 0.0

    return {"success": True}

@router.get("/api/internal/status")
async def get_baileys_status():
    """
    Endpoint for the TUI to poll the current state of Baileys/FastAPI.
    """
    # Format last request time
    last_req_str = "never"
    if metrics_state.last_request_time > 0:
        elapsed = int(time.time() - metrics_state.last_request_time)
        if elapsed < 60:
            last_req_str = f"{elapsed}s ago"
        else:
            last_req_str = f"{elapsed // 60}m ago"

    # Count active connections in the last 5 seconds
    now = time.time()
    active_conn_count = sum(1 for ts in metrics_state.active_clients.values() if now - ts < 5)

    return {
        "fastapi": {
            "status": "RUNNING",
            "request_count": metrics_state.request_count,
            "last_request": last_req_str
        },
        "baileys": {
            "state": gateway_state.state,
            "qr": gateway_state.qr,
            "phone": gateway_state.phone,
            "pid": gateway_state.pid,
            "error": gateway_state.error,
            "uptime": int(time.time() - gateway_state.uptime_start) if gateway_state.uptime_start > 0 else 0,
            "message_count": gateway_state.message_count
        },
        "frontend": {
            "status": "RUNNING",
            "active_connections": max(1, active_conn_count)
        }
    }

@router.get("/wa/status")
async def wa_status():
    qr = gateway_state.qr
    qr_base64 = generate_qr_base64(qr) if qr else ""
    uptime = int(time.time() - gateway_state.uptime_start) if gateway_state.uptime_start > 0 else 0
    return {
        "state": gateway_state.state,
        "qr_base64": qr_base64,
        "uptime": uptime,
        "message_count": gateway_state.message_count,
        "error": gateway_state.error
    }

@router.post("/wa/reset-session")
async def reset_session():
    # 1. Kill old process if running
    old_pid = gateway_state.pid
    if old_pid:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(old_pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                os.kill(old_pid, signal.SIGKILL)
        except Exception as e:
            print(f"Failed to kill Baileys process with PID {old_pid}: {e}")

    # 2. Delete auth folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auth_dir = os.path.join(base_dir, "integrations", "whatsapp", "auth_info_baileys")
    if os.path.exists(auth_dir):
        shutil.rmtree(auth_dir, ignore_errors=True)

    # 3. Reset internal state
    gateway_state.state = "CONNECTING"
    gateway_state.qr = ""
    gateway_state.phone = ""
    gateway_state.pid = 0
    gateway_state.error = ""
    gateway_state.uptime_start = 0.0
    gateway_state.message_count = 0

    # 4. Start process fresh
    try:
        cmd = ["node", os.path.join(base_dir, "integrations", "whatsapp", "whatsapp.js")]
        env = os.environ.copy()
        if "R2CELL_TUI" in env:
            del env["R2CELL_TUI"]
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
    except Exception as e:
        gateway_state.state = "ERROR"
        gateway_state.error = str(e)
        raise HTTPException(status_code=500, detail=f"Failed to spawn WhatsApp gateway: {e}")

    return {"status": "success", "message": "WhatsApp session reset initiated."}

@router.get("/logs/{service}")
async def get_logs(service: str):
    if service.lower() not in ("fastapi", "baileys", "frontend"):
        raise HTTPException(status_code=400, detail="Invalid service name")
    
    async def log_generator():
        log_file = f"logs/{service.lower()}.log"
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                f.write(f"--- Log started for {service} ---\n")
        
        # Open in read mode
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            # Yield last 100 lines
            lines = f.readlines()
            for line in lines[-100:]:
                yield f"data: {line.rstrip()}\n\n"
            
            # Tail the file
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line.rstrip()}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")
