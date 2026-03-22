"""
Writer Agent — composes final Markdown report.
"""

from crewai import Agent
from app.llms.groq_llm import groq_llm_writer


def get_writer_agent() -> Agent:
    """Create the Writer agent."""
    return Agent(
        role="Research Report Writer",
        goal="Write a professional, well-structured Markdown research report using all provided context",
        backstory="Expert at crafting clear, evidence-based research reports with proper citations.",
        tools=[],
        llm=groq_llm_writer,
        verbose=True,
        allow_delegation=False
    )
