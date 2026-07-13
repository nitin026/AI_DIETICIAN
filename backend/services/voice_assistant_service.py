"""Voice assistant orchestration for clinic-style nutrition follow-up demos."""
from __future__ import annotations

from typing import Any

from backend.services.communication_service import classify_inbound_intent, receive_message, send_message
from backend.services.language_service import detect_language, normalize_hinglish_to_english

MEAL_TERMS = ("breakfast", "lunch", "dinner", "nashta", "khana", "roti", "dal", "rice", "poha", "meal")
SUBSTITUTION_TERMS = ("replace", "instead", "alternative", "swap", "badal", "option")
REMINDER_TERMS = ("remind", "reminder", "yaad", "alarm")
CALLBACK_TERMS = ("doctor", "dietitian", "call", "callback")
ADHERENCE_TERMS = ("done", "completed", "skip", "skipped", "missed", "followed", "nahi", "haan")


def classify_voice_intent(text: str) -> tuple[str, str]:
    base_intent, risk_level = classify_inbound_intent(text)
    if base_intent in {"medical_risk", "callback_requested", "adherence_completed", "adherence_skipped", "alternative_requested", "reminder_requested"}:
        return base_intent, risk_level
    lowered = text.lower()
    if any(term in lowered for term in CALLBACK_TERMS):
        return "callback_requested", "medium"
    if any(term in lowered for term in REMINDER_TERMS):
        return "reminder_requested", "low"
    if any(term in lowered for term in SUBSTITUTION_TERMS):
        return "alternative_requested", "low"
    if any(term in lowered for term in ADHERENCE_TERMS):
        return "adherence_update", "low"
    if any(term in lowered for term in MEAL_TERMS):
        return "meal_question", "low"
    return "general_nutrition_question", "low"


def answer_for_intent(intent: str, risk_level: str, transcript: str) -> str:
    if risk_level == "high" or intent == "medical_risk":
        return (
            "I am flagging this as high risk. Please contact your doctor or local emergency service now. "
            "I will also mark this conversation for clinician review."
        )
    if intent == "callback_requested":
        return "I have noted that you want a doctor or dietitian callback. The clinic team should review this request."
    if intent == "adherence_completed":
        return "Great, I have logged this as completed. Keep following the plan and stay hydrated."
    if intent == "adherence_skipped":
        return "I have logged this as skipped. For the next meal, choose a lighter planned option and avoid compensating with extra sugar or fried snacks."
    if intent == "alternative_requested":
        return "A practical Indian alternative is dal, chana, curd, eggs, paneer, or soya depending on your diet preference and medical condition."
    if intent == "reminder_requested":
        return "I can help set a reminder for meals, hydration, supplements, or follow-ups from the clinic communications panel."
    if intent == "meal_question":
        return "For a balanced Indian meal, combine protein, vegetables, controlled carbs, and limited oil. Example: dal, sabzi, curd, and 1-2 rotis."
    return "I can help with meal timing, substitutions, reminders, adherence updates, and when to escalate to a doctor."


def handle_voice_query(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = payload.get("user_id", "demo-user")
    transcript = (payload.get("transcript") or payload.get("message") or "").strip()
    if not transcript:
        raise ValueError("Transcript is required.")

    detected_language = payload.get("detected_language") or detect_language(transcript)
    normalized_query = normalize_hinglish_to_english(transcript)
    intent, risk_level = classify_voice_intent(normalized_query)
    inbound = receive_message({
        "user_id": user_id,
        "channel": "voice",
        "sender": payload.get("caller") or payload.get("recipient") or "+91XXXXXXXXXX",
        "content": transcript,
        "metadata": {
            "source": "voice_assistant",
            "detected_language": detected_language,
            "normalized_query": normalized_query,
        },
    })
    answer = answer_for_intent(intent, risk_level, transcript)
    outbound = send_message({
        "user_id": user_id,
        "channel": "voice",
        "recipient": payload.get("caller") or payload.get("recipient") or "+91XXXXXXXXXX",
        "message_type": "voice_assistant_response",
        "content": answer,
        "metadata": {
            "source": "voice_assistant",
            "intent": intent,
            "risk_level": risk_level,
            "requires_human_review": risk_level in {"medium", "high"},
        },
    })
    return {
        "transcript": transcript,
        "detected_language": detected_language,
        "normalized_query": normalized_query,
        "intent": intent,
        "risk_level": risk_level,
        "answer": answer,
        "requires_human_review": risk_level in {"medium", "high"},
        "inbound_log": inbound,
        "outbound_log": outbound,
    }
