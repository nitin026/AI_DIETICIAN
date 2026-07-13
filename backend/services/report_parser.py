"""Clinical report parsing with Gemini multimodal extraction and local fallbacks."""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from backend.utils.validators import extract_json


class BiomarkerData(BaseModel):
    fbs: float | None = Field(default=None, description="Fasting blood sugar, mg/dL")
    hba1c: float | None = Field(default=None, description="HbA1c, percent")
    hemoglobin: float | None = Field(default=None, description="Hemoglobin, g/dL")
    tsh: float | None = Field(default=None, description="TSH, mIU/L")
    cholesterol: float | None = Field(default=None, description="Total cholesterol, mg/dL")
    triglycerides: float | None = Field(default=None, description="Triglycerides, mg/dL")
    creatinine: float | None = Field(default=None, description="Serum creatinine, mg/dL")
    vitamin_d: float | None = Field(default=None, description="25-OH vitamin D, ng/mL")
    vitamin_b12: float | None = Field(default=None, description="Vitamin B12, pg/mL")


BIOMARKER_PATTERNS: dict[str, list[str]] = {
    "fbs": [r"\b(?:fbs|fasting blood sugar|fasting glucose)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "hba1c": [r"\b(?:hba1c|hb a1c|glycated hemoglobin)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "hemoglobin": [r"\b(?:hemoglobin|haemoglobin|hb)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "tsh": [r"\b(?:tsh|thyroid stimulating hormone)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "cholesterol": [r"\b(?:total cholesterol|cholesterol)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "triglycerides": [r"\b(?:triglycerides|tg)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "creatinine": [r"\b(?:creatinine|serum creatinine)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "vitamin_d": [r"\b(?:vitamin d|25[ -]?oh vitamin d)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
    "vitamin_b12": [r"\b(?:vitamin b12|b12|cobalamin)\b[^\d]{0,30}(\d+(?:\.\d+)?)"],
}


def infer_conditions(biomarkers: BiomarkerData) -> list[str]:
    """Infer likely conditions from common adult screening thresholds."""
    conditions: list[str] = []
    values = biomarkers.model_dump()

    if (values.get("hba1c") or 0) >= 6.5 or (values.get("fbs") or 0) >= 126:
        conditions.append("Type-2 Diabetes")
    elif (values.get("hba1c") or 0) >= 5.7 or (values.get("fbs") or 0) >= 100:
        conditions.append("Prediabetes")

    if values.get("hemoglobin") is not None and values["hemoglobin"] < 12:
        conditions.append("Anemia")
    if values.get("tsh") is not None and values["tsh"] > 4.5:
        conditions.append("Hypothyroidism")
    if values.get("cholesterol") is not None and values["cholesterol"] >= 200:
        conditions.append("High Cholesterol")
    if values.get("triglycerides") is not None and values["triglycerides"] >= 150:
        conditions.append("High Triglycerides")
    if values.get("creatinine") is not None and values["creatinine"] > 1.3:
        conditions.append("Possible Kidney Function Concern")
    if values.get("vitamin_d") is not None and values["vitamin_d"] < 20:
        conditions.append("Vitamin D Deficiency")
    if values.get("vitamin_b12") is not None and values["vitamin_b12"] < 200:
        conditions.append("Vitamin B12 Deficiency")

    return list(dict.fromkeys(conditions))


def biomarker_status(name: str, value: float | None) -> str:
    if value is None:
        return "missing"
    if name == "fbs":
        return "high" if value >= 100 else "normal"
    if name == "hba1c":
        return "high" if value >= 5.7 else "normal"
    if name == "hemoglobin":
        return "low" if value < 12 else "normal"
    if name == "tsh":
        return "high" if value > 4.5 else "normal"
    if name == "cholesterol":
        return "high" if value >= 200 else "normal"
    if name == "triglycerides":
        return "high" if value >= 150 else "normal"
    if name == "creatinine":
        return "high" if value > 1.3 else "normal"
    if name == "vitamin_d":
        return "low" if value < 20 else "normal"
    if name == "vitamin_b12":
        return "low" if value < 200 else "normal"
    return "normal"


async def extract_biomarkers_from_file(
    content: bytes,
    filename: str,
    content_type: str | None = None,
) -> BiomarkerData:
    """Extract biomarkers using Gemini 2.5 Flash when available, then regex fallback."""
    content_type = content_type or _guess_mime_type(filename)
    try:
        return await _extract_with_gemini(content, filename, content_type)
    except Exception as exc:
        logger.warning("Gemini report extraction failed ({}); using local fallback.", exc)
        text = _extract_text_locally(content, filename)
        return _extract_with_regex(text)


async def _extract_with_gemini(content: bytes, filename: str, content_type: str) -> BiomarkerData:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured")

    model = os.environ.get("GEMINI_REPORT_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")).strip()
    schema = {field: "number or null" for field in BiomarkerData.model_fields}
    prompt = (
        "Extract only these biomarkers from the attached clinical report. "
        "Return strict JSON with numeric values only, normalized to common Indian lab units "
        "(glucose/cholesterol/triglycerides mg/dL, HbA1c %, hemoglobin g/dL, TSH mIU/L, "
        f"creatinine mg/dL, vitamin D ng/mL, B12 pg/mL). Keys: {json.dumps(schema)}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": content_type,
                            "data": base64.b64encode(content).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    raw = "".join(
        part.get("text", "")
        for part in data["candidates"][0]["content"].get("parts", [])
    )
    parsed: Any = extract_json(raw)
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else {}
    return BiomarkerData(**(parsed or {}))


def _extract_text_locally(content: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz

            with fitz.open(stream=content, filetype="pdf") as doc:
                return "\n".join(page.get_text("text") for page in doc)
        except Exception as exc:
            logger.warning("PyMuPDF text extraction failed: {}", exc)
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_with_regex(text: str) -> BiomarkerData:
    normalized = re.sub(r"\s+", " ", text.lower())
    values: dict[str, float] = {}
    for field, patterns in BIOMARKER_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                values[field] = float(match.group(1))
                break
    return BiomarkerData(**values)


def _guess_mime_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    return "application/octet-stream"
