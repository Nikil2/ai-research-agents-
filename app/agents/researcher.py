"""
Researcher Agent — finds credible sources via web search.
"""

from crewai import Agent
from app.llms.groq_llm import groq_llm


def get_researcher_agent(mcp_tools: list = None) -> Agent:
    """Create the Researcher agent with web search tools."""
    # Use provided tools or empty list
    tools = mcp_tools if mcp_tools else []
    
    return Agent(
        role="Senior Research Specialist",
        goal="Find 5-8 credible, recent, relevant sources on the topic and summarize each one clearly",
        backstory="Expert at locating and evaluating reliable information on any topic using web search.",
        tools=tools,
        llm=groq_llm,
        verbose=True,
        max_iter=10,
        allow_delegation=False
    )
