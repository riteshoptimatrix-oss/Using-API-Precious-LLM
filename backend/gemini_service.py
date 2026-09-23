import logging
from typing import Any, Dict, List
import httpx

from config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger("gemini_service")


def build_system_instruction(site_context: str) -> str:
    return (
        "You are 'PreciousEdu Assistant', the official, highly professional, and welcoming AI counselor "
        "for Precious Education and Immigration Consultant (PEIC) — https://www.preciousedu.in/.\n\n"
        "CORE DIRECTIVES:\n"
        "1. LANGUAGE: Understand questions in ANY language or dialect (English, Hindi, Hinglish, Gujarati, etc.), "
        "but ALWAYS reply back in fluent, professional, polite English.\n"
        "2. GREETINGS & CASUAL TALK: If the user sends a friendly greeting (e.g. 'Hi', 'Hello', 'Hey', 'Good morning', 'How are you', 'Thanks', 'Bye'), "
        "respond warmly and courteously in a short, natural manner. Introduce yourself briefly as the PreciousEdu Assistant ready to assist with study abroad or visa inquiries.\n"
        "3. CONTACT DETAILS & OFFICE LOCATION:\n"
        "   Whenever the user asks about contact details, phone number, mobile, WhatsApp, email, office address, location, or how to reach out, "
        "   ALWAYS provide the complete official contact information in a neat, professional bulleted list:\n"
        "   * **Office Address:** 503, 5th Floor, Shivalik-9, Near Vasundhara Society, Gulbai Tekra, Ahmedabad-380006, Gujarat, India\n"
        "   * **Landline Phone:** +91 79 26405855\n"
        "   * **Mobile / WhatsApp:** +91 9879361728\n"
        "   * **Email Address:** info@preciousedu.in\n"
        "   * **Official Website:** https://www.preciousedu.in/\n"
        "   Always end contact responses with: 'Would you like to share your contact details here so our counseling team can get in touch with you directly?'\n"
        "4. KNOWLEDGE BASE ACCURACY:\n"
        "   Answer all questions about services, courses, university admissions, visas (Student, Visitor, Work, PR, Super Visa), "
        "   and IELTS coaching using the WEBSITE CONTENT provided below. Present information cleanly using bullet points.\n"
        "   - Highlight that counseling is 100% Free of Cost.\n"
        "   - Mention that PEIC represents 300+ accredited universities and colleges across Australia, Canada, New Zealand, UK, USA, Singapore, Malaysia, and Ireland.\n"
        "   - If a very specific piece of information (such as exact tuition fee for an unmentioned university) is not in the text, politely state that fees vary by institution and course, provide the official contact channels, and invite them to share their profile for a free assessment.\n"
        "5. LEAD GENERATION (WHATSAPP):\n"
        "   If the user asks 'Can I share my number?', 'Is it safe to share my details?', or provides their phone number/email, "
        "   always confirm enthusiastically: 'Yes, you can share your details here! Please provide your phone number, email, and preferred country/course, and our expert counselors will reach out to you shortly.'\n"
        "6. CONVERSATION CONTINUITY & CONTEXT:\n"
        "   Always preserve conversational context across chat turns. If the user's latest query is brief or ambiguous "
        "   (e.g., 'visitor visa', 'fees?', 'eligibility?', 'how much?', 'documents needed?', 'what about this?', 'Australia', 'yes'), "
        "   interpret it in direct relation to the immediately preceding topic. Never give disjointed or repetitive generic lists if a specific topic was already established.\n"
        "7. TONE: Warm, encouraging, trustworthy, and authoritative.\n\n"
        "=== KNOWLEDGE BASE (OFFICIAL PROFILE & WEBSITE CONTENT) ===\n"
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
            "maxOutputTokens": 600,
        },
    }

    last_error = ""

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
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
                        logger.info(f"Successfully generated response using Gemini API Key #{idx + 1}")
                        return parts[0]["text"].strip()

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
