from langchain_core.tools import tool


@tool
def web_scraper(url: str) -> str:
    """Fetch and extract the text content from a web page URL."""
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AgentFlow/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines[:200])
    except Exception as e:
        return f"Failed to scrape {url}: {str(e)}"
