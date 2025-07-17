#!/usr/bin/env python3
"""
测试前端数据加载问题
"""
import requests
import json

def test_frontend_data():
    """测试前端数据加载"""
    base_url = "http://localhost:8000"
    
    print("🔍 测试前端数据加载问题...")
    
    # 1. 测试登录
    print("\n1. 测试登录...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 登录成功")
        else:
            print(f"❌ 登录失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 2. 测试需求API
    print("\n2. 测试需求API...")
    try:
        response = requests.get(f"{base_url}/api/v1/requirements/", headers=headers)
        if response.status_code == 200:
            requirements = response.json()
            print(f"✅ 需求API正常，共 {len(requirements)} 条数据")
            for req in requirements[:3]:
                print(f"  - {req['title']} (ID: {req['id']})")
        else:
            print(f"❌ 需求API失败: {response.text}")
    except Exception as e:
        print(f"❌ 需求API失败: {e}")
    
    # 3. 测试测试用例API
    print("\n3. 测试测试用例API...")
    try:
        response = requests.get(f"{base_url}/api/v1/test-cases/", headers=headers)
        if response.status_code == 200:
            test_cases = response.json()
            print(f"✅ 测试用例API正常，共 {len(test_cases)} 条数据")
            for tc in test_cases[:3]:
                print(f"  - {tc['title']} (ID: {tc['id']})")
        else:
            print(f"❌ 测试用例API失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试用例API失败: {e}")
    
    # 4. 测试知识库API
    print("\n4. 测试知识库API...")
    try:
        response = requests.get(f"{base_url}/api/v1/knowledge/", headers=headers)
        if response.status_code == 200:
            knowledge = response.json()
            print(f"✅ 知识库API正常，共 {len(knowledge)} 条数据")
            for kb in knowledge[:3]:
                print(f"  - {kb['title']} (ID: {kb['id']})")
        else:
            print(f"❌ 知识库API失败: {response.text}")
    except Exception as e:
        print(f"❌ 知识库API失败: {e}")
    
    # 5. 测试生成历史API
    print("\n5. 测试生成历史API...")
    try:
        response = requests.get(f"{base_url}/api/v1/generation/history", headers=headers)
        if response.status_code == 200:
            history = response.json()
            print(f"✅ 生成历史API正常，共 {len(history)} 条数据")
            for hist in history[:3]:
                print(f"  - {hist['generation_type']} (ID: {hist['id']})")
        else:
            print(f"❌ 生成历史API失败: {response.text}")
    except Exception as e:
        print(f"❌ 生成历史API失败: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 如果API都正常但前端无数据，可能的问题：")
    print("1. 前端未登录或token过期")
    print("2. 前端API路径配置错误")
    print("3. 前端网络请求被拦截")
    print("4. 浏览器缓存问题")

if __name__ == "__main__":
    test_frontend_data() 