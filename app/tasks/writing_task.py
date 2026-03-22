"""
Writing Task — what the Writer agent does.
"""

from crewai import Task


def get_writing_task(agent, job_id: str) -> Task:
    """Create the writing task."""
    return Task(
        description=f"""
        Compose a professional Markdown research report using ALL context from researcher, analyst, and fact-checker:
        
        Report structure:
        1. Executive Summary (2-3 paragraphs)
        2. Introduction & Methodology
        3. Findings (organized by theme)
        4. Analysis & Insights
        5. Verification Status (include fact-check results)
        6. Conclusion & Recommendations
        7. Sources & Citations (include all URLs with titles)
        
        Requirements:
        - Use Markdown formatting with proper headings
        - Include verified facts with evidence
        - Flag unverified or contradicted claims
        - Professional tone, clear language
        - ~800-2000 words
        - Proper citations for all sources

        Research context:
        {{research}}

        Analysis context:
        {{analysis}}

        Fact-check context:
        {{factcheck}}
        """,
        expected_output=f"""
        A complete, well-formatted Markdown report ready for publication:
        - Professional structure with all requested sections
        - Clear citations and source attributions
        - Fact-check status clearly indicated
        - Actionable conclusions and recommendations
        - Ready to save to disk as {job_id}.md
        """,
        agent=agent
    )
