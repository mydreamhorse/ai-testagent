"""
监控服务单元测试
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.monitoring_service import (
    MonitoringService, SystemHealthStatus, ExecutionStatus,
    get_monitoring_service
)
from backend.models import (
    SystemMetric, AlertRule, Alert, TestCase, TestCaseEvaluation,
    Defect, CoverageAnalysis, User, GenerationLog
)


class TestSystemHealthStatus:
    """系统健康状态测试"""
    
    def test_system_health_status_initialization(self):
        """测试系统健康状态初始化"""
        status = SystemHealthStatus()
        
        assert status.cpu_usage == 0.0
        assert status.memory_usage == 0.0
        assert status.disk_usage == 0.0
        assert status.active_tests == 0
        assert status.error_rate == 0.0
        assert status.response_time == 0.0
        assert status.status == "healthy"
        assert isinstance(status.timestamp, datetime)
    
    def test_system_health_status_to_dict(self):
        """测试系统健康状态转换为字典"""
        status = SystemHealthStatus()
        status.cpu_usage = 50.0
        status.memory_usage = 60.0
        status.status = "warning"
        
        result = status.to_dict()
        
        assert result["cpu_usage"] == 50.0
        assert result["memory_usage"] == 60.0
        assert result["status"] == "warning"
        assert "timestamp" in result


class TestExecutionStatus:
    """测试执行状态测试"""
    
    def test_execution_status_initialization(self):
        """测试执行状态初始化"""
        execution_id = "test_exec_001"
        status = ExecutionStatus(execution_id)
        
        assert status.execution_id == execution_id
        assert status.status == "running"
        assert status.progress == 0.0
        assert status.total_tests == 0
        assert status.completed_tests == 0
        assert status.passed_tests == 0
        assert status.failed_tests == 0
        assert isinstance(status.start_time, datetime)
        assert status.end_time is None
        assert status.current_test is None
        assert status.errors == []
    
    def test_execution_status_to_dict(self):
        """测试执行状态转换为字典"""
        execution_id = "test_exec_001"
        status = ExecutionStatus(execution_id)
        status.progress = 75.0
        status.total_tests = 10
        status.completed_tests = 7
        status.passed_tests = 6
        status.failed_tests = 1
        status.current_test = "test_case_8"
        
        result = status.to_dict()
        
        assert result["execution_id"] == execution_id
        assert result["progress"] == 75.0
        assert result["total_tests"] == 10
        assert result["completed_tests"] == 7
        assert result["passed_tests"] == 6
        assert result["failed_tests"] == 1
        assert result["current_test"] == "test_case_8"


class TestMonitoringService:
    """监控服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def monitoring_service(self, mock_db):
        """监控服务实例"""
        return MonitoringService(mock_db)
    
    def test_monitoring_service_initialization(self, monitoring_service):
        """测试监控服务初始化"""
        assert monitoring_service.execution_statuses == {}
        assert monitoring_service.monitoring_active == False
        assert monitoring_service.collection_interval == 30
        assert monitoring_service.alert_check_interval == 60
    
    def test_start_stop_monitoring(self, monitoring_service):
        """测试启动和停止监控"""
        # 启动监控
        monitoring_service.start_monitoring()
        assert monitoring_service.monitoring_active == True
        
        # 停止监控
        monitoring_service.stop_monitoring()
        assert monitoring_service.monitoring_active == False
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_system_metrics(self, mock_net_io, mock_disk, mock_memory, 
                                  mock_cpu, monitoring_service):
        """测试收集系统指标"""
        # 设置模拟数据
        mock_cpu.return_value = 45.5
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 67.8
        mock_memory_obj.total = 8589934592  # 8GB
        mock_memory_obj.used = 5825126400   # ~5.4GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 1000000000000  # 1TB
        mock_disk_obj.used = 500000000000    # 500GB
        mock_disk.return_value = mock_disk_obj
        
        mock_net_obj = Mock()
        mock_net_obj.bytes_sent = 1024000
        mock_net_obj.bytes_recv = 2048000
        mock_net_io.return_value = mock_net_obj
        
        # 执行测试
        metrics = monitoring_service.collect_system_metrics()
        
        # 验证结果
        assert metrics["cpu_usage"] == 45.5
        assert metrics["memory_usage"] == 67.8
        assert metrics["disk_usage"] == 50.0  # 500GB / 1TB * 100
        assert metrics["network_bytes_sent"] == 1024000
        assert metrics["network_bytes_recv"] == 2048000
        
        # 验证数据库调用
        assert monitoring_service.db.add.called
        assert monitoring_service.db.commit.called
    
    def test_get_metric_unit(self, monitoring_service):
        """测试获取指标单位"""
        assert monitoring_service._get_metric_unit("cpu_usage") == "percentage"
        assert monitoring_service._get_metric_unit("memory_total") == "bytes"
        assert monitoring_service._get_metric_unit("response_time") == "milliseconds"
        assert monitoring_service._get_metric_unit("unknown_metric") == "count"
    
    def test_collect_business_metrics(self, monitoring_service):
        """测试收集业务指标"""
        # 设置模拟查询结果
        monitoring_service.db.query.return_value.count.return_value = 100
        monitoring_service.db.query.return_value.scalar.return_value = 85.5
        monitoring_service.db.query.return_value.filter.return_value.count.return_value = 50
        
        # 执行测试
        metrics = monitoring_service.collect_business_metrics()
        
        # 验证结果
        assert "test_pass_rate" in metrics
        assert "defect_rate" in metrics
        assert "coverage_rate" in metrics
        assert "active_users" in metrics
        assert "daily_generations" in metrics
    
    def test_monitor_test_execution_new(self, monitoring_service):
        """测试监控新的测试执行"""
        execution_id = "test_exec_001"
        
        # 设置模拟数据
        monitoring_service.db.query.return_value.all.return_value = [Mock(), Mock(), Mock()]
        
        # 执行测试
        status = monitoring_service.monitor_test_execution(execution_id)
        
        # 验证结果
        assert status.execution_id == execution_id
        assert execution_id in monitoring_service.execution_statuses
        assert status.total_tests == 3
    
    def test_monitor_test_execution_existing(self, monitoring_service):
        """测试监控已存在的测试执行"""
        execution_id = "test_exec_001"
        
        # 预先创建执行状态
        existing_status = ExecutionStatus(execution_id)
        existing_status.progress = 50.0
        monitoring_service.execution_statuses[execution_id] = existing_status
        
        # 设置模拟数据
        monitoring_service.db.query.return_value.all.return_value = [Mock(), Mock()]
        
        # 执行测试
        status = monitoring_service.monitor_test_execution(execution_id)
        
        # 验证结果
        assert status is existing_status
        assert status.progress > 50.0  # 应该被更新
    
    def test_check_system_health(self, monitoring_service):
        """测试检查系统健康状态"""
        # 模拟collect_system_metrics和collect_business_metrics
        with patch.object(monitoring_service, 'collect_system_metrics') as mock_sys, \
             patch.object(monitoring_service, 'collect_business_metrics') as mock_bus:
            
            mock_sys.return_value = {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "disk_usage": 30.0
            }
            mock_bus.return_value = {}
            
            # 执行测试
            health_status = monitoring_service.check_system_health()
            
            # 验证结果
            assert health_status.cpu_usage == 45.0
            assert health_status.memory_usage == 60.0
            assert health_status.disk_usage == 30.0
            assert health_status.status == "healthy"
    
    def test_determine_health_status_healthy(self, monitoring_service):
        """测试确定健康状态 - 健康"""
        health_status = SystemHealthStatus()
        health_status.cpu_usage = 50.0
        health_status.memory_usage = 60.0
        health_status.disk_usage = 40.0
        health_status.error_rate = 5.0
        
        result = monitoring_service._determine_health_status(health_status)
        assert result == "healthy"
    
    def test_determine_health_status_warning(self, monitoring_service):
        """测试确定健康状态 - 警告"""
        health_status = SystemHealthStatus()
        health_status.cpu_usage = 75.0  # 超过警告阈值70
        health_status.memory_usage = 60.0
        health_status.disk_usage = 40.0
        health_status.error_rate = 5.0
        
        result = monitoring_service._determine_health_status(health_status)
        assert result == "warning"
    
    def test_determine_health_status_critical(self, monitoring_service):
        """测试确定健康状态 - 关键"""
        health_status = SystemHealthStatus()
        health_status.cpu_usage = 95.0  # 超过关键阈值90
        health_status.memory_usage = 60.0
        health_status.disk_usage = 40.0
        health_status.error_rate = 5.0
        
        result = monitoring_service._determine_health_status(health_status)
        assert result == "critical"
    
    def test_get_historical_metrics(self, monitoring_service):
        """测试获取历史指标数据"""
        # 设置模拟查询结果
        mock_metrics = [
            Mock(metric_value=50.0, recorded_at=datetime.utcnow(), unit="percentage"),
            Mock(metric_value=55.0, recorded_at=datetime.utcnow(), unit="percentage")
        ]
        
        monitoring_service.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_metrics
        
        # 执行测试
        result = monitoring_service.get_historical_metrics("cpu_usage", 24)
        
        # 验证结果
        assert len(result) == 2
        assert result[0]["value"] == 50.0
        assert result[1]["value"] == 55.0
        assert "timestamp" in result[0]
        assert "unit" in result[0]
    
    def test_cleanup_old_metrics(self, monitoring_service):
        """测试清理旧指标数据"""
        # 设置模拟删除结果
        monitoring_service.db.query.return_value.filter.return_value.delete.return_value = 100
        
        # 执行测试
        monitoring_service.cleanup_old_metrics(30)
        
        # 验证数据库调用
        assert monitoring_service.db.query.called
        assert monitoring_service.db.commit.called
    
    def test_collect_system_metrics_error_handling(self, monitoring_service):
        """测试收集系统指标时的错误处理"""
        with patch('psutil.cpu_percent', side_effect=Exception("CPU error")):
            metrics = monitoring_service.collect_system_metrics()
            assert metrics == {}
    
    def test_collect_business_metrics_error_handling(self, monitoring_service):
        """测试收集业务指标时的错误处理"""
        monitoring_service.db.query.side_effect = Exception("Database error")
        
        metrics = monitoring_service.collect_business_metrics()
        assert metrics == {}


