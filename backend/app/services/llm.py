import logging
import random
import time
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from ..config import settings

logger = logging.getLogger(__name__)

def invoke_with_retry(
    llm: BaseChatModel,
    payload,
    *,
    max_attempts: int = 6,
    base_delay: float = 1.5,
    max_delay: float = 15.0,
):
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return llm.invoke(payload)
        except Exception as error:
            last_error = error
            if attempt >= max_attempts:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0.0, delay * 0.2)
            logger.warning(
                "LLM request failed (attempt %s/%s): %s. Retrying in %.2fs.",
                attempt,
                max_attempts,
                error,
                delay,
            )
            time.sleep(delay)
    if last_error:
        raise last_error
    raise RuntimeError("LLM request failed without an exception.")

def _provider() -> str:
    return settings.provider

def _require_google_api_key() -> str:
    api_key = (settings.GOOGLE_API_KEY or "").strip()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Configure it to use Gemini without fallback.")
    return api_key

def get_llm(
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    response_mime_type: Optional[str] = None,
) -> BaseChatModel:
    """
    Factory to return a LangChain chat model based on configured provider.
    """
    provider = _provider()
    if provider == "ollama":
        selected_model = model_name or settings.OLLAMA_MODEL
        logger.info(f"Initializing ChatOllama model: {selected_model}")
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=selected_model,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2 if temperature is None else temperature,
            num_predict=max_tokens or settings.OLLAMA_MAX_TOKENS,
            client_kwargs={"timeout": settings.OLLAMA_TIMEOUT_SECONDS},
            keep_alive=settings.OLLAMA_KEEP_ALIVE,
            format="json" if response_mime_type == "application/json" else "",
            reasoning=False,
        )

    api_key = _require_google_api_key()
    selected_model = model_name or settings.GEMINI_MODEL
    logger.info(f"Initializing ChatGoogleGenerativeAI model: {selected_model}")
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=api_key,
        temperature=0.2 if temperature is None else temperature,
        max_tokens=max_tokens or settings.GEMINI_MAX_TOKENS,
        request_timeout=45,
        retries=3,
        response_mime_type=response_mime_type
    )
