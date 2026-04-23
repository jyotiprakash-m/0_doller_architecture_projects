"""
Configuration settings for the Ghost-Editor.
Modeled after the legal-auditor project structure.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMADB_DIR = BASE_DIR / "chromadb_storage"
DB_PATH = BASE_DIR / "ghost_editor.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMADB_DIR.mkdir(exist_ok=True)

# GitHub settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# Ollama settings (Local LLM)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = ["*"]  # For local development

# Auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ghost-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
