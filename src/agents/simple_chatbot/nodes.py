from src.core.llm import get_llm
from .state import ChatbotState
from .prompts import get_system_prompt

def call_model(state: ChatbotState) -> dict:
    """
    LangGraph execution node.
    Retrieves the current conversation state, prepends the system prompt,
    invokes the ChatOllama client, and returns the generated response.
    """
    try:
        # Get our initialized Ollama model client
        llm = get_llm()
        
        # Prepend system prompt to the message list for context
        messages = [get_system_prompt()] + state["messages"]
        
        # Invoke the LLM
        response = llm.invoke(messages)
        
        # Return the new message to be appended to the state via the reducer
        return {"messages": [response]}
    except Exception as e:
        print(f"Error in call_model node: {e}")
        # Return a clean user-facing error response to prevent system crashes
        from langchain_core.messages import AIMessage
        error_message = AIMessage(
            content="I apologize, but I encountered an error while trying to process your request."
        )
        return {"messages": [error_message]}
