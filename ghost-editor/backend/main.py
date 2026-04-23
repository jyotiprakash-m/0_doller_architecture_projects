"""
Ghost-Editor Backend — FastAPI Entry Point
==========================================
Modeled after the legal-auditor project.
$0 cost, local-first documentation agent.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_HOST, API_PORT, CORS_ORIGINS
import database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ghost-Editor API",
    description="Intelligent AI agent for automated documentation maintenance.",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import webhooks, repos, agent
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(repos.router, prefix="/api/repos", tags=["Repositories"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.on_event("startup")
async def startup():
    """Initialize database and log startup info."""
    database.init_db()
    logger.info("=" * 60)
    logger.info("  GHOST-EDITOR — AI Documentation Agent")
    logger.info("  Local-first, $0 cost documentation management.")
    logger.info("=" * 60)
    logger.info("Database initialized.")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Ghost-Editor Backend",
        "mode": "Local / Privacy-First"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info",
    )
