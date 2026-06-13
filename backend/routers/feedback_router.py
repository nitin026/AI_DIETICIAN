"""Meal feedback and preference-learning endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.request_models import MealFeedbackRequest
from backend.models.response_models import FeedbackResponse
from backend.services.personalization_service import build_preference_memory
from backend.services.storage_service import storage

router = APIRouter()


@router.post("", response_model=FeedbackResponse)
async def save_feedback(request: MealFeedbackRequest) -> FeedbackResponse:
    record = storage.append("meal_feedback", request.model_dump())
    memory = build_preference_memory(storage.list_records("meal_feedback", request.user_id))
    return FeedbackResponse(saved=True, feedback=record, preference_memory=memory)


@router.get("/{user_id}")
async def list_feedback(user_id: str) -> dict:
    records = storage.list_records("meal_feedback", user_id)
    return {"items": records, "preference_memory": build_preference_memory(records)}