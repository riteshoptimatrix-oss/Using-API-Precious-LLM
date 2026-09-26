import base64
import json
import logging
import re
from typing import Any, Dict, Optional
import httpx

try:
    from config import GEMINI_API_KEYS, GEMINI_MODEL
except ImportError:
    from backend.config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger("ocr_service")

# OCR Prompt instructed to output structured invoice/bill data
OCR_SYSTEM_PROMPT = """You are an expert financial document and invoice/bill OCR engine.
Analyze the provided document (bill, invoice, receipt, challan, purchase order, or statement) and extract all relevant information with maximum accuracy.

You MUST respond with valid JSON containing the following structure:
{
  "vendor_name": "Company, Store, Seller, or Vendor Name",
  "bill_number": "Invoice number, Bill number, Receipt number, or Tax Invoice #",
  "bill_date": "Date of issue (e.g. 2026-03-15 or DD/MM/YYYY)",
  "due_date": "Due date if specified, otherwise null",
  "currency": "INR / ₹ / USD / EUR / etc.",
  "subtotal": "Subtotal before tax as clean numeric string (e.g. 1200.00)",
  "tax_amount": "Total GST/VAT/Tax amount (e.g. 216.00)",
  "total_amount": "Final Grand Total amount payable (e.g. 1416.00)",
  "payment_status": "Paid / Unpaid / Pending / Overdue",
  "customer_name": "Client or Customer name (Billed To)",
  "items": [
    {
      "description": "Item, product, or service description",
      "quantity": "Quantity (e.g. 1, 2, 10 kg)",
      "unit_price": "Price per unit",
      "amount": "Total amount for this line item"
    }
  ],
  "raw_text": "Complete transcribed raw text extracted from the document",
  "summary": "Brief 1-line summary (e.g. 'Electricity bill from Torrent Power of Rs 1,416 dated 15-Mar-2026')"
}

IMPORTANT RULES:
1. Extract whatever is visible. If any field is not found or unclear, set it to "" or null (do not invent fake data).
2. Clean numeric values for total_amount, subtotal, and tax_amount (keep numbers and decimal points, strip currency symbols from these fields).
3. If multiple items exist, list them all in the 'items' array. If no item table is visible, include the main fee/charge as a single item.
4. Output valid JSON only. Do not add conversational text.
"""


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Cleans code blocks, backticks, and extracts pure JSON dict robustly."""
    if not raw_text:
        return {}

    text = raw_text.strip()

    # 1. Try finding ```json ... ``` code fence anywhere in text
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return _normalize_ocr_dict(parsed, raw_text)
        except Exception:
            pass

    # 2. Try direct json parse of entire text
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return _normalize_ocr_dict(parsed, raw_text)
    except Exception:
        pass

    # 3. Try finding the outer-most JSON object { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace + 1].strip()
        try:
            parsed = json.loads(json_candidate)
            if isinstance(parsed, dict):
                return _normalize_ocr_dict(parsed, raw_text)
        except Exception as e:
            logger.warning(f"Failed to parse outer brace JSON: {e}")

    # 4. Fallback structure if JSON is completely unparseable
    return {
        "vendor_name": "",
        "bill_number": "",
        "bill_date": "",
        "due_date": "",
        "currency": "INR",
        "subtotal": "",
        "tax_amount": "",
        "total_amount": "",
        "payment_status": "",
        "customer_name": "",
        "items": [],
        "raw_text": raw_text.strip(),
        "summary": "Document text extracted via OCR"
    }


def _normalize_ocr_dict(data: Dict[str, Any], original_raw: str) -> Dict[str, Any]:
    """Ensures consistent types and sensible defaults for all standard bill fields."""
    normalized = {
        "vendor_name": str(data.get("vendor_name") or "").strip(),
        "bill_number": str(data.get("bill_number") or "").strip(),
        "bill_date": str(data.get("bill_date") or "").strip(),
        "due_date": str(data.get("due_date") or "").strip(),
        "currency": str(data.get("currency") or "INR").strip(),
        "subtotal": str(data.get("subtotal") or "").strip(),
        "tax_amount": str(data.get("tax_amount") or "").strip(),
        "total_amount": str(data.get("total_amount") or "").strip(),
        "payment_status": str(data.get("payment_status") or "").strip(),
        "customer_name": str(data.get("customer_name") or "").strip(),
        "items": data.get("items") if isinstance(data.get("items"), list) else [],
        "raw_text": str(data.get("raw_text") or original_raw).strip(),
        "summary": str(data.get("summary") or "").strip()
    }
    # Clean null string literals e.g. "None", "null"
    for k in ["vendor_name", "bill_number", "bill_date", "due_date", "subtotal", "tax_amount", "total_amount", "customer_name"]:
        if normalized[k].lower() in ("none", "null"):
            normalized[k] = ""

    if not normalized["summary"]:
        parts = []
        if normalized["vendor_name"]:
            parts.append(f"Vendor: {normalized['vendor_name']}")
        if normalized["bill_number"]:
            parts.append(f"Bill #{normalized['bill_number']}")
        if normalized["total_amount"]:
            parts.append(f"Amount: {normalized['currency']} {normalized['total_amount']}")
        normalized["summary"] = " | ".join(parts) if parts else "Bill processed via OCR"

    return normalized


def detect_mime_type(filename: str, content_type: Optional[str] = None) -> str:
    """Infers the correct MIME type for Gemini multimodal inlineData."""
    if content_type and content_type != "application/octet-stream" and "/" in content_type:
        return content_type.lower()

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "gif": "image/gif",
        "pdf": "application/pdf"
    }
    return mime_map.get(ext, "image/jpeg")


async def extract_bill_ocr(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
    model_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs OCR and document extraction on bill/invoice using Google Gemini Vision API.
    Rotates automatically across configured GEMINI_API_KEYS if quota or rate limits are reached.
    """
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys configured in .env.")

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    mime_type = detect_mime_type(filename, content_type)
    b64_data = base64.b64encode(file_bytes).decode("utf-8")

    # Fast and reliable multimodal models (gemini-3.5-flash-lite is fastest and highly available)
    model = model_override or "gemini-3.5-flash-lite"
    fallback_models = [model, "gemini-3.6-flash", "gemini-flash-latest"]

    payload = {
        "system_instruction": {
            "parts": [{"text": OCR_SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Extract all invoice and bill details from this file '{filename}'. Format output as JSON."
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    last_error = ""

    # Timeout 25s per attempt for multimodal processing
    async with httpx.AsyncClient(timeout=25.0, verify=False) as client:
        for idx, api_key in enumerate(GEMINI_API_KEYS):
            for current_model in fallback_models:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"
                try:
                    logger.info(f"Attempting OCR on '{filename}' using Key #{idx + 1} with model '{current_model}'")
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

                    if response.is_success and "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        parts = candidate.get("content", {}).get("parts", [])
                        
                        # Gather all text parts (handling potential thought or multi-part output)
                        raw_reply = ""
                        for part in parts:
                            if "text" in part and part["text"]:
                                raw_reply += part["text"]

                        if raw_reply:
                            parsed_data = clean_json_response(raw_reply)
                            logger.info(f"OCR successfully completed for '{filename}' via Key #{idx + 1}")
                            return parsed_data

                    # If model not found (404), try next model
                    if http_code == 404:
                        logger.warning(f"Model '{current_model}' returned 404. Trying fallback model...")
                        continue

                    # Handle error message
                    err_msg = ""
                    if "error" in data and isinstance(data["error"], dict):
                        err_msg = data["error"].get("message", "")
                    elif not response.is_success:
                        err_msg = f"HTTP {http_code}: {response.text[:300]}"

                    last_error = err_msg or f"HTTP {http_code} error"
                    logger.warning(f"Key #{idx + 1} with '{current_model}' failed: {last_error}")

                    # Check for rate limit / quota / temporary capacity spikes
                    is_rate_limit = (
                        http_code in (429, 403, 503) or
                        any(term in last_error.lower() for term in [
                            "quota", "rate", "resource_exhausted", "limit", "high demand", "spikes", "overloaded"
                        ])
                    )
                    if is_rate_limit:
                        logger.warning(f"Quota/capacity limit on Key #{idx + 1}. Rotating to next candidate...")
                        continue  # Try next model or next key

                except (httpx.RequestError, httpx.TimeoutException) as net_err:
                    last_error = f"Network/Timeout error: {net_err}"
                    logger.warning(f"Key #{idx + 1} issue: {net_err}. Trying next key...")
                    break  # Try next key on timeout

    raise RuntimeError(f"OCR extraction failed for '{filename}'. Last error: {last_error}")
