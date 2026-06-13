"""Conversational AI nutrition assistant endpoints."""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger

from backend.config import get_settings
from backend.models.request_models import ChatRequest
from backend.models.response_models import ChatResponse
from backend.prompts.chat_prompt import CHAT_SYSTEM, build_chat_prompt
from backend.rag.retriever import retrieve
from backend.services import llm_service
from backend.services.health_warning_service import (
    build_safety_prefix,
    medication_warnings,
    safety_response_needed,
)
from backend.services.personalization_service import build_preference_memory
from backend.services.storage_service import storage

router = APIRouter()


MAX_HISTORY_CHARS = 1200
MAX_GROCERY_ITEMS = 30


def _short_text(value: object, limit: int = MAX_HISTORY_CHARS) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _compact_meal_plan(meal_plan: dict | None) -> dict | None:
    """Keep chat context small enough for LLM calls."""
    if not meal_plan:
        return None

    compact_week = []
    for day in meal_plan.get("week", []):
        compact_day = {"day": day.get("day")}
        for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
            meal = day.get(meal_key, {})
            compact_day[meal_key] = {
                "name": meal.get("name"),
                "ingredients": meal.get("ingredients", [])[:5],
                "calories": meal.get("calories"),
                "protein_g": meal.get("protein_g"),
                "carbs_g": meal.get("carbs_g"),
                "fat_g": meal.get("fat_g"),
            }
        compact_week.append(compact_day)

    return {"week": compact_week}


def _compact_grocery_list(grocery_list: dict | None) -> dict | None:
    if not isinstance(grocery_list, dict):
        return grocery_list

    compact: dict = {}
    for key, value in grocery_list.items():
        if isinstance(value, list):
            compact[key] = value[:MAX_GROCERY_ITEMS]
        elif isinstance(value, dict):
            compact[key] = dict(list(value.items())[:MAX_GROCERY_ITEMS])
        else:
            compact[key] = value
    return compact


def _compact_chat_history(messages: list[dict]) -> list[dict]:
    return [
        {
            "role": item.get("role"),
            "content": _short_text(item.get("content")),
        }
        for item in messages
    ]


def _context_from_request(request: ChatRequest) -> dict:
    user_id = request.user_id or get_settings().default_user_id
    feedback = storage.list_records("meal_feedback", user_id)
    adherence = storage.list_records("adherence_logs", user_id)
    saved_profile = storage.get_profile(user_id)

    profile_context = {
        "health_profile": (
            request.health_profile.model_dump()
            if request.health_profile
            else saved_profile.get("health_profile")
        ),
        "preference_profile": (
            request.preference_profile.model_dump()
            if request.preference_profile
            else saved_profile.get("preference_profile")
        ),
        "daily_targets": request.daily_targets or saved_profile.get("daily_targets"),
        "meal_plan": _compact_meal_plan(request.meal_plan or saved_profile.get("meal_plan")),
        "grocery_list": _compact_grocery_list(request.grocery_list or saved_profile.get("grocery_list")),
        "feedback_memory": build_preference_memory(feedback),
        "adherence_history": adherence[-10:],
    }

    storage.upsert_profile(user_id, profile_context)
    return profile_context


async def _answer(request: ChatRequest) -> ChatResponse:
    user_id = request.user_id or get_settings().default_user_id
    user_context = _context_from_request(request)

    storage.append(
        "chat_messages",
        {"user_id": user_id, "role": "user", "content": request.message},
    )

    history = storage.list_records("chat_messages", user_id)[-6:]
    compact_history = _compact_chat_history(history)

    health_profile = user_context.get("health_profile") or {}
    medications = health_profile.get("medications", []) if isinstance(health_profile, dict) else []

    warnings = medication_warnings(medications)
    if safety_response_needed(request.message):
        warnings.append(
            "Please involve your clinician before changing medicines, fasting, or using extreme diets."
        )

    query = f"{request.message} Indian nutrition ICMR-NIN diet disease meal planning"
    icmr_context = retrieve(query, k=3)

    prompt = build_chat_prompt(
        message=request.message,
        user_context=user_context,
        chat_history=compact_history,
        icmr_context=icmr_context,
        safety_prefix=build_safety_prefix(medications),
    )

    try:
        answer = await llm_service.generate(prompt, system=CHAT_SYSTEM, task="chat")
    except Exception as exc:
        logger.exception("Chat LLM failed")
        answer = (
            "I could not reach the AI model, so here is a safe baseline: keep meals balanced "
            "with dal/curd/eggs or lean protein, vegetables, whole grains or millets, and avoid "
            "changing medication or disease-specific restrictions without clinician guidance."
        )

    if warnings:
        answer = "**Health warning:** " + " ".join(warnings) + "\n\n" + answer

    saved = storage.append(
        "chat_messages",
        {"user_id": user_id, "role": "assistant", "content": answer},
    )

    return ChatResponse(
        user_id=user_id,
        message_id=saved["id"],
        answer=answer,
        warnings=warnings,
        suggested_actions=[
            "Regenerate this meal",
            "Explain why this meal fits me",
            "Make it cheaper",
            "Reduce sodium",
            "Increase protein",
        ],
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await _answer(request)


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        response = await _answer(request)
        for token in response.answer.split(" "):
            yield f"data: {token} \n\n"
            await asyncio.sleep(0.01)
        yield f"event: done\ndata: {response.message_id}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history/{user_id}")
async def chat_history(user_id: str) -> dict:
    return {"messages": storage.list_records("chat_messages", user_id)}
