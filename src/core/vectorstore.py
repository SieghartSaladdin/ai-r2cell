import os
import re
import shutil
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# OpenAI-compatible router configuration (see .env)
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://ai.qifor.my.id/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini/gemini-embedding-2-preview")

# Configure persistent DB and data directories
# Use paths relative to this file to remain system-agnostic and robust
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(SRC_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "chroma_db")

# check_embedding_ctx_length=False makes the client send raw strings instead of
# OpenAI-specific token ids, which non-OpenAI models behind the router can't read.
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=LLM_API_BASE_URL,
    api_key=LLM_API_KEY,
    check_embedding_ctx_length=False,
)

# Cosine distance makes relevance scores comparable across queries (score = 1 - distance),
# which is what the retrieval threshold in src/tools/search.py relies on.
COLLECTION_NAME = "rag_knowledge_base"
COLLECTION_METADATA = {"hnsw:space": "cosine"}

# Measured on the 10 questions in src/evaluation/questions.json: 1200 puts the answer chunk in the
# top-5 for 9/10 questions (2000 only "works" because it returns almost the whole corpus, and
# 400-800 split answers across chunks so they drop out of the top-5).
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

# Lines produced by "print to PDF" from a browser (timestamp + URL + page counter).
_BROWSER_FOOTER_RE = re.compile(r"(https?://\S+|^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M\b.*)", re.IGNORECASE)
_PRICE_RE = re.compile(r"\$\s?\d[\d,]*")
_PRICE_HEADER_RE = re.compile(r"^Model\s+Storage\s+.*\(USD\)", re.IGNORECASE)
# A page is "fragmented" when its PDF text extraction put words on separate lines.
_FRAGMENTED_BLANK_RATIO = 0.25
# Pages shorter than this after cleaning are leftovers (e.g. orphan section titles of a price table).
_MIN_PAGE_CHARS = 120


def clean_page_text(text: str) -> str:
    """
    Normalizes raw PDF page text before chunking:
    - drops browser print footers (timestamp / URL lines),
    - drops price-table rows and their header: prices live in the SQLite `products` table
      (editable from the dashboard), so a copy in the vector index would go stale,
    - re-flows pages where extraction put (almost) every word on its own line.
    """
    lines = text.split("\n")

    blank = sum(1 for line in lines if not line.strip())
    if lines and blank / len(lines) > _FRAGMENTED_BLANK_RATIO:
        flowed = re.sub(r"\s+", " ", text).strip()
        return re.sub(r"\s*●\s*", "\n● ", flowed).strip()

    kept = []
    for line in lines:
        stripped = line.strip()
        if _BROWSER_FOOTER_RE.search(stripped):
            continue
        if len(_PRICE_RE.findall(stripped)) >= 2 or _PRICE_HEADER_RE.match(stripped):
            continue
        kept.append(re.sub(r"[ \t]+", " ", stripped))
    return "\n".join(kept).strip()


def load_pdf_documents(pdf_path: str) -> list:
    """
    Loads a PDF with PyPDFLoader and cleans every page with `clean_page_text`.
    Pages left without meaningful text (e.g. pure price tables) are skipped.
    """
    docs = []
    for doc in PyPDFLoader(pdf_path).load():
        doc.page_content = clean_page_text(doc.page_content)
        if len(doc.page_content) >= _MIN_PAGE_CHARS:
            docs.append(doc)
    return docs


def get_vector_store() -> Chroma:
    """
    Initializes and returns the persistent Chroma vector store instance.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=DB_DIR,
        collection_metadata=COLLECTION_METADATA,
    )

def ingest_all_pdfs() -> None:
    """
    Scans the src/data/ folder recursively for any .pdf files, loads them using
    PyPDFLoader, splits them using RecursiveCharacterTextSplitter (CHUNK_SIZE /
    CHUNK_OVERLAP), computes embeddings, and stores them in the Chroma index.
    
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
            loaded_docs = load_pdf_documents(pdf_path)
            documents.extend(loaded_docs)
            print(f"Successfully loaded {len(loaded_docs)} pages from {os.path.basename(pdf_path)}.")
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}")

    if not documents:
        print("No document pages could be extracted. Ingestion aborted.")
        return

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
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
            collection_name=COLLECTION_NAME,
            persist_directory=DB_DIR,
            collection_metadata=COLLECTION_METADATA,
        )
        print("Successfully ingested and indexed all document chunks into Chroma database.")
    except Exception as e:
        print(f"Fatal error during Chroma ingestion: {e}")
        raise e

def ingest_single_pdf(pdf_path: str) -> None:
    """
    Loads, splits, and appends a single PDF file to the existing Chroma vector store.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    loaded_docs = load_pdf_documents(pdf_path)
    if not loaded_docs:
        print(f"No pages could be loaded from {pdf_path}")
        return
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(loaded_docs)
    
    # Ensure source metadata uses the exact path
    for chunk in chunks:
        chunk.metadata["source"] = pdf_path
        
    store = get_vector_store()
    store.add_documents(chunks)
    print(f"Successfully ingested and indexed {len(chunks)} chunks from {os.path.basename(pdf_path)}.")

def delete_single_pdf_embeddings(pdf_path: str) -> None:
    """
    Deletes the embedded chunks for a specific PDF from the Chroma vector store.
    """
    store = get_vector_store()
    # Delete from Chroma using metadata filter
    store._collection.delete(where={"source": pdf_path})
    print(f"Deleted embeddings for {pdf_path} from vector store.")