class TestGetMonitoringService:
    """测试获取监控服务函数"""
    
    @patch('backend.services.monitoring_service.get_db')
    def test_get_monitoring_service_with_db(self, mock_get_db):
        """测试使用提供的数据库会话获取监控服务"""
        mock_db = Mock(spec=Session)
        
        service = get_monitoring_service(mock_db)
        
        assert isinstance(service, MonitoringService)
        assert service.db is mock_db
    
    @patch('backend.services.monitoring_service.get_db')
    def test_get_monitoring_service_without_db(self, mock_get_db):
        """测试不提供数据库会话时获取监控服务"""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        service = get_monitoring_service()
        
        assert isinstance(service, MonitoringService)
        assert service.db is mock_db


class TestAlertRuleEngine:
    """告警规则引擎测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def monitoring_service(self, mock_db):
        """监控服务实例"""
        return MonitoringService(mock_db)
    
    @pytest.fixture
    def sample_alert_rule(self):
        """示例告警规则"""
        rule = Mock()
        rule.id = 1
        rule.rule_name = "CPU使用率过高"
        rule.metric_type = "cpu_usage"
        rule.condition_operator = ">"
        rule.threshold_value = 80.0
        rule.severity = "high"
        rule.notification_channels = ["email", "in_app"]
        rule.is_active = True
        return rule
    
    @pytest.fixture
    def sample_metrics(self):
        """示例指标数据"""
        return {
            "cpu_usage": 85.0,
            "memory_usage": 70.0,
            "disk_usage": 45.0,
            "test_pass_rate": 95.0
        }
    
    def test_evaluate_condition_greater_than_true(self, monitoring_service):
        """测试条件评估 - 大于条件为真"""
        result = monitoring_service._evaluate_condition(85.0, ">", 80.0)
        assert result == True
    
    def test_evaluate_condition_greater_than_false(self, monitoring_service):
        """测试条件评估 - 大于条件为假"""
        result = monitoring_service._evaluate_condition(75.0, ">", 80.0)
        assert result == False
    
    def test_evaluate_condition_less_than_true(self, monitoring_service):
        """测试条件评估 - 小于条件为真"""
        result = monitoring_service._evaluate_condition(75.0, "<", 80.0)
        assert result == True
    
    def test_evaluate_condition_equals_true(self, monitoring_service):
        """测试条件评估 - 等于条件为真"""
        result = monitoring_service._evaluate_condition(80.0, "==", 80.0)
        assert result == True
    
    def test_evaluate_condition_invalid_operator(self, monitoring_service):
        """测试条件评估 - 无效操作符"""
        result = monitoring_service._evaluate_condition(85.0, "invalid", 80.0)
        assert result == False
    
    def test_create_alert(self, monitoring_service, sample_alert_rule):
        """测试创建告警"""
        current_value = 85.0
        threshold_value = 80.0
        
        # 模拟数据库操作
        monitoring_service.db.add = Mock()
        monitoring_service.db.commit = Mock()
        monitoring_service.db.refresh = Mock()
        
        alert = monitoring_service._create_alert(sample_alert_rule, current_value, threshold_value)
        
        assert alert.rule_id == sample_alert_rule.id
        assert alert.current_value == current_value
        assert alert.threshold_value == threshold_value
        assert alert.severity == sample_alert_rule.severity
        assert alert.status == "active"
        assert "CPU使用率过高" in alert.alert_message
        
        # 验证数据库操作
        monitoring_service.db.add.assert_called_once()
        monitoring_service.db.commit.assert_called_once()
        monitoring_service.db.refresh.assert_called_once()
    
    def test_evaluate_alert_conditions_trigger_alert(self, monitoring_service, sample_alert_rule, sample_metrics):
        """测试评估告警条件 - 触发告警"""
        # 设置模拟查询结果
        monitoring_service.db.query.return_value.filter.return_value.all.return_value = [sample_alert_rule]
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = None  # 没有现有告警
        
        # 模拟创建告警和发送通知
        with patch.object(monitoring_service, '_create_alert') as mock_create, \
             patch.object(monitoring_service, '_send_alert_notification') as mock_send:
            
            mock_alert = Mock()
            mock_create.return_value = mock_alert
            
            triggered_alerts = monitoring_service.evaluate_alert_conditions(sample_metrics)
            
            assert len(triggered_alerts) == 1
            assert triggered_alerts[0] == mock_alert
            mock_create.assert_called_once()
            mock_send.assert_called_once_with(mock_alert)
    
    def test_evaluate_alert_conditions_no_trigger(self, monitoring_service, sample_alert_rule):
        """测试评估告警条件 - 不触发告警"""
        # 设置不满足条件的指标
        metrics = {"cpu_usage": 70.0}  # 低于阈值80.0
        
        monitoring_service.db.query.return_value.filter.return_value.all.return_value = [sample_alert_rule]
        
        # 模拟解决现有告警
        with patch.object(monitoring_service, '_resolve_existing_alerts') as mock_resolve:
            triggered_alerts = monitoring_service.evaluate_alert_conditions(metrics)
            
            assert len(triggered_alerts) == 0
            mock_resolve.assert_called_once_with(sample_alert_rule.id)
    
    def test_acknowledge_alert_success(self, monitoring_service):
        """测试确认告警 - 成功"""
        alert_id = 1
        user_id = 100
        
        mock_alert = Mock()
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = mock_alert
        monitoring_service.db.commit = Mock()
        
        result = monitoring_service.acknowledge_alert(alert_id, user_id)
        
        assert result == True
        assert mock_alert.status == "acknowledged"
        assert mock_alert.acknowledged_by == user_id
        assert isinstance(mock_alert.acknowledged_at, datetime)
        monitoring_service.db.commit.assert_called_once()
    
    def test_acknowledge_alert_not_found(self, monitoring_service):
        """测试确认告警 - 告警不存在"""
        alert_id = 999
        user_id = 100
        
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = monitoring_service.acknowledge_alert(alert_id, user_id)
        
        assert result == False
    
    def test_resolve_alert_success(self, monitoring_service):
        """测试解决告警 - 成功"""
        alert_id = 1
        user_id = 100
        
        mock_alert = Mock()
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = mock_alert
        monitoring_service.db.commit = Mock()
        
        result = monitoring_service.resolve_alert(alert_id, user_id)
        
        assert result == True
        assert mock_alert.status == "resolved"
        assert isinstance(mock_alert.resolved_at, datetime)
        monitoring_service.db.commit.assert_called_once()
    
    def test_get_active_alerts(self, monitoring_service):
        """测试获取活跃告警"""
        mock_alerts = [Mock(), Mock()]
        monitoring_service.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_alerts
        
        alerts = monitoring_service.get_active_alerts()
        
        assert len(alerts) == 2
        assert alerts == mock_alerts
    
    def test_get_active_alerts_with_severity(self, monitoring_service):
        """测试获取指定严重程度的活跃告警"""
        mock_alerts = [Mock()]
        monitoring_service.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_alerts
        
        alerts = monitoring_service.get_active_alerts(severity="high")
        
        assert len(alerts) == 1
        assert alerts == mock_alerts
    
    def test_create_alert_rule_success(self, monitoring_service):
        """测试创建告警规则 - 成功"""
        rule_data = {
            "rule_name": "测试规则",
            "metric_type": "cpu_usage",
            "condition_operator": ">",
            "threshold_value": 80.0,
            "severity": "high",
            "notification_channels": ["email"],
            "created_by": 1
        }
        
        monitoring_service.db.add = Mock()
        monitoring_service.db.commit = Mock()
        monitoring_service.db.refresh = Mock()
        
        result = monitoring_service.create_alert_rule(rule_data)
        
        assert result is not None
        assert result.rule_name == rule_data["rule_name"]
        assert result.metric_type == rule_data["metric_type"]
        monitoring_service.db.add.assert_called_once()
        monitoring_service.db.commit.assert_called_once()
    
    def test_update_alert_rule_success(self, monitoring_service):
        """测试更新告警规则 - 成功"""
        rule_id = 1
        rule_data = {"threshold_value": 90.0, "severity": "critical"}
        
        mock_rule = Mock()
        mock_rule.threshold_value = 80.0
        mock_rule.severity = "high"
        
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = mock_rule
        monitoring_service.db.commit = Mock()
        
        result = monitoring_service.update_alert_rule(rule_id, rule_data)
        
        assert result == True
        assert mock_rule.threshold_value == 90.0
        assert mock_rule.severity == "critical"
        monitoring_service.db.commit.assert_called_once()
    
    def test_delete_alert_rule_success(self, monitoring_service):
        """测试删除告警规则 - 成功"""
        rule_id = 1
        
        mock_rule = Mock()
        mock_rule.rule_name = "测试规则"
        
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = mock_rule
        monitoring_service.db.delete = Mock()
        monitoring_service.db.commit = Mock()
        
        with patch.object(monitoring_service, '_resolve_existing_alerts') as mock_resolve:
            result = monitoring_service.delete_alert_rule(rule_id)
            
            assert result == True
            mock_resolve.assert_called_once_with(rule_id)
            monitoring_service.db.delete.assert_called_once_with(mock_rule)
            monitoring_service.db.commit.assert_called_once()
    
    def test_get_alert_rules(self, monitoring_service):
        """测试获取告警规则"""
        mock_rules = [Mock(), Mock()]
        monitoring_service.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_rules
        
        rules = monitoring_service.get_alert_rules()
        
        assert len(rules) == 2
        assert rules == mock_rules
    
    def test_send_alert_notification(self, monitoring_service, sample_alert_rule):
        """测试发送告警通知"""
        mock_alert = Mock()
        mock_alert.rule_id = sample_alert_rule.id
        mock_alert.alert_message = "测试告警"
        
        monitoring_service.db.query.return_value.filter.return_value.first.return_value = sample_alert_rule
        
        with patch.object(monitoring_service, '_send_email_notification') as mock_email, \
             patch.object(monitoring_service, '_send_in_app_notification') as mock_app:
            
            monitoring_service._send_alert_notification(mock_alert)
            
            mock_email.assert_called_once_with(mock_alert, sample_alert_rule)
            mock_app.assert_called_once_with(mock_alert, sample_alert_rule)
    
    @pytest.mark.asyncio
    async def test_run_monitoring_loop(self, monitoring_service):
        """测试运行监控循环"""
        monitoring_service.monitoring_active = True
        
        # 模拟方法
        with patch.object(monitoring_service, 'collect_system_metrics') as mock_sys, \
             patch.object(monitoring_service, 'collect_business_metrics') as mock_bus, \
             patch.object(monitoring_service, 'evaluate_alert_conditions') as mock_eval, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_sys.return_value = {"cpu_usage": 50.0}
            mock_bus.return_value = {"test_pass_rate": 90.0}
            mock_eval.return_value = []
            
            # 设置停止条件
            async def stop_after_one_iteration(*args):
                monitoring_service.monitoring_active = False
            
            mock_sleep.side_effect = stop_after_one_iteration
            
            await monitoring_service.run_monitoring_loop()
            
            mock_sys.assert_called_once()
            mock_bus.assert_called_once()
            mock_eval.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])