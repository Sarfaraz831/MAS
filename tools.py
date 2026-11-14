from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# web_search feature:
# - queries Tavily for current web results
# - returns titles, URLs, and snippets so the agent can choose the most relevant sources
# - this works as the discovery stage for the research workflow
@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable infromation on a topic. Returns Titles , URLs , Snippet"""

    result = tavily.search(query=query, max_results=5)

    result_list = []

    for r in result.get("results", []):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        snippet = (r.get("content") or "")[:300].replace("\n", " ")
        result_list.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")

    return "\n----\n".join(result_list)

# scrape_url feature:
# - downloads a web page
# - removes script/style/nav/footer clutter
# - returns readable text content for deeper analysis
# - includes title and source URL so the report can later present proper citations
@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else "Untitled page"

        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return f"Title: {title}\nURL: {url}\n\n{text[:8000]}"
    except Exception as e:
        return f"Could not Scrape URL: {str(e)}"
