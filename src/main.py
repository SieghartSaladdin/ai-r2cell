import sys
import os
import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.metrics import metrics_state
from src.api.chat import router as chat_router
from src.api.documents import router as doc_router
from src.api.gateway import router as gateway_router
from src.api.graph import router as graph_router
from src.core.database import init_db
from src.api.products import router as products_router
from src.api.bookings import router as bookings_router

# Initialize the SQLite database on startup
init_db()


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
@app.middleware("http")
async def track_health_metrics(request, call_next):
    path = request.url.path
    # Track active connections (clients seen in last 5 seconds)
    client_ip = request.client.host if request.client else "unknown"
    metrics_state.active_clients[client_ip] = time.time()
    
    # Exclude internal metrics/polling requests from counting towards general API load
    if not any(k in path for k in ("/api/internal/status", "/wa/status", "/logs/")):
        metrics_state.request_count += 1
        metrics_state.last_request_time = time.time()
        
    response = await call_next(request)
    return response

# CORS middleware so Vue frontend can communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to your actual Vue frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Modular API Routers ───────────────────────
app.include_router(chat_router)
app.include_router(doc_router)
app.include_router(gateway_router)
app.include_router(graph_router)
app.include_router(products_router)
app.include_router(bookings_router)


@app.get("/")
def read_root():
    return {"status": "online", "model": "gemma4:31b-cloud", "engine": "LangGraph"}


if __name__ == "__main__":
    # Start the server on port 8000 when run directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
