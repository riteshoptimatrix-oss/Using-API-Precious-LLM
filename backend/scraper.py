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

OFFICIAL_COMPANY_PROFILE = """=== OFFICIAL CONTACT & CONSULTANCY PROFILE ===
- Organization Name: Precious Education and Immigration Consultant (PEIC)
- Founded: Established in 2005 (5,000+ successful student & immigration stories, 55+ combined management experience)
- Corporate Head Office: 503, 5th Floor, Shivalik-9, Near Vasundhara Society, Gulbai Tekra, Ahmedabad-380006, Gujarat, India
- Official Landline Phone: +91 79 26405855
- Mobile / WhatsApp Hotline: +91 9879361728
- WhatsApp Chat Link: https://api.whatsapp.com/send?phone=919879361728
- Primary Email Address: info@preciousedu.in
- Official Website URL: https://www.preciousedu.in/
- Counseling Policy: Free of cost personalized counseling for all candidates & parents
- Authorized Testing Center: Authorized center to accept registrations for British Council and IDP IELTS examinations
- Partner Network: Represents over 300+ accredited universities and colleges across Australia, Canada, New Zealand, UK, USA, Singapore, Malaysia, and Ireland
- Primary Specializations:
  * Study Abroad & University Admissions
  * Student Visa & Study Permit Processing (SPP, General, Tier IV, F1/M1)
  * IELTS Coaching with certified British Council-trained faculties & preparation library
  * Work Visas (LMIA, PGWP, Open Work Permits, Spousal Work Permits)
  * Permanent Residency & Migration (Express Entry, Provincial Nominee Programs/PNP/OINP, Atlantic Pilot)
  * Visitor & Tourist Visas (Single & Multiple Entry)
  * Super Visa for parents & grandparents
  * Status Restoration, ATIP notes, TRP, and Procedural Fairness Letters
  * Comprehensive Pre-Landing and Post-Landing Support
==============================================="""


def html_to_clean_text(html_content: str) -> str:
    """Strips scripts, styles, and tags while preserving critical footer/contact text."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Extract telephone and mailto links before removing tags
        extracted_contacts = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                extracted_contacts.append(f"Email: {href.replace('mailto:', '').strip()}")
            elif href.startswith("tel:"):
                extracted_contacts.append(f"Phone: {href.replace('tel:', '').strip()}")
            elif "whatsapp.com/send" in href:
                phone_match = re.search(r"phone=([0-9]+)", href)
                if phone_match:
                    extracted_contacts.append(f"WhatsApp: +{phone_match.group(1)}")

        # Only decompose non-text elements (preserve footer & header!)
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = html.unescape(text)

        if extracted_contacts:
            text += "\n\nExtracted Contact Links:\n" + "\n".join(set(extracted_contacts))

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        return text.strip()
    except Exception as e:
        logger.warning(f"Error parsing HTML with BeautifulSoup: {e}")
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
    Returns complete website knowledge base context. Uses cache if valid,
    otherwise scrapes the website and bundles with official company profile.
    """
    cached = read_cache()
    if cached:
        return cached

    base_url = TARGET_SITE.rstrip("/")
    # Fetch primary site and known pages
    pages_to_try = [
        TARGET_SITE,
        f"{base_url}/about-us",
        f"{base_url}/contact-us",
        f"{base_url}/services",
        f"{base_url}/privacy-policy.html",
        f"{base_url}/terms-conditions.html",
    ]

    scraped_content = ""
    async with httpx.AsyncClient(verify=False) as client:
        tasks = [fetch_url(client, url) for url in pages_to_try]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, res in zip(pages_to_try, results):
            if isinstance(res, str) and res.strip():
                clean = html_to_clean_text(res)
                if clean:
                    scraped_content += f"\n\n--- PAGE: {url} ---\n{clean}"
            if len(scraped_content) > 14000:
                break

    # Combine the authoritative structured company profile with live-scraped text
    combined_text = f"{OFFICIAL_COMPANY_PROFILE}\n\n=== LIVE WEBSITE CONTENT ===\n{scraped_content.strip()}"
    combined_text = combined_text[:18000]

    write_cache(combined_text)
    return combined_text
