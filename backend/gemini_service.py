import logging
from typing import Any, Dict, List
import httpx

from config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger("gemini_service")


def format_whatsapp_text(text: str) -> str:
    """
    Sanitizes AI response to follow WhatsApp formatting standards:
    - Removes markdown links [text](url) and outputs clean URLs (which WhatsApp turns into clickable links).
    - Removes accidental brackets and asterisks around URLs (e.g. **https://...** -> https://...).
    - Converts markdown bold **text** to WhatsApp single-asterisk *text*.
    - Converts markdown headings (### Header) to bold lines (*Header*).
    - Ensures clean bullet points using '- ' instead of '* ' to avoid breaking WhatsApp bold syntax.
    """
    if not text:
        return ""

    import re

    # 1. Convert markdown links: [label](url)
    def replace_markdown_link(match):
        label = match.group(1).strip()
        url = match.group(2).strip()
        if label.lower() == url.lower() or label.startswith("http://") or label.startswith("https://") or label.startswith("www."):
            return url
        return f"{label}: {url}"

    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', replace_markdown_link, text)

    # 2. Clean URLs wrapped in asterisks e.g. **https://...** or *https://...*
    text = re.sub(r'\*{1,3}(https?://[^\s\*]+)\*{1,3}', r'\1', text)

    # 3. Clean stray square brackets around URLs e.g. [https://...]
    text = re.sub(r'\[(https?://[^\s\]]+)\]', r'\1', text)

    # 4. Convert markdown headings (### Heading) to WhatsApp bold (*Heading*)
    text = re.sub(r'^[ \t]*#{1,6}[ \t]+([^\n]+)', r'*\1*', text, flags=re.MULTILINE)

    # 5. Clean bullet points (*, •, ·, -) to clean '- ' for WhatsApp readability
    text = re.sub(r'^[ \t]*[\*·•\-][ \t]+', r'- ', text, flags=re.MULTILINE)
    text = re.sub(r'(?:^|\n)[ \t]*·[ \t]*', r'\n- ', text)

    # 6. Convert double asterisks **text** to single asterisks *text* (WhatsApp bold)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)

    # 7. Clean up triple asterisks if any remain
    text = re.sub(r'\*\*\*', r'*', text)

    # 8. Clean redundant blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def build_system_instruction(site_context: str) -> str:
    return (
        "You are 'PreciousEdu Assistant', the official AI counselor for Precious Education and Immigration Consultant (PEIC) — https://www.preciousedu.in/.\n\n"
        "CRITICAL INSTRUCTION - MINIMAL & CONCISE RESPONSES (MANDATORY):\n"
        "- Users read your messages on WhatsApp and mobile screens. Keep all responses SHORT, CRISP, and MINIMAL (typically 2 to 4 sentences or a compact 2-3 item list, under 60-80 words).\n"
        "- NEVER output long lectures, overwhelming paragraphs, or massive questionnaires.\n"
        "- Do NOT repeat marketing slogans or list all 8 countries/universities repeatedly.\n"
        "- Ask only 1 or 2 quick questions at a time to keep the conversation flowing naturally.\n\n"
        "CORE DIRECTIVES:\n"
        "1. LANGUAGE: Understand questions in any language (English, Hindi, Hinglish, Gujarati), but ALWAYS reply in fluent, polite, clear English.\n"
        "2. WHATSAPP FORMATTING:\n"
        "   - NEVER use markdown hyperlinks like [text](url). Use raw plain URLs (e.g. https://www.preciousedu.in/). WhatsApp automatically makes them clickable.\n"
        "   - Never wrap URLs in brackets or asterisks.\n"
        "   - For bold text, use SINGLE asterisks: *bold*.\n"
        "   - Use clean hyphens '-' for lists. Do not use markdown headers (###).\n"
        "3. GREETINGS & CASUAL TALK:\n"
        "   - Keep greetings to 1-2 friendly sentences max: e.g. 'Hello! Welcome to Precious Education. How can I assist you with your study abroad or visa goals today?'\n"
        "4. STUDY VISA & ADMISSIONS INQUIRIES:\n"
        "   - Positively acknowledge their country or course aspiration in 1 short sentence.\n"
        "   - Mention that PEIC provides 100% Free Counseling for top universities worldwide.\n"
        "   - Ask only 1 or 2 essential profile questions (e.g. their current qualification, IELTS/PTE status, or contact number) to guide them further.\n"
        "   - If they ask for the process/flow, provide a super-concise 3-4 step summary, then invite them to share their qualification or phone number for free guidance.\n"
        "   - If details were already shared, acknowledge them and only ask what is still missing.\n"
        "5. CONTACT DETAILS & LOCATION:\n"
        "   - When asked for contact details or address, provide this compact list:\n"
        "     - *Office:* 503, Shivalik-9, Gulbai Tekra, Ahmedabad-380006\n"
        "     - *Phone / WhatsApp:* +91 9879361728 / +91 79 26405855\n"
        "     - *Email:* info@preciousedu.in\n"
        "     - *Website:* https://www.preciousedu.in/\n"
        "6. ACCURACY:\n"
        "   - Base all answers on the official knowledge base below. Keep advice direct and actionable.\n"
        "7. LEAD COLLECTION:\n"
        "   - If the user offers their phone number or asks if they can share details, warmly confirm in 1-2 lines and ask for their qualification and target country.\n\n"
        "=== KNOWLEDGE BASE ===\n"
        f"{site_context}\n"
        "=== END OF KNOWLEDGE BASE ==="
    )


