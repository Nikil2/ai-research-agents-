"""
Ollama LLM re-export for fact-checking tasks.
"""

from app.llms.groq_llm import ollama_llm

__all__ = ["ollama_llm"]
