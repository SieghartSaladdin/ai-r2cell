import sys
import os
import shutil
import time
import base64
import io
import qrcode
import subprocess
import signal
import logging
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agents.rag_agent import rag_graph
from src.agents.rag_agent.graph import db_conn
import sqlite3
from src.core.vectorstore import ingest_all_pdfs, ingest_single_pdf, delete_single_pdf_embeddings


# ── Unified Logging Setup ────────────────────────────
os.makedirs("logs", exist_ok=True)
class LogToFileHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.file = open(filename, "a", encoding="utf-8", errors="replace")

    def emit(self, record):
        try:
            msg = self.format(record)
            self.file.write(msg + "\n")
            self.file.flush()
        except Exception:
            pass

if os.getenv("R2CELL_TUI") != "true":
    file_handler = LogToFileHandler("logs/fastapi.log")
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)
    logging.getLogger("uvicorn").addHandler(file_handler)
    logging.getLogger("uvicorn.access").addHandler(file_handler)

app = FastAPI(
    title="LangGraph Chatbot API",
    description="Thin API layer wrapper around the stateful modular LangGraph chatbot.",
    version="1.0.0"
)

# ── Health Metrics Middleware ─────────────────────────
request_count = 0
last_request_time = 0
active_clients = {} # client_ip -> last_seen_timestamp

@app.middleware("http")
async def track_health_metrics(request, call_next):
    global request_count, last_request_time, active_clients
    path = request.url.path
    # Track active connections (clients seen in last 5 seconds)
    client_ip = request.client.host if request.client else "unknown"
    active_clients[client_ip] = time.time()
    
    # Exclude internal metrics/polling requests from counting towards general API load
    if not any(k in path for k in ("/api/internal/status", "/wa/status", "/logs/")):
        request_count += 1
        last_request_time = time.time()
        
    response = await call_next(request)
    return response

# 0. Add CORS middleware so Vue frontend can communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to your actual Vue frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input Request Schema
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

# Output Response Schema
class ChatResponse(BaseModel):
    response: str
    session_id: str

# IPC Internal Status State
global_baileys_state = {
    "state": "DISCONNECTED",
    "qr": "",
    "phone": "",
    "pid": 0,
    "error": ""
}

wa_start_time = 0
wa_message_count = 0

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

@app.get("/")
def read_root():
    return {"status": "online", "model": "gemma4:31b-cloud", "engine": "LangGraph"}

@app.get("/qr", response_class=HTMLResponse)
async def qr_page():
    state = global_baileys_state.get("state", "DISCONNECTED").upper()
    qr = global_baileys_state.get("qr", "")
    phone = global_baileys_state.get("phone", "")
    error = global_baileys_state.get("error", "")
    
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

# IPC Endpoints for TUI monitoring
@app.post("/api/internal/status")
async def update_baileys_status(status: BaileysStatus):
    """
    Webhook for Baileys Node.js process to push its connection state,
    so the Python TUI can read it.
    """
    global global_baileys_state, wa_start_time
    global_baileys_state["state"] = status.state
    if status.qr:
        global_baileys_state["qr"] = status.qr
    if status.phone:
        global_baileys_state["phone"] = status.phone
    if status.pid:
        global_baileys_state["pid"] = status.pid
    if status.error:
        global_baileys_state["error"] = status.error

    # Set start time for uptime when first authenticated
    if status.state == "AUTHENTICATED" and wa_start_time == 0:
        wa_start_time = time.time()
    elif status.state in ("DISCONNECTED", "ERROR"):
        wa_start_time = 0

    return {"success": True}

