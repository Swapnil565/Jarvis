"""
JARVIS 3.0 Backend - Day 2 Checklist Verification
Test script to verify all 5 checklist items are working correctly
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@jarvis.ai",
    "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "bio": "Test user for JARVIS verification"
}

class JarvisAPITester:
    """Test class for JARVIS API endpoints"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.user_data = None
        
    async def print_step(self, step_num: int, description: str):
        """Print formatted test step"""
        print(f"\n{'='*60}")
        print(f"STEP {step_num}: {description}")
        print(f"{'='*60}")
    
    async def print_result(self, success: bool, message: str, data: Any = None):
        """Print formatted test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        if data:
            print(f"Data: {json.dumps(data, indent=2, default=str)}")
    
    async def test_1_create_user_account(self) -> bool:
        """Test 1: Create a New User Account: POST to /register with email/password; verify in DB."""
        await self.print_step(1, "Create a New User Account")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=TEST_USER
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_data = data.get("data", {})
                    await self.print_result(True, "User registration successful", data)
                    return True
                else:
                    await self.print_result(False, f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            await self.print_result(False, f"Registration error: {str(e)}")
            return False
    
    async def test_2_login_get_jwt(self) -> bool:
        """Test 2: Log In and Receive an Authentication Token: POST to /login; get JWT."""
        await self.print_step(2, "Log In and Receive Authentication Token")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "email": TEST_USER["email"],
                        "password": TEST_USER["password"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    await self.print_result(True, "Login successful, JWT token received", {
                        "token_type": data.get("token_type"),
                        "expires_in": data.get("expires_in"),
                        "user": data.get("user", {})
                    })
                    return True
                else:
                    await self.print_result(False, f"Login failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            await self.print_result(False, f"Login error: {str(e)}")
            return False
    
    async def test_3_verify_endpoint_security(self) -> bool:
        """Test 3: Verify Endpoint Security: Try querying without JWT; expect 401 error."""
        await self.print_step(3, "Verify Endpoint Security (No JWT)")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/query",  # Protected endpoint
                    json={
                        "query": "Hello, who are you?",
                        "context": {}
                    }
                )
                
                if response.status_code == 403:  # Should get 403 Forbidden for no auth
                    await self.print_result(True, "Endpoint properly protected - 403 Forbidden without JWT", {
                        "status_code": response.status_code,
                        "error": response.json()
                    })
                    return True
                else:
                    await self.print_result(False, f"Endpoint security failed: Expected 403, got {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.print_result(False, f"Security test error: {str(e)}")
            return False
    
    async def test_4_basic_conversation(self) -> bool:
        """Test 4: Have a Basic, Stateless Conversation: POST to /query with JWT and a general question; get AI response."""
        await self.print_step(4, "Basic Conversation with JWT Authentication")
        
        if not self.auth_token:
            await self.print_result(False, "No auth token available for conversation test")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    json={
                        "query": "Hello JARVIS! Can you tell me what you are and what you can do?",
                        "context": {}
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await self.print_result(True, "AI conversation successful", {
                        "response": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", ""),
                        "status": data.get("status"),
                        "processing_time_ms": data.get("processing_time_ms")
                    })
                    return True
                else:
                    await self.print_result(False, f"Conversation failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            await self.print_result(False, f"Conversation error: {str(e)}")
            return False
    
    async def test_5_no_personal_memory(self) -> bool:
        """Test 5: Confirm the Bot Has No Personal Memory Yet: Query something personal; expect generic response."""
        await self.print_step(5, "Confirm No Personal Memory (Generic Response)")
        
        if not self.auth_token:
            await self.print_result(False, "No auth token available for memory test")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                # First query to establish context
                response1 = await client.post(
                    f"{self.base_url}/query",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    json={
                        "query": "My favorite color is blue and I love pizza.",
                        "context": {}
                    }
                )
                
                # Second query asking about personal info
                response2 = await client.post(
                    f"{self.base_url}/query",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    json={
                        "query": "What is my favorite color and what food do I love?",
                        "context": {}
                    }
                )
                
                if response2.status_code == 200:
                    data = response2.json()
                    response_text = data.get("response", "").lower()
                    
                    # Check if response indicates no memory of previous conversation
                    no_memory_indicators = [
                        "don't know", "not sure", "haven't mentioned", "no information",
                        "can't recall", "don't have that information", "not provided"
                    ]
                    
                    has_no_memory = any(indicator in response_text for indicator in no_memory_indicators)
                    
                    if has_no_memory:
                        await self.print_result(True, "Bot correctly shows no personal memory", {
                            "response": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", ""),
                            "memory_status": "No personal memory confirmed"
                        })
                        return True
                    else:
                        await self.print_result(False, "Bot may have retained personal information", {
                            "response": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", ""),
                            "memory_status": "Possible memory retention detected"
                        })
                        return False
                else:
                    await self.print_result(False, f"Memory test failed: {response2.status_code} - {response2.text}")
                    return False
                    
        except Exception as e:
            await self.print_result(False, f"Memory test error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all checklist tests in sequence"""
        print(f"\n{'🚀'*20}")
        print("JARVIS 3.0 BACKEND - DAY 2 CHECKLIST VERIFICATION")
        print("Testing all 5 required features...")
        print(f"{'🚀'*20}\n")
        
        tests = [
            self.test_1_create_user_account,
            self.test_2_login_get_jwt,
            self.test_3_verify_endpoint_security,
            self.test_4_basic_conversation,
            self.test_5_no_personal_memory
        ]
        
        results = []
        
        for i, test in enumerate(tests, 1):
            try:
                result = await test()
                results.append(result)
                
                if not result:
                    print(f"\n⚠️ Test {i} failed - continuing with remaining tests...")
                    
            except Exception as e:
                print(f"\n❌ Test {i} crashed: {str(e)}")
                results.append(False)
        
        # Summary
        print(f"\n{'='*60}")
        print("FINAL RESULTS SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(results)
        total = len(results)
        
        test_names = [
            "1. Create User Account (/register)",
            "2. Login & Get JWT Token (/login)",
            "3. Verify Endpoint Security (401/403)",
            "4. Basic AI Conversation (/query)",
            "5. Confirm No Personal Memory"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name}")
        
        print(f"\nOVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! JARVIS 3.0 Backend is ready for Day 2! 🎉")
        else:
            print(f"\n⚠️ {total - passed} tests failed. Review implementation before proceeding.")
        
        return passed == total


async def main():
    """Main test execution"""
    tester = JarvisAPITester()
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print("❌ JARVIS server is not running or not healthy!")
                print(f"Start the server with: python -m app.main")
                return
    except Exception as e:
        print("❌ Cannot connect to JARVIS server!")
        print(f"Error: {str(e)}")
        print(f"Make sure server is running on {BASE_URL}")
        print(f"Start with: python -m app.main")
        return
    
    # Run all tests
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())