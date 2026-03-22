"""
Configuration settings for the Multi-Agent Research Assistant.
Loads environment variables from .env file using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # Groq API
    GROQ_API_KEY: str
    
    # Ollama
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str = "qwen2.5-coder"
    
    # MCP Server
    MCP_SERVER_URL: str = "http://localhost:8000/sse"
    MCP_SERVER_PORT: int = 8000
    
    # Application
    DEBUG: bool = True
    
    class Config:
        """Load from .env file."""
        env_file = ".env"
        case_sensitive = True


# Create singleton settings instance
settings = Settings()

# Export commonly used variables for backward compatibility
DATABASE_URL = settings.DATABASE_URL
GROQ_API_KEY = settings.GROQ_API_KEY
OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
MCP_SERVER_URL = settings.MCP_SERVER_URL
MCP_SERVER_PORT = settings.MCP_SERVER_PORT
DEBUG = settings.DEBUG
