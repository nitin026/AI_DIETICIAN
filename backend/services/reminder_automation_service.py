"""Reminder automation helpers for clinic-style patient follow-up workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.communication_service import send_message
from backend.services.storage_service import storage

REMINDER_TEMPLATES = {
    "meal": "Hi {name}, your {meal_type} is due. Suggested: {meal_name}. Reply 1 if completed, 2 if skipped, 3 for an alternative.",
    "hydration": "Hi {name}, hydration check: please drink {water_ml} ml water now if suitable for your doctor-advised fluid limit. Reply 1 when done.",
    "supplement": "Hi {name}, supplement reminder: {supplement_name}. Reply 1 if taken, 2 if skipped.",
    "adherence": "Hi {name}, quick diet check-in. Reply 1 if you followed your plan today, 2 if you missed it, 3 if you need help.",
    "follow_up": "Hi {name}, your dietitian follow-up is due. Reply 'doctor call' if you want a callback.",
}


def reminder_templates() -> dict[str, str]:
    return REMINDER_TEMPLATES


def render_reminder_message(reminder: dict[str, Any]) -> str:
    metadata = reminder.get("metadata") or {}
    reminder_type = reminder.get("reminder_type") or "adherence"
    template = metadata.get("template") or REMINDER_TEMPLATES.get(reminder_type, REMINDER_TEMPLATES["adherence"])
    values = {
        "name": metadata.get("name") or "there",
        "meal_type": metadata.get("meal_type") or "meal",
        "meal_name": metadata.get("meal_name") or reminder.get("title") or "your planned meal",
        "water_ml": metadata.get("water_ml") or 250,
        "supplement_name": metadata.get("supplement_name") or reminder.get("title") or "your supplement",
    }
    try:
        return template.format(**values)
    except Exception:
        return reminder.get("title") or REMINDER_TEMPLATES["adherence"].format(**values)


def active_reminders(user_id: str | None = None) -> list[dict[str, Any]]:
    reminders = storage.list_records("reminders", user_id)
    return [item for item in reminders if item.get("enabled", item.get("is_active", True))]


def dispatch_reminder(reminder: dict[str, Any]) -> dict[str, Any]:
    metadata = reminder.get("metadata") or {}
    channel = reminder.get("channel") or metadata.get("channel") or "sms"
    if channel == "whatsapp_ready":
        channel = "whatsapp"
    payload = {
        "user_id": reminder.get("user_id", "demo-user"),
        "channel": channel,
        "recipient": metadata.get("recipient") or metadata.get("phone") or "+91XXXXXXXXXX",
        "message_type": f"{reminder.get('reminder_type', 'adherence')}_reminder",
        "content": render_reminder_message(reminder),
        "related_reminder_id": reminder.get("id"),
        "metadata": {
            **metadata,
            "reminder_title": reminder.get("title"),
            "reminder_schedule": reminder.get("schedule") or reminder.get("time"),
            "automation_dispatched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    return send_message(payload)


def dispatch_active_reminders(user_id: str | None = None) -> dict[str, Any]:
    reminders = active_reminders(user_id)
    sent = []
    for reminder in reminders:
        sent.append(dispatch_reminder(reminder))
    return {"dispatched": len(sent), "items": sent}


def adherence_record_from_reply(message: dict[str, Any]) -> dict[str, Any] | None:
    intent = message.get("intent")
    if intent not in {"adherence_completed", "adherence_skipped"}:
        return None
    metadata = message.get("metadata") or {}
    status = "completed" if intent == "adherence_completed" else "skipped"
    return {
        "user_id": message.get("user_id", "demo-user"),
        "date": datetime.now(timezone.utc).date().isoformat(),
        "meal_type": metadata.get("meal_type") or metadata.get("reminder_type") or "check_in",
        "meal_name": metadata.get("meal_name") or metadata.get("reminder_title") or "Communication check-in",
        "status": status,
        "notes": f"Auto-logged from {message.get('channel')} reply: {message.get('content')}",
    }
