"""
Configuration settings for SupportSim AI — Customer Support Agent Training Platform.
All AI processing happens locally via Ollama — $0 inference cost.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMADB_DIR = BASE_DIR / "chromadb_storage"
DB_PATH = BASE_DIR / "supportsim.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(exist_ok=True)

# Ollama settings (local LLM — $0 inference cost)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))  # Higher for more creative persona simulation
LLM_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "600.0"))

# Document processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

# ChromaDB collection name
CHROMA_COLLECTION = "support_knowledge_bases"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))  # Different port from legal-auditor
CORS_ORIGINS = ["*"]  # For local development

# JWT Auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supportsim-change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Stripe Settings (SaaS billing)
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Training simulation settings
MAX_SIM_TURNS = int(os.getenv("MAX_SIM_TURNS", "20"))  # Max messages per training session
DEFAULT_DIFFICULTY = os.getenv("DEFAULT_DIFFICULTY", "medium")
STARTER_CREDITS = int(os.getenv("STARTER_CREDITS", "10"))

# Scenario categories
SCENARIO_CATEGORIES = [
    "billing",
    "technical_support",
    "complaint",
    "feature_request",
    "onboarding",
    "cancellation",
    "account_issue",
    "general_inquiry",
]

# Difficulty levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# Credit costs
CREDIT_COST_SESSION = float(os.getenv("CREDIT_COST_SESSION", "1.0"))
CREDIT_COST_EVALUATION = float(os.getenv("CREDIT_COST_EVALUATION", "0.5"))
CREDIT_COST_SCENARIO_GEN = float(os.getenv("CREDIT_COST_SCENARIO_GEN", "0.3"))
