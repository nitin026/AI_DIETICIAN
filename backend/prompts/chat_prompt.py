"""Prompt builder for the conversational AI Nutrition Assistant."""
from __future__ import annotations

import json
from typing import Any


CHAT_SYSTEM = """You are an AI Nutrition Assistant for an Indian diet-planning app.
Use the user's health profile, dietary preferences, meal plan, grocery list,
nutrient targets, adherence history, and feedback memory.

Rules:
- Give practical Indian food advice with quantities when possible.
- Be disease-aware for diabetes, hypertension, PCOS, anaemia, CKD, thyroid issues, and obesity.
- You may suggest meal swaps, ingredient swaps, lower-cost alternatives, and meal timing.
- Never diagnose, prescribe, stop medications, or promise cures.
- Add a clear safety warning when the user asks risky medical or medication questions.
- Keep answers concise, supportive, and formatted with markdown bullets when useful.
- When referencing retrieved guidelines, append inline citations using page numbers, e.g., (ICMR-NIN Page X)."""


def build_chat_prompt(
    *,
    message: str,
    user_context: dict[str, Any],
    chat_history: list[dict[str, Any]],
    icmr_context: list[dict],
    safety_prefix: str,
) -> str:
    compact_history = [
        {"role": item.get("role"), "content": item.get("content")}
        for item in chat_history[-12:]
    ]
    compact_user_context = json.dumps(user_context, separators=(",", ":"), default=str)
    compact_recent_history = json.dumps(compact_history, separators=(",", ":"), default=str)
    
    formatted_context = []
    for item in icmr_context:
        formatted_context.append(f"Guideline Excerpt (Source: Page {item['page']}): {item['text']}")
    context_str = chr(10).join(formatted_context) if formatted_context else "No retrieved passage."

    return f"""
Safety baseline:
{safety_prefix}

User context:
{compact_user_context}

Recent conversation:
{compact_recent_history}

Relevant ICMR-NIN 2024 context:
{context_str}

User message:
{message}

Answer as the nutrition assistant. If a meal-plan modification is requested,
state the exact meal/ingredient swap and how it changes calories/macros qualitatively.
"""
