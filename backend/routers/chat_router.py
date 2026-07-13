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
from backend.services.language_service import (
    detect_language,
    language_name,
    normalize_hinglish_to_english,
    normalize_language_code,
    translate_text,
)
from backend.services.personalization_service import build_preference_memory
from backend.services.storage_service import storage

router = APIRouter()


MAX_HISTORY_CHARS = 1200
MAX_GROCERY_ITEMS = 30
MAX_MEAL_PLAN_DAYS = 2
MEAL_CONTEXT_KEYWORDS = (
    "meal",
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "diet",
    "plan",
    "swap",
    "replace",
    "ingredient",
    "recipe",
    "calorie",
    "calories",
    "macro",
    "protein",
    "carb",
    "fat",
)
GROCERY_CONTEXT_KEYWORDS = (
    "grocery",
    "groceries",
    "shopping",
    "buy",
    "pantry",
    "ingredient",
    "ingredients",
    "list",
    "cost",
    "budget",
)
CLINICAL_KEYWORDS = (
    "hba1c",
    "fbs",
    "fasting",
    "glucose",
    "sugar",
    "diabetes",
    "prediabetes",
    "bp",
    "blood pressure",
    "cholesterol",
    "triglyceride",
    "creatinine",
    "kidney",
    "hemoglobin",
    "anaemia",
    "anemia",
    "tsh",
    "thyroid",
    "vitamin",
    "b12",
    "medicine",
    "medication",
    "drug",
    "dose",
    "metformin",
    "statin",
    "levothyroxine",
    "report",
    "lab",
    "test",
    "safe",
    "warning",
    "dawai",
    "dawa",
    "bimari",
)


def _short_text(value: object, limit: int = MAX_HISTORY_CHARS) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _needs_context(message: str, keywords: tuple[str, ...]) -> bool:
    text = message.lower()
    return any(keyword in text for keyword in keywords)


