"""Multimodal image/PDF analysis for the AI coach composer."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx


def _mime_type(filename: str, content_type: str | None = None) -> str:
    if content_type:
        return content_type
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


async def analyze_chat_upload(content: bytes, filename: str, content_type: str | None = None) -> dict:
    """Use Gemini multimodal input to summarize an uploaded coach image/report."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is required for chat image analysis.")

    model = os.environ.get("GEMINI_VISION_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")).strip()
    mime_type = _mime_type(filename, content_type)
    prompt = (
        "You are analyzing an upload for an Indian AI dietitian chat. The file may be a food photo, "
        "meal plate, packaged food label, prescription, or lab report.\n"
        "Return a concise clinical/nutrition summary in English with:\n"
        "1. What the image/file appears to show.\n"
        "2. Key nutrition or clinical observations.\n"
        "3. Any safety caveats.\n"
        "4. A suggested user question to ask the chatbot.\n"
        "Do not diagnose from an image alone.\n"
        "Additionally, extract these specific fields into JSON:\n"
        "- dish_name (str)\n"
        "- estimated_calories (float)\n"
        "- protein_g (float)\n"
        "- carbs_g (float)\n"
        "- fat_g (float)\n"
        "- confidence_score (float, 0-1)\n"
        "- nutrition_assessment (str)\n"
        "Return the output as a JSON object with 'summary', 'suggested_message', and 'analysis' (containing the fields above)."
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(content).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1, 
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json"
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json=payload,
        )
        response.raise_for_status()
    import json
    try:
        data = response.json()
        text_content = "".join(
            part.get("text", "")
            for part in data["candidates"][0]["content"].get("parts", [])
        ).strip()
        parsed = json.loads(text_content)
        summary = parsed.get("summary", "")
        suggested = parsed.get("suggested_message", f"Use this uploaded image context and advise me: {summary}")
        analysis = parsed.get("analysis", {})
    except Exception:
        summary = "Could not parse JSON response."
        suggested = "Help me understand this image."
        analysis = {}

    return {
        "filename": filename,
        "content_type": mime_type,
        "summary": summary,
        "suggested_message": suggested,
        "analysis": analysis,
    }
