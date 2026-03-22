"""
Analyst Agent — extracts insights and patterns from research.
"""

from crewai import Agent
from app.llms.groq_llm import groq_llm


def get_analyst_agent() -> Agent:
    """Create the Analyst agent."""
    return Agent(
        role="Data Analyst & Insight Synthesizer",
        goal="Extract the 5-7 most important insights, trends, and statistics from collected research",
        backstory="Expert at finding patterns across sources and structuring complex information clearly.",
        tools=[],
        llm=groq_llm,
        verbose=True,
        allow_delegation=False
    )
