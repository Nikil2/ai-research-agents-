"""
📚 Knowledge Ingestion Agent

Responsibility:
  - Orchestrate PDF upload → extraction → cleaning → chunking → storage
  - This is the first agent in the pipeline
"""
import os
import shutil
from config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from services.pdf_service import extract_text_from_pdf, clean_text, chunk_text, get_file_size
from database.db import insert_document, insert_chunks, get_chunks_by_document


def process_document(file_path: str, original_filename: str) -> dict:
    """
    Full knowledge ingestion pipeline:
      1. Extract text from PDF
      2. Clean the text
      3. Chunk into knowledge pieces
      4. Store document + chunks in SQLite

    Args:
        file_path: Path to the uploaded PDF file
        original_filename: Original name of the uploaded file

    Returns:
        {
            "document_id": int,
            "filename": str,
            "total_pages": int,
            "total_chunks": int,
            "word_count": int,
            "status": "success" | "error",
            "message": str
        }
    """
    try:
        # Step 1: Extract text from PDF
        print(f"📄 Extracting text from: {original_filename}")
        extraction = extract_text_from_pdf(file_path)

        if not extraction["raw_text"].strip():
            return {
                "document_id": None,
                "filename": original_filename,
                "total_pages": extraction["total_pages"],
                "total_chunks": 0,
                "word_count": 0,
                "status": "error",
                "message": "No text could be extracted from this PDF. It may be scanned/image-based.",
            }

        # Step 2: Clean the text
        print("🧹 Cleaning extracted text...")
        cleaned_text = clean_text(extraction["raw_text"])

        # Step 3: Chunk the text
        print("✂️  Chunking text into knowledge pieces...")
        chunks = chunk_text(cleaned_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

        # Step 4: Store in database
        print("💾 Storing in knowledge base...")
        file_size = get_file_size(file_path)
        doc_id = insert_document(
            filename=original_filename,
            total_pages=extraction["total_pages"],
            raw_text=cleaned_text,
            file_size_bytes=file_size,
        )
        insert_chunks(doc_id, chunks)

        # Step 5: Move file to uploads directory for persistence
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        dest_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{original_filename}")
        shutil.move(file_path, dest_path)

        word_count = len(cleaned_text.split())
        print(f"✅ Document processed: {original_filename} → {len(chunks)} chunks, {word_count} words")

        return {
            "document_id": doc_id,
            "filename": original_filename,
            "total_pages": extraction["total_pages"],
            "total_chunks": len(chunks),
            "word_count": word_count,
            "status": "success",
            "message": f"Successfully processed {original_filename}",
        }

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        return {
            "document_id": None,
            "filename": original_filename,
            "total_pages": 0,
            "total_chunks": 0,
            "word_count": 0,
            "status": "error",
            "message": str(e),
        }


def get_document_knowledge(document_id: int) -> list[dict]:
    """Get all knowledge chunks for a document."""
    return get_chunks_by_document(document_id)
