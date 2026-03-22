"""
Fact Checker Agent — verifies claims using local Ollama.
"""

from crewai import Agent
from app.llms.ollama_llm import ollama_llm


def get_fact_checker_agent(mcp_tools: list = None) -> Agent:
    """Create the Fact Checker agent with web search tools."""
    # Use provided tools or empty list
    tools = mcp_tools if mcp_tools else []
    
    return Agent(
        role="Accuracy & Verification Specialist",
        goal="Verify every key claim — label each ✅ Verified, ⚠️ Unverified, or ❌ Contradicted",
        backstory="Skeptical by nature. Cross-checks every claim against multiple independent sources.",
        tools=tools,
        llm=ollama_llm,
        verbose=True,
        allow_delegation=False
    )
