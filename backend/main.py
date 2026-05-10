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
from backend.utils.logger import configure_logger

# ── Routers ───────────────────────────────────────────────────────────────────
from backend.routers import (
    nutrients_router,
    meal_plan_router,
    ingredient_router,
    grocery_router,
)

configure_logger()
settings = get_settings()

app = FastAPI(
    title="AI Dietitian API",
    description=(
        "Personalized Indian AI Dietitian powered by BioMistral + RAG (ICMR-NIN 2024). "
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
    return {"status": "healthy", "model": settings.ollama_model, "provider": settings.llm_provider}


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
