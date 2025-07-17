#!/usr/bin/env python3
"""
插入示例数据脚本
"""
import sys
import os
import requests
import json
from datetime import datetime

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def insert_sample_data():
    """插入示例数据"""
    base_url = "http://localhost:8000"
    
    print("🚀 开始插入示例数据...")
    
    # 1. 创建测试用户
    print("\n1. 创建测试用户...")
    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123"
        },
        {
            "username": "tester",
            "email": "tester@example.com", 
            "password": "tester123"
        },
        {
            "username": "developer",
            "email": "dev@example.com",
            "password": "dev123"
        }
    ]
    
    created_users = []
    for user in users:
        try:
            response = requests.post(f"{base_url}/api/v1/auth/register", json=user)
            if response.status_code == 200:
                print(f"✅ 用户 {user['username']} 创建成功")
                created_users.append(user['username'])
            else:
                print(f"⚠️ 用户 {user['username']} 可能已存在")
                created_users.append(user['username'])
        except Exception as e:
            print(f"❌ 创建用户 {user['username']} 失败: {e}")
    
    # 2. 登录获取token
    print("\n2. 登录获取访问令牌...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 登录成功，获取到访问令牌")
        else:
            print("❌ 登录失败")
            return
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 3. 创建示例需求
    print("\n3. 创建示例需求...")
    requirements = [
        {
            "title": "座椅记忆功能测试需求",
            "description": "座椅记忆功能测试需求",
            "content": """
座椅记忆功能要求：
1. 支持3组记忆位置存储
2. 记忆内容包括前后位置0-250mm、上下位置0-80mm、靠背角度90-160度
3. 调节到记忆位置时间不超过5秒
4. 支持记忆位置命名和删除
5. 断电后记忆数据保持
            """,
            "category": "记忆功能",
            "priority": "high"
        },
        {
            "title": "座椅加热功能测试需求", 
            "description": "座椅加热功能测试需求",
            "content": """
座椅加热功能要求：
1. 支持3档加热温度调节（低、中、高）
2. 加热温度范围：25-45度
3. 加热启动时间不超过30秒
4. 支持定时加热功能
5. 过热保护功能
            """,
            "category": "加热功能",
            "priority": "medium"
        },
        {
            "title": "座椅通风功能测试需求",
            "description": "座椅通风功能测试需求",
            "content": """
座椅通风功能要求：
1. 支持3档风速调节
2. 通风面积覆盖座椅背部和座垫
3. 噪音控制在45分贝以下
4. 支持定时通风功能
5. 与加热功能互斥
            """,
            "category": "通风功能", 
            "priority": "medium"
        },
        {
            "title": "座椅按摩功能测试需求",
            "description": "座椅按摩功能测试需求",
            "content": """
座椅按摩功能要求：
1. 支持5种按摩模式
2. 按摩强度3档可调
3. 按摩时间10-30分钟可设置
4. 支持局部按摩和全身按摩
5. 按摩过程中座椅位置锁定
            """,
            "category": "按摩功能",
            "priority": "low"
        },
        {
            "title": "座椅安全功能测试需求",
            "description": "座椅安全功能测试需求",
            "content": """
座椅安全功能要求：
1. 碰撞时座椅自动回位
2. 安全带未系时座椅调节受限
3. 儿童座椅检测功能
4. 座椅位置传感器故障检测
5. 紧急情况下座椅快速调节
            """,
            "category": "安全功能",
            "priority": "high"
        }
    ]
    
    created_requirements = []
    for req in requirements:
        try:
            response = requests.post(f"{base_url}/api/v1/requirements/", json=req, headers=headers)
            if response.status_code == 200:
                req_data = response.json()
                created_requirements.append(req_data["id"])
                print(f"✅ 需求 '{req['title']}' 创建成功 (ID: {req_data['id']})")
            else:
                print(f"❌ 创建需求 '{req['title']}' 失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建需求失败: {e}")
    
    # 4. 为需求生成测试用例
    print("\n4. 生成测试用例...")
    for req_id in created_requirements:
        try:
            response = requests.post(f"{base_url}/api/v1/generation/test-cases", 
                                  json={"requirement_id": req_id}, 
                                  headers=headers)
            if response.status_code == 200:
                print(f"✅ 为需求 {req_id} 生成测试用例成功")
            else:
                print(f"❌ 为需求 {req_id} 生成测试用例失败: {response.text}")
        except Exception as e:
            print(f"❌ 生成测试用例失败: {e}")
    
    # 5. 创建测试模板
    print("\n5. 创建测试模板...")
    templates = [
        {
            "name": "功能测试模板",
            "category": "功能测试",
            "template_content": """
测试用例模板：{title}

前置条件：
{preconditions}

测试步骤：
{steps}

预期结果：
{expected_result}

测试数据：
{test_data}

注意事项：
{notes}
            """,
            "description": "标准功能测试用例模板"
        },
        {
            "name": "边界测试模板", 
            "category": "边界测试",
            "template_content": """
边界测试用例：{title}

测试目标：
验证{feature}在边界条件下的行为

前置条件：
{preconditions}

测试步骤：
1. 设置{parameter}为最小值
2. 执行{operation}
3. 设置{parameter}为最大值  
4. 执行{operation}
5. 设置{parameter}为无效值
6. 执行{operation}

预期结果：
{expected_result}

边界值：
- 最小值：{min_value}
- 最大值：{max_value}
- 无效值：{invalid_values}
            """,
            "description": "边界值测试用例模板"
        },
        {
            "name": "异常测试模板",
            "category": "异常测试", 
            "template_content": """
异常测试用例：{title}

测试目标：
验证{feature}在异常情况下的处理

前置条件：
{preconditions}

测试步骤：
1. 模拟{exception_scenario}
2. 执行{operation}
3. 观察系统响应
4. 检查错误处理

预期结果：
{expected_result}

异常场景：
{exception_scenarios}

错误处理要求：
{error_handling}
            """,
            "description": "异常情况测试用例模板"
        }
    ]
    
    for template in templates:
        try:
            response = requests.post(f"{base_url}/api/v1/templates/", json=template, headers=headers)
            if response.status_code == 200:
                print(f"✅ 模板 '{template['name']}' 创建成功")
            else:
                print(f"❌ 创建模板 '{template['name']}' 失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建模板失败: {e}")
    
    # 6. 添加知识库数据
    print("\n6. 添加知识库数据...")
    knowledge_items = [
        {
            "title": "汽车座椅功能分类",
            "content": """
汽车座椅主要功能分类：
1. 电动调节功能
   - 前后位置调节
   - 上下高度调节  
   - 靠背角度调节
   - 头枕高度调节
   
2. 记忆功能
   - 位置记忆存储
   - 多组记忆设置
   - 记忆位置调用
   
3. 舒适功能
   - 座椅加热
   - 座椅通风
   - 座椅按摩
   
4. 安全功能
   - 碰撞保护
   - 安全带检测
   - 儿童座椅检测
            """,
            "category": "功能分类",
            "tags": ["座椅功能", "分类", "基础"]
        },
        {
            "title": "测试用例质量标准",
            "content": """
高质量测试用例应具备：
1. 完整性
   - 明确的前置条件
   - 详细的测试步骤
   - 具体的预期结果
   
2. 准确性
   - 技术术语使用正确
   - 操作描述准确
   - 参数值精确
   
3. 可执行性
   - 操作步骤可行
   - 结果可验证
   - 环境要求明确
   
4. 覆盖度
   - 功能点覆盖全面
   - 场景覆盖完整
   - 边界条件覆盖
   
5. 清晰度
   - 语言表达清晰
   - 结构层次分明
   - 逻辑关系清楚
            """,
            "category": "质量标准",
            "tags": ["测试用例", "质量", "标准"]
        }
    ]
    
    for item in knowledge_items:
        try:
            response = requests.post(f"{base_url}/api/v1/knowledge/", json=item, headers=headers)
            if response.status_code == 200:
                print(f"✅ 知识库项目 '{item['title']}' 创建成功")
            else:
                print(f"❌ 创建知识库项目 '{item['title']}' 失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建知识库项目失败: {e}")
    
    print("\n🎉 示例数据插入完成！")
    print(f"\n📊 数据统计:")
    print(f"- 用户: {len(created_users)} 个")
    print(f"- 需求: {len(created_requirements)} 个") 
    print(f"- 模板: {len(templates)} 个")
    print(f"- 知识库: {len(knowledge_items)} 个")
    print(f"\n🔗 访问地址:")
    print(f"- 前端应用: http://localhost:3000")
    print(f"- 后端API: http://localhost:8000")
    print(f"- API文档: http://localhost:8000/docs")
    print(f"\n👤 测试账号:")
    print(f"- 用户名: admin, 密码: admin123")
    print(f"- 用户名: tester, 密码: tester123")
    print(f"- 用户名: developer, 密码: dev123")

if __name__ == "__main__":
    insert_sample_data() 