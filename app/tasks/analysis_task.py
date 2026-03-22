"""
Analysis Task — what the Analyst agent does.
"""

from crewai import Task


def get_analysis_task(agent) -> Task:
    """Create the analysis task."""
    return Task(
        description="""
        Analyze the research findings:
        1. Identify the 5-7 most important insights
        2. Group related findings together
        3. Highlight trends, statistics, and key data points
        4. Note any contradictions or gaps in the research
        5. Rank insights by importance and relevance

        Research context:
        {research}
        """,
        expected_output="""
        A well-organized analysis document with:
        - Top findings with supporting evidence
        - Key trends and patterns
        - Statistics and metrics
        - Gaps in current knowledge
        - Recommendations for further research
        """,
        agent=agent
    )
