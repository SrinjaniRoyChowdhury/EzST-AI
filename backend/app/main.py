"""
main.py
────────
FastAPI application entry point.

Startup sequence:
  1. Load settings
  2. Initialise Neo4j schema (constraints + indexes)
  3. Build / load FAISS RAG index
  4. Register all API routers
  5. Add CORS middleware

Run with:
  uvicorn app.main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.graph.neo4j_client import init_graph_schema, close_driver
from app.rag.rag_pipeline import build_index
from app.api.routes import invoice_routes, auth_routes, gst_routes

settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run initialisation tasks before the server starts accepting requests,
    and clean-up tasks on shutdown.
    """
    print("[START] Starting AI-Powered GST Invoice Compliance System ...")

    # Create upload directories
    os.makedirs(settings.invoice_upload_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.faiss_index_path), exist_ok=True)

    # Initialise Neo4j schema
    try:
        await init_graph_schema()
    except Exception as e:
        print(f"[WARN]  Neo4j init warning: {e}")

    # Build / load FAISS RAG index
    try:
        build_index()
    except Exception as e:
        print(f"[WARN]  RAG index warning: {e}")

    print("[OK]    All systems ready.")
    yield

    # ── Shutdown ──────────────────────────────────────────────
    print("[STOP]  Shutting down ...")
    await close_driver()


# ── App Instance ──────────────────────────────────────────────

app = FastAPI(
    title="AI-Powered B2B Invoice Tracking & GST Compliance",
    description=(
        "Hackathon project: automated invoice sharing, OCR extraction, "
        "AI validation, GST return generation, fraud detection via Neo4j, "
        "and a RAG-powered GST chatbot."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────

app.include_router(auth_routes.router)
app.include_router(invoice_routes.router)
app.include_router(gst_routes.router)


# ── Health Check ──────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": "GST Invoice Compliance System",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/", tags=["System"])
async def root():
    return JSONResponse({
        "message": "Welcome to the AI-Powered GST Invoice Compliance API",
        "docs": "/docs",
        "health": "/health",
    })


# ── Dev runner ────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)