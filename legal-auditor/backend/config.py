"""
Configuration settings for the Legal Document Auditor.
All processing happens locally — zero data leaves this machine.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMADB_DIR = BASE_DIR / "chromadb_storage"
DB_PATH = BASE_DIR / "legal_auditor.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMADB_DIR.mkdir(exist_ok=True)

# Ollama settings (local LLM — $0 inference cost)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_REQUEST_TIMEOUT = float(os.getenv("LLM_REQUEST_TIMEOUT", "600.0"))

# Document processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# ChromaDB collection name
CHROMA_COLLECTION = "legal_documents"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = ["*"]  # For local development

# JWT Auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")

# Stripe Settings (loaded from .env — NEVER hardcode secrets)
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

