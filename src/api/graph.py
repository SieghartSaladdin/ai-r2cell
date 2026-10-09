import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from src.agents.main_agent import main_graph
from src.core.event_bus import register_callback

router = APIRouter(tags=["graph"])

# ── WebSocket Broadcast Manager ─────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
main_loop = None

@router.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()

# Register event bus callback to broadcast message via WebSocket
def ws_broadcast_callback(message: dict):
    global main_loop
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(message),
            main_loop
        )

register_callback(ws_broadcast_callback)

@router.websocket("/api/graph/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, ignore incoming text messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.get("/api/graph/structure")
def get_graph_structure():
    """
    Retrieve the LangGraph nodes and edges structure dynamically.
    """
    try:
        graph = main_graph.get_graph()
        nodes = []
        for node_id, node in graph.nodes.items():
            name = node.name
            if name == "__start__":
                name = "Receive Message"
            elif name == "__end__":
                name = "Send Message"
            elif name == "tools":
                name = "R2Cell Tool Suite"
            elif name == "call_model":
                name = "AI Model Call"
            
            nodes.append({
                "id": node_id,
                "name": name
            })
        
        edges = []
        for edge in graph.edges:
            edges.append({
                "source": edge.source,
                "target": edge.target,
                "conditional": getattr(edge, 'conditional', False)
            })
            
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph structure: {str(e)}")
