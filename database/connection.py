"""
PostgreSQL Database (Neon) — Knowledge Base, Documents, Chat History
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config import DATABASE_URL


def get_connection():
    """Get a PostgreSQL connection with dictionary cursor."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in environment or config.")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def check_connection():
    """Test if database connection is working."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        return False


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_login_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # ── Research Jobs table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            topic VARCHAR(500) NOT NULL,
            depth VARCHAR(50) DEFAULT 'detailed',
            status VARCHAR(50) DEFAULT 'pending',
            error_message TEXT,
            failed_agent VARCHAR(100),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ── Sources table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL,
            url VARCHAR(2048) NOT NULL,
            title VARCHAR(500),
            snippet TEXT,
            full_content TEXT,
            agent_summary TEXT,
            credibility_score FLOAT,
            found_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (job_id) REFERENCES research_jobs(id) ON DELETE CASCADE
        )
    """)

    # ── Agent Outputs table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_outputs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL,
            agent_name VARCHAR(100) NOT NULL,
            output_type VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            llm_used VARCHAR(100),
            tokens_used INTEGER,
            duration_seconds FLOAT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (job_id) REFERENCES research_jobs(id) ON DELETE CASCADE
        )
    """)

    # ── Reports table ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL UNIQUE,
            user_id UUID NOT NULL,
            title VARCHAR(300) NOT NULL,
            content_markdown TEXT NOT NULL,
            file_path VARCHAR(500),
            word_count INTEGER,
            source_count INTEGER,
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            FOREIGN KEY (job_id) REFERENCES research_jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully on Neon with 5 tables: users, research_jobs, sources, agent_outputs, reports")


# ──────────────────────────────────────────────
# DOCUMENT OPERATIONS
# ──────────────────────────────────────────────

def insert_document(filename: str, total_pages: int, raw_text: str, file_size_bytes: int) -> int:
    """Insert a new document and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (filename, total_pages, raw_text, upload_date, file_size_bytes) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (filename, total_pages, raw_text, datetime.now().isoformat(), file_size_bytes)
    )
    doc_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return doc_id


def get_all_documents() -> list[dict]:
    """Get all documents (without raw_text for performance)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, total_pages, upload_date, file_size_bytes FROM documents ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_document_by_id(doc_id: int) -> dict | None:
    """Get a single document by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document(doc_id: int) -> bool:
    """Delete a document and its chunks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ──────────────────────────────────────────────
# CHUNK OPERATIONS
# ──────────────────────────────────────────────

def insert_chunks(document_id: int, chunks: list[str]):
    """Insert multiple knowledge chunks for a document."""
    conn = get_connection()
    cursor = conn.cursor()
    for i, chunk in enumerate(chunks):
        word_count = len(chunk.split())
        cursor.execute(
            "INSERT INTO knowledge_chunks (document_id, chunk_text, chunk_index, word_count) VALUES (%s, %s, %s, %s)",
            (document_id, chunk, i, word_count)
        )
    conn.commit()
    conn.close()


def get_chunks_by_document(document_id: int) -> list[dict]:
    """Get all chunks for a document."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM knowledge_chunks WHERE document_id = %s ORDER BY chunk_index",
        (document_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_chunks(document_id: int, query: str, limit: int = 5) -> list[dict]:
    """
    Simple keyword search across chunks of a document.
    Phase 2 will upgrade this to vector/semantic search (RAG).
    """
    conn = get_connection()
    cursor = conn.cursor()
    keywords = query.lower().split()
    cursor.execute(
        "SELECT * FROM knowledge_chunks WHERE document_id = %s ORDER BY chunk_index",
        (document_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Score each chunk by keyword overlap
    scored = []
    for row in rows:
        chunk_lower = row["chunk_text"].lower()
        score = sum(1 for kw in keywords if kw in chunk_lower)
        if score > 0:
            scored.append((score, dict(row)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


# ──────────────────────────────────────────────
# CHAT HISTORY OPERATIONS
# ──────────────────────────────────────────────

def insert_chat(document_id: int | None, question: str, answer: str, model_used: str) -> int:
    """Save a Q&A interaction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (document_id, question, answer, model_used, timestamp) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (document_id, question, answer, model_used, datetime.now().isoformat())
    )
    chat_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return chat_id


def get_chat_history(document_id: int | None = None, limit: int = 20) -> list[dict]:
    """Get chat history, optionally filtered by document."""
    conn = get_connection()
    cursor = conn.cursor()
    if document_id:
        cursor.execute(
            "SELECT * FROM chat_history WHERE document_id = %s ORDER BY id DESC LIMIT %s",
            (document_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM chat_history ORDER BY id DESC LIMIT %s",
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
