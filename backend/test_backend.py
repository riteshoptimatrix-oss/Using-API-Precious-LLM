import asyncio
import sys
import httpx
from main import app
from gemini_service import format_whatsapp_text
from config import GEMINI_API_KEYS, GEMINI_MODEL


async def test_all():
    print("=== Testing FastAPI Backend Components ===")
    print(f"Total API Keys configured: {len(GEMINI_API_KEYS)}")
    print(f"Configured Model: {GEMINI_MODEL}")

    # 1. Test WhatsApp Formatter Unit Tests
    print("\n1. Testing format_whatsapp_text function...")
    raw_sample = "Explore our site at **[https://www.preciousedu.in/](https://www.preciousedu.in/)** today!"
    formatted = format_whatsapp_text(raw_sample)
    print(f"Original: {raw_sample}")
    print(f"Formatted: {formatted}")
    assert formatted == "Explore our site at https://www.preciousedu.in/ today!"
    assert "[" not in formatted and "]" not in formatted
    assert "**" not in formatted

    raw_bold_and_list = "* **Office Address:** Shivalik-9\n* **Website:** https://www.preciousedu.in/"
    formatted_bold = format_whatsapp_text(raw_bold_and_list)
    print(f"\nFormatted bold & list:\n{formatted_bold}")
    assert "- *Office Address:* Shivalik-9" in formatted_bold

    # Use httpx.AsyncClient with ASGITransport to test FastAPI directly
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 2. Health check test
        print("\n2. Testing GET /api/health...")
        health_res = await client.get("/api/health")
        print(f"Status: {health_res.status_code}")
        print(f"Response: {health_res.json()}")
        assert health_res.status_code == 200
        assert health_res.json().get("status") == "healthy"

        # 3. WhatsApp lead generation rule test
        print("\n3. Testing quick lead pattern: 'can I share my details here?'...")
        lead_res = await client.post("/api/chat", json={"message": "Can I share my details here?"})
        print(f"Status: {lead_res.status_code}")
        lead_reply = lead_res.json().get("reply", "")
        print(f"Response:\n{lead_reply}")
        assert lead_res.status_code == 200
        assert "share your details" in lead_reply.lower()
        assert "qualification" in lead_reply.lower()
        assert "country" in lead_reply.lower()

        # 4. Test empty message & overflow
        print("\n4. Testing empty message handling...")
        empty_res = await client.post("/api/chat", json={"message": "   "})
        assert "Please type a message" in empty_res.json().get("reply", "")

        huge_message = "A" * 2500
        overflow_res = await client.post("/api/chat", json={"message": huge_message})
        assert "too long" in overflow_res.json().get("reply", "")

        # 5. Test Website query: "show me your website"
        print("\n5. Testing website link query: 'show me your website'...")
        web_res = await client.post(
            "/api/chat",
            json={"message": "show me your website"},
            timeout=30.0
        )
        web_reply = web_res.json().get("reply", "")
        print(f"Web Link Reply:\n{web_reply}")
        assert "https://www.preciousedu.in" in web_reply
        assert "**[" not in web_reply
        assert "](http" not in web_reply

        # 6. Test Study Visa flow: "I want to apply for study visa in Canada"
        print("\n6. Testing Study Visa flow query: 'I want to apply for study visa in Canada'...")
        visa_res = await client.post(
            "/api/chat",
            json={
                "message": "I want to apply for study visa in Canada",
                "session_id": "test_visa_session_1"
            },
            timeout=30.0
        )
        visa_reply = visa_res.json().get("reply", "")
        print(f"Study Visa Reply:\n{visa_reply}")
        assert visa_res.status_code == 200
        # Check that it asks for profile details (e.g. qualification or IELTS/PTE or contact info)
        lower_reply = visa_reply.lower()
        assert any(term in lower_reply for term in ["qualification", "education", "doing", "background", "percentage", "study", "course"])
        assert any(term in lower_reply for term in ["ielts", "pte", "english", "contact", "phone", "number", "details"])

        # 7. Test WhatsApp Multi-Turn Continuity & Follow-up Flow (without client-side history)
        print("\n7. Testing WhatsApp Multi-Turn Server-Side Memory ('what is the flow of that ?')...")
        turn1_res = await client.post(
            "/api/predict",
            json={"message": "can i get Australia student visa ?", "session_id": "918980614160"}
        )
        assert turn1_res.status_code == 200
        print("Turn 1 (Australia visa query) passed.")

        turn2_res = await client.post(
            "/api/predict",
            json={"message": "what is the flow of that ?", "session_id": "918980614160"}
        )
        assert turn2_res.status_code == 200
        turn2_reply = turn2_res.json().get("reply", "")
        print(f"Turn 2 ('what is the flow of that ?') Reply:\n{turn2_reply[:300]}...")
        # Bot should know 'that' refers to Australia student visa flow
        assert any(term in turn2_reply.lower() for term in ["australia", "flow", "process", "step", "offer", "admission", "visa"])

        # 8. Test Email inquiry formatting
        print("\n8. Testing Email inquiry ('what is your email id')...")
        email_res = await client.post(
            "/api/predict",
            json={"message": "what is your email id", "session_id": "918980614160"}
        )
        assert email_res.status_code == 200
        email_reply = email_res.json().get("reply", "")
        print(f"Email Reply:\n{email_reply}")
        assert "info@preciousedu.in" in email_reply
        # 9. Test Bill & Document AI OCR Extraction Endpoint
        print("\n9. Testing /api/ocr/bill endpoint with sample document...")
        import os
        from pathlib import Path
        sample_pdf = Path(__file__).resolve().parent.parent / "PreciousEdu.pdf"
        if sample_pdf.exists():
            with open(sample_pdf, "rb") as f:
                pdf_bytes = f.read()
            ocr_res = await client.post(
                "/api/ocr/bill",
                files={"file": ("PreciousEdu.pdf", pdf_bytes, "application/pdf")},
                timeout=35.0
            )
            print(f"OCR Status: {ocr_res.status_code}")
            ocr_json = ocr_res.json()
            assert ocr_res.status_code == 200
            assert ocr_json.get("status") == "success"
            assert "data" in ocr_json
            print(f"OCR Extracted Vendor: {ocr_json['data'].get('vendor_name')}")
            print(f"OCR Summary: {ocr_json['data'].get('summary')}")
            print("OCR Test passed successfully!")
        else:
            print("PreciousEdu.pdf not found, skipping PDF OCR test.")

    print("\n[SUCCESS] All backend, WhatsApp multi-turn memory, and OCR tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(test_all())
