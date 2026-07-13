"""SQLAlchemy persistence models for the AI Dietitian app."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.services.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Profile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    health_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preference_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    daily_targets: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meal_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    grocery_list: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class MealFeedback(Base):
    __tablename__ = "meal_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str | None] = mapped_column(String, nullable=True)
    day: Mapped[str | None] = mapped_column(String, nullable=True)
    meal_type: Mapped[str | None] = mapped_column(String, nullable=True)
    meal_name: Mapped[str] = mapped_column(String, default="")
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    liked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)
    taste_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    digestion: Mapped[str | None] = mapped_column(String, nullable=True)
    hunger_level: Mapped[str | None] = mapped_column(String, nullable=True)
    energy_level: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AdherenceLog(Base):
    __tablename__ = "adherence_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str] = mapped_column(String, index=True)
    meal_type: Mapped[str] = mapped_column(String, default="")
    meal_name: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="completed")
    meals_completed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hydration_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    mood: Mapped[str | None] = mapped_column(String, nullable=True)
    digestion: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String, index=True)
    reminder_type: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    time: Mapped[str | None] = mapped_column(String, nullable=True)
    schedule: Mapped[str | None] = mapped_column(String, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String, nullable=True)
    channel: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CommunicationMessage(Base):
    __tablename__ = "communication_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String, index=True)
    channel: Mapped[str] = mapped_column(String, index=True)
    direction: Mapped[str] = mapped_column(String, index=True)
    message_type: Mapped[str] = mapped_column(String, default="freeform")
    recipient: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    provider: Mapped[str] = mapped_column(String, default="mock")
    provider_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    intent: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, default="low", index=True)
    related_reminder_id: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
