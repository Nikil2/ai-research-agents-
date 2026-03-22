"""
MCP Server with web search and fetch tools.
Run this as a separate process: python -m mcp_server.server
Listens on http://localhost:8001/sse
"""

from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup

mcp = FastMCP("research-tools", port=8001)


@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo API.
    Returns a list of URLs, titles, and snippets.
    
    Args:
        query: Search query
        max_results: Number of results to return (1-10)
    
    Returns:
        JSON-formatted list of search results
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=min(max_results, 10)):
                results.append({
                    "url": result.get("href"),
                    "title": result.get("title"),
                    "snippet": result.get("body", "")
                })
        
        import json
        return json.dumps(results, indent=2)
    
    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool()
def fetch_page(url: str) -> str:
    """
    Fetch a URL and extract clean readable text (no HTML, scripts, or styles).
    
    Args:
        url: URL to fetch
    
    Returns:
        Clean text content from the page (limited to 5000 chars)
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ResearchBot/1.0"
        }
        
        response = httpx.get(
            url,
            headers=headers,
            timeout=10,
            follow_redirects=True
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "noscript"]):
            tag.decompose()
        
        # Get clean text
        text = " ".join(soup.get_text(separator=" ").split())
        
        # Limit to 5000 chars
        return text[:5000]
    
    except Exception as e:
        return f"Fetch failed: {str(e)}"


@mcp.tool()
def extract_snippets(page_text: str, topic: str, num_snippets: int = 5) -> str:
    """
    Extract the most topic-relevant sentences from page text.
    
    Args:
        page_text: Full page text to analyze
        topic: Topic to find relevant content for
        num_snippets: Number of snippets to extract
    
    Returns:
        Topic-relevant snippets separated by newlines
    """
    try:
        # Split into sentences
        sentences = [s.strip() for s in page_text.split(".") if len(s.strip()) > 20]
        
        # Score each sentence by topic relevance
        topic_words = set(topic.lower().split())
        scored = []
        
        for sentence in sentences:
            score = sum(1 for word in topic_words if word.lower() in sentence.lower())
            if score > 0:
                scored.append((sentence, score))
        
        # Get top snippets
        top_snippets = sorted(scored, key=lambda x: x[1], reverse=True)[:num_snippets]
        
        result = "\n\n".join([f"• {s[0]}" for s in top_snippets])
        return result if result else "No relevant snippets found."
    
    except Exception as e:
        return f"Extraction failed: {str(e)}"


if __name__ == "__main__":
    print("Starting MCP Server on port 8001...")
    print("Tools: search_web, fetch_page, extract_snippets")
    print("Endpoint: http://localhost:8001/sse")
    mcp.run(transport="sse")
