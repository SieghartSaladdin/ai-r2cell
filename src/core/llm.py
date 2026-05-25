import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

# Load environment variables if any
load_dotenv()

# Get Ollama base URL if specified, otherwise default to local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = "gemma4:31b-cloud"

def get_llm(temperature: float = 0.7) -> ChatOllama:
    """
    Initializes and returns a ChatOllama LLM client configured for the gemma4:31b-cloud model.
    """
    try:
        # ChatOllama connects to the local Ollama instance
        return ChatOllama(
            model=MODEL_NAME,
            base_url=OLLAMA_BASE_URL,
            temperature=temperature,
            verbose=True
        )
    except Exception as e:
        print(f"Error initializing ChatOllama model {MODEL_NAME}: {e}")
        raise e
