from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings


def get_llm() -> BaseChatModel:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=settings.GEMINI_API_KEY,
    )
    return llm
