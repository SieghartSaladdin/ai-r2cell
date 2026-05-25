import os
import shutil
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Get Ollama base URL if specified, otherwise default to local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Configure persistent DB and data directories
# Use paths relative to this file to remain system-agnostic and robust
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(SRC_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "chroma_db")

# Initialize OllamaEmbeddings for embeddinggemma:latest
embeddings = OllamaEmbeddings(
    model="embeddinggemma:latest",
    base_url=OLLAMA_BASE_URL
)

def get_vector_store() -> Chroma:
    """
    Initializes and returns the persistent Chroma vector store instance.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    return Chroma(
        collection_name="rag_knowledge_base",
        embedding_function=embeddings,
        persist_directory=DB_DIR
    )

def ingest_all_pdfs() -> None:
    """
    Scans the src/data/ folder recursively for any .pdf files, loads them using
    PyPDFLoader, splits them using RecursiveCharacterTextSplitter (chunk_size=1000,
    chunk_overlap=200), computes embeddings, and stores them in the Chroma index.
    
    Ensures idempotency by deleting and recreating the database persistence folder.
    """
    if not os.path.exists(DATA_DIR):
        print(f"Data directory {DATA_DIR} does not exist. Creating it.")
        os.makedirs(DATA_DIR, exist_ok=True)
        return

    # Find all .pdf files in DATA_DIR
    pdf_files = []
    for root, _, files in os.walk(DATA_DIR):
        # Skip chroma_db folder itself to avoid scanning internal DB structures (though they aren't PDFs)
        if "chroma_db" in root:
            continue
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))

    if not pdf_files:
        print(f"No PDF files found to ingest in {DATA_DIR}")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process:")
    for pdf in pdf_files:
        print(f" - {os.path.basename(pdf)}")

    # Load and extract documents from PDFs
    documents = []
    for pdf_path in pdf_files:
        try:
            print(f"Loading document: {os.path.basename(pdf_path)}...")
            loader = PyPDFLoader(pdf_path)
            loaded_docs = loader.load()
            documents.extend(loaded_docs)
            print(f"Successfully loaded {len(loaded_docs)} pages from {os.path.basename(pdf_path)}.")
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}")

    if not documents:
        print("No document pages could be extracted. Ingestion aborted.")
        return

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Successfully split into {len(chunks)} text chunks.")

    # Idempotence: Clear the existing Chroma persistent DB if it exists
    if os.path.exists(DB_DIR):
        print(f"Clearing existing vector database at {DB_DIR} to ensure idempotence...")
        try:
            shutil.rmtree(DB_DIR)
            print("Existing database directory removed successfully.")
        except Exception as e:
            print(f"Warning: Could not remove persistent directory {DB_DIR}: {e}")
            print("Attempting alternate collection deletion...")
            try:
                store = get_vector_store()
                store.delete_collection()
                print("Collection deleted successfully via client.")
            except Exception as collection_err:
                print(f"Failed to delete collection via client: {collection_err}")

    # Re-create database folder
    os.makedirs(DB_DIR, exist_ok=True)

    # Initialize Chroma index and compute embeddings for chunks
    print("Computing embeddings and indexing chunks into Chroma...")
    try:
        store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name="rag_knowledge_base",
            persist_directory=DB_DIR
        )
        print("Successfully ingested and indexed all document chunks into Chroma database.")
    except Exception as e:
        print(f"Fatal error during Chroma ingestion: {e}")
        raise e
