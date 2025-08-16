import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from unittest.mock import patch

from backend.main import app
from backend.models import Alert, AlertRule, SystemMetric, User, Defect, CoverageAnalysis, TestCaseEvaluation
from backend.database import get_db
from backend.routers.auth import get_current_user
from tests.conftest import TestingSessionLocal, override_get_db

# Override the dependencies
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestMonitoringAPI:
    """测试监控和分析API"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.db = TestingSessionLocal()
        
        # 创建测试用户
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)
        
        # 模拟用户认证 - 覆盖get_current_user依赖
        def mock_get_current_user():
            return self.test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        # 模拟用户认证
        self.auth_headers = {"Authorization": "Bearer test_token"}
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理依赖覆盖
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        self.db.close()
    
    def test_create_alert_rule(self):
        """测试创建告警规则"""
        rule_data = {
            "rule_name": "覆盖率低告警",
            "metric_type": "coverage_rate",
            "condition_operator": "<",
            "threshold_value": 0.8,
            "severity": "high",
            "notification_channels": ["email", "in_app"],
            "description": "当覆盖率低于80%时触发告警"
        }
        
        response = client.post(
            "/api/v1/monitoring/alert-rules",
            json=rule_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["rule_name"] == "覆盖率低告警"
        assert data["data"]["threshold_value"] == 0.8
        
        # 验证数据库记录
        db_rule = self.db.query(AlertRule).filter(
            AlertRule.rule_name == "覆盖率低告警"
        ).first()
        assert db_rule is not None
        assert db_rule.created_by == self.test_user.id
    
    def test_get_alert_rules(self):
        """测试获取告警规则列表"""
        # 创建测试告警规则
        rules = [
            AlertRule(
                rule_name="规则1",
                metric_type="coverage_rate",
                condition_operator="<",
                threshold_value=0.8,
                created_by=self.test_user.id,
                is_active=True,
                notification_channels=["email", "in_app"]
            ),
            AlertRule(
                rule_name="规则2",
                metric_type="defect_rate",
                condition_operator=">",
                threshold_value=0.1,
                created_by=self.test_user.id,
                is_active=False,
                notification_channels=["in_app"]
            )
        ]
        
        for rule in rules:
            self.db.add(rule)
        self.db.commit()
        
        # 测试获取所有规则
        response = client.get(
            "/api/v1/monitoring/alert-rules",
            headers=self.auth_headers
        )
        
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["rules"]) == 2
        
        # 测试按状态过滤
        response = client.get(
            "/api/v1/monitoring/alert-rules?is_active=true",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["rules"]) == 1
        assert data["data"]["rules"][0]["rule_name"] == "规则1"
    
    def test_update_alert_rule(self):
        """测试更新告警规则"""
        # 创建测试规则
        test_rule = AlertRule(
            rule_name="原始规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.7,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        # 更新规则
        update_data = {
            "rule_name": "更新后规则",
            "threshold_value": 0.8,
            "severity": "critical"
        }
        
        response = client.put(
            f"/api/v1/monitoring/alert-rules/{test_rule.id}",
            json=update_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["rule_name"] == "更新后规则"
        assert data["data"]["threshold_value"] == 0.8
        
        # 验证数据库更新
        self.db.refresh(test_rule)
        assert test_rule.rule_name == "更新后规则"
        assert test_rule.threshold_value == 0.8
    
    def test_delete_alert_rule(self):
        """测试删除告警规则"""
        # 创建测试规则
        test_rule = AlertRule(
            rule_name="待删除规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.7,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        # 删除规则
        response = client.delete(
            f"/api/v1/monitoring/alert-rules/{test_rule.id}",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证数据库删除
        deleted_rule = self.db.query(AlertRule).filter(
            AlertRule.id == test_rule.id
        ).first()
        assert deleted_rule is None
    
    def test_get_alerts(self):
        """测试获取告警列表"""
        # 创建测试告警规则
        test_rule = AlertRule(
            rule_name="测试规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.8,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        # 创建测试告警
        alerts = [
            Alert(
                rule_id=test_rule.id,
                alert_message="覆盖率过低",
                current_value=0.7,
                threshold_value=0.8,
                severity="high",
                status="active"
            ),
            Alert(
                rule_id=test_rule.id,
                alert_message="覆盖率恢复正常",
                current_value=0.85,
                threshold_value=0.8,
                severity="medium",
                status="resolved"
            )
        ]
        
        for alert in alerts:
            self.db.add(alert)
        self.db.commit()
        
        # 测试获取所有告警
        response = client.get(
            "/api/v1/monitoring/alerts",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["alerts"]) == 2
        
        # 测试按状态过滤
        response = client.get(
            "/api/v1/monitoring/alerts?status=active",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["alerts"]) == 1
        assert data["data"]["alerts"][0]["status"] == "active"
    
    def test_acknowledge_alert(self):
        """测试确认告警"""
        # 创建测试告警规则和告警
        test_rule = AlertRule(
            rule_name="测试规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.8,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        test_alert = Alert(
            rule_id=test_rule.id,
            alert_message="测试告警",
            severity="high",
            status="active"
        )
        self.db.add(test_alert)
        self.db.commit()
        self.db.refresh(test_alert)
        
        # 确认告警
        response = client.post(
            f"/api/v1/monitoring/alerts/{test_alert.id}/acknowledge",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "acknowledged"
        
        # 验证数据库更新
        self.db.refresh(test_alert)
        assert test_alert.status == "acknowledged"
        assert test_alert.acknowledged_by == self.test_user.id
        assert test_alert.acknowledged_at is not None
    
    def test_resolve_alert(self):
        """测试解决告警"""
        # 创建测试告警规则和告警
        test_rule = AlertRule(
            rule_name="测试规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.8,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        test_alert = Alert(
            rule_id=test_rule.id,
            alert_message="测试告警",
            severity="high",
            status="active"
        )
        self.db.add(test_alert)
        self.db.commit()
        self.db.refresh(test_alert)
        
        # 解决告警
        response = client.post(
            f"/api/v1/monitoring/alerts/{test_alert.id}/resolve",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "resolved"
        
        # 验证数据库更新
        self.db.refresh(test_alert)
        assert test_alert.status == "resolved"
        assert test_alert.resolved_at is not None
    
    def test_get_system_metrics(self):
        """测试获取系统指标"""
        # 创建测试指标
        metrics = [
            SystemMetric(
                metric_name="CPU使用率",
                metric_type="performance",
                metric_value=75.5,
                unit="percentage",
                recorded_at=datetime.utcnow() - timedelta(hours=1)
            ),
            SystemMetric(
                metric_name="内存使用率",
                metric_type="performance",
                metric_value=60.2,
                unit="percentage",
                recorded_at=datetime.utcnow() - timedelta(minutes=30)
            ),
            SystemMetric(
                metric_name="测试通过率",
                metric_type="business",
                metric_value=85.0,
                unit="percentage",
                recorded_at=datetime.utcnow() - timedelta(minutes=15)
            )
        ]
        
        for metric in metrics:
            self.db.add(metric)
        self.db.commit()
        
        # 测试获取所有指标
        response = client.get(
            "/api/v1/monitoring/metrics",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["metrics"]) == 3
        
        # 测试按类型过滤
        response = client.get(
            "/api/v1/monitoring/metrics?metric_types=performance",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["metrics"]) == 2
        
        # 测试时间范围过滤
        start_time = (datetime.utcnow() - timedelta(minutes=45)).isoformat()
        response = client.get(
            f"/api/v1/monitoring/metrics?start_time={start_time}",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["metrics"]) == 2  # 最近45分钟的指标
    
    def test_collect_current_metrics(self):
        """测试手动收集指标"""
        response = client.post(
            "/api/v1/monitoring/metrics/collect",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "collected_metrics" in data["data"]
        assert data["data"]["collected_metrics"] > 0
    
    def test_analytics_query(self):
        """测试分析查询"""
        # 创建测试指标数据
        base_time = datetime.utcnow() - timedelta(days=7)
        for i in range(7):
            metric = SystemMetric(
                metric_name="测试通过率",
                metric_type="business",
                metric_value=80 + i * 2,  # 递增的通过率
                unit="percentage",
                recorded_at=base_time + timedelta(days=i)
            )
            self.db.add(metric)
        self.db.commit()
        
        # 执行分析查询
        query_data = {
            "metric_types": ["business"],
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "group_by": "day",
            "aggregation": "avg"
        }
        
        response = client.post(
            "/api/v1/monitoring/analytics/query",
            json=query_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # The response should contain analytics results
        assert "data" in data
    
    def test_analytics_query_with_different_aggregations(self):
        """测试不同聚合方式的分析查询"""
        # 创建测试数据
        base_time = datetime.utcnow() - timedelta(days=3)
        test_values = [75.0, 80.0, 85.0, 90.0, 95.0]
        
        for i, value in enumerate(test_values):
            metric = SystemMetric(
                metric_name="质量分数",
                metric_type="business",
                metric_value=value,
                unit="percentage",
                recorded_at=base_time + timedelta(hours=i)
            )
            self.db.add(metric)
        self.db.commit()
        
        # 测试不同的聚合方式
        aggregations = ["avg", "sum", "min", "max", "count"]
        
        for agg in aggregations:
            query_data = {
                "metric_types": ["business"],
                "start_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "aggregation": agg
            }
            
            response = client.post(
                "/api/v1/monitoring/analytics/query",
                json=query_data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_analytics_query_empty_data(self):
        """测试空数据的分析查询"""
        query_data = {
            "metric_types": ["nonexistent"],
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        response = client.post(
            "/api/v1/monitoring/analytics/query",
            json=query_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_coverage_analytics(self):
        """测试覆盖率分析"""
        # 创建测试覆盖率数据
        coverage_data = [
            CoverageAnalysis(
                requirement_id=1,
                function_module="模块A",
                coverage_percentage=85.0,
                covered_test_cases=17,
                total_test_cases=20,
                analysis_date=datetime.utcnow() - timedelta(days=1)
            ),
            CoverageAnalysis(
                requirement_id=2,
                function_module="模块B",
                coverage_percentage=75.0,
                covered_test_cases=15,
                total_test_cases=20,
                analysis_date=datetime.utcnow() - timedelta(days=2)
            ),
            CoverageAnalysis(
                requirement_id=3,
                function_module="模块C",
                coverage_percentage=45.0,  # Low coverage
                covered_test_cases=9,
                total_test_cases=20,
                analysis_date=datetime.utcnow() - timedelta(days=3)
            )
        ]
        
        for coverage in coverage_data:
            self.db.add(coverage)
        self.db.commit()
        
        # 获取覆盖率分析
        response = client.get(
            "/api/v1/monitoring/analytics/coverage?time_range=30d",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证分析结果包含预期字段
        analysis_data = data["data"]
        assert "trend_analysis" in analysis_data
        assert "current_average" in analysis_data
        assert "recommendations" in analysis_data
    
    def test_coverage_analytics_different_time_ranges(self):
        """测试不同时间范围的覆盖率分析"""
        # 创建不同时间的覆盖率数据
        time_ranges = [1, 5, 10, 15, 20, 25, 35]  # days ago
        
        for days_ago in time_ranges:
            coverage = CoverageAnalysis(
                requirement_id=days_ago,
                function_module=f"模块{days_ago}",
                coverage_percentage=70.0 + (days_ago % 20),
                covered_test_cases=14 + (days_ago % 6),
                total_test_cases=20,
                analysis_date=datetime.utcnow() - timedelta(days=days_ago)
            )
            self.db.add(coverage)
        self.db.commit()
        
        # 测试不同时间范围
        for time_range in ["7d", "30d", "90d"]:
            response = client.get(
                f"/api/v1/monitoring/analytics/coverage?time_range={time_range}",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_coverage_analytics_empty_data(self):
        """测试空覆盖率数据的分析"""
        response = client.get(
            "/api/v1/monitoring/analytics/coverage?time_range=7d",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should handle empty data gracefully
        analysis_data = data["data"]
        assert analysis_data["trend_analysis"] in ["insufficient_data", "no_valid_data"]
    
    def test_defect_analytics(self):
        """测试缺陷分析"""
        # 创建测试缺陷数据
        defects = [
            Defect(
                test_case_id=1,
                defect_type="functional",
                severity="high",
                description="登录功能缺陷",
                status="open",
                detected_at=datetime.utcnow() - timedelta(days=1)
            ),
            Defect(
                test_case_id=2,
                defect_type="performance",
                severity="medium",
                description="响应时间过长",
                status="resolved",
                detected_at=datetime.utcnow() - timedelta(days=2),
                resolved_at=datetime.utcnow() - timedelta(hours=12)
            ),
            Defect(
                test_case_id=3,
                defect_type="functional",
                severity="critical",
                description="登录验证失败",
                status="open",
                detected_at=datetime.utcnow() - timedelta(days=3)
            ),
            Defect(
                test_case_id=4,
                defect_type="usability",
                severity="low",
                description="界面显示问题",
                status="resolved",
                detected_at=datetime.utcnow() - timedelta(days=4),
                resolved_at=datetime.utcnow() - timedelta(days=2)
            )
        ]
        
        for defect in defects:
            self.db.add(defect)
        self.db.commit()
        
        # 获取缺陷分析
        response = client.get(
            "/api/v1/monitoring/analytics/defects?time_range=30d",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证分析结果
        analysis_data = data["data"]
        assert "total_defects" in analysis_data
        assert analysis_data["total_defects"] == 4
        assert "patterns" in analysis_data
        assert "by_severity" in analysis_data["patterns"]
        assert "by_type" in analysis_data["patterns"]
        assert "recommendations" in analysis_data
        
        # 验证严重程度分布
        severity_dist = analysis_data["patterns"]["by_severity"]
        assert severity_dist["critical"] == 1
        assert severity_dist["high"] == 1
        assert severity_dist["medium"] == 1
        assert severity_dist["low"] == 1
    
    def test_defect_analytics_with_patterns(self):
        """测试缺陷模式识别"""
        # 创建具有重复模式的缺陷数据
        defects = [
            Defect(
                test_case_id=1,
                defect_type="functional",
                severity="high",
                description="authentication failure in login module",
                status="open",
                detected_at=datetime.utcnow() - timedelta(days=1)
            ),
            Defect(
                test_case_id=2,
                defect_type="functional",
                severity="medium",
                description="authentication timeout issue",
                status="open",
                detected_at=datetime.utcnow() - timedelta(days=2)
            ),
            Defect(
                test_case_id=3,
                defect_type="security",
                severity="critical",
                description="authentication bypass vulnerability",
                status="open",
                detected_at=datetime.utcnow() - timedelta(days=3)
            )
        ]
        
        for defect in defects:
            self.db.add(defect)
        self.db.commit()
        
        response = client.get(
            "/api/v1/monitoring/analytics/defects?time_range=30d",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证模式识别
        analysis_data = data["data"]
        recurring_patterns = analysis_data["patterns"]["recurring_patterns"]
        
        # 应该识别出"authentication"作为重复模式
        pattern_keywords = [p["pattern_keyword"] for p in recurring_patterns]
        assert "authentication" in pattern_keywords
    
    def test_defect_analytics_resolution_times(self):
        """测试缺陷解决时间分析"""
        now = datetime.utcnow()
        
        # 创建已解决的缺陷数据
        defects = [
            Defect(
                test_case_id=1,
                defect_type="functional",
                severity="high",
                description="快速解决的缺陷",
                status="resolved",
                detected_at=now - timedelta(days=5),
                resolved_at=now - timedelta(days=4)  # 1天解决
            ),
            Defect(
                test_case_id=2,
                defect_type="performance",
                severity="medium",
                description="慢速解决的缺陷",
                status="resolved",
                detected_at=now - timedelta(days=15),
                resolved_at=now - timedelta(days=5)  # 10天解决
            )
        ]
        
        for defect in defects:
            self.db.add(defect)
        self.db.commit()
        
        response = client.get(
            "/api/v1/monitoring/analytics/defects?time_range=30d",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证解决时间统计
        analysis_data = data["data"]
        resolution_stats = analysis_data["resolution_statistics"]
        
        assert resolution_stats is not None
        assert "average_days" in resolution_stats
        assert "total_resolved" in resolution_stats
        assert resolution_stats["total_resolved"] == 2
        assert resolution_stats["average_days"] == 5.5  # (1+10)/2
    
    def test_monitoring_dashboard(self):
        """测试监控仪表板"""
        # 创建一些测试数据
        self._create_test_metrics()
        self._create_test_alerts()
        
        response = client.get(
            "/api/v1/monitoring/dashboard?time_range=24h",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证仪表板数据结构
        dashboard_data = data["data"]
        assert "system_overview" in dashboard_data
        assert "performance_metrics" in dashboard_data
        assert "business_metrics" in dashboard_data
        assert "alerts" in dashboard_data
    
    def test_monitoring_dashboard_different_time_ranges(self):
        """测试不同时间范围的监控仪表板"""
        time_ranges = ["1h", "6h", "24h", "7d", "30d"]
        
        for time_range in time_ranges:
            response = client.get(
                f"/api/v1/monitoring/dashboard?time_range={time_range}",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_monitoring_dashboard_with_specific_metrics(self):
        """测试指定指标的监控仪表板"""
        # 创建测试指标
        self._create_test_metrics()
        
        # 请求特定指标
        response = client.get(
            "/api/v1/monitoring/dashboard?time_range=24h&metrics=cpu_usage,memory_usage",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def _create_test_metrics(self):
        """创建测试指标数据"""
        base_time = datetime.utcnow() - timedelta(hours=2)
        
        metrics = [
            SystemMetric(
                metric_name="cpu_usage",
                metric_type="performance",
                metric_value=75.5,
                unit="percentage",
                recorded_at=base_time
            ),
            SystemMetric(
                metric_name="memory_usage",
                metric_type="performance",
                metric_value=60.2,
                unit="percentage",
                recorded_at=base_time + timedelta(minutes=30)
            ),
            SystemMetric(
                metric_name="test_pass_rate",
                metric_type="business",
                metric_value=85.0,
                unit="percentage",
                recorded_at=base_time + timedelta(hours=1)
            )
        ]
        
        for metric in metrics:
            self.db.add(metric)
        self.db.commit()
    
    def _create_test_alerts(self):
        """创建测试告警数据"""
        # 创建告警规则
        rule = AlertRule(
            rule_name="测试告警规则",
            metric_type="cpu_usage",
            condition_operator=">",
            threshold_value=80.0,
            severity="high",
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        # 创建告警
        alert = Alert(
            rule_id=rule.id,
            alert_message="CPU使用率过高",
            current_value=85.0,
            threshold_value=80.0,
            severity="high",
            status="active"
        )
        self.db.add(alert)
        self.db.commit()
    
    def test_system_health(self):
        """测试系统健康检查"""
        response = client.get(
            "/api/v1/monitoring/health",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # 验证健康检查数据结构
        health_data = data["data"]
        assert "status" in health_data
        assert "checks" in health_data
        
        # 验证状态字段
        status = health_data["status"]
        assert "cpu_usage" in status
        assert "memory_usage" in status
        assert "disk_usage" in status
        assert "status" in status
        
        # 验证检查结果
        checks = health_data["checks"]
        assert "cpu_check" in checks
        assert "memory_check" in checks
        assert "disk_check" in checks
        assert "error_rate_check" in checks
        
        # 验证检查结果值
        for check_name, check_result in checks.items():
            assert check_result in ["pass", "warning", "fail"]
    
    def test_system_health_status_determination(self):
        """测试系统健康状态判断"""
        # 多次调用健康检查，验证状态一致性
        for _ in range(3):
            response = client.get(
                "/api/v1/monitoring/health",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            health_status = data["data"]["status"]["status"]
            assert health_status in ["healthy", "warning", "critical", "unknown"]
    
    def test_invalid_metric_type(self):
        """测试无效的指标类型"""
        rule_data = {
            "rule_name": "无效指标规则",
            "metric_type": "invalid_metric",  # 无效类型
            "condition_operator": "<",
            "threshold_value": 0.8
        }
        
        response = client.post(
            "/api/v1/monitoring/alert-rules",
            json=rule_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_invalid_condition_operator(self):
        """测试无效的条件操作符"""
        rule_data = {
            "rule_name": "无效操作符规则",
            "metric_type": "coverage_rate",
            "condition_operator": "invalid_op",  # 无效操作符
            "threshold_value": 0.8
        }
        
        response = client.post(
            "/api/v1/monitoring/alert-rules",
            json=rule_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 临时移除认证覆盖
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        response = client.get("/api/v1/monitoring/alert-rules")
        
        assert response.status_code == 401  # 未授权
        
        # 恢复认证覆盖
        def mock_get_current_user():
            return self.test_user
        app.dependency_overrides[get_current_user] = mock_get_current_user
    
    def test_access_other_user_rules(self):
        """测试访问其他用户的规则"""
        # 创建另一个用户
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        self.db.add(other_user)
        self.db.commit()
        self.db.refresh(other_user)
        
        # 创建其他用户的规则
        other_rule = AlertRule(
            rule_name="其他用户规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.8,
            created_by=other_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(other_rule)
        self.db.commit()
        self.db.refresh(other_rule)
        
        # 尝试访问其他用户的规则
        response = client.put(
            f"/api/v1/monitoring/alert-rules/{other_rule.id}",
            json={"rule_name": "尝试修改"},
            headers=self.auth_headers
        )
        
        assert response.status_code == 404  # 找不到（权限控制）
    
    def test_analytics_query_invalid_date_range(self):
        """测试无效日期范围的分析查询"""
        query_data = {
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),  # 结束日期早于开始日期
            "aggregation": "avg"
        }
        
        response = client.post(
            "/api/v1/monitoring/analytics/query",
            json=query_data,
            headers=self.auth_headers
        )
        
        # 应该能处理无效日期范围
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_analytics_query_invalid_aggregation(self):
        """测试无效聚合方式的分析查询"""
        query_data = {
            "metric_types": ["business"],
            "aggregation": "invalid_aggregation"
        }
        
        response = client.post(
            "/api/v1/monitoring/analytics/query",
            json=query_data,
            headers=self.auth_headers
        )
        
        # 应该回退到默认聚合方式
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_alert_rule_threshold_edge_cases(self):
        """测试告警规则阈值边界情况"""
        edge_cases = [
            {"threshold_value": 0.0},
            {"threshold_value": 100.0},
            {"threshold_value": -1.0},
            {"threshold_value": 999999.99}
        ]
        
        for case in edge_cases:
            rule_data = {
                "rule_name": f"边界测试规则_{case['threshold_value']}",
                "metric_type": "coverage_rate",
                "condition_operator": ">",
                **case
            }
            
            response = client.post(
                "/api/v1/monitoring/alert-rules",
                json=rule_data,
                headers=self.auth_headers
            )
            
            # 应该能处理各种阈值
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_metrics_collection_performance(self):
        """测试指标收集性能"""
        import time
        
        start_time = time.time()
        
        response = client.post(
            "/api/v1/monitoring/metrics/collect",
            headers=self.auth_headers
        )
        
        end_time = time.time()
        collection_time = end_time - start_time
        
        assert response.status_code == 200
        assert collection_time < 5.0  # 应该在5秒内完成
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["collected_metrics"] > 0
    
    def test_large_dataset_analytics(self):
        """测试大数据集分析"""
        # 创建大量测试数据
        base_time = datetime.utcnow() - timedelta(days=30)
        
        # 创建1000个指标数据点
        metrics = []
        for i in range(1000):
            metric = SystemMetric(
                metric_name="large_dataset_test",
                metric_type="business",
                metric_value=50 + (i % 50),  # 50-99的循环值
                unit="percentage",
                recorded_at=base_time + timedelta(minutes=i)
            )
            metrics.append(metric)
        
        # 批量插入
        self.db.add_all(metrics)
        self.db.commit()
        
        # 执行分析查询
        query_data = {
            "metric_types": ["business"],
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "aggregation": "avg"
        }
        
        response = client.post(
            "/api/v1/monitoring/analytics/query",
            json=query_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_concurrent_alert_operations(self):
        """测试并发告警操作"""
        import threading
        import time
        
        # 创建测试告警规则
        test_rule = AlertRule(
            rule_name="并发测试规则",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=0.8,
            created_by=self.test_user.id,
            notification_channels=["in_app"]
        )
        self.db.add(test_rule)
        self.db.commit()
        self.db.refresh(test_rule)
        
        # 创建测试告警
        test_alert = Alert(
            rule_id=test_rule.id,
            alert_message="并发测试告警",
            severity="medium",
            status="active"
        )
        self.db.add(test_alert)
        self.db.commit()
        self.db.refresh(test_alert)
        
        results = []
        
        def acknowledge_alert():
            response = client.post(
                f"/api/v1/monitoring/alerts/{test_alert.id}/acknowledge",
                headers=self.auth_headers
            )
            results.append(response.status_code)
        
        def resolve_alert():
            time.sleep(0.1)  # 稍微延迟
            response = client.post(
                f"/api/v1/monitoring/alerts/{test_alert.id}/resolve",
                headers=self.auth_headers
            )
            results.append(response.status_code)
        
        # 并发执行确认和解决操作
        thread1 = threading.Thread(target=acknowledge_alert)
        thread2 = threading.Thread(target=resolve_alert)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # 至少有一个操作应该成功
        assert any(status == 200 for status in results)