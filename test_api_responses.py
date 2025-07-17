#!/usr/bin/env python3
"""
测试API响应修复
"""
import requests
import json

def test_api_responses():
    """测试所有API响应修复"""
    base_url = "http://localhost:8000"
    
    print("🔍 测试API响应修复...")
    
    # 1. 登录获取token
    print("\n1. 登录获取token...")
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 登录成功")
        else:
            print(f"❌ 登录失败: {login_response.text}")
            return
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 2. 测试需求解析API
    print("\n2. 测试需求解析API...")
    try:
        # 先获取一个需求ID
        requirements_response = requests.get(f"{base_url}/api/v1/requirements/", headers=headers)
        if requirements_response.status_code == 200:
            requirements = requirements_response.json()
            if requirements:
                requirement_id = requirements[0]["id"]
                print(f"✅ 找到需求ID: {requirement_id}")
                
                # 测试解析API
                parse_response = requests.post(f"{base_url}/api/v1/requirements/{requirement_id}/parse", headers=headers)
                if parse_response.status_code == 200:
                    result = parse_response.json()
                    print(f"✅ 需求解析API正常")
                    print(f"  - 响应结构: {list(result.keys())}")
                else:
                    print(f"❌ 需求解析API失败: {parse_response.text}")
            else:
                print("❌ 没有找到需求")
        else:
            print(f"❌ 获取需求列表失败: {requirements_response.text}")
    except Exception as e:
        print(f"❌ 需求解析API测试失败: {e}")
    
    # 3. 测试测试用例评估API
    print("\n3. 测试测试用例评估API...")
    try:
        # 先获取一个测试用例ID
        test_cases_response = requests.get(f"{base_url}/api/v1/test-cases/", headers=headers)
        if test_cases_response.status_code == 200:
            test_cases = test_cases_response.json()
            if test_cases:
                test_case_id = test_cases[0]["id"]
                print(f"✅ 找到测试用例ID: {test_case_id}")
                
                # 测试评估API
                evaluate_response = requests.post(f"{base_url}/api/v1/test-cases/{test_case_id}/evaluate", headers=headers)
                if evaluate_response.status_code == 200:
                    result = evaluate_response.json()
                    print(f"✅ 测试用例评估API正常")
                    print(f"  - 响应结构: {list(result.keys())}")
                    if "data" in result:
                        print(f"  - data结构: {list(result['data'].keys())}")
                else:
                    print(f"❌ 测试用例评估API失败: {evaluate_response.text}")
            else:
                print("❌ 没有找到测试用例")
        else:
            print(f"❌ 获取测试用例列表失败: {test_cases_response.text}")
    except Exception as e:
        print(f"❌ 测试用例评估API测试失败: {e}")
    
    # 4. 测试批量评估API
    print("\n4. 测试批量评估API...")
    try:
        if test_cases:
            test_case_ids = [tc["id"] for tc in test_cases[:2]]  # 取前2个
            batch_response = requests.post(f"{base_url}/api/v1/test-cases/batch-evaluate", 
                                        json=test_case_ids, headers=headers)
            if batch_response.status_code == 200:
                result = batch_response.json()
                print(f"✅ 批量评估API正常")
                print(f"  - 响应结构: {list(result.keys())}")
                if "data" in result:
                    print(f"  - data结构: {list(result['data'].keys())}")
            else:
                print(f"❌ 批量评估API失败: {batch_response.text}")
    except Exception as e:
        print(f"❌ 批量评估API测试失败: {e}")
    
    # 5. 测试生成API
    print("\n5. 测试生成API...")
    try:
        if requirements:
            requirement_id = requirements[0]["id"]
            generation_response = requests.post(f"{base_url}/api/v1/generation/test-cases", 
                                             json={
                                                 "requirement_id": requirement_id,
                                                 "generation_type": "test_cases"
                                             }, headers=headers)
            if generation_response.status_code == 200:
                result = generation_response.json()
                print(f"✅ 生成API正常")
                print(f"  - 响应结构: {list(result.keys())}")
            else:
                print(f"❌ 生成API失败: {generation_response.text}")
    except Exception as e:
        print(f"❌ 生成API测试失败: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 修复总结:")
    print("1. 前端axios拦截器已自动返回response.data")
    print("2. 所有response.data.xxx应改为response.xxx")
    print("3. 对于APIResponse结构，数据在response.data中")
    print("4. 对于直接返回的数据，数据在response中")

if __name__ == "__main__":
    test_api_responses() 