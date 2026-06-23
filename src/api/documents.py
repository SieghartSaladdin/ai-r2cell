import os
import shutil
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File
from src.core.vectorstore import ingest_single_pdf, delete_single_pdf_embeddings

router = APIRouter(tags=["documents"])

@router.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    """
    POST route to upload a PDF document and trigger dynamic vector store indexing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Define the destination directory (src/data/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

@router.get("/api/docs")
def list_docs():
    """
    Lists all PDF files in the src/data directory.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

@router.get("/api/docs/preview-json/{filename}")
def get_pdf_json(filename: str):
    """
    Serves a PDF document as a base64 encoded JSON response to completely bypass IDM interception.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


@router.delete("/api/docs/{filename}")
def delete_doc(filename: str):
    """
    Deletes a PDF document from disk and removes its embeddings from Chroma.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
