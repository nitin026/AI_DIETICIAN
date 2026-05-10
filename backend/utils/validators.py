"""
utils/validators.py
Input sanitation & JSON-repair utilities.
"""
from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger


def extract_json(raw: str) -> dict | list:
    """
    Extract the first valid JSON object or array from a raw LLM string.
    Handles markdown code fences (```json … ```) and stray text.
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Attempt to locate JSON boundaries
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = cleaned.find(start_char)
        end = cleaned.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start: end + 1])
            except json.JSONDecodeError:
                continue
    logger.error("Could not extract valid JSON from LLM output:\n{}", raw[:500])
    raise ValueError("LLM returned non-parseable JSON.")


def sanitize_string_list(items: list[Any]) -> list[str]:
    """Coerce list items to strings and strip whitespace."""
    return [str(i).strip() for i in items if i]
