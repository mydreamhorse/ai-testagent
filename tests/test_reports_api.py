import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from backend.main import app
from backend.models import Report, ReportTemplate, User
from backend.database import get_db
from backend.routers.auth import get_current_user
from tests.conftest import TestingSessionLocal, override_get_db

# Mock authentication for testing
def mock_get_current_user():
    """Mock current user for testing"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )

# Override the dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

class TestReportsAPI:
    """测试报告管理API"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.db = TestingSessionLocal()
        
        # 创建测试报告模板
        self.test_template = ReportTemplate(
            template_name="测试报告模板",
            template_type="execution",
            template_content="<html><body>{{content}}</body></html>",
            template_config={"charts": ["bar", "pie"]},
            created_by=1,  # Mock user ID
            is_default=True
        )
        self.db.add(self.test_template)
        self.db.commit()
        self.db.refresh(self.test_template)
        
        # 模拟用户认证（不需要实际的token，因为我们已经mock了认证）
        self.auth_headers = {}
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        self.db.close()
    
    def test_get_reports_list(self):
        """测试获取报告列表"""
        # 创建测试报告
        test_report = Report(
            title="测试执行报告",
            report_type="execution",
            template_id=self.test_template.id,
            generated_by=1,  # Mock user ID
            status="completed",
            report_data={"test_count": 10, "pass_rate": 0.8}
        )
        self.db.add(test_report)
        self.db.commit()
        
        # 测试获取报告列表
        response = client.get(
            "/api/v1/reports/",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reports" in data["data"]
        assert len(data["data"]["reports"]) >= 1
        assert data["data"]["reports"][0]["title"] == "测试执行报告"
    
    def test_get_reports_with_filters(self):
        """测试带过滤条件的报告列表"""
        # 创建不同类型的报告
        reports = [
            Report(
                title="执行报告1",
                report_type="execution",
                generated_by=1,  # Mock user ID
                status="completed"
            ),
            Report(
                title="缺陷分析报告1",
                report_type="defect_analysis",
                generated_by=1,  # Mock user ID
                status="generating"
            )
        ]
        
        for report in reports:
            self.db.add(report)
        self.db.commit()
        
        # 测试按类型过滤
        response = client.get(
            "/api/v1/reports/?report_type=execution",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["reports"]) == 1
        assert data["data"]["reports"][0]["report_type"] == "execution"
        
        # 测试按状态过滤
        response = client.get(
            "/api/v1/reports/?status=generating",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["reports"]) == 1
        assert data["data"]["reports"][0]["status"] == "generating"
    
    def test_get_single_report(self):
        """测试获取单个报告详情"""
        # 创建测试报告
        test_report = Report(
            title="详细测试报告",
            report_type="coverage",
            generated_by=1,  # Mock user ID
            status="completed",
            report_data={"coverage_rate": 0.85, "modules": ["module1", "module2"]}
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 测试获取报告详情
        response = client.get(
            f"/api/v1/reports/{test_report.id}",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "详细测试报告"
        assert data["data"]["report_data"]["coverage_rate"] == 0.85
    
    def test_get_nonexistent_report(self):
        """测试获取不存在的报告"""
        response = client.get(
            "/api/v1/reports/99999",
            headers=self.auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "报告不存在" in data["detail"]
    
    def test_create_report(self):
        """测试创建报告"""
        report_data = {
            "title": "新建测试报告",
            "report_type": "execution",
            "template_id": self.test_template.id,
            "data_range_start": "2024-01-01T00:00:00",
            "data_range_end": "2024-01-31T23:59:59",
            "report_data": {"initial": "data"}
        }
        
        response = client.post(
            "/api/v1/reports/",
            json=report_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "新建测试报告"
        assert data["data"]["status"] == "created"
        
        # 验证数据库中的记录
        db_report = self.db.query(Report).filter(
            Report.title == "新建测试报告"
        ).first()
        assert db_report is not None
        assert db_report.generated_by == 1  # Mock user ID
    
    def test_create_report_with_invalid_template(self):
        """测试使用无效模板创建报告"""
        report_data = {
            "title": "无效模板报告",
            "report_type": "execution",
            "template_id": 99999  # 不存在的模板ID
        }
        
        response = client.post(
            "/api/v1/reports/",
            json=report_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "报告模板不存在" in data["detail"]
    
    def test_update_report(self):
        """测试更新报告"""
        # 创建测试报告
        test_report = Report(
            title="原始标题",
            report_type="execution",
            generated_by=1,  # Mock user ID
            status="generating"
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 更新报告
        update_data = {
            "title": "更新后的标题",
            "status": "completed",
            "report_data": {"updated": "data"}
        }
        
        response = client.put(
            f"/api/v1/reports/{test_report.id}",
            json=update_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "更新后的标题"
        assert data["data"]["status"] == "completed"
        
        # 验证数据库更新
        self.db.refresh(test_report)
        assert test_report.title == "更新后的标题"
        assert test_report.status == "completed"
    
    def test_delete_report(self):
        """测试删除报告"""
        # 创建测试报告
        test_report = Report(
            title="待删除报告",
            report_type="execution",
            generated_by=1  # Mock user ID
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 删除报告
        response = client.delete(
            f"/api/v1/reports/{test_report.id}",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "删除成功" in data["message"]
        
        # 验证数据库中已删除
        deleted_report = self.db.query(Report).filter(
            Report.id == test_report.id
        ).first()
        assert deleted_report is None
    
    def test_generate_report_async(self):
        """测试异步生成报告"""
        generation_request = {
            "report_type": "execution",
            "title": "异步生成报告",
            "template_id": self.test_template.id,
            "data_range_start": "2024-01-01T00:00:00",
            "data_range_end": "2024-01-31T23:59:59",
            "filters": {"priority": "high"},
            "export_format": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate",
            json=generation_request,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "生成任务已启动" in data["message"]
        assert "report_id" in data["data"]
        assert data["data"]["status"] == "generating"
        
        # 验证数据库中创建了报告记录
        report_id = data["data"]["report_id"]
        db_report = self.db.query(Report).filter(Report.id == report_id).first()
        assert db_report is not None
        assert db_report.status == "generating"
    
    def test_export_report(self):
        """测试导出报告"""
        # 创建已完成的报告
        test_report = Report(
            title="导出测试报告",
            report_type="execution",
            generated_by=1,  # Mock user ID
            status="completed",
            report_data={"test_results": "data"}
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 测试导出
        response = client.get(
            f"/api/v1/reports/{test_report.id}/export?format=pdf",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "导出成功" in data["message"]
        assert data["data"]["format"] == "pdf"
    
    def test_export_incomplete_report(self):
        """测试导出未完成的报告"""
        # 创建未完成的报告
        test_report = Report(
            title="未完成报告",
            report_type="execution",
            generated_by=1,  # Mock user ID
            status="generating"
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 尝试导出
        response = client.get(
            f"/api/v1/reports/{test_report.id}/export?format=pdf",
            headers=self.auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "尚未生成完成" in data["detail"]
    
    def test_share_report(self):
        """测试分享报告"""
        # 创建测试报告
        test_report = Report(
            title="分享测试报告",
            report_type="execution",
            generated_by=self.test_user.id,
            status="completed"
        )
        self.db.add(test_report)
        self.db.commit()
        self.db.refresh(test_report)
        
        # 分享报告
        share_request = {
            "report_id": test_report.id,
            "share_via_link": True,
            "expiry_date": "2024-12-31T23:59:59"
        }
        
        response = client.post(
            "/api/v1/reports/share",
            json=share_request,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "分享成功" in data["message"]
        assert "share_token" in data["data"]
        assert "share_url" in data["data"]
    
    def test_invalid_report_type(self):
        """测试无效的报告类型"""
        report_data = {
            "title": "无效类型报告",
            "report_type": "invalid_type"  # 无效类型
        }
        
        response = client.post(
            "/api/v1/reports/",
            json=report_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_pagination(self):
        """测试分页功能"""
        # 创建多个报告
        for i in range(15):
            report = Report(
                title=f"报告{i+1}",
                report_type="execution",
                generated_by=self.test_user.id
            )
            self.db.add(report)
        self.db.commit()
        
        # 测试第一页
        response = client.get(
            "/api/v1/reports/?skip=0&limit=10",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["reports"]) == 10
        assert data["data"]["total"] == 15
        
        # 测试第二页
        response = client.get(
            "/api/v1/reports/?skip=10&limit=10",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["reports"]) == 5
        assert data["data"]["total"] == 15