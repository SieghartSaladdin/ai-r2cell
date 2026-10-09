import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.agents.main_agent import main_graph
from src.agents.main_agent.graph import db_conn
from src.core.gateway_state import gateway_state
from src.core.event_bus import send_graph_event

router = APIRouter(tags=["chat"])

# Input Request Schema
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

# Output Response Schema
class ChatResponse(BaseModel):
    response: str
    session_id: str

@router.get("/api/chat/threads")
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
                state = main_graph.get_state({"configurable": {"thread_id": thread_id}})
                messages = state.values.get("messages", []) if state.values else []
                
                # Filter to only HumanMessage and AIMessage for user-facing lists
                chat_messages = [m for m in messages if m.__class__.__name__ in ("HumanMessage", "AIMessage")]
                
                # Fetch checkpoint creation time from the LangGraph state object
                last_active = state.created_at if hasattr(state, "created_at") else None
                
                last_msg_text = ""
                last_msg_sender = ""
                if chat_messages:
                    last_msg = chat_messages[-1]
                    last_msg_text = last_msg.content
                    last_msg_sender = "AI" if last_msg.__class__.__name__ == "AIMessage" else "User"
                
                threads.append({
                    "thread_id": thread_id,
                    "last_active": last_active,
                    "message_count": len(chat_messages),
                    "last_message": last_msg_text,
                    "last_message_sender": last_msg_sender
                })
            except Exception:
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


@router.get("/api/chat/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    """
    Retrieve all messages for a specific conversation session (thread_id).
    """
    try:
        # Retrieve graph state
        state = main_graph.get_state({"configurable": {"thread_id": thread_id}})
        messages = state.values.get("messages", []) if state.values else []
        
        serialized = []
        for msg in messages:
            # Filter to only HumanMessage and AIMessage to exclude raw tool inputs/outputs
            if msg.__class__.__name__ not in ("HumanMessage", "AIMessage"):
                continue
            sender = "bot" if msg.__class__.__name__ == "AIMessage" else "user"
            serialized.append({
                "sender": sender,
                "text": msg.content,
                "type": msg.__class__.__name__
            })
        return serialized
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")


@router.delete("/api/chat/threads/{thread_id}")
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


@router.delete("/api/chat/threads")
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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST route to converse with the stateful chatbot.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Increment message count
        gateway_state.message_count += 1

        # 1. Configure the checkpointer session via thread ID
        config = {"configurable": {"thread_id": request.session_id}}
        
        # 2. Package user message
        input_state = {"messages": [HumanMessage(content=request.message)]}
        
        # Signal Receive Message node is running
        send_graph_event("__start__", "running", request.session_id)
        await asyncio.sleep(0.3)
        send_graph_event("__start__", "completed", request.session_id)

        # 3. Invoke the compiled graph asynchronously in a background thread to prevent blocking the event loop
        response_state = await asyncio.to_thread(main_graph.invoke, input_state, config=config)
        
        # Signal Send Message node is running
        send_graph_event("__end__", "running", request.session_id)
        await asyncio.sleep(0.3)
        send_graph_event("__end__", "completed", request.session_id)
        
        # 4. Extract the last AI response
        last_message = response_state["messages"][-1]
        
        return ChatResponse(
            response=last_message.content,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")
