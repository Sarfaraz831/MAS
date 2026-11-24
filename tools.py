from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import os
import re
import socket
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
import requests
from tavily import TavilyClient

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MAX_URLS_PER_BATCH = 5
MAX_PASSAGES_PER_SOURCE = 12
PASSAGE_CHAR_LIMIT = 500


def is_safe_url(url: str) -> bool:
    """Validate URL and prevent requests to private/internal IP addresses."""
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
            return False

        addresses = socket.getaddrinfo(hostname, None)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
            if not ip.is_global:
                return False

        return True
    except (ValueError, socket.gaierror, OSError):
        return False


def extract_citable_passages(html_bytes: bytes) -> tuple[str, list[str]]:
    """Parse HTML into clean, numbered passages suitable for claim-level citations."""
    soup = BeautifulSoup(html_bytes, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Untitled page"

    for tag in soup(["script", "style", "nav", "footer", "aside", "header", "form"]):
        tag.decompose()

    blocks = []
    for el in soup.find_all(["p", "li", "h1", "h2", "h3", "blockquote", "td"]):
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if len(text) < 40:
            continue
        blocks.append(text)

    passages: list[str] = []
    buffer = ""
    seen = set()

    for block in blocks:
        if block in seen:
            continue
        seen.add(block)

        if len(buffer) + len(block) + 1 <= PASSAGE_CHAR_LIMIT:
            buffer = f"{buffer} {block}".strip()
        else:
            if buffer:
                passages.append(buffer)
            buffer = block[:PASSAGE_CHAR_LIMIT]

        if len(passages) >= MAX_PASSAGES_PER_SOURCE:
            break

    if buffer and len(passages) < MAX_PASSAGES_PER_SOURCE:
        passages.append(buffer)

    return title, passages


def _fetch_single_source(source_id: str, url: str) -> str:
    """Fetch a single URL with per-hop SSRF validation and return numbered passages."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
    current_url = url
    response = None

    try:
        for _ in range(5):
            if not is_safe_url(current_url):
                return f"=== SOURCE {source_id} ===\nURL: {url}\nError: URL is not allowed for security reasons."

            response = requests.get(
                current_url,
                timeout=15,
                headers=headers,
                allow_redirects=False,
                stream=True,
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                response = None
                if not location:
                    return f"=== SOURCE {source_id} ===\nURL: {url}\nError: Redirect missing Location header."
                current_url = urljoin(current_url, location)
                continue
            break
        else:
            return f"=== SOURCE {source_id} ===\nURL: {url}\nError: Too many redirects."

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "text/plain" not in content_type:
            return f"=== SOURCE {source_id} ===\nURL: {current_url}\nError: Unsupported content type ({content_type})."

        raw_bytes = response.raw.read(1_000_000, decode_content=True)
        title, passages = extract_citable_passages(raw_bytes)

        if not passages:
            return f"=== SOURCE {source_id} ===\nTitle: {title}\nURL: {current_url}\nNo readable passages extracted."

        formatted_passages = "\n".join(
            f"[{source_id}:P{idx}] {passage}"
            for idx, passage in enumerate(passages, start=1)
        )
        return (
            f"=== SOURCE {source_id} ===\n"
            f"Title: {title}\n"
            f"URL: {current_url}\n"
            f"Passages:\n{formatted_passages}"
        )
    except Exception as e:
        return f"=== SOURCE {source_id} ===\nURL: {url}\nError: Could not scrape URL ({str(e)})"
    finally:
        if response is not None:
            response.close()


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns titles, URLs, and snippets."""
    try:
        result = tavily.search(query=query, max_results=5)
        result_list = []

        for r in result.get("results", []):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = (r.get("content") or "")[:300].replace("\n", " ")
            result_list.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")

        return "\n----\n".join(result_list) if result_list else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
def scrape_urls(urls: list[str]) -> str:
    """Scrape multiple URLs in parallel and return numbered passages ([S1:P1], [S2:P1], etc.)
    for claim-level citations. Pass up to 5 URLs at once."""
    if not urls:
        return "Error: No URLs provided."

    unique_urls = list(dict.fromkeys(u.strip() for u in urls if u.strip()))[:MAX_URLS_PER_BATCH]

    if not unique_urls:
        return "Error: No URLs provided."

    results_by_index: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=min(len(unique_urls), MAX_URLS_PER_BATCH)) as executor:
        future_to_idx = {
            executor.submit(_fetch_single_source, f"S{idx}", url): idx
            for idx, url in enumerate(unique_urls, start=1)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results_by_index[idx] = future.result()

    ordered_outputs = [results_by_index[idx] for idx in sorted(results_by_index)]
    return "\n\n".join(ordered_outputs)