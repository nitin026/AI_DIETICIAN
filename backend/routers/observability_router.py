"""Operational observability endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.services.observability_service import build_observability_snapshot

router = APIRouter()


@router.get("/snapshot")
async def observability_snapshot(user_id: str | None = Query(default=None)) -> dict:
    return build_observability_snapshot(user_id)
