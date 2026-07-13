"""Lightweight multilingual helpers for chat and voice workflows."""
from __future__ import annotations

import os
import re
from typing import Any

import httpx
from loguru import logger

from backend.services import llm_service
from backend.utils.validators import extract_json


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "hinglish": "Hinglish",
}

SUPPORTED_LANGUAGE_CODES = set(LANGUAGE_NAMES)

SCRIPT_RANGES = (("hi", r"[\u0900-\u097F]"),)

HINGLISH_MEDICAL_TERMS = {
    "aata": "wheat flour",
    "atta": "wheat flour",
    "bimari": "medical condition",
    "bp": "blood pressure",
    "chakkar": "dizziness",
    "chawal": "rice",
    "cheeni": "sugar",
    "chini": "sugar",
    "dahi": "curd yogurt",
    "dal": "lentils pulses",
    "dawai": "medicine",
    "dawa": "medicine",
    "gas": "acidity bloating",
    "hb": "hemoglobin",
    "khana": "food meal",
    "kamzori": "weakness fatigue",
    "namak": "salt sodium",
    "nashta": "breakfast",
    "paani": "water",
    "pet": "stomach abdomen",
    "raat": "night dinner",
    "roti": "chapati wheat flatbread",
    "sabzi": "vegetable curry",
    "shaam": "evening",
    "subah": "morning",
    "sugar": "blood glucose diabetes",
    "tel": "oil fat",
    "thakan": "fatigue tiredness",
    "wajan": "weight",
}

HINGLISH_HINTS = {
    "mujhe", "mera", "meri", "mere", "kya", "kaise", "kitna", "nahi", "haan",
    "karu", "karna", "khana", "dawai", "dawa", "roti", "chawal", "dal", "subah",
    "raat", "bimari", "paani", "nashta", "shaam", "chini", "namak", "wajan",
}


def detect_language(text: str) -> str:
    if not text.strip():
        return "en"
    for code, pattern in SCRIPT_RANGES:
        if re.search(pattern, text):
            return code
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if words & HINGLISH_HINTS:
        return "hinglish"
    return "en"


def normalize_language_code(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.strip().lower().split("-")[0]
    return normalized if normalized in SUPPORTED_LANGUAGE_CODES else None


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code or "English")


async def translate_text(text: str, target_language: str = "en", source_language: str | None = None) -> str:
    target_language = normalize_language_code(target_language) or "en"
    source_language = normalize_language_code(source_language) or detect_language(text)
    if not text.strip() or target_language == source_language:
        return text
    if target_language == "hinglish":
        prompt = (
            f"You are a professional medical and nutrition translator. "
            f"Convert the following text from {language_name(source_language)} to Hinglish (Hindi written in Roman/Latin script, mixed with common English medical/nutrition terms) "
            f"for an Indian clinical nutrition application.\n"
            f"STRICT RULES:\n"
            f"- Use ROMAN script only (Latin letters A-Z). DO NOT use Devanagari or any Hindi script characters.\n"
            f"- Combine natural Hindi grammar and phrasing (written in Roman alphabet, e.g., 'aap', 'kaise', 'karna') with common English words for medical, nutrition, and food terms (e.g., 'protein', 'calories', 'blood pressure', 'kidney').\n"
            f"- Preserve all numerical values, units (mg, mcg, kcal), medicine names, and lab values.\n"
            f"- Output ONLY the final converted Hinglish text. Do not add any greeting, explanation, markdown block wrappers, or meta-comments.\n\n"
            f"Text to translate:\n{text}"
        )
    elif target_language == "hi":
        prompt = (
            f"You are a professional medical and nutrition translator. "
            f"Translate the following text from {language_name(source_language)} to Hindi (using Devanagari script) "
            f"for an Indian clinical nutrition application.\n"
            f"STRICT RULES:\n"
            f"- Translate all content into clear, grammatically correct Hindi using Devanagari script.\n"
            f"- Preserve all numerical values, units (mg, mcg, kcal), clinical metrics, specific medical/medicine names, and specific food/ingredient names in their standard form (you can transliterate them into Devanagari if appropriate, e.g., 'Metformin' as 'मेटफॉर्मिन', or keep them as English terms where standard in India).\n"
            f"- Keep the tone professional, helpful, and encouraging.\n"
            f"- Output ONLY the final translated text. Do not add any greeting, explanation, markdown block wrappers, or meta-comments.\n\n"
            f"Text to translate:\n{text}"
        )
    else:
        prompt = (
            f"You are a professional medical and nutrition translator. "
            f"Translate the following text from {language_name(source_language)} to {language_name(target_language)} (English) "
            f"for an Indian clinical nutrition application.\n"
            f"STRICT RULES:\n"
            f"- Translate all content into clear, grammatically correct English.\n"
            f"- Preserve all numerical values, units (mg, mcg, kcal), clinical metrics, specific medical/medicine names (e.g., Metformin, TSH), and specific food/ingredient names (e.g., Paneer, Roti, Dal).\n"
            f"- Keep the tone professional, helpful, and clear.\n"
            f"- Output ONLY the final translated text. Do not add any greeting, explanation, markdown block wrappers, or meta-comments.\n\n"
            f"Text to translate:\n{text}"
        )
    try:
        return await llm_service.generate(prompt, task="translation")
    except Exception as exc:
        logger.warning("Translation failed ({}); returning original text.", exc)
        return text


