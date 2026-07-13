"""Voice transcription endpoints for multilingual coach queries."""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.services.language_service import transcribe_audio
from backend.services.voice_assistant_service import handle_voice_query

router = APIRouter()

class VoiceAssistantRequest(BaseModel):
    user_id: str = "demo-user"
    transcript: str = Field(..., min_length=1, max_length=1000)
    caller: str = "+91XXXXXXXXXX"
    detected_language: str | None = None


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    source_language: str | None = Form(default=None),
) -> dict:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded audio is empty.")
    return await transcribe_audio(
        content,
        file.filename or "voice.webm",
        file.content_type,
        source_language=source_language,
    )


@router.post("/assistant")
async def voice_assistant(request: VoiceAssistantRequest) -> dict:
    try:
        return handle_voice_query(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
