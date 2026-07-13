"""Communication workflow service for mock SMS, WhatsApp, voice, and in-app messages."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from backend.services.communication_providers import get_communication_provider, provider_status

from backend.services.storage_service import storage

COMPLETED_REPLIES = {"1", "done", "completed", "complete", "yes", "y", "ha", "haan"}
SKIPPED_REPLIES = {"2", "skip", "skipped", "no", "n", "nahi"}
ALTERNATIVE_REPLIES = {"3", "alternative", "swap", "change", "option"}
RISK_TERMS = (
    "chest pain", "faint", "fainted", "severe dizziness", "breathless", "very low sugar",
    "hypoglycemia", "blood in stool", "pregnant bleeding", "emergency", "suicide",
)


def _now_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def classify_inbound_intent(content: str) -> tuple[str, str]:
    text = content.strip().lower()
    if any(term in text for term in RISK_TERMS):
        return "medical_risk", "high"
    if text in COMPLETED_REPLIES:
        return "adherence_completed", "low"
    if text in SKIPPED_REPLIES:
        return "adherence_skipped", "medium"
    if text in ALTERNATIVE_REPLIES or "replace" in text or "instead" in text:
        return "alternative_requested", "low"
    if "call" in text or "doctor" in text or "dietitian" in text:
        return "callback_requested", "medium"
    if "remind" in text:
        return "reminder_requested", "low"
    return "freeform_reply", "low"


def send_message(payload: dict[str, Any]) -> dict[str, Any]:
    provider_message_id = _now_id("mockmsg")
    record = {
        **payload,
        "direction": "outbound",
        "status": "sent",
        "provider": "mock",
        "provider_message_id": provider_message_id,
        "risk_level": "low",
        "metadata": {
            **payload.get("metadata", {}),
            "mock_delivery_note": "Stored locally. Replace MockProvider with Plivo SMS/WhatsApp/Voice API later.",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    saved = storage.append("communication_messages", record)
    return {
        "sent": True,
        "provider": "mock",
        "message": saved,
        "plivo_alignment": "This mirrors an outbound programmable messaging call without requiring live credentials.",
    }


def receive_message(payload: dict[str, Any]) -> dict[str, Any]:
    intent, risk_level = classify_inbound_intent(payload.get("content", ""))
    record = {
        **payload,
        "recipient": payload.get("sender"),
        "direction": "inbound",
        "message_type": "inbound_reply",
        "status": "received",
        "provider": "mock",
        "provider_message_id": _now_id("inbound"),
        "intent": intent,
        "risk_level": risk_level,
        "metadata": {
            **payload.get("metadata", {}),
            "received_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    saved = storage.append("communication_messages", record)
    from backend.services.reminder_automation_service import adherence_record_from_reply

    adherence_record = adherence_record_from_reply(saved)
    adherence_saved = None
    if adherence_record:
        adherence_saved = storage.append("adherence_logs", adherence_record)
    action = _recommended_action(intent, risk_level)
    return {
        "received": True,
        "message": saved,
        "intent": intent,
        "risk_level": risk_level,
        "recommended_action": action,
        "adherence_logged": bool(adherence_saved),
        "adherence_record": adherence_saved,
    }


def history(user_id: str) -> list[dict[str, Any]]:
    return storage.list_records("communication_messages", user_id)


def metrics(user_id: str | None = None) -> dict[str, Any]:
    records = storage.list_records("communication_messages", user_id)
    by_channel = Counter(item.get("channel", "unknown") for item in records)
    by_status = Counter(item.get("status", "unknown") for item in records)
    by_intent = Counter(item.get("intent") or "none" for item in records if item.get("direction") == "inbound")
    high_risk = [item for item in records if item.get("risk_level") == "high"]
    outbound = [item for item in records if item.get("direction") == "outbound"]
    inbound = [item for item in records if item.get("direction") == "inbound"]
    reply_rate = round((len(inbound) / len(outbound)) * 100, 1) if outbound else 0.0
    return {
        "total_messages": len(records),
        "outbound_messages": len(outbound),
        "inbound_messages": len(inbound),
        "reply_rate_percent": reply_rate,
        "high_risk_count": len(high_risk),
        "by_channel": dict(by_channel),
        "by_status": dict(by_status),
        "by_intent": dict(by_intent),
        "latest_high_risk": high_risk[-5:],
    }


def _recommended_action(intent: str, risk_level: str) -> str:
    if risk_level == "high":
        return "Escalate to doctor immediately and show emergency guidance."
    if intent == "adherence_skipped":
        return "Send a lighter alternative and flag this in the adherence dashboard."
    if intent == "alternative_requested":
        return "Route to AI coach for a diet-safe substitution."
    if intent == "callback_requested":
        return "Create a doctor or dietitian callback task."
    if intent == "adherence_completed":
        return "Mark check-in as successful."
    return "Store reply and keep it available in the communication timeline."


def communication_provider_status() -> dict[str, Any]:
    return provider_status()

