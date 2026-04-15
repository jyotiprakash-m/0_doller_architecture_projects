import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from services import db
from routers import profiles, audits, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Geo-Sentinel Auditor API",
    description="Hyper-local SEO Analysis using Agentic AI.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(audits.router)
app.include_router(reports.router)


@app.on_event("startup")
async def startup():
    """Initialize database and log startup info."""
    db.init_db()
    logger.info("=" * 60)
    logger.info("  GEO-SENTINEL AUDITOR — Hyper-Local SEO")
    logger.info("  All Agents run locally via Ollama. $0 cost.")
    logger.info("=" * 60)
    logger.info("Database initialized.")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Geo-Sentinel Auditor",
    }
