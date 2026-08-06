import os
from typing import Any
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from config import settings
from logger import logger


def get_primary_llm() -> Any:
    """Instantiates the primary agent LLM (Groq with Ollama fallback)."""
    if settings.GROQ_API_KEY:
        try:
            logger.info(f"Initializing Groq LLM model: {settings.GROQ_MODEL}")
            return ChatGroq(
                model=settings.GROQ_MODEL,
                temperature=settings.MODEL_TEMPERATURE,
                api_key=settings.GROQ_API_KEY,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM ({e}), falling back to ChatOllama.")

    logger.info(f"Initializing Ollama LLM model: {settings.OLLAMA_TEXT_MODEL}")
    return ChatOllama(
        model=settings.OLLAMA_TEXT_MODEL,
        temperature=settings.MODEL_TEMPERATURE,
        base_url=settings.OLLAMA_BASE_URL,
    )


def get_guardrail_llm() -> Any:
    """Instantiates the classifier LLM (Ollama or Groq)."""
    logger.info(f"Initializing Guardrail LLM model: {settings.OLLAMA_TEXT_MODEL}")
    return ChatOllama(
        model=settings.OLLAMA_TEXT_MODEL,
        temperature=0.0,
        base_url=settings.OLLAMA_BASE_URL,
    )


def get_vision_llm() -> Any:
    """Instantiates the vision model."""
    logger.info(f"Initializing Vision LLM model: {settings.OLLAMA_VISION_MODEL}")
    return ChatOllama(
        model=settings.OLLAMA_VISION_MODEL,
        temperature=0.0,
        base_url=settings.OLLAMA_BASE_URL,
    )
