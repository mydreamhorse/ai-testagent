#!/usr/bin/env python3
"""
综合端到端测试 - 验证完整系统功能
"""

import pytest
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """获取认证headers"""
    # 注册测试用户
    user_data = {
        "username": "finaltest",
        "email": "finaltest@example.com",
        "password": "test123456"
    }
    
    # 注册用户
    response = client.post("/api/v1/auth/register", json=user_data)
    if response.status_code != 200:
        # 如果用户已存在，直接登录
        pass
    
    # 登录用户
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200, f"登录失败: {response.text}"
    
    token_data = response.json()
    token = token_data["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_requirement_id(client, auth_headers):
    """创建测试需求并返回ID"""
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
    
    response = client.post("/api/v1/requirements/", json=requirement_data, headers=auth_headers)
    assert response.status_code == 200, f"创建需求失败: {response.text}"
    requirement = response.json()
    return requirement["id"]

def test_system_health(client):
    """测试系统健康检查"""
    response = client.get("/health")
    assert response.status_code == 200, f"健康检查失败: {response.text}"

def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200, f"根端点失败: {response.text}"
    data = response.json()
    assert "message" in data

def test_user_registration_and_login(client):
    """测试用户注册和登录"""
    user_data = {
        "username": "finaltest",
        "email": "finaltest@example.com",
        "password": "test123456"
    }
    
    # 注册用户
    response = client.post("/api/v1/auth/register", json=user_data)
    if response.status_code == 400 and "already registered" in response.text:
        # 用户已存在，直接登录
        pass
    else:
        assert response.status_code == 200, f"用户注册失败: {response.text}"
        user = response.json()
        assert user["username"] == user_data["username"]
    
    # 登录用户
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200, f"用户登录失败: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data

def test_requirement_management(client, auth_headers):
    """测试需求管理"""
    # 获取需求列表
    response = client.get("/api/v1/requirements/", headers=auth_headers)
    assert response.status_code == 200, f"获取需求列表失败: {response.text}"
    requirements = response.json()
    assert isinstance(requirements, list)

def test_requirement_parsing(client, auth_headers, test_requirement_id):
    """测试需求解析"""
    response = client.post(f"/api/v1/requirements/{test_requirement_id}/parse", headers=auth_headers)
    assert response.status_code == 200, f"需求解析失败: {response.text}"
    parse_result = response.json()
    assert "data" in parse_result
    assert "features_count" in parse_result["data"]
    
    # 验证特征被保存
    response = client.get(f"/api/v1/requirements/{test_requirement_id}/features", headers=auth_headers)
    assert response.status_code == 200, f"获取特征失败: {response.text}"
    features = response.json()
    assert isinstance(features, list)

def test_test_case_generation(client, auth_headers, test_requirement_id):
    """测试测试用例生成"""
    # 先生成特征
    response = client.post(f"/api/v1/requirements/{test_requirement_id}/parse", headers=auth_headers)
    assert response.status_code == 200, f"需求解析失败: {response.text}"
    
    generation_data = {
        "requirement_id": test_requirement_id,
        "generation_type": "test_cases",
        "options": {
            "test_types": ["function", "boundary", "exception", "security"]
        }
    }
    
    response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=auth_headers)
    assert response.status_code == 200, f"测试用例生成失败: {response.text}"
    generation_result = response.json()
    assert "message" in generation_result
    
    # 验证测试用例被创建
    response = client.get(f"/api/v1/test-cases/?requirement_id={test_requirement_id}", headers=auth_headers)
    assert response.status_code == 200, f"获取测试用例失败: {response.text}"
    test_cases = response.json()
    assert isinstance(test_cases, list)
    assert len(test_cases) > 0

def test_quality_evaluation(client, auth_headers, test_requirement_id):
    """测试质量评估"""
    # 先生成特征
    response = client.post(f"/api/v1/requirements/{test_requirement_id}/parse", headers=auth_headers)
    assert response.status_code == 200, f"需求解析失败: {response.text}"
    
    # 先生成测试用例
    generation_data = {
        "requirement_id": test_requirement_id,
        "generation_type": "test_cases"
    }
    response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=auth_headers)
    assert response.status_code == 200
    
    # 获取测试用例
    response = client.get(f"/api/v1/test-cases/?requirement_id={test_requirement_id}", headers=auth_headers)
    assert response.status_code == 200
    test_cases = response.json()
    assert len(test_cases) > 0
    
    # 评估单个测试用例
    test_case_id = test_cases[0]["id"]
    response = client.post(f"/api/v1/test-cases/{test_case_id}/evaluate", headers=auth_headers)
    assert response.status_code == 200, f"测试用例评估失败: {response.text}"
    eval_result = response.json()
    assert "data" in eval_result
    assert "evaluation" in eval_result["data"]
    
    # 批量评估所有测试用例
    test_case_ids = [tc["id"] for tc in test_cases]
    response = client.post("/api/v1/test-cases/batch-evaluate", json=test_case_ids, headers=auth_headers)
    assert response.status_code == 200, f"批量评估失败: {response.text}"
    batch_result = response.json()
    assert "data" in batch_result
    assert "average_score" in batch_result["data"]

