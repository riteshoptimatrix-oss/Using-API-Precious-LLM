import asyncio
import html
import json
import logging
import re
import time
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

from config import CACHE_FILE, CACHE_TTL, TARGET_SITE

logger = logging.getLogger("scraper")


def html_to_clean_text(html_content: str) -> str:
    """Strips scripts, styles, tags, and excessive whitespace from HTML."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = html.unescape(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        return text.strip()
    except Exception as e:
        logger.warning(f"Error parsing HTML with BeautifulSoup: {e}")
        # Fallback to regex stripping
        clean = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<style\b[^>]*>.*?</style>", " ", clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = html.unescape(clean)
        clean = re.sub(r"[ \t]+", " ", clean)
        clean = re.sub(r"\n\s*\n+", "\n", clean)
        return clean.strip()


async def fetch_url(client: httpx.AsyncClient, url: str, timeout: float = 6.0) -> Optional[str]:
    """Fetches a single URL with error handling and timeout."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PreciousEduBot/1.0)"}
        response = await client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        if response.status_code < 400:
            return response.text
        return None
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


async def fetch_all_pages(urls: List[str]) -> Dict[str, Optional[str]]:
    """Fetches multiple URLs concurrently."""
    async with httpx.AsyncClient(verify=False) as client:
        tasks = [fetch_url(client, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        pages = {}
        for url, res in zip(urls, results):
            if isinstance(res, str):
                pages[url] = res
            else:
                pages[url] = None
        return pages


def read_cache() -> Optional[str]:
    """Reads valid cached site context from disk if not expired."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_time = data.get("time", 0)
            content = data.get("content", "")
            if (time.time() - cached_time) < CACHE_TTL and content:
                return content
        except Exception as e:
            logger.warning(f"Failed to read cache file: {e}")
    return None


def write_cache(content: str) -> None:
    """Saves scraped content to local cache file."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"time": time.time(), "content": content}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write cache file: {e}")


async def get_site_context() -> str:
    """
    Returns website content. Uses cache if valid, otherwise scrapes the target site
    and its primary subpages in parallel.
    """
    cached = read_cache()
    if cached:
        return cached

    base = TARGET_SITE.rstrip("/")
    pages_to_try = [
        TARGET_SITE,
        f"{base}/about",
        f"{base}/about-us",
        f"{base}/courses",
        f"{base}/contact",
        f"{base}/contact-us",
    ]

    results = await fetch_all_pages(pages_to_try)

    combined_text = ""
    for url in pages_to_try:
        page_html = results.get(url)
        if page_html:
            clean = html_to_clean_text(page_html)
            if clean:
                combined_text += f"\n\n--- PAGE: {url} ---\n{clean}"
        if len(combined_text) > 15000:
            break

    if not combined_text.strip():
        # Fallback to expired cache if available
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("content"):
                    return data["content"]
            except Exception:
                pass
        return "Website data could not be fetched at this time."

    # Limit total size to prevent prompt overflow
    combined_text = combined_text[:18000]
    write_cache(combined_text)
    return combined_text
