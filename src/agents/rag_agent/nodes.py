from langchain_core.messages import SystemMessage
from src.core.llm import get_llm
from src.core.vectorstore import get_vector_store
from src.agents.rag_agent.state import RAGState
from src.agents.rag_agent.prompts import SYSTEM_PROMPT

def retrieve(state: RAGState) -> dict:
    """
    Retrieval Node.
    Extracts the latest user message, queries the persistent Chroma DB using 
    embeddinggemma:latest, and formats the matching chunks as a context block.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"context": ""}
        
    # Get the latest human query
    user_query = messages[-1].content
    print(f"[RAG-Retrieval] Querying ChromaDB for: '{user_query}'...")
    
    try:
        # Load Chroma store and execute similarity search
        store = get_vector_store()
        docs = store.similarity_search(user_query, k=4)
        
        if not docs:
            print("[RAG-Retrieval] No relevant document chunks found.")
            return {"context": ""}
            
        # Format the matching segments
        formatted_chunks = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", 0) + 1
            content = doc.page_content.strip()
            
            import os
            filename = os.path.basename(source)
            
            formatted_chunks.append(
                f"--- Chunk {i+1} [Source: {filename}, Page: {page}] ---\n{content}"
            )
            
        context_str = "\n\n".join(formatted_chunks)
        print(f"[RAG-Retrieval] Successfully loaded {len(docs)} relevant context chunks.")
        return {"context": context_str}
        
    except Exception as e:
        print(f"[RAG-Retrieval] Error querying ChromaDB: {e}")
        return {"context": f"Error occurred during search: {str(e)}"}

def call_model(state: RAGState) -> dict:
    """
    Generation Node (LLM Call).
    Loads the system prompt, formats the retrieved context into the placeholder,
    and queries the Ollama model.
    """
    messages = state.get("messages", [])
    context = state.get("context", "")
    
    # 1. Inject the retrieved context directly into the system template
    templated_prompt = SYSTEM_PROMPT.format(context=context)
    system_message = SystemMessage(content=templated_prompt)
    
    # 2. Package instructions + conversation history
    full_messages = [system_message] + list(messages)
    
    try:
        # Load ChatOllama (low temperature for strictly factual adherence)
        llm = get_llm(temperature=0.1)
        response = llm.invoke(full_messages)
        return {"messages": [response]}
        
    except Exception as e:
        print(f"[RAG-Generation] Error calling LLM: {e}")
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(
            content="I apologize, but I am currently experiencing issues loading our specifications list. Please try again shortly."
        )
        return {"messages": [error_msg]}
