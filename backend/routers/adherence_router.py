"""Calendar adherence, hydration, sleep, mood, digestion, and weight tracking."""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.request_models import AdherenceLogRequest
from backend.models.response_models import AdherenceResponse
from backend.services.personalization_service import adherence_summary
from backend.services.storage_service import storage

router = APIRouter()


@router.post("", response_model=AdherenceResponse)
async def save_adherence(request: AdherenceLogRequest) -> AdherenceResponse:
    record = storage.append("adherence_logs", request.model_dump())
    summary = adherence_summary(storage.list_records("adherence_logs", request.user_id))
    return AdherenceResponse(saved=True, log=record, summary=summary)


@router.get("/{user_id}")
async def list_adherence(user_id: str) -> dict:
    records = storage.list_records("adherence_logs", user_id)
    return {"items": records, "summary": adherence_summary(records)}