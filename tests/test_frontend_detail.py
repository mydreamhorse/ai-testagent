#!/usr/bin/env python3
"""
测试前端测试用例详情页面
"""
import requests
import json

def test_frontend_detail():
    """测试前端测试用例详情页面"""
    print("🔍 测试前端测试用例详情页面...")
    
    # 1. 测试前端页面访问
    print("\n1. 测试前端页面访问...")
    try:
        response = requests.get("http://localhost:3000/test-cases/92")
        if response.status_code == 200:
            print("✅ 前端页面访问正常")
            # 检查页面是否包含Vue应用
            if "汽车座椅软件测试智能体" in response.text:
                print("✅ 页面包含正确的标题")
            else:
                print("❌ 页面标题不正确")
        else:
            print(f"❌ 前端页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端页面访问失败: {e}")
    
    # 2. 测试API端点
    print("\n2. 测试API端点...")
    try:
        # 先登录获取token
        login_response = requests.post("http://localhost:8000/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试测试用例详情API
            detail_response = requests.get("http://localhost:8000/api/v1/test-cases/92", headers=headers)
            if detail_response.status_code == 200:
                print("✅ 测试用例详情API正常")
                test_case = detail_response.json()
                print(f"  - 标题: {test_case['title']}")
            else:
                print(f"❌ 测试用例详情API失败: {detail_response.text}")
            
            # 测试评估API
            eval_response = requests.get("http://localhost:8000/api/v1/test-cases/92/evaluation", headers=headers)
            if eval_response.status_code == 200:
                print("✅ 测试用例评估API正常")
                evaluation = eval_response.json()
                print(f"  - 总分: {evaluation['total_score']}")
            else:
                print(f"❌ 测试用例评估API失败: {eval_response.text}")
        else:
            print(f"❌ 登录失败: {login_response.text}")
    except Exception as e:
        print(f"❌ API测试失败: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 如果API正常但前端页面空白，请检查：")
    print("1. 浏览器开发者工具的控制台错误")
    print("2. 网络请求是否正常")
    print("3. 前端路由是否正确")
    print("4. 用户是否已登录")

if __name__ == "__main__":
    test_frontend_detail() 