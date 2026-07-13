"""
main.py
FastAPI application entry point.
Registers routers, middleware, error handlers, and startup events.
"""
from __future__ import annotations

import traceback
import time

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config import get_settings
from backend.services.langsmith_service import trace_run
from backend.services.llm_service import get_task_model
from backend.utils.logger import configure_logger

# â”€â”€ Routers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from backend.routers import (
    nutrients_router,
    meal_plan_router,
    ingredient_router,
    grocery_router,
    chat_router,
    chat_image_router,
    feedback_router,
    adherence_router,
    analytics_router,
    reminders_router,
    report_router,
    voice_router,
    communication_router,
    clinic_router,
    observability_router,
)

configure_logger()
settings = get_settings()

app = FastAPI(
    title="AI Dietitian API",
    description=(
        "Personalized Indian AI Dietitian powered by hosted LLMs + RAG (ICMR-NIN 2024). "
        "âš ï¸ For informational purposes only â€” not a substitute for medical advice."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# â”€â”€ CORS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def langsmith_trace_middleware(request: Request, call_next):
    start = time.perf_counter()
    inputs = {
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host if request.client else None,
    }
    with trace_run("HTTP Request", "chain", inputs=inputs) as run:
        try:
            response = await call_next(request)
        except Exception as exc:
            run.end(outputs={
                "error": type(exc).__name__,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            })
            raise
        run.end(outputs={
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        })
        return response

# â”€â”€ Routers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app.include_router(nutrients_router.router, prefix="/predict-nutrients", tags=["Nutrition"])
app.include_router(meal_plan_router.router, prefix="/generate-meal-plan", tags=["Meal Plan"])
app.include_router(ingredient_router.router, prefix="/validate-ingredients", tags=["Ingredients"])
app.include_router(grocery_router.router, prefix="/generate-grocery-list", tags=["Grocery"])
app.include_router(chat_router.router, prefix="/chat", tags=["AI Chatbot"])
app.include_router(chat_image_router.router, prefix="/api", tags=["AI Chatbot"])
app.include_router(feedback_router.router, prefix="/feedback", tags=["Feedback Learning"])
app.include_router(adherence_router.router, prefix="/adherence", tags=["Adherence Calendar"])
app.include_router(analytics_router.router, prefix="/analytics", tags=["AI Health Insights"])
app.include_router(reminders_router.router, prefix="/reminders", tags=["Reminders"])
app.include_router(report_router.router, prefix="/api", tags=["Clinical Reports"])
app.include_router(voice_router.router, prefix="/api/voice", tags=["Voice"])
app.include_router(communication_router.router, prefix="/api/communications", tags=["Communications"])
app.include_router(clinic_router.router, prefix="/api/clinic", tags=["Clinic Dashboard"])
app.include_router(observability_router.router, prefix="/api/observability", tags=["Observability"])

# â”€â”€ Global exception handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Health check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Startup: pre-load vector store â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting AI Dietitian API â€¦")
    try:
        from backend.services.database import init_db
        init_db()
        logger.info("SQLite database initialized âœ“")
    except Exception as exc:
        logger.warning("Database initialization failed: {}", exc)

    try:
        from backend.rag.retriever import _load_vectorstore
        _load_vectorstore()
        logger.info("Vector store pre-loaded âœ“")
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
