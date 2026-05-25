import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agents.simple_chatbot import chatbot_graph

app = FastAPI(
    title="LangGraph Chatbot API",
    description="Thin API layer wrapper around the stateful modular LangGraph chatbot.",
    version="1.0.0"
)

# Input Request Schema
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

# Output Response Schema
class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.get("/")
def read_root():
    return {"status": "online", "model": "gemma4:31b-cloud", "engine": "LangGraph"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    POST route to converse with the stateful chatbot.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # 1. Configure the checkpointer session via thread ID
        config = {"configurable": {"thread_id": request.session_id}}
        
        # 2. Package user message
        input_state = {"messages": [HumanMessage(content=request.message)]}
        
        # 3. Invoke the compiled graph with persistent thread context
        response_state = chatbot_graph.invoke(input_state, config=config)
        
        # 4. Extract the last AI response
        last_message = response_state["messages"][-1]
        
        return ChatResponse(
            response=last_message.content,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

if __name__ == "__main__":
    # Start the server on port 8000 when run directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
