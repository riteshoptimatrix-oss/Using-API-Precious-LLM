import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

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
from gemini_service import ask_gemini
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

# --- Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
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


# --- Request & Response Models ---
class ChatHistoryItem(BaseModel):
    role: str = Field(description="Role: 'user' or 'bot'/'model'")
    text: str = Field(description="Turn message text")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Current user message")
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list, description="Past chat conversation turns")
    session_id: Optional[str] = Field(default="", description="Unique session identifier")


class ChatResponse(BaseModel):
    reply: str
    session_id: str


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
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint. Accepts the user's message and past history,
    injects cached website context, and queries Gemini with automated key rotation.
    """
    user_message = request.message.strip()
    session_id = request.session_id.strip() if request.session_id else f"sess_{uuid.uuid4().hex[:16]}"

    if not user_message:
        return ChatResponse(
            reply="Please type a message so I can help you.",
            session_id=session_id
        )

    # Security check: message length limit
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return ChatResponse(
            reply=f"Your message is too long (maximum {MAX_MESSAGE_LENGTH} characters allowed). Please shorten your question.",
            session_id=session_id
        )

    if not GEMINI_API_KEYS:
        return ChatResponse(
            reply="Server configuration error: No Gemini API keys are configured on the backend.",
            session_id=session_id
        )

    # Fast pattern match for lead collection
    user_msg_lower = user_message.lower()
    for pattern in SHARE_DETAILS_PATTERNS:
        if pattern in user_msg_lower:
            return ChatResponse(
                reply="Yes, you can share your details here.",
                session_id=session_id
            )

    try:
        # Retrieve scraped & cached website content + real-time on-demand live lookup
        site_context = await get_site_context(user_message)

        # Enforce history turn limit to prevent token budget exploitation
        trimmed_history = request.history[-MAX_HISTORY_TURNS:] if request.history else []
        history_dicts = [{"role": item.role, "text": item.text} for item in trimmed_history]

        # Call Gemini with fallback key rotation
        reply = await ask_gemini(
            user_message=user_message,
            site_context=site_context,
            history=history_dicts
        )

        return ChatResponse(reply=reply, session_id=session_id)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        # Scrub any secrets from error message before returning to user
        safe_err = str(e)
        for k in GEMINI_API_KEYS:
            if k in safe_err:
                safe_err = safe_err.replace(k, "[REDACTED_KEY]")
        return ChatResponse(
            reply=f"Sorry, something went wrong while generating a response. ({safe_err})",
            session_id=session_id
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
