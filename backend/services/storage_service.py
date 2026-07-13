"""SQLite-backed persistence adapter preserving the old storage API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select

from backend.models.db_models import AdherenceLog, ChatMessage, CommunicationMessage, MealFeedback, Profile, Reminder
from backend.services.database import SessionLocal


MODEL_BY_COLLECTION = {
    "chat_messages": ChatMessage,
    "meal_feedback": MealFeedback,
    "adherence_logs": AdherenceLog,
    "notifications": Reminder,
    "reminders": Reminder,
    "communication_messages": CommunicationMessage,
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _model_to_dict(obj: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for column in obj.__table__.columns:
        key = column.key
        if key == "metadata":
            val = getattr(obj, "metadata_json", None)
            data["metadata"] = _jsonable(val)
        else:
            out_key = "metadata" if key == "metadata_json" else key
            data[out_key] = _jsonable(getattr(obj, key))
    if isinstance(obj, Reminder):
        data.setdefault("enabled", obj.enabled)
        data.setdefault("is_active", obj.is_active)
    if isinstance(obj, AdherenceLog):
        if data.get("water_ml") is None and data.get("hydration_ml") is not None:
            data["water_ml"] = data["hydration_ml"]
    return data


class SqlStorage:
    """Thread-safe scoped-session adapter for profile and append/list operations."""

    def get_profile(self, user_id: str) -> dict[str, Any]:
        session = SessionLocal()
        try:
            profile = session.get(Profile, user_id)
            return _model_to_dict(profile) if profile else {}
        finally:
            SessionLocal.remove()

    def upsert_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        session = SessionLocal()
        try:
            profile = session.get(Profile, user_id)
            if profile is None:
                profile = Profile(user_id=user_id)
                session.add(profile)
            for key in ("health_profile", "preference_profile", "daily_targets", "meal_plan", "grocery_list"):
                if key in updates:
                    setattr(profile, key, updates[key])
            session.commit()
            session.refresh(profile)
            return _model_to_dict(profile)
        except Exception:
            session.rollback()
            raise
        finally:
            SessionLocal.remove()

    def append(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        model = MODEL_BY_COLLECTION.get(collection)
        if model is None:
            raise ValueError(f"Unknown storage collection: {collection}")
        session = SessionLocal()
        try:
            obj = self._record_to_model(model, record)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return _model_to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            SessionLocal.remove()

    def list_records(self, collection: str, user_id: str | None = None) -> list[dict[str, Any]]:
        model = MODEL_BY_COLLECTION.get(collection)
        if model is None:
            raise ValueError(f"Unknown storage collection: {collection}")
        session = SessionLocal()
        try:
            stmt = select(model)
            if user_id and hasattr(model, "user_id"):
                stmt = stmt.where(model.user_id == user_id)
            if hasattr(model, "created_at"):
                stmt = stmt.order_by(model.created_at)
            return [_model_to_dict(obj) for obj in session.execute(stmt).scalars().all()]
        finally:
            SessionLocal.remove()

    def _record_to_model(self, model: type, record: dict[str, Any]) -> Any:
        if model is ChatMessage:
            return ChatMessage(
                id=record.get("id"),
                user_id=record.get("user_id", "demo-user"),
                role=record.get("role", "user"),
                content=record.get("content", ""),
            )
        if model is MealFeedback:
            return MealFeedback(
                id=record.get("id"),
                user_id=record.get("user_id", "demo-user"),
                date=record.get("date"),
                day=record.get("day"),
                meal_type=record.get("meal_type"),
                meal_name=record.get("meal_name", ""),
                rating=record.get("rating"),
                liked=record.get("liked"),
                difficulty=record.get("difficulty"),
                taste_preference=record.get("taste_preference"),
                feedback_text=record.get("feedback_text") or record.get("notes"),
                digestion=record.get("digestion"),
                hunger_level=record.get("hunger_level"),
                energy_level=record.get("energy_level"),
                notes=record.get("notes"),
            )
        if model is AdherenceLog:
            return AdherenceLog(
                id=record.get("id"),
                user_id=record.get("user_id", "demo-user"),
                date=str(record.get("date", "")),
                meal_type=record.get("meal_type", ""),
                meal_name=record.get("meal_name", ""),
                status=record.get("status", "completed"),
                meals_completed=record.get("meals_completed"),
                hydration_ml=record.get("hydration_ml") or record.get("water_ml"),
                water_ml=record.get("water_ml"),
                sleep_hours=record.get("sleep_hours"),
                weight_kg=record.get("weight_kg"),
                mood=record.get("mood"),
                digestion=record.get("digestion"),
                notes=record.get("notes"),
                calories=record.get("calories"),
                protein_g=record.get("protein_g"),
                carbs_g=record.get("carbs_g"),
                fat_g=record.get("fat_g"),
            )
        if model is Reminder:
            return Reminder(
                id=record.get("id"),
                user_id=record.get("user_id", "demo-user"),
                reminder_type=record.get("reminder_type"),
                title=record.get("title", ""),
                time=record.get("time") or record.get("schedule"),
                schedule=record.get("schedule"),
                frequency=record.get("frequency"),
                channel=record.get("channel"),
                is_active=record.get("is_active", record.get("enabled", True)),
                enabled=record.get("enabled", record.get("is_active", True)),
                metadata_json=record.get("metadata", {}),
            )
        if model is CommunicationMessage:
            return CommunicationMessage(
                id=record.get("id"),
                user_id=record.get("user_id", "demo-user"),
                channel=record.get("channel", "sms"),
                direction=record.get("direction", "outbound"),
                message_type=record.get("message_type", "freeform"),
                recipient=record.get("recipient") or record.get("sender"),
                content=record.get("content", ""),
                status=record.get("status", "queued"),
                provider=record.get("provider", "mock"),
                provider_message_id=record.get("provider_message_id"),
                intent=record.get("intent"),
                risk_level=record.get("risk_level", "low"),
                related_reminder_id=record.get("related_reminder_id"),
                metadata_json=record.get("metadata", {}),
            )
        raise ValueError(f"Unsupported model: {model}")


storage = SqlStorage()


