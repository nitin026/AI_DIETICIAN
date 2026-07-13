"""Multimodal upload support for AI coach chat."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.chat_image_service import analyze_chat_upload

router = APIRouter()


@router.post("/chat-image")
async def analyze_chat_image(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        return await analyze_chat_upload(content, file.filename or "upload", file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


from backend.models.response_models import VisualMealAnalysis
from pydantic import BaseModel
from backend.services.storage_service import storage

class AdherenceLogRequest(BaseModel):
    user_id: str
    date: str
    analysis: VisualMealAnalysis


@router.post("/chat-image/log-adherence")
async def log_visual_adherence(request: AdherenceLogRequest) -> dict:
    analysis = request.analysis
    meal_data = {
        "user_id": request.user_id,
        "date": request.date,
        "meal_type": "visual_log",
        "meal_name": analysis.dish_name,
        "status": "completed",
        "calories": analysis.estimated_calories,
        "protein_g": analysis.protein_g,
        "carbs_g": analysis.carbs_g,
        "fat_g": analysis.fat_g,
        "notes": analysis.nutrition_assessment,
    }
    saved = storage.append("adherence_logs", meal_data)
    return {"saved": True, "log": saved}