async def ask_gemini(
    user_message: str,
    site_context: str,
    history: List[Dict[str, str]],
    model_override: str = None
) -> str:
    """
    Sends chat request to Google Gemini API with automatic API key rotation.
    If a key exhausts quota, hits rate limits, or receives authentication errors,
    it automatically falls back to the next key in the pool.
    """
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys configured. Please add keys to .env.")

    model = model_override or GEMINI_MODEL
    system_instruction = build_system_instruction(site_context)

    # Convert conversation history to Gemini contents structure
    contents = []
    for h in history:
        role = "model" if h.get("role") in ("bot", "model") else "user"
        text = h.get("text", "")
        if text:
            contents.append({
                "role": role,
                "parts": [{"text": text}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 300,
        },
    }

    last_error = ""

    # Use 9.0s timeout per key so any stall or glitch fails over quickly to the next key
    async with httpx.AsyncClient(timeout=9.0, verify=False) as client:
        for idx, api_key in enumerate(GEMINI_API_KEYS):
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                http_code = response.status_code

                try:
                    data = response.json()
                except Exception:
                    data = {}

                # Successful candidate response
                if response.is_success and "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    parts = candidate.get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_reply = parts[0]["text"].strip()
                        formatted_reply = format_whatsapp_text(raw_reply)
                        logger.info(f"Successfully generated response using Gemini API Key #{idx + 1}")
                        return formatted_reply

                # Handle error responses
                err_msg = ""
                if "error" in data and isinstance(data["error"], dict):
                    err_msg = data["error"].get("message", "")
                elif not response.is_success:
                    err_msg = f"HTTP {http_code}: {response.text}"

                last_error = err_msg or f"HTTP {http_code} unknown error"

                # Sanitize error to prevent key leakage
                for k in GEMINI_API_KEYS:
                    if k in last_error:
                        last_error = last_error.replace(k, "[REDACTED_KEY]")

                # Check if it's a quota, rate limit, auth, or model deprecation/not-found issue
                is_quota_or_auth = (
                    http_code in (429, 403, 400, 404)
                    or any(term in last_error.lower() for term in [
                        "quota", "rate", "limit", "api key", "permission", "resource_exhausted", "not found"
                    ])
                )

                if is_quota_or_auth:
                    logger.warning(
                        f"Gemini API key #{idx + 1} failed (HTTP {http_code}: {last_error}). "
                        f"Rotating to next available key..."
                    )
                    continue

                # For unrecoverable payload/syntax errors, raise immediately
                raise RuntimeError(f"Gemini API error: {last_error}")

            except httpx.RequestError as net_err:
                last_error = f"Network connection error: {net_err}"
                logger.warning(f"Key #{idx + 1} network issue: {net_err}. Trying next key...")
                continue

    raise RuntimeError(
        f"All configured Gemini API keys failed or exhausted their quota. Last error: {last_error}"
    )
