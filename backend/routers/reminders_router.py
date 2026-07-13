"""Reminder and notification architecture endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.request_models import ReminderRequest
from backend.services.storage_service import storage
from backend.services.reminder_automation_service import active_reminders, dispatch_active_reminders, dispatch_reminder, reminder_templates

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

@router.get("/templates/list")
async def list_reminder_templates() -> dict:
    return {"templates": reminder_templates()}


@router.get("/active/{user_id}")
async def list_active_reminders(user_id: str) -> dict:
    return {"items": active_reminders(user_id)}


@router.post("/dispatch/{reminder_id}")
async def dispatch_single_reminder(reminder_id: str) -> dict:
    reminders = storage.list_records("reminders")
    reminder = next((item for item in reminders if item.get("id") == reminder_id), None)
    if not reminder:
        return {"dispatched": False, "error": "Reminder not found"}
    return dispatch_reminder(reminder)


@router.post("/dispatch-active")
async def dispatch_all_active_reminders(user_id: str | None = None) -> dict:
    return dispatch_active_reminders(user_id)
