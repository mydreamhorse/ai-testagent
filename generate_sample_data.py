#!/usr/bin/env python3
"""
生成完整示例数据脚本
"""
import sys
import os
import requests
import json
from datetime import datetime, timedelta
import random

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def generate_sample_data():
    """生成完整的示例数据"""
    base_url = "http://localhost:8000"
    
    print("🚀 开始生成完整示例数据...")
    
    # 1. 登录获取token
    print("\n1. 登录获取访问令牌...")
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
    
    # 0. 生成需求数据
    print("\n0. 生成需求数据...")
    requirements = [
        {
            "title": "座椅记忆功能需求",
            "description": "用户可将座椅位置记忆并一键恢复，支持多组记忆。",
            "content": "1. 支持至少2组座椅位置记忆\n2. 记忆内容包括前后、上下、靠背角度\n3. 一键恢复记忆位置，调节时间≤5秒",
            "status": "completed"
        },
        {
            "title": "座椅加热功能需求",
            "description": "座椅可加热，温度可调，具备过热保护。",
            "content": "1. 支持3档温度调节（25/35/45℃）\n2. 具备过热自动断电保护\n3. 加热响应时间≤30秒",
            "status": "completed"
        },
        {
            "title": "座椅通风功能需求",
            "description": "座椅可通风，风速可调，噪音低于45分贝。",
            "content": "1. 支持3档风速调节\n2. 通风噪音≤45dB\n3. 通风面积覆盖座椅背部和座垫",
            "status": "completed"
        },
        {
            "title": "座椅按摩功能需求",
            "description": "座椅具备多模式按摩和定时功能。",
            "content": "1. 支持揉捏、敲击、振动三种按摩模式\n2. 支持10/30分钟定时\n3. 按摩强度可调",
            "status": "completed"
        },
        {
            "title": "座椅安全功能需求",
            "description": "碰撞自动回位，安全带未系时调节受限。",
            "content": "1. 碰撞时座椅自动回位\n2. 安全带未系时座椅调节受限\n3. 回位时间≤2秒",
            "status": "completed"
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

    # 0.5 生成知识库数据
    print("\n0.5 生成知识库数据...")
    knowledge_items = [
        {
            "category": "seat_functions",
            "subcategory": "memory",
            "title": "座椅记忆功能原理",
            "content": "座椅记忆功能通过电机和位置传感器记录并恢复用户设定的座椅位置。",
            "tags": ["记忆", "电机", "传感器"],
            "source": "行业标准",
            "confidence": 0.98
        },
        {
            "category": "seat_functions",
            "subcategory": "heating",
            "title": "座椅加热安全要求",
            "content": "加热功能需具备过热保护，温度传感器实时监控，防止烫伤。",
            "tags": ["加热", "安全", "温度传感器"],
            "source": "企业规范",
            "confidence": 0.95
        },
        {
            "category": "test_standards",
            "subcategory": "performance",
            "title": "座椅性能测试标准",
            "content": "座椅性能测试包括耐久性、舒适性、调节速度等多项指标。",
            "tags": ["性能", "测试", "标准"],
            "source": "GB/T 12345-2020",
            "confidence": 0.97
        },
        {
            "category": "failure_modes",
            "subcategory": "heating",
            "title": "加热功能常见失效模式",
            "content": "常见失效包括加热不均、温控失灵、过热保护失效等。",
            "tags": ["加热", "失效模式"],
            "source": "经验总结",
            "confidence": 0.92
        },
        {
            "category": "seat_functions",
            "subcategory": "ventilation",
            "title": "座椅通风系统结构",
            "content": "通风系统由风扇、风道和控制单元组成，保证座椅通风效果。",
            "tags": ["通风", "结构", "风扇"],
            "source": "技术手册",
            "confidence": 0.96
        }
    ]
    for kb in knowledge_items:
        try:
            response = requests.post(f"{base_url}/api/v1/knowledge/", json=kb, headers=headers)
            if response.status_code == 200:
                print(f"✅ 知识库 '{kb['title']}' 创建成功")
            else:
                print(f"❌ 创建知识库 '{kb['title']}' 失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建知识库失败: {e}")

    # 0.6 生成模板数据
    print("\n0.6 生成模板数据...")
    templates = [
        {
            "name": "功能测试基础模板",
            "category": "function",
            "description": "用于测试功能基本实现的标准模板",
            "template_content": """测试标题: {function_name}基本功能测试
测试类型: 功能测试
优先级: {priority}
前置条件: {preconditions}
测试步骤:
1. {step1}
2. {step2}
3. {step3}
预期结果: {expected_result}""",
            "variables": {
                "function_name": "功能名称",
                "priority": "high",
                "preconditions": "系统正常启动",
                "step1": "打开功能控制界面",
                "step2": "执行功能操作",
                "step3": "验证功能结果",
                "expected_result": "功能正常工作"
            }
        },
        {
            "name": "边界值测试模板",
            "category": "boundary",
            "description": "用于测试边界条件的标准模板",
            "template_content": """测试标题: {function_name}边界值测试
测试类型: 边界测试
优先级: {priority}
前置条件: {preconditions}
测试步骤:
1. 设置参数为最小值 {min_value}
2. 执行功能操作
3. 设置参数为最大值 {max_value}
4. 执行功能操作
5. 设置参数为临界值 {critical_value}
6. 执行功能操作
预期结果: 所有边界值都能正常处理""",
            "variables": {
                "function_name": "功能名称",
                "priority": "medium",
                "preconditions": "系统正常启动",
                "min_value": "0",
                "max_value": "100",
                "critical_value": "50"
            }
        },
        {
            "name": "异常测试模板",
            "category": "exception",
            "description": "用于测试异常情况处理的标准模板",
            "template_content": """测试标题: {function_name}异常测试
测试类型: 异常测试
优先级: {priority}
前置条件: {preconditions}
测试步骤:
1. 模拟异常情况 {exception_scenario}
2. 执行功能操作
3. 观察系统响应
4. 检查错误处理
预期结果: 系统正确处理异常，不崩溃""",
            "variables": {
                "function_name": "功能名称",
                "priority": "high",
                "preconditions": "系统正常启动",
                "exception_scenario": "网络中断"
            }
        },
        {
            "name": "性能测试模板",
            "category": "performance",
            "description": "用于测试性能指标的标准模板",
            "template_content": """测试标题: {function_name}性能测试
测试类型: 性能测试
优先级: {priority}
前置条件: {preconditions}
测试步骤:
1. 启动性能监控工具
2. 执行功能操作 {operation_count} 次
3. 记录响应时间
4. 检查资源使用情况
预期结果: 响应时间不超过 {max_response_time}ms，资源使用正常""",
            "variables": {
                "function_name": "功能名称",
                "priority": "medium",
                "preconditions": "系统正常启动",
                "operation_count": "100",
                "max_response_time": "5000"
            }
        },
        {
            "name": "安全测试模板",
            "category": "security",
            "description": "用于测试安全性的标准模板",
            "template_content": """测试标题: {function_name}安全测试
测试类型: 安全测试
优先级: {priority}
前置条件: {preconditions}
测试步骤:
1. 尝试未授权访问
2. 输入恶意数据 {malicious_input}
3. 测试权限控制
4. 检查安全日志
预期结果: 系统拒绝未授权访问，正确处理恶意输入""",
            "variables": {
                "function_name": "功能名称",
                "priority": "high",
                "preconditions": "系统正常启动",
                "malicious_input": "SQL注入测试"
            }
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
    
    # 2. 创建测试用例
    print("\n2. 创建测试用例...")
    test_cases = [
        {
            "title": "记忆功能基本功能测试",
            "description": "测试座椅记忆功能的基本存储和调用功能",
            "test_type": "function",
            "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 记忆功能已激活",
            "test_steps": """1. 打开记忆功能控制界面
2. 选择记忆位置1
3. 调整座椅到期望位置（前后200mm，上下50mm，靠背120度）
4. 点击存储按钮
5. 将座椅调整到其他位置
6. 选择记忆位置1并点击调用
7. 观察座椅是否自动调节到存储位置""",
            "expected_result": "座椅位置成功存储，调用时座椅自动调节到存储位置，调节时间不超过5秒",
            "priority": "high",
            "requirement_id": 4
        },
        {
            "title": "记忆功能边界值测试",
            "description": "测试记忆功能在边界条件下的表现",
            "test_type": "boundary",
            "preconditions": "1. 系统正常启动\n2. 记忆功能已激活",
            "test_steps": """1. 设置前后位置为最小值0mm
2. 存储记忆位置
3. 设置前后位置为最大值250mm
4. 存储记忆位置
5. 设置上下位置为最小值0mm
6. 存储记忆位置
7. 设置上下位置为最大值80mm
8. 存储记忆位置
9. 设置靠背角度为最小值90度
10. 存储记忆位置
11. 设置靠背角度为最大值160度
12. 存储记忆位置""",
            "expected_result": "所有边界值都能正常存储和调用，系统不报错",
            "priority": "medium",
            "requirement_id": 4
        },
        {
            "title": "记忆功能异常测试",
            "description": "测试记忆功能在异常情况下的处理",
            "test_type": "exception",
            "preconditions": "1. 系统正常启动\n2. 记忆功能已激活",
            "test_steps": """1. 在调节过程中突然断电
2. 重新上电后检查记忆数据
3. 尝试调用记忆位置
4. 在存储过程中突然断电
5. 重新上电后检查记忆数据
6. 尝试存储新的记忆位置""",
            "expected_result": "断电后记忆数据保持，重新上电后功能正常",
            "priority": "high",
            "requirement_id": 4
        },
        {
            "title": "加热功能基本功能测试",
            "description": "测试座椅加热功能的基本加热和温度调节",
            "test_type": "function",
            "preconditions": "1. 系统正常启动\n2. 加热功能已激活\n3. 环境温度25度",
            "test_steps": """1. 打开加热功能控制界面
2. 选择低档加热
3. 启动加热功能
4. 观察加热指示灯
5. 等待30秒后检查座椅温度
6. 切换到中档加热
7. 等待30秒后检查座椅温度
8. 切换到高档加热
9. 等待30秒后检查座椅温度""",
            "expected_result": "加热功能正常启动，温度逐渐升高，各档位温度差异明显",
            "priority": "high",
            "requirement_id": 5
        },
        {
            "title": "加热功能温度范围测试",
            "description": "测试加热功能的温度范围和精度",
            "test_type": "boundary",
            "preconditions": "1. 系统正常启动\n2. 加热功能已激活\n3. 温度传感器正常",
            "test_steps": """1. 设置加热温度为最小值25度
2. 启动加热功能
3. 等待温度稳定后记录实际温度
4. 设置加热温度为最大值45度
5. 启动加热功能
6. 等待温度稳定后记录实际温度
7. 设置加热温度为中间值35度
8. 启动加热功能
9. 等待温度稳定后记录实际温度""",
            "expected_result": "实际温度与设定温度误差在±2度范围内",
            "priority": "medium",
            "requirement_id": 5
        },
        {
            "title": "加热功能过热保护测试",
            "description": "测试加热功能的过热保护机制",
            "test_type": "security",
            "preconditions": "1. 系统正常启动\n2. 加热功能已激活\n3. 过热保护功能正常",
            "test_steps": """1. 设置加热温度为45度
2. 启动加热功能
3. 持续加热直到触发过热保护
4. 观察过热保护指示灯
5. 检查加热功能是否自动停止
6. 等待冷却后重新启动加热功能""",
            "expected_result": "过热保护正常触发，加热功能自动停止，冷却后可重新启动",
            "priority": "high",
            "requirement_id": 5
        },
        {
            "title": "通风功能基本功能测试",
            "description": "测试座椅通风功能的基本通风和风速调节",
            "test_type": "function",
            "preconditions": "1. 系统正常启动\n2. 通风功能已激活\n3. 通风风扇正常",
            "test_steps": """1. 打开通风功能控制界面
2. 选择低档风速
3. 启动通风功能
4. 观察通风指示灯
5. 检查座椅背部和座垫通风效果
6. 切换到中档风速
7. 检查通风效果
8. 切换到高档风速
9. 检查通风效果""",
            "expected_result": "通风功能正常启动，各档位风速差异明显，通风面积覆盖座椅背部和座垫",
            "priority": "high",
            "requirement_id": 6
        },
        {
            "title": "通风功能噪音测试",
            "description": "测试通风功能的噪音控制",
            "test_type": "performance",
            "preconditions": "1. 系统正常启动\n2. 通风功能已激活\n3. 噪音测试设备正常",
            "test_steps": """1. 启动低档通风
2. 测量噪音水平
3. 启动中档通风
4. 测量噪音水平
5. 启动高档通风
6. 测量噪音水平
7. 记录各档位噪音数据""",
            "expected_result": "所有档位噪音控制在45分贝以下",
            "priority": "medium",
            "requirement_id": 6
        },
        {
            "title": "按摩功能基本功能测试",
            "description": "测试座椅按摩功能的基本按摩和模式调节",
            "test_type": "function",
            "preconditions": "1. 系统正常启动\n2. 按摩功能已激活\n3. 按摩机构正常",
            "test_steps": """1. 打开按摩功能控制界面
2. 选择按摩模式1（揉捏）
3. 设置按摩强度为低档
4. 启动按摩功能
5. 观察按摩效果
6. 切换到按摩模式2（敲击）
7. 设置按摩强度为中档
8. 观察按摩效果
9. 切换到按摩模式3（振动）
10. 设置按摩强度为高档
11. 观察按摩效果""",
            "expected_result": "按摩功能正常启动，各模式按摩效果明显，强度调节有效",
            "priority": "medium",
            "requirement_id": 7
        },
        {
            "title": "按摩功能定时测试",
            "description": "测试按摩功能的定时功能",
            "test_type": "function",
            "preconditions": "1. 系统正常启动\n2. 按摩功能已激活\n3. 定时功能正常",
            "test_steps": """1. 选择按摩模式1
2. 设置按摩时间为10分钟
3. 启动按摩功能
4. 观察定时器显示
5. 等待按摩自动停止
6. 设置按摩时间为30分钟
7. 启动按摩功能
8. 观察定时器显示
9. 等待按摩自动停止""",
            "expected_result": "定时功能正常工作，按摩在设定时间后自动停止",
            "priority": "medium",
            "requirement_id": 7
        },
        {
            "title": "安全功能碰撞保护测试",
            "description": "测试座椅在碰撞时的自动回位功能",
            "test_type": "security",
            "preconditions": "1. 系统正常启动\n2. 碰撞传感器正常\n3. 座椅位置已调节",
            "test_steps": """1. 将座椅调节到非默认位置
2. 模拟碰撞信号
3. 观察座椅是否自动回位
4. 检查回位速度和位置
5. 重复测试多次
6. 检查碰撞后功能恢复""",
            "expected_result": "碰撞时座椅自动回位到安全位置，回位时间不超过2秒",
            "priority": "high",
            "requirement_id": 8
        },
        {
            "title": "安全功能安全带检测测试",
            "description": "测试安全带未系时座椅调节受限功能",
            "test_type": "security",
            "preconditions": "1. 系统正常启动\n2. 安全带传感器正常\n3. 座椅调节功能正常",
            "test_steps": """1. 确保安全带未系
2. 尝试调节座椅前后位置
3. 观察调节是否受限
4. 尝试调节座椅上下位置
5. 观察调节是否受限
6. 系上安全带
7. 尝试调节座椅位置
8. 观察调节是否正常""",
            "expected_result": "安全带未系时座椅调节受限，系上安全带后调节正常",
            "priority": "high",
            "requirement_id": 8
        }
    ]
    
    created_test_cases = []
    for tc in test_cases:
        try:
            response = requests.post(f"{base_url}/api/v1/test-cases/", json=tc, headers=headers)
            if response.status_code == 200:
                tc_data = response.json()
                created_test_cases.append(tc_data["id"])
                print(f"✅ 测试用例 '{tc['title']}' 创建成功 (ID: {tc_data['id']})")
            else:
                print(f"❌ 创建测试用例 '{tc['title']}' 失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建测试用例失败: {e}")
    
    # 3. 为测试用例生成评估数据
    print("\n3. 生成测试用例评估数据...")
    for tc_id in created_test_cases:
        try:
            # 生成随机评估分数
            completeness_score = random.uniform(80, 95)
            accuracy_score = random.uniform(85, 95)
            executability_score = random.uniform(80, 90)
            coverage_score = random.uniform(75, 90)
            clarity_score = random.uniform(80, 95)
            total_score = (completeness_score + accuracy_score + executability_score + coverage_score + clarity_score) / 5
            
            evaluation_data = {
                "test_case_id": tc_id,
                "completeness_score": round(completeness_score, 1),
                "accuracy_score": round(accuracy_score, 1),
                "executability_score": round(executability_score, 1),
                "coverage_score": round(coverage_score, 1),
                "clarity_score": round(clarity_score, 1),
                "total_score": round(total_score, 1),
                "evaluation_details": {
                    "strengths": [
                        "测试步骤详细清晰",
                        "预期结果具体明确",
                        "前置条件完整"
                    ],
                    "weaknesses": [
                        "可以增加更多边界条件测试",
                        "建议添加异常场景测试"
                    ]
                },
                "suggestions": [
                    "建议增加更多边界值测试用例",
                    "可以添加性能测试相关内容",
                    "建议完善异常处理测试"
                ],
                "evaluator_type": "ai"
            }
            
            response = requests.post(f"{base_url}/api/v1/test-cases/{tc_id}/evaluate", json=evaluation_data, headers=headers)
            if response.status_code == 200:
                print(f"✅ 测试用例 {tc_id} 评估数据生成成功")
            else:
                print(f"❌ 测试用例 {tc_id} 评估数据生成失败: {response.text}")
        except Exception as e:
            print(f"❌ 生成评估数据失败: {e}")
    
    # 4. 生成生成历史记录
    print("\n4. 生成生成历史记录...")
    generation_history = [
        {
            "requirement_id": 4,
            "generation_type": "test_cases",
            "status": "completed",
            "generated_count": 3,
            "processing_time": 25,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "requirement_id": 5,
            "generation_type": "test_cases",
            "status": "completed",
            "generated_count": 3,
            "processing_time": 28,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "requirement_id": 6,
            "generation_type": "test_cases",
            "status": "completed",
            "generated_count": 2,
            "processing_time": 22,
            "created_at": (datetime.now() - timedelta(hours=12)).isoformat()
        },
        {
            "requirement_id": 7,
            "generation_type": "test_cases",
            "status": "completed",
            "generated_count": 2,
            "processing_time": 20,
            "created_at": (datetime.now() - timedelta(hours=6)).isoformat()
        },
        {
            "requirement_id": 8,
            "generation_type": "test_cases",
            "status": "completed",
            "generated_count": 2,
            "processing_time": 30,
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
        }
    ]
    
    for history in generation_history:
        try:
            response = requests.post(f"{base_url}/api/v1/generation/history", json=history, headers=headers)
            if response.status_code == 200:
                print(f"✅ 生成历史记录创建成功")
            else:
                print(f"❌ 创建生成历史记录失败: {response.text}")
        except Exception as e:
            print(f"❌ 创建生成历史记录失败: {e}")
    
    print("\n🎉 完整示例数据生成完成！")
    print(f"\n📊 数据统计:")
    print(f"- 测试用例: {len(created_test_cases)} 个")
    print(f"- 评估数据: {len(created_test_cases)} 个")
    print(f"- 生成历史: {len(generation_history)} 条")
    print(f"\n🔗 访问地址:")
    print(f"- 前端应用: http://localhost:3000")
    print(f"- 后端API: http://localhost:8000")
    print(f"- API文档: http://localhost:8000/docs")
    print(f"\n👤 测试账号:")
    print(f"- 用户名: admin, 密码: admin123")

if __name__ == "__main__":
    generate_sample_data() 