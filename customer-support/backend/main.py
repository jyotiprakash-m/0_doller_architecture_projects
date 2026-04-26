"""
SupportSim AI — Customer Support Agent Training Platform
=========================================================
AI-powered training using agentic workflows and local LLMs.
All processing runs LOCALLY via Ollama — $0 cost, full privacy.

Stack: FastAPI + LangGraph + LlamaIndex + ChromaDB + Ollama + Streamlit
"""
import logging
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Suppress Pydantic V2 validate_default warning from older dependencies
warnings.filterwarnings("ignore", message=".*validate_default.*", category=UserWarning)

from config import API_HOST, API_PORT, CORS_ORIGINS
from services import db
from routers import auth, knowledge_base, simulation, evaluation, analytics, billing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and services on startup."""
    db.init_db()
    logger.info("=" * 60)
    logger.info("  SUPPORTSIM AI — Agent Training Platform")
    logger.info("  All AI runs locally via Ollama. $0 cost.")
    logger.info("  Train smarter. Support better.")
    logger.info("=" * 60)
    logger.info("Database initialized.")

    # Try to initialize RAG engine (non-blocking)
    try:
        from services.rag_engine import rag_engine
        rag_engine.initialize()
        logger.info("RAG Engine ready (Ollama + ChromaDB).")
    except Exception as e:
        logger.warning(f"RAG Engine not available: {e}")
        logger.warning("Knowledge bases can still be created. Start Ollama for full functionality.")
    yield


# Create FastAPI app
app = FastAPI(
    title="SupportSim AI",
    description="AI-powered customer support agent training platform. "
                "Simulates customer interactions, evaluates responses, "
                "and provides personalized feedback — all running locally.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (for Streamlit frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(knowledge_base.router)
app.include_router(simulation.router)
app.include_router(evaluation.router)
app.include_router(analytics.router)
app.include_router(billing.router)



@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SupportSim AI",
        "description": "Customer Support Agent Training Platform",
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
        loop="asyncio",
    )
