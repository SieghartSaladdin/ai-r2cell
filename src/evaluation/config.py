import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

load_dotenv()

def get_judge_llm(provider: str = None, model: str = None) -> BaseChatModel:
    """
    Initializes the LangChain chat model based on the selected provider.
    Supports 'router' (default: the same OpenAI-compatible router the app uses, see .env)
    and 'openai' (OpenAI or another OpenAI-compatible API configured via OPENAI_* variables).
    """
    provider = provider or os.getenv("RAG_EVAL_PROVIDER", "router").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        model = model or os.getenv("RAG_EVAL_LLM_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")  # Support custom proxy or local vLLM/Ollama endpoints
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.0)
    else:
        from langchain_openai import ChatOpenAI
        model = model or os.getenv("RAG_EVAL_LLM_MODEL") or os.getenv("LLM_MODEL", "COMBO_GEMINI")
        return ChatOpenAI(
            model=model,
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_API_BASE_URL"),
            temperature=0.0,
            timeout=120,
        )

def get_judge_embeddings(provider: str = None, model: str = None) -> Embeddings:
    """
    Initializes the LangChain embeddings client.
    """
    provider = provider or os.getenv("RAG_EVAL_PROVIDER", "router").lower()
    
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        model = model or os.getenv("RAG_EVAL_EMBED_MODEL", "text-embedding-3-small")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        return OpenAIEmbeddings(model=model, api_key=api_key, base_url=base_url)
    else:
        from langchain_openai import OpenAIEmbeddings
        model = model or os.getenv("RAG_EVAL_EMBED_MODEL") or os.getenv("EMBEDDING_MODEL", "gemini/gemini-embedding-2-preview")
        return OpenAIEmbeddings(
            model=model,
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_API_BASE_URL"),
            check_embedding_ctx_length=False,
        )

def get_ragas_wrappers(provider: str = None, llm_model: str = None, embed_model: str = None):
    """
    Returns Ragas-wrapped LLM and Embedding models.
    """
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    
    llm = get_judge_llm(provider, llm_model)
    embeddings = get_judge_embeddings(provider, embed_model)
    
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)
