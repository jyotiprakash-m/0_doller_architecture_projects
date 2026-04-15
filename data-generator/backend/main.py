"""
Synthetic Data Generator for Developers — FastAPI Backend
==========================================================
All AI processing runs LOCALLY via Ollama.
All data stays on YOUR machine. Zero cloud dependency. $0 cost.

Stack: FastAPI + Ollama + DuckDB + Faker
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import API_HOST, API_PORT, CORS_ORIGINS
from services import db
from routers import auth, schemas, generate, export, payments
from services.auth_utils import get_current_user_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Synthetic Data Generator",
    description="AI-powered synthetic data generation for developers. Privacy-first, all processing happens locally.",
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
app.include_router(schemas.router)
app.include_router(generate.router)
app.include_router(export.router)
app.include_router(payments.router)


@app.on_event("startup")
async def startup():
    """Initialize database and log startup info."""
    db.init_db()
    logger.info("=" * 60)
    logger.info("  SYNTHETIC DATA GENERATOR — Privacy First")
    logger.info("  All AI runs locally via Ollama. $0 cost.")
    logger.info("  GDPR/CCPA compliant synthetic data.")
    logger.info("=" * 60)
    logger.info("SQLite metadata database initialized.")

    # Try to verify Ollama connection (non-blocking)
    try:
        from services.agentic_engine import agentic_generation_engine as generation_engine
        # from services.generation_engine import generation_engine
        llm = generation_engine._get_llm()
        logger.info(f"Ollama LLM ready (model: {llm.model}).")
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        logger.warning("Data generation will use heuristic fallbacks. Start Ollama for AI-powered schema analysis.")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Synthetic Data Generator",
        "privacy": "All data stays local",
        "cost": "$0",
    }


@app.get("/api/dashboard")
async def dashboard(user_id: str = Depends(get_current_user_id)):
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
