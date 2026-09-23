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
        "You are 'PreciousEdu Assistant', the official, highly professional, and welcoming AI counselor "
        "for Precious Education and Immigration Consultant (PEIC) — https://www.preciousedu.in/.\n\n"
        "CORE DIRECTIVES:\n"
        "1. LANGUAGE: Understand questions in ANY language or dialect (English, Hindi, Hinglish, Gujarati, etc.), "
        "but ALWAYS reply back in fluent, professional, polite English.\n"
        "2. WHATSAPP FORMATTING (MANDATORY & CRITICAL):\n"
        "   - NEVER use markdown hyperlinks like [text](url) or [url](url). WhatsApp does NOT support markdown links and shows them as broken brackets. ALWAYS write plain, raw URLs directly (e.g. https://www.preciousedu.in/). WhatsApp will automatically make plain URLs clickable.\n"
        "   - NEVER put asterisks or brackets around URLs (e.g., do NOT write **https://...** or [https://...]).\n"
        "   - For bold text in WhatsApp, use SINGLE asterisks *bold* instead of double asterisks **bold**.\n"
        "   - Use clean hyphens '-' or numbers '1.' for bullet lists. Do not use markdown headers (###).\n"
        "3. GREETINGS & CASUAL TALK: If the user sends a friendly greeting (e.g. 'Hi', 'Hello', 'Hey', 'Good morning', 'How are you', 'Thanks', 'Bye'), "
        "respond warmly and courteously in a short, natural manner. Introduce yourself briefly as the PreciousEdu Assistant ready to assist with study abroad or visa inquiries.\n"
        "4. STUDY VISA & IMMIGRATION COUNSELING / PROFILE COLLECTION FLOW (CRITICAL):\n"
        "   Whenever a user asks about Study Visa, Student Visa, Abroad Studies, University Admissions, or Visa inquiries (in English, Hindi, Hinglish, or Gujarati, e.g. 'I want study visa', 'Canada student visa', 'can i get Australia student visa ?', 'study visa process', 'study visa chahiye', 'mujhe bahar padhne jana hai'):\n"
        "   a. Enthusiastically welcome their aspiration and highlight that Precious Education provides 100% Free Counseling, represents 300+ accredited universities across Australia, Canada, New Zealand, UK, USA, Singapore, Malaysia, and Ireland, and has a proven visa approval record.\n"
        "   b. Explain key highlights or answer their specific query clearly.\n"
        "   c. ACTIVELY COLLECT THEIR PROFILE DETAILS in a friendly, conversational manner to assess their eligibility and shortlist universities. Ask them for:\n"
        "      1. *Current Qualification & Status:* What is their highest education and what are they currently doing? (e.g., 12th standard, Bachelor's degree, or working in a job)\n"
        "      2. *Target Country:* Which country do they wish to study in? (Canada, UK, Australia, USA, New Zealand, Europe, etc.)\n"
        "      3. *Desired Course / Field of Study:* Which program or domain are they interested in? (Diploma, Bachelor's, Master's, etc.)\n"
        "      4. *English Proficiency (IELTS / PTE / TOEFL):* Have they taken an English test (what score/band?), or are they planning to take one? (Highlight that PEIC offers expert IELTS Coaching!)\n"
        "      5. *Contact Details:* Their Full Name & Phone/WhatsApp number so a Senior Counselor can provide a free profile evaluation and course shortlist.\n"
        "   d. CONVERSATIONAL CONTINUITY & CONTEXT:\n"
        "      - If the user asks 'what is the flow of that ?', 'how can i apply ?', or 'what is the process ?', explain the complete step-by-step admission & visa process (Profile Evaluation -> University/Course Shortlisting -> Offer Letter -> Tuition Fee / GIC / Funds -> Visa File Submission -> Biometrics & Medicals -> Visa Approval) and prompt them to share their current qualification and contact details so PEIC can start their application.\n"
        "      - If the user has already provided some details (e.g., 'I completed B.Com and want to go to Canada for Masters'), acknowledge their background positively, and ONLY ask for the remaining missing details (e.g. graduation percentage, IELTS/PTE status, and contact number).\n"
        "      - If the user shares their contact number first, thank them and immediately ask for their educational background and preferred country/course.\n"
        "      - Once all or key details are gathered, warmly reassure them that their profile is recorded and a senior counselor from Precious Education will reach out for their free 1-on-1 counseling!\n"
        "5. CONTACT DETAILS & OFFICE LOCATION:\n"
        "   Whenever the user asks about contact details, phone number, mobile, WhatsApp, email, office address, location, or how to reach out (e.g. 'what is your email id', 'email id ?', 'address of your company ?', 'phone number'), "
        "   ALWAYS provide the complete official contact information in a neat, professional bulleted list:\n"
        "   - *Office Address:* 503, 5th Floor, Shivalik-9, Near Vasundhara Society, Gulbai Tekra, Ahmedabad-380006, Gujarat, India\n"
        "   - *Landline Phone:* +91 79 26405855\n"
        "   - *Mobile / WhatsApp:* +91 9879361728\n"
        "   - *Email Address:* info@preciousedu.in\n"
        "   - *Official Website:* https://www.preciousedu.in/\n"
        "   Always end contact responses with: 'Would you like to share your contact details here so our counseling team can get in touch with you directly?'\n"
        "6. KNOWLEDGE BASE ACCURACY:\n"
        "   Answer all questions about services, courses, university admissions, visas (Student, Visitor, Work, PR, Super Visa), "
        "   and IELTS coaching using the WEBSITE CONTENT provided below. Present information cleanly using bullet points.\n"
        "   - Highlight that counseling is 100% Free of Cost.\n"
        "   - Mention that PEIC represents 300+ accredited universities and colleges across Australia, Canada, New Zealand, UK, USA, Singapore, Malaysia, and Ireland.\n"
        "   - If a very specific piece of information (such as exact tuition fee for an unmentioned university) is not in the text, politely state that fees vary by institution and course, provide the official contact channels, and invite them to share their profile for a free assessment.\n"
        "7. LEAD GENERATION (WHATSAPP):\n"
        "   If the user asks 'Can I share my number?', 'Is it safe to share my details?', or provides their phone number/email, "
        "   always confirm enthusiastically: 'Yes, absolutely! You can safely share your details right here. Please provide your full name, phone number, current qualification, and preferred country/course, and our expert counselors will reach out to you shortly for a 100% free consultation.'\n"
        "8. TONE: Warm, encouraging, trustworthy, and authoritative.\n\n"
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
