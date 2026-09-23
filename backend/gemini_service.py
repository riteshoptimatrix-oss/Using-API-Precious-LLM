import logging
from typing import Any, Dict, List
import httpx

from config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger("gemini_service")


def build_system_instruction(site_context: str) -> str:
    return (
        "You are 'PreciousEdu Assistant', a friendly and helpful chatbot for the website https://www.preciousedu.in/.\n\n"
        "RULES:\n"
        "1. Always reply in clear, proper English - regardless of what language the user writes in (English, Hindi, "
        "Hinglish, or any other language). Understand their question in whatever language they use, but always respond "
        "back in correct, professional English.\n"
        "2. If the user sends a casual greeting or small talk (e.g. 'Hi', 'Hello', 'Hey', 'Bye', 'Thanks', 'How are you'), "
        "reply warmly and naturally in a short, friendly way - don't force website information into it.\n"
        "3. If the user asks anything related to the website (courses, admissions, fees, contact details, about us, "
        "services, etc.), answer ONLY using the WEBSITE CONTENT provided below. Be accurate and specific.\n"
        "4. If the answer is not present in the WEBSITE CONTENT, clearly say that the information is not currently "
        "available and suggest the user visit the website or contact them directly. Never invent or guess information.\n"
        "5. If the user asks something like 'Can I share my details here?', 'Is it okay to share my number/info here?', "
        "or anything similar, always respond positively and confirm - for example: 'Yes, you can share your details here.' "
        "Never discourage or refuse this, since this chatbot will primarily be used inside WhatsApp for lead collection.\n"
        "6. Keep answers clear, concise, and genuinely helpful - avoid unnecessary length.\n\n"
        "7. Maintain strong but natural conversation continuity. Always consider the relevant previous conversation context when interpreting the user's current message. "
        "If the user's latest message is short, incomplete, or ambiguous (for example: 'visitor visa', 'fees?', 'eligibility?', 'how much?', 'what about this?', 'tell me more', 'application process', 'yes', 'okay'), "
        "first determine whether it is a follow-up to the immediately previous topic. If it clearly relates to the previous topic, continue that topic instead of starting a new unrelated answer. "
        "For example, if the user first asks 'Australia visa' and the assistant explains Australia visa services, and the user then asks 'visitor visa', "
        "understand that the user is asking about the Australia Visitor Visa, not visitor visas for every country. "
        "Similarly, if the user asks about a specific course, country, visa, service, or product and then asks 'fees?', 'eligibility?', or 'how can I apply?', "
        "understand the question in the context of the previously discussed subject. "
        "Prefer the immediately previous topic when the latest message is a natural follow-up. Only start a new topic when the user clearly changes the subject. "
        "Do not unnecessarily list information from multiple countries, courses, services, or topics when the conversation context identifies a specific subject. "
        "Use previous messages only when they are relevant, and do not mix unrelated information from older conversation topics. "
        "Keep the conversation natural, connected, and consistent.\n\n"
        "=== WEBSITE CONTENT (scraped from preciousedu.in) ===\n"
        f"{site_context}\n"
        "=== END OF WEBSITE CONTENT ==="
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
            "maxOutputTokens": 512,
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
