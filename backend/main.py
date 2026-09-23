import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import (
    ALLOWED_ORIGINS,
    GEMINI_API_KEYS,
    GEMINI_MODEL,
    HOST,
    MAX_HISTORY_TURNS,
    MAX_MESSAGE_LENGTH,
    PORT,
    TARGET_SITE,
    mask_key,
)
from gemini_service import ask_gemini, format_whatsapp_text
from scraper import get_site_context

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("Starting PreciousEdu AI Chatbot Backend")
    logger.info(f"Loaded {len(GEMINI_API_KEYS)} Gemini API Key(s) for automatic rotation:")
    for idx, key in enumerate(GEMINI_API_KEYS, start=1):
        logger.info(f"  - Key #{idx} [GEMINI_API_{idx}]: {mask_key(key)}")
    logger.info(f"Configured Model: {GEMINI_MODEL}")
    logger.info(f"Target Scrape Site: {TARGET_SITE}")
    logger.info(f"Allowed CORS Origins: {ALLOWED_ORIGINS}")
    logger.info("==================================================")
    yield
    logger.info("Shutting down PreciousEdu Chatbot Backend")


app = FastAPI(
    title="PreciousEdu AI Chatbot API",
    description="Production-grade FastAPI Backend for PreciousEdu Chatbot with multi-key Gemini API rotation.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Security & Flexible Webhook Middleware ---
@app.middleware("http")
async def security_and_webhook_middleware(request: Request, call_next):
    # If WABA / Flow Builder sends POST to /predict, /api/predict, or /api/chat without explicit application/json header, auto-adapt it
    if request.method == "POST" and any(request.url.path.rstrip("/").endswith(p) for p in ["/predict", "/api/chat", "/api/predict"]):
        ct = request.headers.get("content-type", "")
        if not ct or "json" not in ct.lower():
            # Update scope headers so FastAPI/Starlette parses body as JSON
            headers = list(request.scope.get("headers", []))
            headers.append((b"content-type", b"application/json"))
            request.scope["headers"] = headers

    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# --- CORS Middleware ---
is_wildcard = "*" in ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else ALLOWED_ORIGINS,
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Models (WABA & Web Compatible) ---
class ChatHistoryItem(BaseModel):
    role: str = Field(description="Role: 'user' or 'bot'/'model'")
    text: str = Field(description="Turn message text")


class ChatRequest(BaseModel):
    message: Optional[str] = Field(default="", description="Current user message")
    query: Optional[str] = Field(default="", description="Alternative alias for message")
    text: Optional[str] = Field(default="", description="Alternative alias for message")
    body: Optional[str] = Field(default="", description="Alternative alias for message")
    keywords: Optional[str] = Field(default="", description="Alternative alias for message")
    keyword: Optional[str] = Field(default="", description="Alternative alias for message")
    question: Optional[str] = Field(default="", description="Alternative alias for message")
    prompt: Optional[str] = Field(default="", description="Alternative alias for message")
    content: Optional[str] = Field(default="", description="Alternative alias for message")
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list, description="Past chat conversation turns")
    session_id: Optional[str] = Field(default="", description="Unique session identifier or WhatsApp phone number")

    class Config:
        extra = "allow"


class ChatResponse(BaseModel):
    reply: str
    response: Optional[str] = None
    message: Optional[str] = None
    output: Optional[str] = None
    answer: Optional[str] = None
    text: Optional[str] = None
    data: Optional[str] = None
    session_id: str
    status: Optional[str] = "success"



# Server-side conversation memory for WhatsApp/WABA webhooks (keyed by phone number / session_id)
SESSION_MEMORY: Dict[str, List[Dict[str, str]]] = {}
SESSION_TIMESTAMP: Dict[str, float] = {}
SESSION_TTL_SECONDS = 86400  # 24 hours


