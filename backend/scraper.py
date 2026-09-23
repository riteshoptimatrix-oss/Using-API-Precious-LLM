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

# Comprehensive A-to-Z Knowledge Base directly extracted from https://www.preciousedu.in/
FULL_WEBSITE_KNOWLEDGE_BASE = """
================================================================================
PRECIOUS EDUCATION AND IMMIGRATION CONSULTANT (PEIC) — COMPLETE KNOWLEDGE BASE
Official Website: https://www.preciousedu.in/
Tagline: "You Dream it and we Make it" | "One Stop Solution For All Your Study Abroad Needs"
================================================================================

1. ABOUT US & CREDENTIALS:
- Established: 2005 (18+ years of dedicated service in overseas education and migration).
- Track Record: 5,000+ success stories over the past 12+ years.
- Leadership: Management team holds a cumulative 55+ man-years of experience in international education & immigration.
- Partner Network: Represents over 300+ accredited universities and colleges across Australia, Canada, New Zealand, UK, USA, Singapore, Malaysia, and Ireland.
- Counseling Policy: 100% Free of Cost personalized counseling for students, applicants, and parents.
- Approach: Tailored personalized counseling avoiding an assembly-line method; assessing student background, career goals, and finances.
- Visa Success Ratio: Exceptionally high visa success ratio driven by deep mastery of admission processes and official visa rules.
- Global Solutions: Comprehensive education, immigration, and visa solutions under one roof.

2. OFFICIAL CONTACT DETAILS:
- Corporate Head Office Address: 
  503, 5th Floor, Shivalik-9, Near Vasundhara Society, Gulbai Tekra, Ahmedabad - 380006, Gujarat, India.
- Landline Telephone: +91 79 26405855
- Mobile Helpline & WhatsApp: +91 9879361728
- Direct WhatsApp Link: https://api.whatsapp.com/send?phone=919879361728
- Official Email: info@preciousedu.in
- Website: https://www.preciousedu.in/

3. COMPLETE A-TO-Z SERVICES OFFERED:

A. STUDY VISA SERVICES:
- Study Permit / Student Visa application & filing
- Study Permit Extension / Renewal
- College & University Admissions across 300+ institutions worldwide
- College Transfer & DLI (Designated Learning Institution) Change
- Scholarships assistance for meritorious and deserving candidates
- Pre-Landing & Post-Landing services (accommodation, airport pickup, settlement guidance)

B. IELTS COACHING & TESTING:
- Official Authorized Center to accept registrations for British Council and IDP IELTS exams
- Experienced, British Council-trained faculties providing personalized input
- Tailored coaching with comprehensive preparatory library: study CDs, brochures, video tapes, and mock tests
- Dedicated individual attention to boost band scores across Listening, Reading, Writing, and Speaking

C. WORK VISA SERVICES:
- Labor Market Impact Assessment (LMIA)
- Employer-Specific Work Permits
- Work Permit Renewals and Extensions
- Post Graduate Work Permit (PGWP) (applications submitted inside or outside Canada)
- Open Work Permits under Public Policies
- Bridging Open Work Permits (BOWP)
- Off-Campus Work Permits (including Co-Op Work Permits)
- Spousal Open Work Permits (SOWP)
- Visitor Visa conversion to Work Permit
- International Experience Canada (IEC)
- Legal Status Restoration

D. IMMIGRATION & PERMANENT RESIDENCY (PR) SERVICES:
- Express Entry (Federal Skilled Worker, Canadian Experience Class, Federal Skilled Trades)
- Family Sponsorship (Spouse, dependent children, parents)
- Ontario Immigrant Nominee Program (OINP)
- Provincial Nominee Programs (PNP) across Canadian provinces
- Rural Community Immigration Pilot (RCIP)
- Atlantic Immigration Pilot Program (AIPP)
- Agri-Food Pilot Program
- PR Card Renewal applications
- Canadian Citizenship applications
- Skilled Migration through CSIC (ICCRC) members

E. VISIT & TEMPORARY RESIDENT VISAS (TRV):
- Temporary Resident Visa (TRV)
- Visitor / Tourist Visas (Single Entry and Multiple Entry)
- Visitor Record Extensions
- Super Visa (dedicated multi-entry long-term visas for Parents and Grandparents)
- Travel & Super Visa Medical Insurance

F. VISA INADMISSIBILITY & LEGAL REMEDIES:
- Temporary Resident Permit (TRP)
- Procedural Fairness Letters (PFL) drafting and official legal response
- Addressing Allegations of Misrepresentation
- Humanitarian and Compassionate (H&C) Considerations for Permanent Residency
- Medical Inadmissibility remedies
- Residency Obligation appeals and compliance
- ATIP Notes (Access to Information and Privacy / GCMS Notes analysis)
- Amendment of Temporary Resident Documents

4. COUNTRY-SPECIFIC VISA SPECIALIZATIONS:

* CANADA:
  - Student Visas under SPP & General Category
  - Dependent Visas (Spouse & Child: Student Dependent, PR Dependent & Citizen Dependent)
  - Visitor & Business Visas (Single and Multiple Entry)
  - Skilled Migration & Provincial Nominee Programs (through licensed CSIC members)
  - PGWP, Spousal Open Work Permits, Super Visa, and Express Entry

* AUSTRALIA:
  - Student Visa (Subclass 500)
  - Dependent Visa (Spouse and Child): Student Dependent, PR Dependent, Citizen Dependent
  - Visitor Visa (Subclass 600) & Business Visas (Single and Multiple Entry)
  - Work Permits & Skilled Migration (Subclass 189, 190, 491)

* UNITED KINGDOM (UK):
  - Student Visa (Tier IV / Student Route)
  - Student Visitor Visa
  - Dependent Visas (Student Dependent, PR Dependent & Citizen Dependent)
  - Visitor Visa & Business Visa (Single and Multiple Entry)
  - Skilled Worker Work Permits (Tier 1 / Skilled Worker)

* UNITED STATES OF AMERICA (USA):
  - Student Visas (F1 & M1 categories)
  - Dependent Visas (F2 & M2 for Spouse and Children)
  - Visitor & Business Visas (B1/B2 Single and Multiple Entry)
  - Exchange Visitor Work Permits (J1 visa)

* NEW ZEALAND:
  - Student Visa
  - Work Permit for Spouse of PR & Citizen Dependent
  - Visitor Visa for Student Dependent
  - Business Visa (Single and Multiple Entry)

* SINGAPORE:
  - Student Visa
  - Visitor Visa & Business Visa (Single and Multiple Entry)
  - Work Permits (E-Pass & S-Pass)
  - Singapore Landed PR

* MALAYSIA & IRELAND:
  - Comprehensive University Admissions and Student Visa Processing

5. LEAD CAPTURE & WHATSAPP INTEGRATION:
- Website visitors can submit details via "Request a call back".
- WhatsApp Hotline (+91 9879361728) is actively used for rapid consultation.
- Visitors are always encouraged to share their phone number, email, and preferred country/course in the chat.
================================================================================
"""