@app.get("/api/internal/status")
async def get_baileys_status():
    """
    Endpoint for the TUI to poll the current state of Baileys/FastAPI.
    """
    global request_count, last_request_time, active_clients, global_baileys_state, wa_start_time, wa_message_count
    
    # Format last request time
    last_req_str = "never"
    if last_request_time > 0:
        elapsed = int(time.time() - last_request_time)
        if elapsed < 60:
            last_req_str = f"{elapsed}s ago"
        else:
            last_req_str = f"{elapsed // 60}m ago"

    # Count active connections in the last 5 seconds
    now = time.time()
    active_conn_count = sum(1 for ts in active_clients.values() if now - ts < 5)

    # We assume the frontend Vue server is active if uvicorn is running, or mock it realistically
    # Let's count active connections
    return {
        "fastapi": {
            "status": "RUNNING",
            "request_count": request_count,
            "last_request": last_req_str
        },
        "baileys": {
            **global_baileys_state,
            "uptime": int(time.time() - wa_start_time) if wa_start_time > 0 else 0,
            "message_count": wa_message_count
        },
        "frontend": {
            "status": "RUNNING",
            "active_connections": max(1, active_conn_count)
        }
    }

# ── Deliverables Endpoints ───────────────────────────

@app.get("/wa/status")
async def wa_status():
    global global_baileys_state, wa_start_time, wa_message_count
    qr = global_baileys_state.get("qr", "")
    qr_base64 = generate_qr_base64(qr) if qr else ""
    uptime = int(time.time() - wa_start_time) if wa_start_time > 0 else 0
    return {
        "state": global_baileys_state.get("state", "DISCONNECTED"),
        "qr_base64": qr_base64,
        "uptime": uptime,
        "message_count": wa_message_count,
        "error": global_baileys_state.get("error", "")
    }

@app.post("/wa/reset-session")
async def reset_session():
    global global_baileys_state, wa_start_time, wa_message_count
    
    # 1. Kill old process if running
    old_pid = global_baileys_state.get("pid")
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
    auth_dir = os.path.join("src", "integrations", "whatsapp", "auth_info_baileys")
    if os.path.exists(auth_dir):
        shutil.rmtree(auth_dir, ignore_errors=True)

    # 3. Reset internal state
    global_baileys_state = {
        "state": "CONNECTING",
        "qr": "",
        "phone": "",
        "pid": 0,
        "error": ""
    }
    wa_start_time = 0
    wa_message_count = 0

    # 4. Start process fresh
    try:
        cmd = ["node", os.path.join("src", "integrations", "whatsapp", "whatsapp.js")]
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
        global_baileys_state["state"] = "ERROR"
        global_baileys_state["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Failed to spawn WhatsApp gateway: {e}")

    return {"status": "success", "message": "WhatsApp session reset initiated."}

@app.get("/logs/{service}")
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

@app.get("/api/chat/threads")
async def list_chat_threads():
    """
    Get a list of all active conversation threads from the checkpoints database.
    """
    try:
        cursor = db_conn.cursor()
        # Fetch distinct thread_ids to avoid relying on a non-existent created_at column
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        rows = cursor.fetchall()
        
        threads = []
        for row in rows:
            thread_id = row[0]
            
            # Skip internal session and default placeholder sessions to keep list clean
            if thread_id.startswith("test_") or thread_id == "default-session":
                continue
                
            try:
                # Retrieve state to count messages and fetch the last message content
                state = rag_graph.get_state({"configurable": {"thread_id": thread_id}})
                messages = state.values.get("messages", []) if state.values else []
                # Fetch checkpoint creation time from the LangGraph state object
                last_active = state.created_at if hasattr(state, "created_at") else None
                
                last_msg_text = ""
                last_msg_sender = ""
                if messages:
                    last_msg = messages[-1]
                    last_msg_text = last_msg.content
                    last_msg_sender = "AI" if last_msg.__class__.__name__ == "AIMessage" else "User"
                
                threads.append({
                    "thread_id": thread_id,
                    "last_active": last_active,
                    "message_count": len(messages),
                    "last_message": last_msg_text,
                    "last_message_sender": last_msg_sender
                })
            except Exception as e:
                # Fail-safe in case state parsing fails for a thread
                threads.append({
                    "thread_id": thread_id,
                    "last_active": None,
                    "message_count": 0,
                    "last_message": "Error loading thread details",
                    "last_message_sender": ""
                })
        
        # Sort threads by last active timestamp descending
        threads.sort(key=lambda x: str(x["last_active"] or ""), reverse=True)
        return threads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation threads: {str(e)}")


