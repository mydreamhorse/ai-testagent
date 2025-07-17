#!/usr/bin/env python3
"""
测试测试用例详情页面数据加载
"""
import requests
import json

def test_testcase_detail():
    """测试测试用例详情页面数据加载"""
    base_url = "http://localhost:8000"
    
    print("🔍 测试测试用例详情页面数据加载...")
    
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
    
    # 2. 测试测试用例详情API
    print("\n2. 测试测试用例详情API...")
    test_case_id = 92  # 使用一个存在的测试用例ID
    try:
        response = requests.get(f"{base_url}/api/v1/test-cases/{test_case_id}", headers=headers)
        if response.status_code == 200:
            test_case = response.json()
            print(f"✅ 测试用例详情API正常")
            print(f"  - 标题: {test_case['title']}")
            print(f"  - 类型: {test_case['test_type']}")
            print(f"  - 优先级: {test_case['priority']}")
        else:
            print(f"❌ 测试用例详情API失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试用例详情API失败: {e}")
    
    # 3. 测试测试用例评估API
    print("\n3. 测试测试用例评估API...")
    try:
        response = requests.get(f"{base_url}/api/v1/test-cases/{test_case_id}/evaluation", headers=headers)
        if response.status_code == 200:
            evaluation = response.json()
            print(f"✅ 测试用例评估API正常")
            print(f"  - 总分: {evaluation['total_score']}")
            print(f"  - 完整性: {evaluation['completeness_score']}")
        else:
            print(f"❌ 测试用例评估API失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试用例评估API失败: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 如果API都正常但前端页面空白，可能的问题：")
    print("1. 前端路由配置问题")
    print("2. 前端组件渲染问题")
    print("3. 浏览器缓存问题")
    print("4. 前端JavaScript错误")

if __name__ == "__main__":
    test_testcase_detail() 