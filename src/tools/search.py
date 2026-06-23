import os
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.core.vectorstore import get_vector_store
from src.core.event_bus import send_graph_event

@tool
def query_knowledge_base(query: str, config: RunnableConfig = None) -> str:
    """
    Queries the persistent Chroma vector database to search for relevant information
    such as product specifications, features, components, pricing, list tables,
    and business policies. Consolidates the top matching document chunks.
    
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
        
        # Perform similarity search with k=5 to retrieve sufficient context
        results = store.similarity_search(query, k=5)
        
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
