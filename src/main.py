import sys
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agents.rag_agent import rag_graph
from src.core.vectorstore import ingest_all_pdfs

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
        response_state = rag_graph.invoke(input_state, config=config)
        
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
        # Trigger dynamic vector store ingestion
        ingest_all_pdfs()
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

if __name__ == "__main__":
    # Start the server on port 8000 when run directly
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
