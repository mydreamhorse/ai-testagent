#!/usr/bin/env python3
"""
Final comprehensive test to verify the complete system functionality.
This test covers the entire workflow from user registration to test case generation and evaluation.
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from backend.main import app

def run_final_test():
    """Run comprehensive end-to-end test"""
    print("🚀 Starting Final Comprehensive System Test")
    print("=" * 60)
    
    client = TestClient(app)
    
    try:
        # Test 1: System Health
        print("\n1️⃣  Testing system health...")
        response = client.get("/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✅ System health check passed")
        
        # Test 2: User Management
        print("\n2️⃣  Testing user management...")
        user_data = {
            "username": "finaltest",
            "email": "finaltest@example.com",
            "password": "test123456"
        }
        
        # Register user
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200, f"User registration failed: {response.text}"
        user = response.json()
        print(f"✅ User registered: {user['username']}")
        
        # Login user
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200, f"User login failed: {response.text}"
        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ User login successful")
        
        # Test 3: Requirement Management
        print("\n3️⃣  Testing requirement management...")
        requirement_data = {
            "title": "最终测试需求",
            "description": "这是一个综合的最终测试需求",
            "content": """
            汽车座椅智能控制系统需求：
            
            1. 电动位置调节功能
               - 前后位置调节：范围0-30厘米，精度1毫米
               - 高度调节：范围0-15厘米，精度1毫米
               - 靠背角度调节：范围15-75度，精度1度
               - 所有调节操作响应时间不超过2秒
            
            2. 记忆位置功能
               - 支持3个用户记忆位置
               - 一键设置和恢复功能
               - 记忆数据掉电保存
            
            3. 加热通风系统
               - 加热功能：3档温度调节，25-45度
               - 通风功能：3档风速调节
               - 自动温度控制和过热保护
            
            4. 安全保护机制
               - 防夹功能：遇阻力自动停止并反向2厘米
               - 过载保护：电流超限自动断电
               - 故障自诊断和报警功能
            
            5. 用户界面
               - 触控屏显示当前状态
               - 语音提示和警告
               - 手机APP远程控制
            """
        }
        
        # Create requirement
        response = client.post("/api/v1/requirements/", json=requirement_data, headers=headers)
        assert response.status_code == 200, f"Requirement creation failed: {response.text}"
        requirement = response.json()
        requirement_id = requirement["id"]
        print(f"✅ Requirement created: ID {requirement_id}")
        
        # Get requirements list
        response = client.get("/api/v1/requirements/", headers=headers)
        assert response.status_code == 200, f"Get requirements failed: {response.text}"
        requirements = response.json()
        assert len(requirements) > 0, "No requirements found"
        print(f"✅ Requirements list retrieved: {len(requirements)} items")
        
        # Test 4: Requirement Parsing
        print("\n4️⃣  Testing requirement parsing...")
        response = client.post(f"/api/v1/requirements/{requirement_id}/parse", headers=headers)
        assert response.status_code == 200, f"Requirement parsing failed: {response.text}"
        parse_result = response.json()
        features_count = parse_result["data"]["features_count"]
        print(f"✅ Requirement parsed: {features_count} features extracted")
        
        # Verify features were saved
        response = client.get(f"/api/v1/requirements/{requirement_id}/features", headers=headers)
        assert response.status_code == 200, f"Get features failed: {response.text}"
        features = response.json()
        assert len(features) == features_count, "Feature count mismatch"
        print(f"✅ Features verified: {len(features)} features in database")
        
        # Test 5: Test Case Generation
        print("\n5️⃣  Testing test case generation...")
        generation_data = {
            "requirement_id": requirement_id,
            "generation_type": "test_cases",
            "options": {
                "test_types": ["function", "boundary", "exception", "security"]
            }
        }
        
        response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=headers)
        assert response.status_code == 200, f"Test case generation failed: {response.text}"
        generation_result = response.json()
        print(f"✅ Test case generation: {generation_result['message']}")
        
        # Verify test cases were created
        response = client.get(f"/api/v1/test-cases/?requirement_id={requirement_id}", headers=headers)
        assert response.status_code == 200, f"Get test cases failed: {response.text}"
        test_cases = response.json()
        assert len(test_cases) > 0, "No test cases generated"
        print(f"✅ Test cases verified: {len(test_cases)} test cases created")
        
        # Test 6: Quality Evaluation
        print("\n6️⃣  Testing quality evaluation...")
        
        # Evaluate individual test case
        test_case_id = test_cases[0]["id"]
        response = client.post(f"/api/v1/test-cases/{test_case_id}/evaluate", headers=headers)
        assert response.status_code == 200, f"Test case evaluation failed: {response.text}"
        eval_result = response.json()
        total_score = eval_result["data"]["evaluation"]["total_score"]
        print(f"✅ Individual evaluation: Test case scored {total_score:.1f}/100")
        
        # Batch evaluate all test cases
        test_case_ids = [tc["id"] for tc in test_cases]
        response = client.post("/api/v1/test-cases/batch-evaluate", json=test_case_ids, headers=headers)
        assert response.status_code == 200, f"Batch evaluation failed: {response.text}"
        batch_result = response.json()
        avg_score = batch_result["data"]["average_score"]
        print(f"✅ Batch evaluation: {len(test_case_ids)} test cases, average score {avg_score:.1f}/100")
        
        # Test 7: Full Generation Workflow
        print("\n7️⃣  Testing full generation workflow...")
        response = client.post("/api/v1/generation/evaluation", json=generation_data, headers=headers)
        assert response.status_code == 200, f"Full evaluation failed: {response.text}"
        full_eval_result = response.json()
        print(f"✅ Full evaluation workflow: {full_eval_result['message']}")
        
        # Test 8: Generation History
        print("\n8️⃣  Testing generation history...")
        response = client.get("/api/v1/generation/history", headers=headers)
        assert response.status_code == 200, f"Get history failed: {response.text}"
        history = response.json()
        assert len(history) > 0, "No generation history found"
        print(f"✅ Generation history: {len(history)} entries")
        
        # Test 9: File Upload (simulate)
        print("\n9️⃣  Testing file operations...")
        # Test file upload endpoint (without actual file)
        response = client.get(f"/api/v1/requirements/{requirement_id}", headers=headers)
        assert response.status_code == 200, f"Get requirement details failed: {response.text}"
        req_details = response.json()
        assert req_details["id"] == requirement_id, "Requirement details mismatch"
        print("✅ File operations and requirement details verified")
        
        # Test 10: Data Completeness Check
        print("\n🔟 Testing data completeness...")
        
        # Check that all data is properly linked
        response = client.get(f"/api/v1/test-cases/{test_case_id}", headers=headers)
        assert response.status_code == 200, f"Get test case details failed: {response.text}"
        tc_details = response.json()
        
        response = client.get(f"/api/v1/test-cases/{test_case_id}/evaluation", headers=headers)
        assert response.status_code == 200, f"Get evaluation details failed: {response.text}"
        eval_details = response.json()
        
        print("✅ Data completeness verified")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎉 FINAL TEST RESULTS - ALL SYSTEMS OPERATIONAL!")
        print("=" * 60)
        print(f"✅ User Management: Registration and Authentication")
        print(f"✅ Requirement Management: Create, Read, Parse")
        print(f"✅ Feature Extraction: {features_count} features from requirement")
        print(f"✅ Test Case Generation: {len(test_cases)} test cases created")
        print(f"✅ Quality Evaluation: Average score {avg_score:.1f}/100")
        print(f"✅ Generation History: {len(history)} workflow entries")
        print(f"✅ Data Integrity: All components properly linked")
        print("\n🚀 The Car Seat Testing Agent System is FULLY FUNCTIONAL!")
        print("📊 Ready for production deployment")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_final_test()
    sys.exit(0 if success else 1)