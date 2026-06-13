"""
main.py
FastAPI application entry point.
Registers routers, middleware, error handlers, and startup events.
"""
from __future__ import annotations

import traceback

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config import get_settings
from backend.services.llm_service import get_task_model
from backend.utils.logger import configure_logger

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.routers import (
    nutrients_router,
    meal_plan_router,
    ingredient_router,
    grocery_router,
    chat_router,
    feedback_router,
    adherence_router,
    analytics_router,
    reminders_router,
)

configure_logger()
settings = get_settings()

app = FastAPI(
    title="AI Dietitian API",
    description=(
        "Personalized Indian AI Dietitian powered by hosted LLMs + RAG (ICMR-NIN 2024). "
        "⚠️ For informational purposes only — not a substitute for medical advice."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(nutrients_router.router, prefix="/predict-nutrients", tags=["Nutrition"])
app.include_router(meal_plan_router.router, prefix="/generate-meal-plan", tags=["Meal Plan"])
app.include_router(ingredient_router.router, prefix="/validate-ingredients", tags=["Ingredients"])
app.include_router(grocery_router.router, prefix="/generate-grocery-list", tags=["Grocery"])
app.include_router(chat_router.router, prefix="/chat", tags=["AI Chatbot"])
app.include_router(feedback_router.router, prefix="/feedback", tags=["Feedback Learning"])
app.include_router(adherence_router.router, prefix="/adherence", tags=["Adherence Calendar"])
app.include_router(analytics_router.router, prefix="/analytics", tags=["AI Health Insights"])
app.include_router(reminders_router.router, prefix="/reminders", tags=["Reminders"])

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on {}: {}\n{}", request.url, exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": "Validation error", "detail": str(exc)})


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    meal_provider, meal_model = get_task_model("meal_plan")
    return {
        "status": "healthy",
        "model": settings.active_model_name,
        "provider": settings.llm_provider,
        "meal_planning_provider": meal_provider,
        "meal_planning_model": meal_model,
    }


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "message": "AI Dietitian API",
        "disclaimer": (
            "This AI dietitian is an informational assistant and is not a substitute "
            "for professional medical advice, diagnosis, or treatment."
        ),
        "docs": "/docs",
    }


# ── Startup: pre-load vector store ───────────────────────────────────────────
@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting AI Dietitian API …")
    try:
        from backend.rag.retriever import _load_vectorstore
        _load_vectorstore()
        logger.info("Vector store pre-loaded ✓")
    except Exception as exc:
        logger.warning("Vector store not ready ({}). Run `python -m backend.rag.ingest` first.", exc)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=False,
    )
