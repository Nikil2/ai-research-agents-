"""
🧠 Explanation & Reasoning Agent

Responsibility:
  - Take a student's question
  - Retrieve relevant knowledge chunks
  - Build a context-grounded prompt
  - Get AI response (Ollama / Groq hybrid)
  - Save to chat history
"""
from database.db import search_chunks, get_document_by_id, insert_chat
from services.llm_service import get_ai_response


SYSTEM_PROMPT = """You are an intelligent academic tutor AI. Your role is to help students understand their study material.

Rules:
1. Answer ONLY based on the provided context from the student's documents.
2. If the context doesn't contain enough information, say so honestly.
3. Explain concepts clearly and simply — like a good tutor would.
4. Use examples and analogies when helpful.
5. Structure your answers with headings and bullet points for readability.
6. If the student asks something outside the document scope, politely redirect them.

You are NOT a generic chatbot. You are a knowledge-grounded academic assistant."""


def answer_question(question: str, document_id: int) -> dict:
    """
    Full Q&A pipeline:
      1. Retrieve relevant chunks from document
      2. Build context-grounded prompt
      3. Get AI response (hybrid: Ollama → Groq fallback)
      4. Save to chat history

    Args:
        question: Student's question
        document_id: ID of the document to search

    Returns:
        {
            "answer": str,
            "model_used": str,
            "source": "ollama" | "groq",
            "context_chunks": int,
            "document_id": int,
            "chat_id": int
        }
    """
    # Step 1: Verify document exists
    doc = get_document_by_id(document_id)
    if not doc:
        return {
            "answer": "Document not found. Please upload a document first.",
            "model_used": "none",
            "source": "none",
            "context_chunks": 0,
            "document_id": document_id,
            "chat_id": None,
        }

    # Step 2: Retrieve relevant chunks
    relevant_chunks = search_chunks(document_id, question, limit=5)

    if not relevant_chunks:
        # If no keyword match, use first few chunks as general context
        from database.db import get_chunks_by_document
        all_chunks = get_chunks_by_document(document_id)
        relevant_chunks = all_chunks[:3]  # First 3 chunks as fallback

    # Step 3: Build context-grounded prompt
    context = "\n\n---\n\n".join([chunk["chunk_text"] for chunk in relevant_chunks])

    prompt = f"""Based on the following study material context, answer the student's question.

=== STUDY MATERIAL CONTEXT ===
{context}
=== END CONTEXT ===

Student's Question: {question}

Provide a clear, educational answer grounded in the above context."""

    # Step 4: Get AI response
    try:
        ai_result = get_ai_response(prompt, system_prompt=SYSTEM_PROMPT)
        answer = ai_result["response"]
        model_used = ai_result["model"]
        source = ai_result["source"]
    except Exception as e:
        answer = f"I'm sorry, I couldn't generate a response right now. Error: {str(e)}"
        model_used = "none"
        source = "error"

    # Step 5: Save to chat history
    chat_id = insert_chat(
        document_id=document_id,
        question=question,
        answer=answer,
        model_used=f"{source}:{model_used}",
    )

    return {
        "answer": answer,
        "model_used": model_used,
        "source": source,
        "context_chunks": len(relevant_chunks),
        "document_id": document_id,
        "chat_id": chat_id,
    }


def general_question(question: str) -> dict:
    """
    Answer a general question without document context.
    Uses the LLM directly.
    """
    prompt = f"""Answer the following academic question clearly and helpfully.

Question: {question}"""

    try:
        ai_result = get_ai_response(prompt, system_prompt=SYSTEM_PROMPT)
        answer = ai_result["response"]
        model_used = ai_result["model"]
        source = ai_result["source"]
    except Exception as e:
        answer = f"I'm sorry, I couldn't generate a response right now. Error: {str(e)}"
        model_used = "none"
        source = "error"

    chat_id = insert_chat(
        document_id=None,
        question=question,
        answer=answer,
        model_used=f"{source}:{model_used}",
    )

    return {
        "answer": answer,
        "model_used": model_used,
        "source": source,
        "context_chunks": 0,
        "document_id": None,
        "chat_id": chat_id,
    }
