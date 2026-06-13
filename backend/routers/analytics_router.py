"""AI health insights and nutrition analytics endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.request_models import AnalyticsRequest
from backend.models.response_models import AnalyticsResponse
from backend.services.nutrient_reference import score_nutrient_adequacy
from backend.services.personalization_service import adherence_summary, build_preference_memory
from backend.services.storage_service import storage

router = APIRouter()


@router.post("", response_model=AnalyticsResponse)
async def analytics(request: AnalyticsRequest) -> AnalyticsResponse:
    feedback = storage.list_records("meal_feedback", request.user_id)
    adherence_records = storage.list_records("adherence_logs", request.user_id)
    adherence = adherence_summary(adherence_records)
    preference_memory = build_preference_memory(feedback)
    targets = request.daily_targets or {}
    adequacy = score_nutrient_adequacy(targets, request.nutrient_intake or targets)

    nutrient_score = adequacy.get("overall_score", 0)
    adherence_score = adherence.get("average_score", 0)
    health_score = round((nutrient_score * 0.55) + (adherence_score * 0.45), 1)
    risk = "low" if adherence_score >= 75 else "medium" if adherence_score >= 45 else "high"

    insights = []
    if adequacy.get("overall_score", 0) < 75:
        insights.append("Several micronutrient targets need attention; add diverse vegetables, pulses, dairy/fortified foods, nuts, and seeds.")
    if adherence.get("skipped_meals", 0) > adherence.get("completed_meals", 0):
        insights.append("Skipped meals are becoming frequent; plan lower-effort backup meals and snacks.")
    if preference_memory.get("disliked_meals"):
        insights.append("Future meal plans should down-rank repeatedly disliked meals.")
    if not insights:
        insights.append("Current nutrition and adherence signals look stable. Keep variety high across grains, pulses, vegetables, fruits, and protein foods.")

    return AnalyticsResponse(
        user_id=request.user_id,
        nutrient_adequacy=adequacy,
        adherence=adherence,
        preference_memory=preference_memory,
        health_score=health_score,
        predicted_adherence_risk=risk,
        insights=insights,
    )