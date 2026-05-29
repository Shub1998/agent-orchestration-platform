from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for current information about a topic. Returns a summary of search results."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No results found for: {query}"
        formatted = []
        for r in results:
            formatted.append(f"**{r.get('title', 'No title')}**\n{r.get('body', '')}\nSource: {r.get('href', '')}")
        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        return f"Search failed: {str(e)}"
