"""
Health check endpoint — verifies all services are operational.
"""

from fastapi import APIRouter
from database.connection import check_connection
from database.schemas import HealthResponse
import httpx
import os
from config import OLLAMA_BASE_URL, MCP_SERVER_URL

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health of all backend services.
    Returns status of: Database, Groq, Ollama, MCP Server
    """
    
    # 1. Check PostgreSQL Database
    try:
        db_ok = check_connection()
        database_status = "connected" if db_ok else "disconnected"
    except Exception as e:
        db_ok = False
        database_status = "disconnected"
    
    # 2. Check Groq API
    groq_key = os.getenv("GROQ_API_KEY")
    groq_ok = bool(groq_key and groq_key.strip())
    groq_status = "reachable" if groq_ok else "unreachable"
    
    # 3. Check Ollama
    ollama_ok = False
    ollama_status = "not running"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                ollama_ok = True
                ollama_status = "running"
    except Exception:
        ollama_status = "not running"
    
    # 4. Check MCP Server
    mcp_status = "not started"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(MCP_SERVER_URL)
            if response.status_code in [200, 404, 405]:  # 404/405 OK for health check
                mcp_status = "running"
    except Exception:
        mcp_status = "not started"
    
    # Determine overall status
    all_critical_ok = db_ok and groq_ok
    overall_status = "healthy" if all_critical_ok else "degraded"
    
    return HealthResponse(
        status=overall_status,
        database=database_status,
        groq_status=groq_status,
        ollama_status=ollama_status,
        mcp_server=mcp_status,
        version="1.0.0"
    )
