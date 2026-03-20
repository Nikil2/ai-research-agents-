"""
Configuration for the Cognitive Multi-Agent AI Academic Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────
# Your Neon PostgreSQL connection string (set this in your .env file)
DATABASE_URL = os.getenv("DATABASE_URL")


# ──────────────────────────────────────────────
# FILE UPLOADS
# ──────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".pdf"}

# ──────────────────────────────────────────────
# OLLAMA (Local LLM — Primary)
# ──────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"  # Change to "mistral" or any model you have pulled

# ──────────────────────────────────────────────
# GROQ (Cloud LLM — Fallback)
# ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Set via environment variable
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ──────────────────────────────────────────────
# TEXT CHUNKING
# ──────────────────────────────────────────────
CHUNK_SIZE = 500       # words per chunk
CHUNK_OVERLAP = 50     # overlapping words between chunks
