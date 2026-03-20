"""
🎓 Cognitive Multi-Agent AI Academic Assistant
   Phase 1 — Core Foundation

FastAPI Backend — Main Entry Point
"""
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from database.db import (
    init_db,
    get_all_documents,
    get_document_by_id,
    delete_document,
    get_chunks_by_document,
    get_chat_history,
)
from agents.knowledge_agent import process_document
from agents.explanation_agent import answer_question, general_question
from models.schemas import (
    DocumentResponse,
    DocumentDetailResponse,
    UploadResponse,
    QuestionRequest,
    AnswerResponse,
    ChatHistoryItem,
    HealthResponse,
)


# ──────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────

app = FastAPI(
    title="Cognitive Multi-Agent AI Academic Assistant",
    description="Phase 1 — Knowledge Ingestion + Basic Q&A Pipeline",
    version="1.0.0",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# STARTUP — Initialize Database
# ──────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    print("🚀 Academic Assistant API is running — Phase 1")


# ──────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check system health: Ollama, Groq, Database."""
    import ollama as ollama_lib
    from config import GROQ_API_KEY

    # Check Ollama
    try:
        ollama_lib.list()
        ollama_status = "connected"
    except Exception:
        ollama_status = "unavailable"

    # Check Groq
    groq_status = "configured" if GROQ_API_KEY else "not configured (set GROQ_API_KEY)"

    return HealthResponse(
        status="running",
        ollama_status=ollama_status,
        groq_status=groq_status,
        database="connected",
        version="1.0.0 — Phase 1",
    )


# ──────────────────────────────────────────────
# PDF UPLOAD
# ──────────────────────────────────────────────

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF document.
    The Knowledge Ingestion Agent will:
      1. Extract text
      2. Clean it
      3. Chunk it
      4. Store in knowledge base
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. Got: {ext}")

    # Read file content
    content = await file.read()

    # Validate file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {MAX_FILE_SIZE_MB}MB.",
        )

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Run Knowledge Ingestion Agent
    result = process_document(tmp_path, file.filename or "document.pdf")

    if result["status"] == "error":
        # Clean up temp file on error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=result["message"])

    return UploadResponse(**result)


# ──────────────────────────────────────────────
# DOCUMENTS
# ──────────────────────────────────────────────

@app.get("/documents", response_model=list[DocumentResponse])
def list_documents():
    """Get all uploaded documents."""
    docs = get_all_documents()
    return [DocumentResponse(**doc) for doc in docs]


@app.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: int):
    """Get document details with its knowledge chunks."""
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = get_chunks_by_document(doc_id)
    return DocumentDetailResponse(**doc, chunks=chunks)


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: int):
    """Delete a document and all its knowledge chunks."""
    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {doc_id} deleted successfully"}


# ──────────────────────────────────────────────
# ASK QUESTION (Explanation Agent)
# ──────────────────────────────────────────────

@app.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    """
    Ask a question.
    - If document_id is provided → context-grounded answer from that document
    - If no document_id → general AI answer
    """
    if req.document_id:
        result = answer_question(req.question, req.document_id)
    else:
        result = general_question(req.question)

    return AnswerResponse(**result)


# ──────────────────────────────────────────────
# CHAT HISTORY
# ──────────────────────────────────────────────

@app.get("/chat-history", response_model=list[ChatHistoryItem])
def get_history(document_id: int | None = None, limit: int = 20):
    """Get chat history, optionally filtered by document."""
    history = get_chat_history(document_id=document_id, limit=limit)
    return [ChatHistoryItem(**item) for item in history]


# ──────────────────────────────────────────────
# RUN SERVER
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
