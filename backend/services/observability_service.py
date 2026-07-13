"""Operational metrics for communication, reminders, voice assistant, and clinic workflows."""
from __future__ import annotations

from collections import Counter
from typing import Any

from backend.services.storage_service import storage
from backend.services.communication_service import communication_provider_status


def build_observability_snapshot(user_id: str | None = None) -> dict[str, Any]:
    communications = storage.list_records("communication_messages", user_id)
    reminders = storage.list_records("notifications", user_id)
    adherence = storage.list_records("adherence_logs", user_id)

    inbound = [item for item in communications if item.get("direction") == "inbound"]
    outbound = [item for item in communications if item.get("direction") == "outbound"]
    voice = [item for item in communications if item.get("channel") == "voice"]
    high_risk = [item for item in communications if item.get("risk_level") == "high"]
    medium_risk = [item for item in communications if item.get("risk_level") == "medium"]
    sent = [item for item in communications if item.get("status") == "sent"]
    received = [item for item in communications if item.get("status") == "received"]
    completed = [item for item in adherence if item.get("status") == "completed"]
    skipped = [item for item in adherence if item.get("status") == "skipped"]

    reply_rate = round((len(inbound) / len(outbound)) * 100, 1) if outbound else 0.0
    delivery_success = round((len(sent) / len(outbound)) * 100, 1) if outbound else 0.0
    adherence_completion = round((len(completed) / len(adherence)) * 100, 1) if adherence else 0.0

    return {
        "scope": user_id or "all_users",
        "kpis": {
            "total_messages": len(communications),
            "outbound_messages": len(outbound),
            "inbound_messages": len(inbound),
            "reply_rate_percent": reply_rate,
            "delivery_success_percent": delivery_success,
            "voice_interactions": len(voice),
            "active_reminders": sum(1 for item in reminders if item.get("enabled", item.get("is_active", True))),
            "adherence_completion_percent": adherence_completion,
            "high_risk_alerts": len(high_risk),
            "medium_risk_alerts": len(medium_risk),
        },
        "breakdowns": {
            "by_channel": dict(Counter(item.get("channel") or "unknown" for item in communications)),
            "by_status": dict(Counter(item.get("status") or "unknown" for item in communications)),
            "by_direction": dict(Counter(item.get("direction") or "unknown" for item in communications)),
            "by_intent": dict(Counter(item.get("intent") or "none" for item in inbound)),
            "by_risk": dict(Counter(item.get("risk_level") or "low" for item in communications)),
            "reminders_by_type": dict(Counter(item.get("reminder_type") or "unknown" for item in reminders)),
        },
        "alerts": _observability_alerts(reply_rate, delivery_success, high_risk, skipped),
        "recent_events": communications[-20:],
        "demo_readiness": _demo_readiness(communications, reminders, voice),
        "provider_status": communication_provider_status(),
    }


def _observability_alerts(reply_rate: float, delivery_success: float, high_risk: list[dict], skipped: list[dict]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if high_risk:
        alerts.append({"priority": "high", "message": f"{len(high_risk)} high-risk patient messages need clinician review."})
    if reply_rate < 25 and delivery_success > 0:
        alerts.append({"priority": "medium", "message": "Reply rate is low. Consider clearer reminder copy or a voice follow-up."})
    if delivery_success < 90 and delivery_success > 0:
        alerts.append({"priority": "medium", "message": "Delivery success is below target for an operational communication system."})
    if len(skipped) >= 3:
        alerts.append({"priority": "medium", "message": f"{len(skipped)} skipped adherence logs detected."})
    return alerts


def _demo_readiness(communications: list[dict], reminders: list[dict], voice: list[dict]) -> dict[str, Any]:
    checks = {
        "has_outbound_message": any(item.get("direction") == "outbound" for item in communications),
        "has_inbound_reply": any(item.get("direction") == "inbound" for item in communications),
        "has_voice_interaction": bool(voice),
        "has_saved_reminder": bool(reminders),
        "has_risk_signal": any(item.get("risk_level") in {"medium", "high"} for item in communications),
    }
    score = round(sum(1 for ok in checks.values() if ok) / len(checks) * 100, 1)
    return {"score_percent": score, "checks": checks}


