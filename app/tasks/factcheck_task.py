"""
Fact Check Task — what the Fact Checker agent does.
"""

from crewai import Task


def get_factcheck_task(agent) -> Task:
    """Create the fact check task."""
    return Task(
        description="""
        Verify the accuracy of key claims from the research and analysis:
        1. Extract all factual claims and statistics
        2. Use search_web to verify each major claim
        3. Cross-reference with multiple sources
        4. Label each claim: ✅ Verified, ⚠️ Unverified, or ❌ Contradicted
        5. Flag any misinformation or outdated data

        Research context:
        {research}

        Analysis context:
        {analysis}
        """,
        expected_output="""
        A fact-check report with:
        - Each major claim evaluated
        - Verification status (✅/⚠️/❌)
        - Supporting evidence or contradiction sources
        - Confidence level for each verification
        - Red flags or suspicious information
        """,
        agent=agent
    )