def get_session_history(session_id: str, client_history: Optional[List[ChatHistoryItem]]) -> List[Dict[str, str]]:
    """
    Returns appropriate conversation history:
    - If client explicitly provides history (e.g. Web UI), use client history.
    - If client sends empty history (e.g. WhatsApp webhook), use server-side SESSION_MEMORY for this session_id.
    """
    if client_history and len(client_history) > 0:
        return [{"role": item.role, "text": item.text} for item in client_history[-MAX_HISTORY_TURNS:]]

    if not session_id:
        return []

    # Clean up stale sessions (> 24 hours) periodically
    now = time.time()
    if len(SESSION_MEMORY) > 500:
        stale_keys = [k for k, last_t in SESSION_TIMESTAMP.items() if (now - last_t) > SESSION_TTL_SECONDS]
        for k in stale_keys:
            SESSION_MEMORY.pop(k, None)
            SESSION_TIMESTAMP.pop(k, None)

    return list(SESSION_MEMORY.get(session_id, []))[-MAX_HISTORY_TURNS:]


def save_session_history(session_id: str, user_text: str, bot_text: str) -> None:
    """Records conversation turn in server memory so WhatsApp users experience full conversational continuity."""
    if not session_id:
        return
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []
    SESSION_MEMORY[session_id].append({"role": "user", "text": user_text})
    SESSION_MEMORY[session_id].append({"role": "bot", "text": bot_text})
    # Keep last 20 messages (10 conversation turns)
    SESSION_MEMORY[session_id] = SESSION_MEMORY[session_id][-20:]
    SESSION_TIMESTAMP[session_id] = time.time()


# WhatsApp lead inquiry shortcut patterns (matches original index.php logic)
SHARE_DETAILS_PATTERNS = [
    "can i share", "share my details", "share details here", "share my number",
    "share my info", "share my information", "is it safe to share", "can i give my details",
    "can i give my number", "can i send my details", "can i provide my details"
]


@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "service": "PreciousEdu Chatbot API",
        "model": GEMINI_MODEL,
        "api_keys_configured": len(GEMINI_API_KEYS),
        "target_site": TARGET_SITE
    }