def html_to_clean_text(html_content: str) -> str:
    """Strips scripts, styles, and tags while preserving all readable content."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = html.unescape(text)
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


async def fetch_url(client: httpx.AsyncClient, url: str, timeout: float = 5.0) -> Optional[str]:
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


async def live_search_website(user_query: str) -> str:
    """
    Real-time dynamic scraping:
    When a user asks a question, this function performs an on-the-fly live fetch
    of https://www.preciousedu.in/ to extract exact matching text, paragraphs,
    contact info, or links in real-time.
    """
    if not user_query or len(user_query.strip()) < 3:
        return ""

    query_tokens = [w.lower() for w in re.findall(r"\w+", user_query) if len(w) > 3]
    if not query_tokens:
        query_tokens = [w.lower() for w in re.findall(r"\w+", user_query)]

    try:
        async with httpx.AsyncClient(timeout=4.0, verify=False) as client:
            html_text = await fetch_url(client, TARGET_SITE)
            if not html_text:
                return ""

            soup = BeautifulSoup(html_text, "html.parser")
            for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
                tag.decompose()

            # Find matching sections or paragraphs
            matching_blocks = []
            for element in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "div", "footer"]):
                elem_text = element.get_text(separator=" ", strip=True)
                if not elem_text or len(elem_text) < 15:
                    continue
                elem_lower = elem_text.lower()
                # Check for token match
                if any(token in elem_lower for token in query_tokens):
                    clean_block = re.sub(r"\s+", " ", elem_text).strip()
                    if clean_block not in matching_blocks:
                        matching_blocks.append(clean_block)
                if len(matching_blocks) >= 6:
                    break

            if matching_blocks:
                return (
                    f"=== REAL-TIME LIVE SITE SCRAPING (ACCESSED JUST NOW) ===\n"
                    f"User Query Focus: {user_query}\n"
                    + "\n- ".join(matching_blocks)
                    + "\n========================================================"
                )
    except Exception as e:
        logger.debug(f"Real-time site lookup failed: {e}")

    return ""


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


async def get_site_context(user_query: str = "") -> str:
    """
    Returns complete website knowledge base context.
    Combines the core encyclopedia with real-time live search tailored to the user's question.
    """
    base_context = read_cache()

    if not base_context:
        base_url = TARGET_SITE.rstrip("/")
        pages_to_try = [
            TARGET_SITE,
            f"{base_url}/terms-conditions.html",
            f"{base_url}/privacy-policy.html",
        ]

        scraped_content = ""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                tasks = [fetch_url(client, url) for url in pages_to_try]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for url, res in zip(pages_to_try, results):
                    if isinstance(res, str) and res.strip():
                        clean = html_to_clean_text(res)
                        if clean:
                            scraped_content += f"\n\n--- LIVE PAGE: {url} ---\n{clean}"
        except Exception as e:
            logger.warning(f"Live scrape error: {e}")

        base_context = f"{FULL_WEBSITE_KNOWLEDGE_BASE}\n\n=== LIVE SITE CONTENT ===\n{scraped_content.strip()}"
        base_context = base_context[:18000]
        write_cache(base_context)

    # If the user asked a specific query, perform on-the-fly real-time scrape
    if user_query:
        live_realtime_matches = await live_search_website(user_query)
        if live_realtime_matches:
            return f"{live_realtime_matches}\n\n{base_context}"

    return base_context
