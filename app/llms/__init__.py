"""
LLM configurations for Groq and Ollama.
"""

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from config import GROQ_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

# Groq LLM — fast, cheap, good for thinking tasks
groq_llm = ChatGroq(
    model="mixtral-8x7b-32768",
    api_key=GROQ_API_KEY,
    temperature=0.3,
    max_tokens=2000
)

# Groq LLM for writing — higher temp for creativity
groq_llm_writer = ChatGroq(
    model="mixtral-8x7b-32768",
    api_key=GROQ_API_KEY,
    temperature=0.7,
    max_tokens=4000
)

# Ollama LLM — local, free, good for fact checking
ollama_llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
    num_ctx=4096
)
