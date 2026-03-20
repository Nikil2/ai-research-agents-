"""
LLM Service — Hybrid AI (Ollama Local + Groq Cloud Fallback)

Strategy:
  1. Try Ollama (local) first → free, private, no API key
  2. If Ollama fails → fall back to Groq (cloud) → fast, free tier
  3. Return response + which model was used
"""
import ollama
import requests
import json
from config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_API_URL,
)


def query_ollama(prompt: str, system_prompt: str = "") -> dict:
    """
    Query local Ollama model.

    Returns: {"response": str, "model": str, "source": "ollama"}
    Raises: Exception if Ollama is unavailable
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
    )

    return {
        "response": response["message"]["content"],
        "model": OLLAMA_MODEL,
        "source": "ollama",
    }


def query_groq(prompt: str, system_prompt: str = "") -> dict:
    """
    Query Groq cloud API (OpenAI-compatible).

    Returns: {"response": str, "model": str, "source": "groq"}
    Raises: Exception if Groq API fails
    """
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not set. Set it via environment variable.")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {
        "response": data["choices"][0]["message"]["content"],
        "model": GROQ_MODEL,
        "source": "groq",
    }


def get_ai_response(prompt: str, system_prompt: str = "") -> dict:
    """
    Hybrid LLM call:
      1. Try Ollama (local) first
      2. Fall back to Groq (cloud) if Ollama fails

    Returns:
        {
            "response": str,
            "model": str,
            "source": "ollama" | "groq",
        }
    """
    # ── Try Ollama first ──
    try:
        result = query_ollama(prompt, system_prompt)
        print(f"✅ Response from Ollama ({OLLAMA_MODEL})")
        return result
    except Exception as e:
        print(f"⚠️  Ollama failed: {e}")

    # ── Fall back to Groq ──
    try:
        result = query_groq(prompt, system_prompt)
        print(f"✅ Response from Groq ({GROQ_MODEL})")
        return result
    except Exception as e:
        print(f"❌ Groq also failed: {e}")
        raise Exception(
            "Both Ollama and Groq are unavailable. "
            "Make sure Ollama is running locally (ollama serve) "
            "or set GROQ_API_KEY environment variable."
        )