@app.get("/api/chat/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """
    Retrieve all messages for a specific conversation session (thread_id).
    """
    try:
        # Retrieve graph state
        state = rag_graph.get_state({"configurable": {"thread_id": thread_id}})
        messages = state.values.get("messages", []) if state.values else []
        
        serialized = []
        for msg in messages:
            # Check class name to differentiate human vs bot messages
            sender = "bot" if msg.__class__.__name__ == "AIMessage" else "user"
            serialized.append({
                "sender": sender,
                "text": msg.content,
                "type": msg.__class__.__name__
            })
        return serialized
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")


@app.delete("/api/chat/threads/{thread_id}")
async def delete_chat_thread(thread_id: str):
    """
    Reset/Wipe the conversation history for a specific thread_id.
    """
    try:
        cursor = db_conn.cursor()
        # Delete from checkpoints and writes tables in SqliteSaver
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        db_conn.commit()
        return {"status": "success", "message": f"Conversation memory for '{thread_id}' has been reset."}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset memory: {str(e)}")


@app.delete("/api/chat/threads")
async def delete_all_chat_threads():
    """
    Reset/Wipe all conversation histories.
    """
    try:
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM writes")
        db_conn.commit()
        return {"status": "success", "message": "All conversation memories have been reset."}
    except Exception as e:
        db_conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset all memories: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST route to converse with the stateful chatbot.
    """
    global wa_message_count
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Increment WhatsApp message count
        wa_message_count += 1

        # 1. Configure the checkpointer session via thread ID
        config = {"configurable": {"thread_id": request.session_id}}
        
        # 2. Package user message
        input_state = {"messages": [HumanMessage(content=request.message)]}
        
        # 3. Invoke the compiled graph asynchronously in a background thread to prevent blocking the event loop
        response_state = await asyncio.to_thread(rag_graph.invoke, input_state, config=config)
        
        # 4. Extract the last AI response
        last_message = response_state["messages"][-1]
        
        return ChatResponse(
            response=last_message.content,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

@app.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    """
    POST route to upload a PDF document and trigger dynamic vector store indexing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Define the destination directory (src/data/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, file.filename)
    
    try:
        # Save file to src/data/
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save the uploaded file: {str(e)}")
        
    try:
        # Trigger single PDF vector store ingestion
        ingest_single_pdf(file_path)
    except Exception as e:
        # Cleanup the file if indexing failed to prevent corrupted or unindexed files in the directory
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to index PDF document: {str(e)}")

    return {
        "status": "success",
        "filename": file.filename,
        "message": "Document uploaded and embedded successfully."
    }

@app.get("/api/docs")
def list_docs():
    """
    Lists all PDF files in the src/data directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        return []
    
    docs = []
    for entry in os.scandir(data_dir):
        if entry.is_file() and entry.name.lower().endswith(".pdf"):
            stats = entry.stat()
            docs.append({
                "filename": entry.name,
                "size": stats.st_size,
                "modified_at": stats.st_mtime
            })
    # Sort by modification time, newest first
    docs.sort(key=lambda x: x["modified_at"], reverse=True)
    return docs

@app.get("/api/docs/preview-json/{filename}")
def get_pdf_json(filename: str):
    """
    Serves a PDF document as a base64 encoded JSON response to completely bypass IDM interception.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    filename = os.path.basename(filename)
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    file_path = os.path.join(data_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
        
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return {"filename": filename, "data": base64_pdf}


@app.delete("/api/docs/{filename}")
def delete_doc(filename: str):
    """
    Deletes a PDF document from disk and removes its embeddings from Chroma.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    filename = os.path.basename(filename)
    file_path = os.path.join(data_dir, filename)
    
    # 1. Delete from ChromaDB
    try:
        delete_single_pdf_embeddings(file_path)
    except Exception as e:
        # Log error and continue with file deletion
        print(f"Error deleting embeddings for {filename}: {e}")

    # 2. Delete from disk
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from disk: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return {"status": "success", "message": f"Successfully deleted {filename} and its embeddings."}


if __name__ == "__main__":
    # Start the server on port 8000 when run directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
