"""
services/llm_service.py
Unified LLM interface supporting Groq, HuggingFace, and Ollama.
Reads API key directly from environment to bypass any caching issues.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.utils.validators import extract_json

# Force reload .env every time this module is imported
load_dotenv(override=True)


def _get_groq_key() -> str:
    """Read Groq key fresh from environment each call — bypasses lru_cache issues."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    return key


def _get_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "groq").strip()


def _get_groq_model() -> str:
    return os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()


def _get_ollama_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()


def _get_ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.1").strip()


def _get_hf_token() -> str:
    return os.environ.get("HF_API_TOKEN", "").strip()


def _get_hf_model() -> str:
    return os.environ.get("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3").strip()


def _get_timeout() -> int:
    return int(os.environ.get("LLM_TIMEOUT_SECONDS", "120"))


def _get_max_retries() -> int:
    return int(os.environ.get("LLM_MAX_RETRIES", "3"))


def _retry_decorator():
    return retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(_get_max_retries()),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )


@_retry_decorator()
async def call_groq(prompt: str, system: str = "") -> str:
    """Call Groq API (free, fast — recommended)."""
    key = _get_groq_key()

    if not key:
        raise ValueError(
            "\n\n❌ GROQ_API_KEY is empty!\n"
            "Make sure your .env file contains:\n"
            "GROQ_API_KEY=gsk_your_actual_key_here\n"
            "Get a free key at: https://console.groq.com\n"
        )

    model = _get_groq_model()
    logger.debug("Calling Groq | model={} | prompt_len={}", model, len(prompt))

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=_get_timeout()) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 8000,
            },
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        logger.debug("Groq response received | len={}", len(result))
        return result


@_retry_decorator()
async def call_huggingface(prompt: str, system: str = "") -> str:
    """Call HuggingFace Router API (new 2025 format)."""
    token = _get_hf_token()
    model = _get_hf_model()

    if not token:
        raise ValueError("HF_API_TOKEN is empty in .env")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=_get_timeout()) as client:
        response = await client.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 2048,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


@_retry_decorator()
async def call_ollama(prompt: str, system: str = "") -> str:
    """Call local Ollama server."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=_get_timeout()) as client:
        response = await client.post(
            f"{_get_ollama_url()}/api/chat",
            json={
                "model": _get_ollama_model(),
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def generate(prompt: str, system: str = "") -> str:
    """Route to the configured LLM provider."""
    provider = _get_provider()
    logger.info("LLM provider: {} | prompt_len: {}", provider, len(prompt))

    if provider == "groq":
        return await call_groq(prompt, system)
    elif provider == "huggingface":
        return await call_huggingface(prompt, system)
    elif provider == "ollama":
        return await call_ollama(prompt, system)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use: groq | huggingface | ollama")


async def generate_json(prompt: str, system: str = "") -> Any:
    """Generate and parse a JSON response from the LLM."""
    raw = await generate(prompt, system)
    return extract_json(raw)