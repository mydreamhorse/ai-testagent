"""
监控服务集成测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, SystemMetric, AlertRule, Alert, User
from backend.services.monitoring_service import MonitoringService


class TestMonitoringIntegration:
    """监控服务集成测试"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        # 使用内存数据库进行测试
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
    
    @pytest.fixture
    def test_user(self, db_session):
        """创建测试用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def monitoring_service(self, db_session):
        """创建监控服务实例"""
        return MonitoringService(db_session)
    
    def test_save_system_metrics_integration(self, monitoring_service, db_session):
        """测试保存系统指标集成"""
        metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 68.2,
            "disk_usage": 45.0
        }
        
        # 保存指标
        monitoring_service._save_system_metrics(metrics)
        
        # 验证数据库中的数据
        saved_metrics = db_session.query(SystemMetric).all()
        assert len(saved_metrics) == 3
        
        # 验证具体指标
        cpu_metric = db_session.query(SystemMetric).filter(
            SystemMetric.metric_name == "cpu_usage"
        ).first()
        assert cpu_metric is not None
        assert cpu_metric.metric_value == 75.5
        assert cpu_metric.unit == "percentage"
        assert cpu_metric.metric_type == "system"
    
    def test_create_and_evaluate_alert_rule_integration(self, monitoring_service, test_user, db_session):
        """测试创建和评估告警规则集成"""
        # 创建告警规则
        rule_data = {
            "rule_name": "CPU使用率告警",
            "metric_type": "cpu_usage",
            "condition_operator": ">",
            "threshold_value": 80.0,
            "severity": "high",
            "notification_channels": ["email", "in_app"],
            "created_by": test_user.id,
            "description": "CPU使用率超过80%时触发告警"
        }
        
        alert_rule = monitoring_service.create_alert_rule(rule_data)
        assert alert_rule is not None
        assert alert_rule.id is not None
        
        # 验证规则已保存到数据库
        saved_rule = db_session.query(AlertRule).filter(AlertRule.id == alert_rule.id).first()
        assert saved_rule is not None
        assert saved_rule.rule_name == "CPU使用率告警"
        
        # 测试触发告警的指标
        metrics = {"cpu_usage": 85.0}  # 超过阈值
        triggered_alerts = monitoring_service.evaluate_alert_conditions(metrics)
        
        assert len(triggered_alerts) == 1
        alert = triggered_alerts[0]
        assert alert.rule_id == alert_rule.id
        assert alert.current_value == 85.0
        assert alert.status == "active"
        
        # 验证告警已保存到数据库
        saved_alert = db_session.query(Alert).filter(Alert.id == alert.id).first()
        assert saved_alert is not None
        assert saved_alert.severity == "high"
    
    def test_alert_lifecycle_integration(self, monitoring_service, test_user, db_session):
        """测试告警生命周期集成"""
        # 创建告警规则
        rule_data = {
            "rule_name": "内存使用率告警",
            "metric_type": "memory_usage",
            "condition_operator": ">",
            "threshold_value": 90.0,
            "severity": "critical",
            "notification_channels": ["email"],
            "created_by": test_user.id
        }
        
        alert_rule = monitoring_service.create_alert_rule(rule_data)
        
        # 触发告警
        metrics = {"memory_usage": 95.0}
        triggered_alerts = monitoring_service.evaluate_alert_conditions(metrics)
        alert = triggered_alerts[0]
        
        # 确认告警
        success = monitoring_service.acknowledge_alert(alert.id, test_user.id)
        assert success == True
        
        # 验证告警状态
        updated_alert = db_session.query(Alert).filter(Alert.id == alert.id).first()
        assert updated_alert.status == "acknowledged"
        assert updated_alert.acknowledged_by == test_user.id
        assert updated_alert.acknowledged_at is not None
        
        # 解决告警
        success = monitoring_service.resolve_alert(alert.id, test_user.id)
        assert success == True
        
        # 验证告警状态
        resolved_alert = db_session.query(Alert).filter(Alert.id == alert.id).first()
        assert resolved_alert.status == "resolved"
        assert resolved_alert.resolved_at is not None
    
    def test_historical_metrics_integration(self, monitoring_service, db_session):
        """测试历史指标查询集成"""
        # 创建一些历史指标数据
        now = datetime.utcnow()
        
        metrics_data = [
            ("cpu_usage", 50.0, now - timedelta(hours=2)),
            ("cpu_usage", 60.0, now - timedelta(hours=1)),
            ("cpu_usage", 70.0, now),
            ("memory_usage", 40.0, now - timedelta(hours=2)),
            ("memory_usage", 50.0, now - timedelta(hours=1))
        ]
        
        for metric_name, value, timestamp in metrics_data:
            metric = SystemMetric(
                metric_name=metric_name,
                metric_type="system",
                metric_value=value,
                unit="percentage",
                recorded_at=timestamp
            )
            db_session.add(metric)
        
        db_session.commit()
        
        # 查询CPU使用率历史数据
        cpu_history = monitoring_service.get_historical_metrics("cpu_usage", 24)
        assert len(cpu_history) == 3
        
        # 验证数据按时间排序
        values = [item["value"] for item in cpu_history]
        assert values == [50.0, 60.0, 70.0]
        
        # 查询内存使用率历史数据
        memory_history = monitoring_service.get_historical_metrics("memory_usage", 24)
        assert len(memory_history) == 2
    
    def test_cleanup_old_metrics_integration(self, monitoring_service, db_session):
        """测试清理旧指标数据集成"""
        # 创建新旧指标数据
        now = datetime.utcnow()
        old_date = now - timedelta(days=35)  # 35天前
        recent_date = now - timedelta(days=5)  # 5天前
        
        # 旧数据
        old_metric = SystemMetric(
            metric_name="cpu_usage",
            metric_type="system",
            metric_value=50.0,
            unit="percentage",
            recorded_at=old_date
        )
        
        # 新数据
        recent_metric = SystemMetric(
            metric_name="cpu_usage",
            metric_type="system",
            metric_value=60.0,
            unit="percentage",
            recorded_at=recent_date
        )
        
        db_session.add(old_metric)
        db_session.add(recent_metric)
        db_session.commit()
        
        # 验证数据存在
        total_metrics = db_session.query(SystemMetric).count()
        assert total_metrics == 2
        
        # 清理30天前的数据
        monitoring_service.cleanup_old_metrics(30)
        
        # 验证只剩下新数据
        remaining_metrics = db_session.query(SystemMetric).all()
        assert len(remaining_metrics) == 1
        assert remaining_metrics[0].recorded_at == recent_date
    
    def test_get_active_alerts_integration(self, monitoring_service, test_user, db_session):
        """测试获取活跃告警集成"""
        # 创建多个告警规则
        rules_data = [
            {
                "rule_name": "CPU告警",
                "metric_type": "cpu_usage",
                "condition_operator": ">",
                "threshold_value": 80.0,
                "severity": "high",
                "created_by": test_user.id
            },
            {
                "rule_name": "内存告警",
                "metric_type": "memory_usage",
                "condition_operator": ">",
                "threshold_value": 90.0,
                "severity": "critical",
                "created_by": test_user.id
            }
        ]
        
        alert_rules = []
        for rule_data in rules_data:
            rule = monitoring_service.create_alert_rule(rule_data)
            alert_rules.append(rule)
        
        # 触发告警
        metrics = {
            "cpu_usage": 85.0,
            "memory_usage": 95.0
        }
        
        triggered_alerts = monitoring_service.evaluate_alert_conditions(metrics)
        assert len(triggered_alerts) == 2
        
        # 获取所有活跃告警
        active_alerts = monitoring_service.get_active_alerts()
        assert len(active_alerts) == 2
        
        # 获取特定严重程度的告警
        critical_alerts = monitoring_service.get_active_alerts(severity="critical")
        assert len(critical_alerts) == 1
        assert critical_alerts[0].severity == "critical"
        
        high_alerts = monitoring_service.get_active_alerts(severity="high")
        assert len(high_alerts) == 1
        assert high_alerts[0].severity == "high"


if __name__ == "__main__":
    pytest.main([__file__])