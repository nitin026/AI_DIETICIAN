"""Doctor and dietitian dashboard endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.services.clinic_dashboard_service import build_clinic_overview, build_patient_dashboard

router = APIRouter()


@router.get("/patient/{user_id}")
async def patient_dashboard(user_id: str) -> dict:
    return build_patient_dashboard(user_id)


@router.get("/overview")
async def clinic_overview(user_ids: list[str] | None = Query(default=None)) -> dict:
    return build_clinic_overview(user_ids)
