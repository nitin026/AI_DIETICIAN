"""Reminder and notification architecture endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.request_models import ReminderRequest
from backend.services.storage_service import storage

router = APIRouter()


@router.post("")
async def create_reminder(request: ReminderRequest) -> dict:
    reminder = storage.append("notifications", request.model_dump())
    return {
        "saved": True,
        "reminder": reminder,
        "delivery_note": (
            "In-app reminders are stored now. Email, push, and WhatsApp can be wired "
            "through this channel field without changing the frontend contract."
        ),
    }


@router.get("/{user_id}")
async def list_reminders(user_id: str) -> dict:
    return {"items": storage.list_records("notifications", user_id)}