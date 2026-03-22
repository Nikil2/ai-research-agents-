"""
LLM configurations for Groq and Ollama.
"""

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from crewai.llm import LLM
from config import GROQ_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

# Native CrewAI LLM wrapper for Groq
groq_llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.3
)

groq_llm_writer = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.7
)

# Native CrewAI LLM wrapper for Ollama
ollama_llm = LLM(
    model=f"ollama/{OLLAMA_MODEL}",
    base_url=OLLAMA_BASE_URL,
    temperature=0.2
)
