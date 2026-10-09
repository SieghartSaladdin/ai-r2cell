import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables if any
load_dotenv()

# OpenAI-compatible router configuration (see .env)
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://ai.qifor.my.id/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
MODEL_NAME = os.getenv("LLM_MODEL", "COMBO_GEMINI")

def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """
    Initializes and returns a ChatOpenAI client pointed at the OpenAI-compatible router
    and configured for the model named by MODEL_NAME.
    """
    try:
        return ChatOpenAI(
            model=MODEL_NAME,
            base_url=LLM_API_BASE_URL,
            api_key=LLM_API_KEY,
            temperature=temperature,
            timeout=90,
            max_retries=2,
        )
    except Exception as e:
        print(f"Error initializing ChatOpenAI model {MODEL_NAME}: {e}")
        raise e


def warmup_llm() -> None:
    """
    Sends one tiny request to the router so the first real customer message doesn't pay the
    cold-start cost of the model behind it. Failures are logged and ignored: warm-up is best effort.
    """
    import time
    start = time.time()
    try:
        get_llm(temperature=0).bind(max_tokens=5).invoke("ping")
        print(f"[LLM] Warm-up OK in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"[LLM] Warm-up failed (ignored): {e}")
