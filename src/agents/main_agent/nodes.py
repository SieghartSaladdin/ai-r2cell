from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from src.core.llm import get_llm
from src.agents.main_agent.state import MainState
from src.agents.main_agent.prompts import SYSTEM_PROMPT
from src.core.event_bus import send_graph_event
from src.tools.search import query_knowledge_base
from src.tools.booking import query_products, book_cod_appointment, get_bandung_gmaps_location

def call_model(state: MainState, config: RunnableConfig = None) -> dict:
    """
    Generation Node (LLM Call).
    Prepend system prompt and calls the Ollama model with bound RAG and booking tools.
    The model dynamically decides which tools to invoke.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown") if config else "unknown"
    send_graph_event("call_model", "running", thread_id)
    
    try:
        messages = state.get("messages", [])
        
        # 1. Load LLM client and bind the search and booking/inventory tools
        llm = get_llm(temperature=0.1)
        llm_with_tools = llm.bind_tools([
            query_knowledge_base,
            query_products,
            book_cod_appointment,
            get_bandung_gmaps_location
        ])
        
        # 2. Prepend system persona instructions to conversation history
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        full_messages = [system_message] + list(messages)
        
        # 3. Invoke LLM client
        response = llm_with_tools.invoke(full_messages)
        return {"messages": [response]}
        
    except Exception as e:
        print(f"[MainAgent-Generation] Error calling LLM: {e}")
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(
            content="I apologize, but I am currently experiencing issues loading our services. Please try again shortly."
        )
        return {"messages": [error_msg]}
    finally:
        send_graph_event("call_model", "completed", thread_id)
