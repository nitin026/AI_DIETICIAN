"""Provider abstraction for programmable communication delivery."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from backend.config import get_settings


@dataclass(frozen=True)
class DeliveryResult:
    provider: str
    status: str
    provider_message_id: str
    metadata: dict[str, Any]


class CommunicationProvider(Protocol):
    name: str

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        ...

    def status(self) -> dict[str, Any]:
        ...


class MockCommunicationProvider:
    name = "mock"

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        channel = payload.get("channel", "sms")
        return DeliveryResult(
            provider=self.name,
            status="sent",
            provider_message_id=f"mock_{channel}_{uuid4().hex[:12]}",
            metadata={
                "mock_delivery_note": "Stored locally. Replace provider with a real SMS/WhatsApp/Voice adapter when credentials are available.",
                "channel": channel,
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "ready": True,
            "mode": "local_demo",
            "supports": ["sms", "whatsapp", "voice", "in_app"],
            "notes": "No external network calls are made in mock mode.",
        }


class PlivoReadyProvider:
    name = "plivo_ready"

    def __init__(self) -> None:
        self.settings = get_settings()

    def send(self, payload: dict[str, Any]) -> DeliveryResult:
        return DeliveryResult(
            provider=self.name,
            status="queued_for_provider_integration",
            provider_message_id=f"plivo_ready_{uuid4().hex[:12]}",
            metadata={
                "adapter_note": "This placeholder preserves the delivery contract. Add the real Plivo REST call here when credentials are configured.",
                "channel": payload.get("channel", "sms"),
                "configured": self._configured(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "ready": self._configured(),
            "mode": "adapter_placeholder",
            "supports": ["sms", "whatsapp", "voice"],
            "missing": self._missing(),
            "notes": "Use this adapter boundary to wire a real programmable communications SDK/API later.",
        }

    def _configured(self) -> bool:
        return not self._missing()

    def _missing(self) -> list[str]:
        missing: list[str] = []
        for key in ("communication_provider", "plivo_auth_id", "plivo_auth_token", "plivo_source_number"):
            if not getattr(self.settings, key, ""):
                missing.append(key.upper())
        return missing


def get_communication_provider() -> CommunicationProvider:
    settings = get_settings()
    provider = getattr(settings, "communication_provider", "mock").lower()
    if provider in {"plivo", "plivo_ready"}:
        return PlivoReadyProvider()
    return MockCommunicationProvider()


def provider_status() -> dict[str, Any]:
    return get_communication_provider().status()
