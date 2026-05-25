from langchain_core.messages import SystemMessage

# Define the chatbot's system persona and instructions
SYSTEM_PROMPT = (
    "You are a helpful, polite, and intelligent AI assistant. "
    "Your goal is to assist the user by answering their questions clearly, "
    "concisely, and with absolute technical accuracy. "
    "Maintain a professional and friendly tone at all times."
)

def get_system_prompt() -> SystemMessage:
    """
    Returns the SystemMessage wrapper containing the system instructions.
    """
    return SystemMessage(content=SYSTEM_PROMPT)
