"""Doctor and dietitian dashboard summaries for patient communication workflows."""
from __future__ import annotations

from collections import Counter
from typing import Any

from backend.services.communication_service import metrics as communication_metrics
from backend.services.personalization_service import adherence_summary
from backend.services.storage_service import storage


def build_patient_dashboard(user_id: str) -> dict[str, Any]:
    communications = storage.list_records("communication_messages", user_id)
    adherence_records = storage.list_records("adherence_logs", user_id)
    feedback_records = storage.list_records("meal_feedback", user_id)
    reminders = storage.list_records("reminders", user_id)

    high_risk = [item for item in communications if item.get("risk_level") == "high"]
    medium_risk = [item for item in communications if item.get("risk_level") == "medium"]
    skipped = [item for item in adherence_records if item.get("status") == "skipped"]
    inbound = [item for item in communications if item.get("direction") == "inbound"]
    outbound = [item for item in communications if item.get("direction") == "outbound"]
    intent_counts = Counter(item.get("intent") or "none" for item in inbound)
    channel_counts = Counter(item.get("channel") or "unknown" for item in communications)

    summary = adherence_summary(adherence_records)
    risk_level = _patient_risk_level(high_risk, medium_risk, skipped, summary)
    suggested_action = _suggested_action(risk_level, high_risk, medium_risk, skipped, intent_counts)

    return {
        "user_id": user_id,
        "risk_level": risk_level,
        "suggested_action": suggested_action,
        "communication_metrics": communication_metrics(user_id),
        "adherence_summary": summary,
        "counts": {
            "communications": len(communications),
            "inbound": len(inbound),
            "outbound": len(outbound),
            "active_reminders": sum(1 for item in reminders if item.get("enabled", item.get("is_active", True))),
            "feedback_records": len(feedback_records),
            "skipped_adherence_logs": len(skipped),
            "high_risk_alerts": len(high_risk),
            "medium_risk_alerts": len(medium_risk),
        },
        "intent_counts": dict(intent_counts),
        "channel_counts": dict(channel_counts),
        "alerts": _build_alerts(high_risk, medium_risk, skipped),
        "timeline": communications[-30:],
        "latest_adherence": adherence_records[-10:],
        "latest_feedback": feedback_records[-10:],
    }


def build_clinic_overview(user_ids: list[str] | None = None) -> dict[str, Any]:
    if not user_ids:
        user_ids = _discover_user_ids()
    patients = [build_patient_dashboard(user_id) for user_id in user_ids]
    return {
        "patient_count": len(patients),
        "high_risk_patients": sum(1 for item in patients if item.get("risk_level") == "high"),
        "medium_risk_patients": sum(1 for item in patients if item.get("risk_level") == "medium"),
        "patients": patients,
    }


def _discover_user_ids() -> list[str]:
    ids = set()
    for collection in ("communication_messages", "adherence_logs", "meal_feedback", "reminders"):
        for item in storage.list_records(collection):
            user_id = item.get("user_id")
            if user_id:
                ids.add(user_id)
    return sorted(ids) or ["demo-user"]


def _patient_risk_level(high_risk: list[dict], medium_risk: list[dict], skipped: list[dict], summary: dict[str, Any]) -> str:
    if high_risk:
        return "high"
    if len(medium_risk) >= 2 or len(skipped) >= 3:
        return "medium"
    if summary.get("average_score", 0) and summary.get("average_score", 0) < 60:
        return "medium"
    return "low"


def _suggested_action(risk_level: str, high_risk: list[dict], medium_risk: list[dict], skipped: list[dict], intents: Counter) -> str:
    if high_risk:
        return "Call the patient or escalate to a doctor now. Review the latest high-risk message before giving nutrition advice."
    if intents.get("callback_requested"):
        return "Schedule a doctor or dietitian callback."
    if len(skipped) >= 3:
        return "Send a simplified meal plan and ask why meals are being skipped."
    if medium_risk:
        return "Review medium-risk replies and send a follow-up check-in."
    if risk_level == "medium":
        return "Review adherence barriers and send a supportive follow-up message."
    return "Continue routine reminders and weekly progress review."


def _build_alerts(high_risk: list[dict], medium_risk: list[dict], skipped: list[dict]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for item in high_risk[-5:]:
        alerts.append({
            "priority": "high",
            "title": "High-risk patient message",
            "detail": item.get("content", ""),
            "created_at": item.get("created_at"),
        })
    for item in medium_risk[-5:]:
        alerts.append({
            "priority": "medium",
            "title": "Needs clinician review",
            "detail": item.get("content", ""),
            "created_at": item.get("created_at"),
        })
    if len(skipped) >= 3:
        alerts.append({
            "priority": "medium",
            "title": "Repeated skipped meals",
            "detail": f"{len(skipped)} skipped adherence logs recorded.",
            "created_at": skipped[-1].get("created_at") if skipped else None,
        })
    return alerts
