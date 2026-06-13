"""
Small persistence adapter for chat, feedback, adherence, and analytics data.

This project currently ships without a database dependency. The adapter keeps
the rest of the app database-shaped while storing records in a local JSON file,
so it can be swapped for Postgres/SQLAlchemy without changing API contracts.
"""
from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from backend.config import get_settings


_DEFAULT_STATE: dict[str, Any] = {
    "profiles": {},
    "chat_messages": [],
    "meal_feedback": [],
    "adherence_logs": [],
    "notifications": [],
}


class JsonStorage:
    """Thread-safe JSON document store with append/update helpers."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or get_settings().storage_path)
        self._lock = Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps(_DEFAULT_STATE, indent=2), encoding="utf-8")

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = deepcopy(_DEFAULT_STATE)
        for key, value in _DEFAULT_STATE.items():
            data.setdefault(key, deepcopy(value))
        return data

    def _write_unlocked(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_profile(self, user_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = self._read_unlocked()
            current = data["profiles"].get(user_id, {})
            merged = {**current, **profile, "updated_at": self._now()}
            data["profiles"][user_id] = merged
            self._write_unlocked(data)
            return merged

    def get_profile(self, user_id: str) -> dict[str, Any]:
        with self._lock:
            return self._read_unlocked()["profiles"].get(user_id, {})

    def append(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = self._read_unlocked()
            stored = {
                "id": record.get("id") or str(uuid.uuid4()),
                "created_at": record.get("created_at") or self._now(),
                **record,
            }
            data.setdefault(collection, []).append(stored)
            self._write_unlocked(data)
            return stored

    def list_records(self, collection: str, user_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            records = list(self._read_unlocked().get(collection, []))
        if user_id:
            records = [r for r in records if r.get("user_id") == user_id]
        return records


storage = JsonStorage()