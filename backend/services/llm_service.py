"""
services/llm_service.py
Unified LLM interface supporting Gemini, Groq, HuggingFace, and Ollama.
Reads API keys directly from environment to bypass any caching issues.
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
    return os.environ.get("LLM_PROVIDER", "groq").strip().lower()


def _get_task_provider(task: str | None = None, provider: str | None = None) -> str:
    """Resolve the best provider for a specific task, falling back to LLM_PROVIDER."""
    if provider:
        return provider.strip().lower()
    if task:
        env_key = f"{task.upper()}_LLM_PROVIDER"
        configured = os.environ.get(env_key, "").strip().lower()
        if configured:
            return configured
    return _get_provider()


def get_task_model(task: str) -> tuple[str, str]:
    """Return the configured provider and model name for status reporting."""
    provider = _get_task_provider(task=task)
    models = {
        "gemini": _get_gemini_model,
        "groq": _get_groq_model,
        "huggingface": _get_hf_model,
        "biomistral": _get_biomistral_model,
        "ollama": _get_ollama_model,
    }
    getter = models.get(provider)
    return provider, getter() if getter else "unknown"


def _get_task_fallback_provider(task: str | None = None, provider: str | None = None) -> str:
    if provider:
        return provider.strip().lower()
    if task:
        env_key = f"{task.upper()}_FALLBACK_LLM_PROVIDER"
        configured = os.environ.get(env_key, "").strip().lower()
        if configured:
            return configured
    return ""


def _get_gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _get_gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()


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


def _get_biomistral_model() -> str:
    return os.environ.get("BIOMISTRAL_MODEL_ID", "m/biomistral").strip()


def _get_biomistral_url() -> str:
    return os.environ.get("BIOMISTRAL_BASE_URL", _get_ollama_url()).strip()


def _get_biomistral_meal_schema() -> dict[str, Any]:
    meal = {
        "type": "object",
        "properties": {
            "n": {
                "type": "string",
                "description": "Specific authentic Indian dish name, never a generic meal label",
            },
            "i": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Three to five ingredients used by the named dish",
            },
        },
        "required": ["n", "i"],
    }
    return {
        "type": "object",
        "properties": {
            key: meal for key in ("b", "m", "l", "e", "d")
        },
        "required": ["b", "m", "l", "e", "d"],
    }


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
async def call_gemini(prompt: str, system: str = "", *, json_mode: bool = False) -> str:
    """Call Google Gemini via the Generative Language REST API."""
    key = _get_gemini_key()

    if not key:
        raise ValueError(
            "\n\nGEMINI_API_KEY is empty.\n"
            "Add this to your .env file:\n"
            "GEMINI_API_KEY=your_google_ai_studio_key_here\n"
            "LLM_PROVIDER=gemini\n"
            "GEMINI_MODEL=gemini-2.5-flash\n"
        )

    model = _get_gemini_model()
    logger.debug("Calling Gemini | model={} | prompt_len={}", model, len(prompt))

    payload: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
        },
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=_get_timeout()) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    parts = data["candidates"][0]["content"].get("parts", [])
    result = "".join(part.get("text", "") for part in parts).strip()
    logger.debug("Gemini response received | len={}", len(result))
    return result


@_retry_decorator()
async def call_groq(prompt: str, system: str = "", *, json_mode: bool = False) -> str:
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

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": int(os.environ.get("GROQ_MAX_TOKENS", "8000")),
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=_get_timeout()) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        logger.debug("Groq response received | len={}", len(result))
        return result


@_retry_decorator()
async def call_huggingface(prompt: str, system: str = "", *, model: str | None = None) -> str:
    """Call HuggingFace Router API (new 2025 format)."""
    token = _get_hf_token()
    model = model or _get_hf_model()

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


async def call_biomistral(prompt: str, system: str = "") -> str:
    """Call the completion-only local BioMistral model through Ollama."""
    timeout = int(os.environ.get("BIOMISTRAL_TIMEOUT_SECONDS", "300"))
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{_get_biomistral_url()}/api/generate",
            json={
                "model": _get_biomistral_model(),
                "system": system,
                "prompt": prompt,
                "stream": False,
                "format": _get_biomistral_meal_schema(),
                "options": {
                    "temperature": 0,
                    "num_predict": int(os.environ.get("BIOMISTRAL_MAX_TOKENS", "500")),
                },
            },
        )
        if response.status_code == 404:
            raise ValueError(
                f"BioMistral model '{_get_biomistral_model()}' is not installed. "
                f"Run: ollama pull {_get_biomistral_model()}"
            )
        response.raise_for_status()
        return response.json()["response"]


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


async def generate(
    prompt: str,
    system: str = "",
    *,
    task: str | None = None,
    provider: str | None = None,
) -> str:
    """Route to the configured LLM provider."""
    provider = _get_task_provider(task=task, provider=provider)
    task_label = task or "default"
    logger.info("LLM task: {} | provider: {} | prompt_len: {}", task_label, provider, len(prompt))

    async def call_text_provider(provider_name: str) -> str:
        if provider_name == "groq":
            return await call_groq(prompt, system)
        if provider_name == "gemini":
            return await call_gemini(prompt, system)
        if provider_name == "huggingface":
            return await call_huggingface(prompt, system)
        if provider_name == "biomistral":
            return await call_biomistral(prompt, system)
        if provider_name == "ollama":
            return await call_ollama(prompt, system)
        raise ValueError(f"Unknown LLM_PROVIDER '{provider_name}'. Use: gemini | groq | huggingface | biomistral | ollama")

    try:
        return await call_text_provider(provider)
    except Exception as exc:
        fallback_provider = _get_task_fallback_provider(task)
        if not fallback_provider or fallback_provider == provider:
            raise
        logger.warning(
            "LLM task '{}' failed on provider '{}' ({}); trying fallback provider '{}'.",
            task_label,
            provider,
            exc,
            fallback_provider,
        )
        return await call_text_provider(fallback_provider)


async def generate_json(
    prompt: str,
    system: str = "",
    *,
    task: str | None = None,
    provider: str | None = None,
) -> Any:
    """Generate and parse a JSON response from the LLM."""
    provider = _get_task_provider(task=task, provider=provider)
    task_label = task or "default_json"
    logger.info("LLM JSON task: {} | provider: {} | prompt_len: {}", task_label, provider, len(prompt))

    async def call_json_provider(provider_name: str) -> str:
        if provider_name == "gemini":
            return await call_gemini(prompt, system, json_mode=True)
        if provider_name == "groq":
            return await call_groq(prompt, system, json_mode=True)
        if provider_name == "huggingface":
            return await call_huggingface(prompt, system)
        if provider_name == "biomistral":
            return await call_biomistral(prompt, system)
        if provider_name == "ollama":
            return await call_ollama(prompt, system)
        raise ValueError(f"Unknown LLM_PROVIDER '{provider_name}'. Use: gemini | groq | huggingface | biomistral | ollama")

    try:
        raw = await call_json_provider(provider)
    except Exception as exc:
        fallback_provider = _get_task_fallback_provider(task)
        if not fallback_provider or fallback_provider == provider:
            raise
        logger.warning(
            "LLM JSON task '{}' failed on provider '{}' ({}); trying fallback provider '{}'.",
            task_label,
            provider,
            exc,
            fallback_provider,
        )
        raw = await call_json_provider(fallback_provider)
    return extract_json(raw)
