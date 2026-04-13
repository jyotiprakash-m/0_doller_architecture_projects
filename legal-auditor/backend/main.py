"""
Privacy-First Legal Document Auditor — FastAPI Backend
=====================================================
All AI processing runs LOCALLY via Ollama.
All data stays on YOUR machine. Zero cloud dependency. $0 cost.

Stack: FastAPI + LlamaIndex + ChromaDB + Ollama
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import API_HOST, API_PORT, CORS_ORIGINS
from services import db
from routers import documents, audit, chat, auth, payments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Legal Document Auditor",
    description="Privacy-first AI-powered legal document analysis. All processing happens locally.",
    version="1.0.0",
)

# CORS middleware (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(chat.router)
app.include_router(payments.router)


@app.on_event("startup")
async def startup():
    """Initialize database and log startup info."""
    db.init_db()
    logger.info("=" * 60)
    logger.info("  LEGAL DOCUMENT AUDITOR — Privacy First")
    logger.info("  All AI runs locally via Ollama. $0 cost.")
    logger.info("  No data leaves this machine. Ever.")
    logger.info("=" * 60)
    logger.info("Database initialized.")

    # Try to initialize RAG engine (non-blocking)
    try:
        from services.rag_engine import rag_engine
        rag_engine.initialize()
        logger.info("RAG Engine ready (Ollama + ChromaDB).")
    except Exception as e:
        logger.warning(f"RAG Engine not available: {e}")
        logger.warning("Documents can still be uploaded. Start Ollama for full functionality.")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Legal Document Auditor",
        "privacy": "All data stays local",
        "cost": "$0",
    }


@app.get("/api/dashboard")
async def dashboard(user_id: str = Depends(auth.get_current_user_id)):
    """Get dashboard statistics for the logged-in user."""
    stats = db.get_dashboard_stats(user_id)
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info",
    )
