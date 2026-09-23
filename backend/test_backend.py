import asyncio
import sys
import httpx
from main import app
from config import GEMINI_API_KEYS, GEMINI_MODEL


async def test_all():
    print("=== Testing FastAPI Backend Components ===")
    print(f"Total API Keys configured: {len(GEMINI_API_KEYS)}")
    print(f"Configured Model: {GEMINI_MODEL}")

    # Use httpx.AsyncClient with ASGITransport to test FastAPI directly without needing a separate process
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check test
        print("\n1. Testing GET /api/health...")
        health_res = await client.get("/api/health")
        print(f"Status: {health_res.status_code}")
        print(f"Response: {health_res.json()}")
        assert health_res.status_code == 200
        assert health_res.json().get("status") == "healthy"

        # 2. WhatsApp lead generation rule test
        print("\n2. Testing quick lead pattern: 'can I share my details here?'...")
        lead_res = await client.post("/api/chat", json={"message": "Can I share my details here?"})
        print(f"Status: {lead_res.status_code}")
        print(f"Response: {lead_res.json()}")
        assert lead_res.status_code == 200
        assert "Yes, you can share your details here." in lead_res.json().get("reply", "")

        # 3. Test empty message
        print("\n3. Testing empty message handling...")
        empty_res = await client.post("/api/chat", json={"message": "   "})
        print(f"Status: {empty_res.status_code}")
        print(f"Response: {empty_res.json()}")
        assert "Please type a message" in empty_res.json().get("reply", "")

        # 3b. Test message length security limit
        print("\n3b. Testing message length security limit (>2000 chars)...")
        huge_message = "A" * 2500
        overflow_res = await client.post("/api/chat", json={"message": huge_message})
        print(f"Status: {overflow_res.status_code}")
        print(f"Response: {overflow_res.json()}")
        assert "too long" in overflow_res.json().get("reply", "")

        # 4. Test actual Gemini Chat & Key Rotation
        print("\n4. Testing Gemini Chat with live API key and website context...")
        chat_res = await client.post(
            "/api/chat",
            json={
                "message": "Hi, what services or courses do you offer?",
                "history": [],
                "session_id": "test_session_123"
            },
            timeout=30.0
        )
        print(f"Status: {chat_res.status_code}")
        reply = chat_res.json().get("reply", "")
        print(f"Gemini Reply: {reply[:250]}...")
        assert chat_res.status_code == 200
        assert len(reply) > 0

    print("\n[SUCCESS] All backend tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_all())