def test_full_generation_workflow(client, auth_headers, test_requirement_id):
    """测试完整生成工作流程"""
    # 先生成特征
    response = client.post(f"/api/v1/requirements/{test_requirement_id}/parse", headers=auth_headers)
    assert response.status_code == 200, f"需求解析失败: {response.text}"
    
    # 先生成测试用例
    generation_data = {
        "requirement_id": test_requirement_id,
        "generation_type": "test_cases"
    }
    response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=auth_headers)
    assert response.status_code == 200, f"测试用例生成失败: {response.text}"
    
    # 然后进行评估
    evaluation_data = {
        "requirement_id": test_requirement_id,
        "generation_type": "evaluation"
    }
    
    response = client.post("/api/v1/generation/evaluation", json=evaluation_data, headers=auth_headers)
    assert response.status_code == 200, f"完整评估失败: {response.text}"
    full_eval_result = response.json()
    assert "message" in full_eval_result

def test_generation_history(client, auth_headers):
    """测试生成历史"""
    response = client.get("/api/v1/generation/history", headers=auth_headers)
    assert response.status_code == 200, f"获取历史失败: {response.text}"
    history = response.json()
    assert isinstance(history, list)

def test_requirement_details(client, auth_headers, test_requirement_id):
    """测试需求详情"""
    response = client.get(f"/api/v1/requirements/{test_requirement_id}", headers=auth_headers)
    assert response.status_code == 200, f"获取需求详情失败: {response.text}"
    req_details = response.json()
    assert req_details["id"] == test_requirement_id

def test_data_completeness(client, auth_headers, test_requirement_id):
    """测试数据完整性"""
    # 先生成特征和测试用例
    response = client.post(f"/api/v1/requirements/{test_requirement_id}/parse", headers=auth_headers)
    assert response.status_code == 200, f"需求解析失败: {response.text}"
    
    generation_data = {
        "requirement_id": test_requirement_id,
        "generation_type": "test_cases"
    }
    response = client.post("/api/v1/generation/test-cases", json=generation_data, headers=auth_headers)
    assert response.status_code == 200, f"测试用例生成失败: {response.text}"
    
    # 获取测试用例
    response = client.get(f"/api/v1/test-cases/?requirement_id={test_requirement_id}", headers=auth_headers)
    assert response.status_code == 200
    test_cases = response.json()
    assert len(test_cases) > 0
    
    # 验证测试用例数据完整性
    for test_case in test_cases:
        assert "id" in test_case, "测试用例应该有ID"
        assert "title" in test_case, "测试用例应该有标题"
        assert "test_type" in test_case, "测试用例应该有类型"
        assert "test_steps" in test_case, "测试用例应该有测试步骤"
        assert "expected_result" in test_case, "测试用例应该有预期结果"
    
            # 检查测试用例详情
        test_case_id = test_cases[0]["id"]
        response = client.get(f"/api/v1/test-cases/{test_case_id}", headers=auth_headers)
        assert response.status_code == 200, f"获取测试用例详情失败: {response.text}"
        tc_details = response.json()
        assert tc_details["id"] == test_case_id
    
        # 先生成评估
        evaluation_data = {
            "requirement_id": test_requirement_id,
            "generation_type": "evaluation"
        }
        response = client.post("/api/v1/generation/evaluation", json=evaluation_data, headers=auth_headers)
        assert response.status_code == 200, f"生成评估失败: {response.text}"
    
                # 检查评估详情
        response = client.get(f"/api/v1/test-cases/{test_case_id}/evaluation", headers=auth_headers)
        assert response.status_code == 200, f"获取评估详情失败: {response.text}"
        eval_details = response.json()
        # 评估详情直接返回评估数据，不需要包装在data字段中
        assert "accuracy_score" in eval_details, "评估详情应该包含准确度分数"
        assert "total_score" in eval_details, "评估详情应该包含总分" 