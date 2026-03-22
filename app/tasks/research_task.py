"""
Research Task — what the Researcher agent does.
"""

from crewai import Task


def get_research_task(agent, topic: str, depth: str) -> Task:
    """Create the research task."""
    detail_level = {
        "quick": "3-4 sources, brief summaries",
        "detailed": "5-6 sources, detailed summaries",
        "deep_dive": "7-8 sources, comprehensive analysis"
    }[depth]

    return Task(
        description=f"""
        Research this topic thoroughly: '{topic}'
        Depth requirement: {detail_level}

        Steps:
        1. Use search_web() to find relevant sources (run 2-3 different queries)
        2. Use fetch_page() to get full content of the best results
        3. Summarize each source: what it says, key facts, relevance
        4. Note the URL, title, and key points for each source
        """,
        expected_output="""
        A structured list of sources. For each source:
        - URL
        - Title
        - 2-3 paragraph summary
        - 3-5 key facts or statistics
        - Relevance score 0.0-1.0
        """,
        agent=agent
    )