def _compact_meal_plan(meal_plan: dict | None, max_days: int = MAX_MEAL_PLAN_DAYS) -> dict | None:
    """Keep chat context small enough for LLM calls."""
    if not meal_plan:
        return None

    compact_week = []
    for day in meal_plan.get("week", [])[:max_days]:
        compact_day = {"day": day.get("day")}
        for meal_key in ("breakfast", "mid_morning_snack", "lunch", "evening_snack", "dinner"):
            meal = day.get(meal_key, {})
            compact_day[meal_key] = {
                "name": meal.get("name"),
                "calories": meal.get("calories"),
                "protein_g": meal.get("protein_g"),
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


def _is_clinical_query(message: str, context: dict) -> bool:
    text = message.lower()
    if any(keyword in text for keyword in CLINICAL_KEYWORDS):
        return True
    profile = context.get("health_profile") or {}
    if isinstance(profile, dict) and profile.get("lab_report") and any(word in text for word in ("diet", "meal", "eat", "avoid")):
        return True
    return False


def _compact_lab_report(report: dict | None) -> dict | None:
    if not isinstance(report, dict):
        return None
    biomarkers = {
        key: value
        for key, value in (report.get("biomarkers") or {}).items()
        if value is not None
    }
    return {
        "biomarkers": biomarkers,
        "statuses": report.get("statuses") or {},
        "inferred_conditions": report.get("inferred_conditions") or [],
    } if biomarkers else None


def _build_patient_ehr_context(user_id: str, context: dict, history: list[dict]) -> dict:
    health_profile = context.get("health_profile") or {}
    preference_profile = context.get("preference_profile") or {}
    recent_consultations = [
        {
            "role": item.get("role"),
            "content": _short_text(item.get("content"), 500),
            "created_at": item.get("created_at"),
        }
        for item in history[-8:]
    ]
    return {
        "user_id": user_id,
        "structured_profile": {
            "age": health_profile.get("age") if isinstance(health_profile, dict) else None,
            "gender": health_profile.get("gender") if isinstance(health_profile, dict) else None,
            "height_cm": health_profile.get("height_cm") if isinstance(health_profile, dict) else None,
            "weight_kg": health_profile.get("weight_kg") if isinstance(health_profile, dict) else None,
            "activity_level": health_profile.get("activity_level") if isinstance(health_profile, dict) else None,
            "diseases": health_profile.get("diseases", []) if isinstance(health_profile, dict) else [],
            "medications": health_profile.get("medications", []) if isinstance(health_profile, dict) else [],
            "dietary_preference": preference_profile.get("dietary_preference") if isinstance(preference_profile, dict) else None,
            "regional_cuisine": preference_profile.get("regional_cuisine") if isinstance(preference_profile, dict) else None,
        },
        "latest_lab_report": _compact_lab_report(health_profile.get("lab_report") if isinstance(health_profile, dict) else None),
        "daily_targets": context.get("daily_targets"),
        "recent_consultations": recent_consultations,
        "recent_adherence": context.get("adherence_history", [])[-5:],
    }


def _request_profile_updates(request: ChatRequest) -> dict:
    updates = {}
    if request.health_profile:
        updates["health_profile"] = request.health_profile.model_dump()
    if request.preference_profile:
        updates["preference_profile"] = request.preference_profile.model_dump()
    if request.daily_targets:
        updates["daily_targets"] = request.daily_targets
    if request.meal_plan:
        updates["meal_plan"] = request.meal_plan
    if request.grocery_list:
        updates["grocery_list"] = request.grocery_list
    return updates


def _context_from_request(request: ChatRequest) -> dict:
    user_id = request.user_id or get_settings().default_user_id
    feedback = storage.list_records("meal_feedback", user_id)
    adherence = storage.list_records("adherence_logs", user_id)
    saved_profile = storage.get_profile(user_id)
    profile_updates = _request_profile_updates(request)
    if profile_updates:
        saved_profile = storage.upsert_profile(user_id, profile_updates)

    include_meal_plan = bool(request.meal_plan) or _needs_context(request.message, MEAL_CONTEXT_KEYWORDS)
    include_grocery_list = bool(request.grocery_list) or _needs_context(request.message, GROCERY_CONTEXT_KEYWORDS)

    profile_context = {
        "health_profile": saved_profile.get("health_profile"),
        "preference_profile": saved_profile.get("preference_profile"),
        "daily_targets": saved_profile.get("daily_targets"),
        "meal_plan": (
            _compact_meal_plan(request.meal_plan or saved_profile.get("meal_plan"))
            if include_meal_plan
            else None
        ),
        "grocery_list": (
            _compact_grocery_list(request.grocery_list or saved_profile.get("grocery_list"))
            if include_grocery_list
            else None
        ),
        "feedback_memory": build_preference_memory(feedback),
        "adherence_history": adherence[-10:],
    }

    return profile_context


async def _answer(request: ChatRequest) -> ChatResponse:
    user_id = request.user_id or get_settings().default_user_id
    user_context = _context_from_request(request)
    detected_language = normalize_language_code(request.preferred_language) or detect_language(request.message)
    english_message = (
        await translate_text(request.message, "en", detected_language)
        if detected_language != "en"
        else request.message
    )
    rag_message = normalize_hinglish_to_english(english_message if detected_language != "hinglish" else request.message)

    storage.append(
        "chat_messages",
        {"user_id": user_id, "role": "user", "content": request.message},
    )

    history = storage.list_records("chat_messages", user_id)[-6:]
    compact_history = _compact_chat_history(history)
    ehr_context = _build_patient_ehr_context(user_id, user_context, history)

    health_profile = user_context.get("health_profile") or {}
    medications = health_profile.get("medications", []) if isinstance(health_profile, dict) else []

    warnings = medication_warnings(medications)
    if safety_response_needed(rag_message):
        warnings.append(
            "Please involve your clinician before changing medicines, fasting, or using extreme diets."
        )

    query = f"{rag_message} Indian nutrition ICMR-NIN diet disease meal planning biomarkers medicines"
    icmr_context = retrieve(query, k=4)

    prompt = build_chat_prompt(
        message=english_message,
        user_context=user_context,
        chat_history=compact_history,
        icmr_context=icmr_context,
        safety_prefix=build_safety_prefix(medications),
    )
    prompt += (
        "\n\nPatient EHR-style context for grounding (do not invent missing data):\n"
        f"{ehr_context}\n\n"
        "Use this context only when relevant. If lab values or medicines imply risk, explain the risk plainly "
        "and recommend clinician confirmation before changing medicines or supplements."
    )
    if detected_language != "en":
        prompt += (
            f"\n\nThe user asked in {language_name(detected_language)}. Reason over the English "
            "RAG context above, but keep the clinical advice culturally appropriate for India. "
            "The final answer will be translated back to the user's language."
        )
    else:
        prompt += "\n\nThe user asked in English. Please reply in English."
    task = "clinical" if _is_clinical_query(rag_message, user_context) else "chat"

    try:
        answer = await llm_service.generate(prompt, system=CHAT_SYSTEM, task=task)
    except Exception as exc:
        if task == "clinical":
            logger.warning("Clinical LLM failed ({}); falling back to chat model.", exc)
            try:
                answer = await llm_service.generate(prompt, system=CHAT_SYSTEM, task="chat")
            except Exception:
                logger.exception("Chat fallback failed")
                answer = ""
        else:
            logger.exception("Chat LLM failed")
            answer = ""
    if not answer:
        answer = (
            "I could not reach the AI model, so here is a safe baseline: keep meals balanced "
            "with dal/curd/eggs or lean protein, vegetables, whole grains or millets, and avoid "
            "changing medication or disease-specific restrictions without clinician guidance."
        )

    if warnings:
        answer = "**Health warning:** " + " ".join(warnings) + "\n\n" + answer
    if detected_language != "en":
        answer = await translate_text(answer, detected_language, "en")

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
        detected_language=detected_language,
        english_message=english_message if detected_language != "en" else None,
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
