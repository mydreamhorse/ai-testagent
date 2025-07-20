#!/usr/bin/env python3
"""
Test script for API endpoints
"""

import os
import sys
import asyncio
import httpx

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from fastapi.testclient import TestClient

def test_api_endpoints():
    """Test API endpoints"""
    print("🧪 Testing API Endpoints...")
    
    # Create test client
    client = TestClient(app)
    
    try:
        # Test 1: Health check
        print("\n1️⃣  Testing health endpoint...")
        response = client.get("/health")
        assert response.status_code == 200
        print("✓ Health endpoint working")
        
        # Test 2: Root endpoint
        print("\n2️⃣  Testing root endpoint...")
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✓ Root endpoint working")
        
        # Test 3: User registration
        print("\n3️⃣  Testing user registration...")
        user_data = {
            "username": "testapi",
            "email": "testapi@example.com", 
            "password": "testpass123"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        if response.status_code == 400 and "already registered" in response.text:
            print("✓ User already exists, proceeding with login")
        else:
            assert response.status_code == 200, f"用户注册失败: {response.text}"
            user = response.json()
            print(f"✓ User registration working: {user['username']}")
        
        # Test 4: User login
        print("\n4️⃣  Testing user login...")
        login_data = {
            "username": "testapi",
            "password": "testpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token_data = response.json()
        token = token_data["access_token"]
        print("✓ User login working")
        
        # Set authorization header
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 5: Create requirement
        print("\n5️⃣  Testing requirement creation...")
        requirement_data = {
            "title": "API测试需求",
            "description": "通过API创建的测试需求",
            "content": "这是一个座椅电动调节功能的API测试需求。包含前后调节、高度调节和角度调节功能。"
        }
        response = client.post("/api/v1/requirements/", json=requirement_data, headers=headers)
        assert response.status_code == 200
        requirement = response.json()
        requirement_id = requirement["id"]
        print(f"✓ Requirement creation working: ID {requirement_id}")
        
        # Test 6: Parse requirement
        print("\n6️⃣  Testing requirement parsing...")
        response = client.post(f"/api/v1/requirements/{requirement_id}/parse", headers=headers)
        assert response.status_code == 200
        parse_result = response.json()
        print(f"✓ Requirement parsing working: {parse_result['data']['features_count']} features")
        
        # Test 7: Generate test cases
        print("\n7️⃣  Testing test case generation...")
        generation_data = {
            "requirement_id": requirement_id,
            "generation_type": "test_cases"
        }
        response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=headers)
        assert response.status_code == 200
        generation_result = response.json()
        print(f"✓ Test case generation working: {generation_result['message']}")
        
        # Test 8: Get test cases
        print("\n8️⃣  Testing test case retrieval...")
        response = client.get(f"/api/v1/test-cases/?requirement_id={requirement_id}", headers=headers)
        assert response.status_code == 200
        test_cases = response.json()
        print(f"✓ Test case retrieval working: {len(test_cases)} test cases")
        
        # Test 9: Evaluate test cases
        if test_cases:
            print("\n9️⃣  Testing test case evaluation...")
            test_case_id = test_cases[0]["id"]
            response = client.post(f"/api/v1/test-cases/{test_case_id}/evaluate", headers=headers)
            assert response.status_code == 200
            eval_result = response.json()
            print(f"✓ Test case evaluation working: Score {eval_result['data']['evaluation']['total_score']:.1f}")
        
        print("\n" + "="*60)
        print("✅ ALL API TESTS PASSED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ API TEST FAILED: {str(e)}")
        raise

if __name__ == "__main__":
    test_api_endpoints()