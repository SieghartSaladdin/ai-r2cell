import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

load_dotenv()

def get_judge_llm(provider: str = None, model: str = None) -> BaseChatModel:
    """
    Initializes the LangChain chat model based on the selected provider.
    Supports 'ollama' and 'openai' (or OpenAI-compatible local/cloud APIs).
    """
    provider = provider or os.getenv("RAG_EVAL_PROVIDER", "ollama").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        model = model or os.getenv("RAG_EVAL_LLM_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")  # Support custom proxy or local vLLM/Ollama endpoints
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.0)
    else:
        # Default to local/cloud Ollama instance
        from langchain_ollama import ChatOllama
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = model or os.getenv("RAG_EVAL_LLM_MODEL", "gemma4:31b-cloud")
        return ChatOllama(model=model, base_url=base_url, temperature=0.0)

def get_judge_embeddings(provider: str = None, model: str = None) -> Embeddings:
    """
    Initializes the LangChain embeddings client.
    """
    provider = provider or os.getenv("RAG_EVAL_PROVIDER", "ollama").lower()
    
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        model = model or os.getenv("RAG_EVAL_EMBED_MODEL", "text-embedding-3-small")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        return OpenAIEmbeddings(model=model, api_key=api_key, base_url=base_url)
    else:
        # Default to Ollama embeddings
        from langchain_ollama import OllamaEmbeddings
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = model or os.getenv("RAG_EVAL_EMBED_MODEL", "embeddinggemma:latest")
        return OllamaEmbeddings(model=model, base_url=base_url)

def get_ragas_wrappers(provider: str = None, llm_model: str = None, embed_model: str = None):
    """
    Returns Ragas-wrapped LLM and Embedding models.
    """
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    
    llm = get_judge_llm(provider, llm_model)
    embeddings = get_judge_embeddings(provider, embed_model)
    
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)