async def transcribe_audio(
    content: bytes,
    filename: str,
    content_type: str | None = None,
    source_language: str | None = None,
) -> dict[str, Any]:
    """Transcribe regional-language audio and provide an English RAG query."""
    try:
        native_text = await _transcribe_with_groq(content, filename, content_type, source_language)
    except Exception as groq_exc:
        logger.warning("Groq transcription failed ({}); trying Gemini.", groq_exc)
        native_text = await _transcribe_with_gemini(content, filename, content_type, source_language)

    detected = normalize_language_code(source_language) or detect_language(native_text)
    english_text = await translate_text(native_text, "en", detected) if detected != "en" else native_text
    return {
        "transcript": native_text,
        "english_text": english_text,
        "detected_language": detected,
        "language_name": language_name(detected),
    }


def normalize_hinglish_to_english(text: str) -> str:
    """Expand common Hinglish clinical words before English RAG retrieval."""
    if re.search(r"[\u0900-\u097F]", text):
        return text
    tokens = re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    expanded: list[str] = []
    for token in tokens:
        replacement = HINGLISH_MEDICAL_TERMS.get(token.lower())
        expanded.append(f"{token} ({replacement})" if replacement else token)
    return " ".join(expanded)


async def _transcribe_with_groq(
    content: bytes,
    filename: str,
    content_type: str | None,
    source_language: str | None,
) -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise ValueError("GROQ_API_KEY is not configured")
    model = os.environ.get("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
    data = {"model": model, "response_format": "json"}
    normalized_language = normalize_language_code(source_language)
    if normalized_language in {"en", "hi"}:
        data["language"] = normalized_language
    files = {"file": (filename, content, content_type or "audio/webm")}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            data=data,
            files=files,
        )
        response.raise_for_status()
    return response.json().get("text", "").strip()


async def _transcribe_with_gemini(
    content: bytes,
    filename: str,
    content_type: str | None,
    source_language: str | None,
) -> str:
    import base64

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured")
    model = os.environ.get("GEMINI_VOICE_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    prompt = (
        "Transcribe this audio accurately. For Hindi, use Devanagari script. For Hinglish, keep natural "
        "Roman Hindi mixed with English medical words. Return JSON: {\"transcript\":\"...\"}."
    )
    if source_language:
        prompt += f" Expected language: {language_name(source_language)}."
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": content_type or "audio/webm",
                            "data": base64.b64encode(content).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json=payload,
        )
        response.raise_for_status()
    data = response.json()
    raw = "".join(part.get("text", "") for part in data["candidates"][0]["content"].get("parts", []))
    parsed = extract_json(raw)
    return (parsed or {}).get("transcript", "").strip()
