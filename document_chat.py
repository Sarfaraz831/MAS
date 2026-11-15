import ipaddress
import re
import socket
from io import BytesIO
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_DOCUMENT_CHARS = 80000
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_PDF_PAGES = 100

_COPYRIGHT_PATTERNS = (
    ("Copyright or rights notice", re.compile(r"\bcopyright\b|\ball rights reserved\b|©|\(c\)", re.IGNORECASE)),
    ("Creative Commons reference", re.compile(r"\bcreative commons\b|\bCC\s+BY(?:-[A-Z]+)*\b", re.IGNORECASE)),
    ("License or public-domain reference", re.compile(r"\bpublic domain\b|\blicen[cs]e(?:d)?\s+under\b", re.IGNORECASE)),
)

_SAFETY_PATTERNS = (
    ("self-harm related content", re.compile(r"\bself[- ]harm|suicid(?:e|al)\b", re.IGNORECASE)),
    ("violence-related content", re.compile(r"\bviolent|violence|weapon|attack|kill(?:ing)?\b", re.IGNORECASE)),
    ("sexual content", re.compile(r"\bsexual(?:ly)? explicit|pornograph(?:y|ic)\b", re.IGNORECASE)),
    ("dangerous-instruction-related content", re.compile(r"\bmake a bomb|build an explosive|weapon construction\b", re.IGNORECASE)),
    ("possible embedded prompt instructions", re.compile(r"\b(ignore|disregard) (all )?(previous|prior) instructions\b|\bsystem prompt\b", re.IGNORECASE)),
)


def analyze_copyright(text: str) -> dict:
    indicators = [
        label
        for label, pattern in _COPYRIGHT_PATTERNS
        if pattern.search(text)
    ]
    return {
        "status": "indicators_found" if indicators else "no_indicators_found",
        "indicators": indicators,
        "notice": "Heuristic notice scan only; this does not determine ownership or grant usage rights.",
    }


def analyze_safety(text: str) -> list[str]:
    """Return advisory, keyword-based safety flags; never block user content."""
    return [label for label, pattern in _SAFETY_PATTERNS if pattern.search(text)]


def _validate_public_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not supported.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("The URL contains an invalid port.") from exc
    allowed_port = 80 if parsed.scheme == "http" else 443
    if port not in (None, allowed_port):
        raise ValueError("Only standard HTTP and HTTPS ports are supported.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Local and private network URLs are not supported.")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(hostname, port or allowed_port, type=socket.SOCK_STREAM)
        }
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise ValueError("Local and private network URLs are not supported.")
    except OSError as exc:
        raise ValueError("The URL host could not be resolved.") from exc
    return url.strip()


def _read_url_bytes(response: requests.Response) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_SOURCE_BYTES:
        raise ValueError("The linked file is larger than 8 MB.")
    content = bytearray()
    for chunk in response.iter_content(chunk_size=65536):
        content.extend(chunk)
        if len(content) > MAX_SOURCE_BYTES:
            raise ValueError("The linked file is larger than 8 MB.")
    return bytes(content)


def _clean_text(content: str) -> str:
    normalized = re.sub(r"\n{3,}", "\n\n", content).strip()
    if len(normalized) > MAX_DOCUMENT_CHARS:
        suffix = "\n[Document text truncated.]"
        return normalized[: MAX_DOCUMENT_CHARS - len(suffix)] + suffix
    return normalized


def extract_pdf(data: bytes, filename: str) -> dict:
    if not data.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")

        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"[Page {page_number}]\n{page_text.strip()}")
        if not pages:
            raise ValueError("No selectable text was found. Scanned PDFs require OCR, which is not supported yet.")

        metadata = reader.metadata
        metadata_text = ""
        if metadata:
            metadata_text = "\n".join(
                str(value)
                for value in (metadata.title, metadata.author, metadata.subject)
                if value
            )
        full_content = f"{metadata_text}\n\n" + "\n\n".join(pages)
        return {
            "title": filename,
            "source_url": None,
            "content": _clean_text(full_content),
            "copyright": analyze_copyright(full_content),
            "safetyWarnings": analyze_safety(full_content),
        }
    except ValueError:
        raise
    except (OSError, PyPdfError) as exc:
        raise ValueError("The PDF could not be read. It may be damaged or use unsupported encryption.") from exc


def extract_url(url: str) -> dict:
    safe_url = _validate_public_url(url)
    try:
        with requests.get(
            safe_url,
            timeout=(3, 10),
            headers={"User-Agent": "MAS-DocumentChat/1.0"},
            allow_redirects=False,
            stream=True,
        ) as response:
            if response.is_redirect:
                raise ValueError("Redirecting URLs are not supported. Enter the final destination URL.")
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            data = _read_url_bytes(response)
            if content_type == "application/pdf":
                source = extract_pdf(data, safe_url.rsplit("/", 1)[-1] or "linked-document.pdf")
                source["source_url"] = safe_url
                return source
            if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise ValueError("Only web pages, plain text, and PDF links are supported.")

            encoding = response.encoding or "utf-8"
            raw_text = data.decode(encoding, errors="replace")
    except requests.RequestException as exc:
        raise ValueError("The URL could not be fetched.") from exc

    if content_type == "text/plain":
        title = safe_url
        text = raw_text
        license_links = ""
    else:
        soup = BeautifulSoup(raw_text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else safe_url
        license_links = "\n".join(
            anchor.get("href", "")
            for anchor in soup.find_all("a", href=True)
            if "license" in anchor.get("href", "").lower()
            or "creativecommons.org" in anchor.get("href", "").lower()
        )
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
    full_content = f"Title: {title}\nSource URL: {safe_url}\n\n{text}\n{license_links}"
    content = _clean_text(full_content)
    if not content:
        raise ValueError("No readable text was found at this URL.")
    return {
        "title": title[:300],
        "source_url": safe_url,
        "content": content,
        "copyright": analyze_copyright(full_content),
        "safetyWarnings": analyze_safety(full_content),
    }
