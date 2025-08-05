#!/usr/bin/env python3

import asyncio
import json
import httpx
from app.services.sl1_service import sl1_service

async def test_sl1_integration():
    """
    Test the full webhook -> SL1 integration pipeline
    """
    print("🧪 Testing SL1 Integration")
    print("=" * 50)
    
    # Test 1: Direct SL1 service test
    print("\n📡 Testing direct SL1 service...")
    test_message = "Test alert from GenHook - SL1 integration working!"
    
    success = await sl1_service.send_alert(test_message)
    if success:
        print("✅ Direct SL1 service test PASSED")
    else:
        print("❌ Direct SL1 service test FAILED")
    
    # Test 2: Full webhook endpoint test
    print("\n🔗 Testing full webhook endpoint...")
    
    # Sample GitHub webhook payload
    github_payload = {
        "action": "opened",
        "pull_request": {
            "title": "Test PR for SL1 Integration",
            "user": {
                "login": "testuser"
            }
        },
        "repository": {
            "name": "GenHook-Test"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/webhook/github",
                json=github_payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Webhook endpoint test PASSED")
                print(f"   Generated message: {result.get('generated_message', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
            else:
                print(f"❌ Webhook endpoint test FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Webhook endpoint test FAILED - Server not running")
        print("   Start the server with: cd backend && python3 main.py")
    except Exception as e:
        print(f"❌ Webhook endpoint test FAILED - Error: {e}")
    
    print("\n🎯 Integration Test Summary:")
    print("- SL1 Service: HTTP Basic Auth with retry logic")
    print("- Webhook Endpoint: /webhook/{service}")
    print("- Full Pipeline: Webhook → Extract → Template → SL1")
    print("\n📝 To test manually:")
    print("curl -X POST http://localhost:8000/webhook/github \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"action\":\"opened\",\"pull_request\":{\"title\":\"Test\",\"user\":{\"login\":\"testuser\"}},\"repository\":{\"name\":\"TestRepo\"}}'")

if __name__ == "__main__":
    asyncio.run(test_sl1_integration())