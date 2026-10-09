import os
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.core.vectorstore import get_vector_store
from src.core.event_bus import send_graph_event

# Chunks scoring below this cosine relevance (1 - distance) are dropped instead of being passed to
# the LLM. This is only a noise floor, not an off-topic gate: with this tiny corpus the right
# answer can score as low as 0.43 (the warranty chunk for short questions) while unrelated
# questions reach 0.53, so any stricter value drops real answers. SEARCH_K covers the whole index
# (7 chunks today). Re-measure both after the corpus grows or the embedding model changes.
MIN_RELEVANCE = float(os.getenv("RAG_MIN_RELEVANCE", "0.40"))
SEARCH_K = 8

@tool
def query_knowledge_base(query: str, config: RunnableConfig = None) -> str:
    """
    Queries the persistent Chroma vector database for company knowledge documents:
    the phone grading guide (Like New, Grade A/B/C+/C criteria), warranty, ordering and
    wholesale information, and other business policies. Consolidates the top matching chunks.
    Do NOT use this for prices or stock levels: use `query_products` for those.
    
    Args:
        query (str): The search query to locate relevant context.

    Returns:
        str: A consolidated string of relevant context chunks or a message stating no match was found.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown") if config else "unknown"
    send_graph_event("tools", "running", thread_id)
    
    try:
        # Obtain persistent vector store instance
        store = get_vector_store()
        
        # Retrieve the top matches with their cosine relevance scores, then drop weak matches
        scored = store.similarity_search_with_relevance_scores(query, k=SEARCH_K)
        results = [doc for doc, score in scored if score >= MIN_RELEVANCE]
        
        if not results:
            return "No relevant information found in the knowledge base."
            
        # Format the retrieved chunks for easy inclusion into prompt contexts
        formatted_chunks = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", 0) + 1  # Standardizing page numbers to 1-indexed
            content = doc.page_content.strip()
            
            # Extract only the filename from the source path
            filename = os.path.basename(source) if source != "Unknown" else "Unknown File"
            
            formatted_chunks.append(
                f"--- Chunk {i+1} [Source: {filename}, Page: {page}] ---\n{content}"
            )
            
        return "\n\n".join(formatted_chunks)
        
    except Exception as e:
        return f"Error occurred while searching the knowledge base: {str(e)}"
    finally:
        send_graph_event("tools", "completed", thread_id)