@app.post("/api/chat", response_model=ChatResponse)
@app.post("/predict", response_model=ChatResponse)
@app.post("/api/predict", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, raw_req: Request):
    """
    Main chat endpoint. Compatible with both Web Frontend and WABA chatbot builders.
    Accepts message, query, or text, with fallback response keys (reply, response, output).
    """
    # 1. Read raw body and log it for transparent debugging
    raw_dict = {}
    try:
        body_bytes = await raw_req.body()
        if body_bytes:
            raw_dict = json.loads(body_bytes.decode("utf-8", errors="ignore"))
            logger.info(f"Incoming /predict payload: {json.dumps(raw_dict)}")
    except Exception as e:
        logger.warning(f"Could not parse raw request body: {e}")

    # 2. Extract potential user message from typed request or raw dictionary
    possible_values = [
        request.message, request.query, request.text, request.body,
        request.question, request.prompt, request.content,
        request.keywords, request.keyword,
        raw_dict.get("message"), raw_dict.get("query"), raw_dict.get("text"),
        raw_dict.get("body"), raw_dict.get("question"), raw_dict.get("prompt"),
        raw_dict.get("content"), raw_dict.get("keywords"), raw_dict.get("keyword"),
        raw_dict.get("input"), raw_dict.get("user_message")
    ]

    # Include any extra arbitrary fields parsed by Pydantic
    if hasattr(request, "__pydantic_extra__") and request.__pydantic_extra__:
        for extra_k, extra_v in request.__pydantic_extra__.items():
            if isinstance(extra_v, str):
                possible_values.append(extra_v)
            elif isinstance(extra_v, dict):
                for sub_v in extra_v.values():
                    if isinstance(sub_v, str):
                        possible_values.append(sub_v)

    # Check nested dicts (e.g. if start_node or start_nodeObject is passed)
    for k, v in raw_dict.items():
        if isinstance(v, dict):
            for sub_k in ["message", "text", "body", "keywords", "keyword", "query"]:
                if sub_k in v and v[sub_k]:
                    possible_values.append(v[sub_k])

    user_message = ""
    for val in possible_values:
        if val and isinstance(val, str):
            clean_val = val.strip()
            # Skip unresolved template tags like {{start_node...}}
            if clean_val and not (clean_val.startswith("{{") and clean_val.endswith("}}")):
                user_message = clean_val
                break

    # If the user only sent an unresolved template tag, log warning
    if not user_message:
        for val in possible_values:
            if val and isinstance(val, str) and val.strip().startswith("{{"):
                logger.warning(f"Unresolved template tag detected in request: {val}")

    # WABA session & phone identification: check all common WhatsApp builder parameter names
    possible_sessions = [
        request.session_id,
        raw_dict.get("session_id"),
        raw_dict.get("wa_id"),
        raw_dict.get("phone"),
        raw_dict.get("mobile"),
        raw_dict.get("sender"),
        raw_dict.get("from"),
        raw_dict.get("receiver_number"),
        raw_dict.get("phone_number"),
        raw_dict.get("contact"),
        raw_dict.get("user_id"),
    ]
    session_id = ""
    for s in possible_sessions:
        if s and isinstance(s, str):
            clean_s = s.strip()
            if clean_s and not (clean_s.startswith("{{") and clean_s.endswith("}}")):
                session_id = clean_s
                break
    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:16]}"

    if not user_message:
        logger.info(f"Empty user_message received. Returning prompt to type a message. Raw payload: {raw_dict}")
        text = "Please type a message so I can help you."
        return ChatResponse(reply=text, response=text, message=text, output=text, answer=text, text=text, data=text, session_id=session_id)

    # Security check: message length limit
    if len(user_message) > MAX_MESSAGE_LENGTH:
        text = f"Your message is too long (maximum {MAX_MESSAGE_LENGTH} characters allowed). Please shorten your question."
        return ChatResponse(reply=text, response=text, message=text, output=text, answer=text, text=text, data=text, session_id=session_id)

    if not GEMINI_API_KEYS:
        text = "Server configuration error: No Gemini API keys are configured on the backend."
        return ChatResponse(reply=text, response=text, message=text, output=text, answer=text, text=text, data=text, session_id=session_id, status="error")

    # Fast pattern match for lead collection
    user_msg_lower = user_message.lower()
    for pattern in SHARE_DETAILS_PATTERNS:
        if pattern in user_msg_lower:
            text = format_whatsapp_text(
                "Yes, absolutely! You can share your details right here.\n\n"
                "Please let us know:\n"
                "- *Name & Contact Number*\n"
                "- *Highest Qualification & Target Country*\n"
                "- *IELTS / PTE Score* (if taken)\n\n"
                "Our senior counselor will get in touch with you shortly for a 100% free profile evaluation!"
            )
            save_session_history(session_id, user_message, text)
            return ChatResponse(reply=text, response=text, message=text, output=text, answer=text, text=text, data=text, session_id=session_id)

    try:
        # Retrieve scraped & cached website content instantly without blocking network requests
        site_context = await get_site_context(user_message)

        # Retrieve conversation history (seamlessly supports WhatsApp webhooks using session_id)
        history_dicts = get_session_history(session_id, request.history)

        # Call Gemini with fallback key rotation
        reply = await ask_gemini(
            user_message=user_message,
            site_context=site_context,
            history=history_dicts
        )

        # Save conversation turn in server-side session memory for future turns
        save_session_history(session_id, user_message, reply)

        return ChatResponse(
            reply=reply,
            response=reply,
            message=reply,
            output=reply,
            answer=reply,
            text=reply,
            data=reply,
            session_id=session_id,
            status="success"
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        # Scrub any secrets from error message before returning to user
        safe_err = str(e)
        for k in GEMINI_API_KEYS:
            if k in safe_err:
                safe_err = safe_err.replace(k, "[REDACTED_KEY]")
        err_reply = f"Sorry, something went wrong while generating a response. ({safe_err})"
        return ChatResponse(
            reply=err_reply,
            response=err_reply,
            message=err_reply,
            output=err_reply,
            answer=err_reply,
            text=err_reply,
            data=err_reply,
            session_id=session_id,
            status="error"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
