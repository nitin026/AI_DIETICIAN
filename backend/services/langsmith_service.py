"""Optional LangSmith tracing helpers.

Tracing is controlled entirely by environment variables so local development
works without LangSmith credentials.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from loguru import logger

try:
    import langsmith as ls
except ImportError:  # pragma: no cover - exercised only before dependency install
    ls = None


TRUE_VALUES = {"1", "true", "yes", "on"}


class NoopRun:
    def end(self, outputs: dict[str, Any] | None = None) -> None:
        return None


def tracing_enabled() -> bool:
    return (
        os.environ.get("LANGSMITH_TRACING", "").strip().lower() in TRUE_VALUES
        and bool(os.environ.get("LANGSMITH_API_KEY", "").strip())
        and ls is not None
    )


def trace_full_payloads() -> bool:
    return os.environ.get("LANGSMITH_TRACE_FULL_PAYLOADS", "").strip().lower() in TRUE_VALUES


def text_payload(name: str, value: str) -> dict[str, Any]:
    payload: dict[str, Any] = {f"{name}_chars": len(value or "")}
    if trace_full_payloads():
        payload[name] = value
    return payload


@contextmanager
def trace_run(
    name: str,
    run_type: str = "chain",
    *,
    inputs: dict[str, Any] | None = None,
) -> Iterator[Any]:
    if not tracing_enabled():
        yield NoopRun()
        return

    project_name = os.environ.get("LANGSMITH_PROJECT", "").strip() or None
    try:
        with ls.trace(name, run_type, project_name=project_name, inputs=inputs or {}) as run:
            yield run
    except Exception as exc:
        logger.warning("LangSmith tracing failed for '{}': {}", name, exc)
        yield NoopRun()
