import asyncio
import httpx
from gemini_service import ask_gemini
import config

async def test_key_rotation():
    print("=== Testing Automatic Key Fallback & Rotation ===")
    
    # Temporarily prepend an invalid key to test fallback
    real_keys = list(config.GEMINI_API_KEYS)
    invalid_key = "AIzaSyFakeInvalidKeyForTestingRotation12345"
    config.GEMINI_API_KEYS = [invalid_key] + real_keys
    
    print(f"Total keys in test list: {len(config.GEMINI_API_KEYS)}")
    print(f"Key #1 is intentionally invalid: {invalid_key[:15]}...")
    print(f"Key #2 is valid: {real_keys[0][:15]}...")
    
    try:
        reply = await ask_gemini(
            user_message="Hello, test rotation",
            site_context="Precious Education is an education consultancy.",
            history=[]
        )
        print("\nRotation Test Result:")
        print(f"Successfully received response after automatic fallback:\n{reply[:120]}...")
        assert len(reply) > 0
        print("\n[SUCCESS] Key rotation logic successfully fell back from invalid key to working key!")
    finally:
        # Restore original keys
        config.GEMINI_API_KEYS = real_keys

if __name__ == "__main__":
    asyncio.run(test_key_rotation())
