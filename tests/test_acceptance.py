"""
智能测试报告系统验收测试
"""

import pytest
import requests
import time
import json
from typing import Dict, Any
import os
import subprocess

# 测试配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_PREFIX = "/api/v1"
TEST_USER = {"username": "admin", "password": "admin123"}

class TestSystemAcceptance:
    """系统验收测试类"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """获取认证token"""
        # First try to register the user
        try:
            register_response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json={
                "username": TEST_USER["username"],
                "email": "admin@example.com",
                "password": TEST_USER["password"]
            })
        except:
            pass  # User might already exist
        
        # Login with form data (OAuth2PasswordRequestForm)
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """认证请求头"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

class TestReportGeneration(TestSystemAcceptance):
    """报告生成功能验收测试"""
    
    def test_generate_execution_report(self, auth_headers):
        """测试生成测试执行报告"""
        # 准备测试数据
        report_data = {
            "report_type": "execution",
            "title": "验收测试执行报告",
            "time_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
        }
        
        # 生成报告
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            headers=auth_headers,
            json=report_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "report_id" in result["data"]
        
        report_id = result["data"]["report_id"]
        
        # 等待报告生成完成
        max_wait = 60  # 最大等待60秒
        wait_time = 0
        
        while wait_time < max_wait:
            status_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/reports/{report_id}",
                headers=auth_headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["data"]["status"] == "completed":
                    break
                elif status_data["data"]["status"] == "failed":
                    pytest.fail("报告生成失败")
            
            time.sleep(2)
            wait_time += 2
        
        assert wait_time < max_wait, "报告生成超时"
        
        # 验证报告内容
        report_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/reports/{report_id}",
            headers=auth_headers
        )
        
        assert report_response.status_code == 200
        report = report_response.json()["data"]
        assert report["status"] == "completed"
        assert report["report_type"] == "execution"
        assert "report_data" in report
    
    def test_generate_defect_analysis_report(self, auth_headers):
        """测试生成缺陷分析报告"""
        report_data = {
            "report_type": "defect_analysis",
            "title": "缺陷分析报告",
            "time_range": {
                "start": "2024-01-01", 
                "end": "2024-01-31"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            headers=auth_headers,
            json=report_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_generate_coverage_report(self, auth_headers):
        """测试生成覆盖率分析报告"""
        report_data = {
            "report_type": "coverage",
            "title": "覆盖率分析报告",
            "time_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            headers=auth_headers,
            json=report_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_export_report_pdf(self, auth_headers):
        """测试导出PDF格式报告"""
        # 先生成一个报告
        report_data = {
            "report_type": "execution",
            "title": "PDF导出测试报告"
        }
        
        gen_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            headers=auth_headers,
            json=report_data
        )
        
        report_id = gen_response.json()["data"]["report_id"]
        
        # 等待报告完成
        time.sleep(10)
        
        # 导出PDF
        export_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/reports/{report_id}/export?format=pdf",
            headers=auth_headers
        )
        
        assert export_response.status_code == 200
        assert export_response.headers["content-type"] == "application/pdf"

class TestDataAnalytics(TestSystemAcceptance):
    """数据分析功能验收测试"""
    
    def test_get_statistics(self, auth_headers):
        """测试获取统计数据"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analytics/stats?metric=coverage&period=30d",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
    
    def test_get_trend_analysis(self, auth_headers):
        """测试获取趋势分析"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analytics/trends?type=defects&range=30d",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "trend_data" in result["data"]
    
    def test_get_intelligent_suggestions(self, auth_headers):
        """测试获取智能建议"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analytics/suggestions?context=optimization",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "suggestions" in result["data"]

class TestMonitoring(TestSystemAcceptance):
    """监控功能验收测试"""
    
    def test_system_health_check(self, auth_headers):
        """测试系统健康检查"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/monitoring/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["overall_status"] in ["healthy", "warning", "critical"]
    
    def test_get_metrics(self, auth_headers):
        """测试获取监控指标"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/monitoring/metrics?metric=response_time&period=1h",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data_points" in result["data"]
    
    def test_create_alert_rule(self, auth_headers):
        """测试创建告警规则"""
        alert_data = {
            "rule_name": "测试告警规则",
            "metric_type": "error_rate",
            "condition": {
                "operator": "greater_than",
                "threshold": 0.1,
                "duration": "5m"
            },
            "severity": "warning",
            "notification_channels": ["email"],
            "is_active": True
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/monitoring/alerts",
            headers=auth_headers,
            json=alert_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

class TestTemplateManagement(TestSystemAcceptance):
    """模板管理功能验收测试"""
    
    def test_create_template(self, auth_headers):
        """测试创建报告模板"""
        template_data = {
            "template_name": "验收测试模板",
            "template_type": "execution",
            "template_content": "<html><body>{{content}}</body></html>",
            "template_config": {
                "sections": ["summary", "details"]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/templates",
            headers=auth_headers,
            json=template_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "template_id" in result["data"]
    
    def test_get_templates(self, auth_headers):
        """测试获取模板列表"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/templates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "items" in result["data"]

class TestFrontendIntegration:
    """前端集成验收测试"""
    
    def test_frontend_accessibility(self):
        """测试前端页面可访问性"""
        response = requests.get(FRONTEND_URL)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_api_integration(self):
        """测试前端API集成"""
        # 这里可以使用Selenium等工具进行更详细的前端测试
        # 目前只做基础的可访问性测试
        pass

class TestPerformance(TestSystemAcceptance):
    """性能验收测试"""
    
    def test_api_response_time(self, auth_headers):
        """测试API响应时间"""
        start_time = time.time()
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/reports",
            headers=auth_headers
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        assert response.status_code == 200
        assert response_time < 2000, f"API响应时间过长: {response_time}ms"
    
    def test_concurrent_requests(self, auth_headers):
        """测试并发请求处理"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/monitoring/status",
                headers=auth_headers
            )
            return response.status_code == 200
        
        # 并发发送10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 所有请求都应该成功
        assert all(results), "并发请求处理失败"

class TestDataIntegrity(TestSystemAcceptance):
    """数据完整性验收测试"""
    
    def test_database_consistency(self, auth_headers):
        """测试数据库数据一致性"""
        # 创建测试数据
        report_data = {
            "report_type": "execution",
            "title": "数据一致性测试报告"
        }
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/reports/generate",
            headers=auth_headers,
            json=report_data
        )
        
        report_id = response.json()["data"]["report_id"]
        
        # 验证数据是否正确存储
        get_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/reports/{report_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        report = get_response.json()["data"]
        assert report["title"] == report_data["title"]
        assert report["report_type"] == report_data["report_type"]

def run_acceptance_tests():
    """运行验收测试"""
    print("🧪 开始执行验收测试...")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未运行，请先启动服务")
            return False
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请检查服务状态")
        return False
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code != 200:
            print("❌ 前端服务未运行，请先启动服务")
            return False
    except requests.exceptions.RequestException:
        print("❌ 无法连接到前端服务，请检查服务状态")
        return False
    
    # 运行pytest测试
    result = subprocess.run([
        "python", "-m", "pytest", 
        "tests/test_acceptance.py", 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 验收测试全部通过")
        return True
    else:
        print("❌ 验收测试失败")
        print(result.stdout)
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = run_acceptance_tests()
    exit(0 if success else 1)