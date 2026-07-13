"""Mock communication endpoints for SMS, WhatsApp, voice, and in-app workflows."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.models.request_models import CommunicationInboundRequest, CommunicationSendRequest
from backend.services.communication_service import communication_provider_status, history, metrics, receive_message, send_message

router = APIRouter()


@router.post("/send-reminder")
async def send_reminder(request: CommunicationSendRequest) -> dict:
    return send_message(request.model_dump())


@router.post("/inbound-reply")
async def inbound_reply(request: CommunicationInboundRequest) -> dict:
    return receive_message(request.model_dump())


@router.get("/history/{user_id}")
async def communication_history(user_id: str) -> dict:
    return {"items": history(user_id)}


@router.get("/metrics")
async def communication_metrics(user_id: str | None = Query(default=None)) -> dict:
    return metrics(user_id)


@router.get("/provider/status")
async def provider_status() -> dict:
    return communication_provider_status()
