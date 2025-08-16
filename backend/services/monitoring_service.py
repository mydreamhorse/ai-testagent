"""
智能测试报告系统 - 监控服务模块

该模块实现实时监控和告警功能，包括：
- 系统指标收集
- 测试执行状态监控
- 告警规则引擎
- 通知服务
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from backend.models import (
    SystemMetric, AlertRule, Alert, TestCase, TestCaseEvaluation, 
    Defect, CoverageAnalysis, User, GenerationLog
)
from backend.database import get_db


logger = logging.getLogger(__name__)


class SystemHealthStatus:
    """系统健康状态数据类"""
    def __init__(self):
        self.cpu_usage: float = 0.0
        self.memory_usage: float = 0.0
        self.disk_usage: float = 0.0
        self.active_tests: int = 0
        self.error_rate: float = 0.0
        self.response_time: float = 0.0
        self.timestamp: datetime = datetime.utcnow()
        self.status: str = "healthy"  # healthy, warning, critical
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "active_tests": self.active_tests,
            "error_rate": self.error_rate,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }


class ExecutionStatus:
    """测试执行状态数据类"""
    def __init__(self, execution_id: str):
        self.execution_id: str = execution_id
        self.status: str = "running"  # running, completed, failed, cancelled
        self.progress: float = 0.0
        self.total_tests: int = 0
        self.completed_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0
        self.start_time: datetime = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.current_test: Optional[str] = None
        self.errors: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "progress": self.progress,
            "total_tests": self.total_tests,
            "completed_tests": self.completed_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_test": self.current_test,
            "errors": self.errors
        }


class MonitoringService:
    """监控服务主类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.execution_statuses: Dict[str, ExecutionStatus] = {}
        self.monitoring_active = False
        self.collection_interval = 30  # 30秒收集一次指标
        self.alert_check_interval = 60  # 60秒检查一次告警
        
    def start_monitoring(self):
        """启动监控服务"""
        self.monitoring_active = True
        logger.info("监控服务已启动")
        
    def stop_monitoring(self):
        """停止监控服务"""
        self.monitoring_active = False
        logger.info("监控服务已停止")
        
    def collect_system_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 网络IO
            net_io = psutil.net_io_counters()
            
            metrics = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv
            }
            
            # 保存到数据库
            self._save_system_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统指标时出错: {str(e)}")
            return {}
    
    def _save_system_metrics(self, metrics: Dict[str, float]):
        """保存系统指标到数据库"""
        try:
            timestamp = datetime.utcnow()
            
            for metric_name, value in metrics.items():
                # 确定指标类型和单位
                metric_type = "system"
                unit = self._get_metric_unit(metric_name)
                
                system_metric = SystemMetric(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    metric_value=value,
                    unit=unit,
                    recorded_at=timestamp
                )
                
                self.db.add(system_metric)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"保存系统指标时出错: {str(e)}")
            self.db.rollback()
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """获取指标单位"""
        unit_mapping = {
            "cpu_usage": "percentage",
            "memory_usage": "percentage", 
            "disk_usage": "percentage",
            "memory_total": "bytes",
            "memory_used": "bytes",
            "disk_total": "bytes",
            "disk_used": "bytes",
            "network_bytes_sent": "bytes",
            "network_bytes_recv": "bytes",
            "response_time": "milliseconds",
            "error_rate": "percentage",
            "test_pass_rate": "percentage"
        }
        return unit_mapping.get(metric_name, "count")
    
    def collect_business_metrics(self) -> Dict[str, float]:
        """收集业务指标"""
        try:
            # 测试通过率
            total_evaluations = self.db.query(TestCaseEvaluation).count()
            if total_evaluations > 0:
                avg_score = self.db.query(func.avg(TestCaseEvaluation.total_score)).scalar() or 0
                test_pass_rate = avg_score
            else:
                test_pass_rate = 0
            
            # 缺陷率
            total_test_cases = self.db.query(TestCase).count()
            total_defects = self.db.query(Defect).count()
            defect_rate = (total_defects / total_test_cases * 100) if total_test_cases > 0 else 0
            
            # 覆盖率
            avg_coverage = self.db.query(func.avg(CoverageAnalysis.coverage_percentage)).scalar() or 0
            
            # 活跃用户数
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # 最近24小时的生成日志数量
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_generations = self.db.query(GenerationLog).filter(
                GenerationLog.created_at >= yesterday
            ).count()
            
            metrics = {
                "test_pass_rate": test_pass_rate,
                "defect_rate": defect_rate,
                "coverage_rate": avg_coverage,
                "active_users": active_users,
                "daily_generations": recent_generations
            }
            
            # 保存业务指标
            self._save_business_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集业务指标时出错: {str(e)}")
            return {}
    
    def _save_business_metrics(self, metrics: Dict[str, float]):
        """保存业务指标到数据库"""
        try:
            timestamp = datetime.utcnow()
            
            for metric_name, value in metrics.items():
                unit = self._get_metric_unit(metric_name)
                
                system_metric = SystemMetric(
                    metric_name=metric_name,
                    metric_type="business",
                    metric_value=value,
                    unit=unit,
                    recorded_at=timestamp
                )
                
                self.db.add(system_metric)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"保存业务指标时出错: {str(e)}")
            self.db.rollback()
    
    def monitor_test_execution(self, execution_id: str) -> ExecutionStatus:
        """监控测试执行状态"""
        if execution_id not in self.execution_statuses:
            self.execution_statuses[execution_id] = ExecutionStatus(execution_id)
        
        status = self.execution_statuses[execution_id]
        
        # 更新执行状态（这里可以根据实际的测试执行系统来获取状态）
        # 目前使用模拟数据
        try:
            # 从数据库获取相关测试用例信息
            test_cases = self.db.query(TestCase).all()
            evaluations = self.db.query(TestCaseEvaluation).all()
            
            status.total_tests = len(test_cases)
            status.completed_tests = len(evaluations)
            
            if status.total_tests > 0:
                status.progress = (status.completed_tests / status.total_tests) * 100
                
                # 计算通过和失败的测试
                passed_tests = len([e for e in evaluations if e.total_score >= 70])
                failed_tests = status.completed_tests - passed_tests
                
                status.passed_tests = passed_tests
                status.failed_tests = failed_tests
                
                # 更新状态
                if status.completed_tests == status.total_tests:
                    status.status = "completed"
                    status.end_time = datetime.utcnow()
                elif status.failed_tests > status.passed_tests:
                    status.status = "failed"
                else:
                    status.status = "running"
            
        except Exception as e:
            logger.error(f"监控测试执行时出错: {str(e)}")
            status.errors.append(str(e))
            status.status = "failed"
        
        return status
    
    def check_system_health(self) -> SystemHealthStatus:
        """检查系统健康状态"""
        health_status = SystemHealthStatus()
        
        try:
            # 收集当前系统指标
            system_metrics = self.collect_system_metrics()
            business_metrics = self.collect_business_metrics()
            
            # 更新健康状态
            health_status.cpu_usage = system_metrics.get("cpu_usage", 0)
            health_status.memory_usage = system_metrics.get("memory_usage", 0)
            health_status.disk_usage = system_metrics.get("disk_usage", 0)
            
            # 计算活跃测试数量
            health_status.active_tests = len([s for s in self.execution_statuses.values() 
                                            if s.status == "running"])
            
            # 计算错误率
            total_executions = len(self.execution_statuses)
            failed_executions = len([s for s in self.execution_statuses.values() 
                                   if s.status == "failed"])
            health_status.error_rate = (failed_executions / total_executions * 100) if total_executions > 0 else 0
            
            # 模拟响应时间（实际应该从应用性能监控获取）
            health_status.response_time = 150.0  # ms
            
            # 确定整体健康状态
            health_status.status = self._determine_health_status(health_status)
            
        except Exception as e:
            logger.error(f"检查系统健康状态时出错: {str(e)}")
            health_status.status = "critical"
        
        return health_status
    
    def _determine_health_status(self, health_status: SystemHealthStatus) -> str:
        """确定系统健康状态"""
        # 定义阈值
        cpu_critical = 90
        cpu_warning = 70
        memory_critical = 90
        memory_warning = 80
        disk_critical = 95
        disk_warning = 85
        error_rate_critical = 20
        error_rate_warning = 10
        
        # 检查关键指标
        if (health_status.cpu_usage >= cpu_critical or 
            health_status.memory_usage >= memory_critical or
            health_status.disk_usage >= disk_critical or
            health_status.error_rate >= error_rate_critical):
            return "critical"
        
        if (health_status.cpu_usage >= cpu_warning or
            health_status.memory_usage >= memory_warning or
            health_status.disk_usage >= disk_warning or
            health_status.error_rate >= error_rate_warning):
            return "warning"
        
        return "healthy"
    
    def get_historical_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """获取历史指标数据"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            metrics = self.db.query(SystemMetric).filter(
                and_(
                    SystemMetric.metric_name == metric_name,
                    SystemMetric.recorded_at >= start_time
                )
            ).order_by(SystemMetric.recorded_at).all()
            
            return [
                {
                    "value": metric.metric_value,
                    "timestamp": metric.recorded_at.isoformat(),
                    "unit": metric.unit
                }
                for metric in metrics
            ]
            
        except Exception as e:
            logger.error(f"获取历史指标数据时出错: {str(e)}")
            return []
    
    def cleanup_old_metrics(self, days: int = 30):
        """清理旧的指标数据"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = self.db.query(SystemMetric).filter(
                SystemMetric.recorded_at < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"清理了 {deleted_count} 条旧指标数据")
            
        except Exception as e:
            logger.error(f"清理旧指标数据时出错: {str(e)}")
            self.db.rollback()


    def evaluate_alert_conditions(self, metrics: Dict[str, float]) -> List[Alert]:
        """评估告警条件"""
        triggered_alerts = []
        
        try:
            # 获取所有活跃的告警规则
            active_rules = self.db.query(AlertRule).filter(
                AlertRule.is_active == True
            ).all()
            
            for rule in active_rules:
                try:
                    # 检查指标是否存在
                    if rule.metric_type not in metrics:
                        continue
                    
                    current_value = metrics[rule.metric_type]
                    threshold_value = rule.threshold_value
                    
                    # 评估条件
                    condition_met = self._evaluate_condition(
                        current_value, rule.condition_operator, threshold_value
                    )
                    
                    if condition_met:
                        # 检查是否已经有活跃的告警
                        existing_alert = self.db.query(Alert).filter(
                            and_(
                                Alert.rule_id == rule.id,
                                Alert.status == "active"
                            )
                        ).first()
                        
                        if not existing_alert:
                            # 创建新告警
                            alert = self._create_alert(rule, current_value, threshold_value)
                            triggered_alerts.append(alert)
                            
                            # 发送通知
                            self._send_alert_notification(alert)
                    else:
                        # 条件不满足，检查是否需要解决现有告警
                        self._resolve_existing_alerts(rule.id)
                        
                except Exception as e:
                    logger.error(f"评估告警规则 {rule.rule_name} 时出错: {str(e)}")
                    continue
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"评估告警条件时出错: {str(e)}")
            return []
    
    def _evaluate_condition(self, current_value: float, operator: str, threshold_value: float) -> bool:
        """评估条件表达式"""
        operators = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y
        }
        
        if operator not in operators:
            logger.warning(f"不支持的操作符: {operator}")
            return False
        
        return operators[operator](current_value, threshold_value)
    
    def _create_alert(self, rule: AlertRule, current_value: float, threshold_value: float) -> Alert:
        """创建告警"""
        alert_message = f"{rule.rule_name}: {rule.metric_type} 当前值 {current_value} {rule.condition_operator} 阈值 {threshold_value}"
        
        alert = Alert(
            rule_id=rule.id,
            alert_message=alert_message,
            current_value=current_value,
            threshold_value=threshold_value,
            severity=rule.severity,
            status="active",
            triggered_at=datetime.utcnow()
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"创建告警: {alert_message}")
        return alert
    
    def _resolve_existing_alerts(self, rule_id: int):
        """解决现有告警"""
        try:
            active_alerts = self.db.query(Alert).filter(
                and_(
                    Alert.rule_id == rule_id,
                    Alert.status == "active"
                )
            ).all()
            
            for alert in active_alerts:
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
                logger.info(f"自动解决告警: {alert.alert_message}")
            
            if active_alerts:
                self.db.commit()
                
        except Exception as e:
            logger.error(f"解决告警时出错: {str(e)}")
            self.db.rollback()
    
    def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        try:
            # 获取告警规则的通知渠道配置
            rule = self.db.query(AlertRule).filter(AlertRule.id == alert.rule_id).first()
            if not rule or not rule.notification_channels:
                return
            
            notification_channels = rule.notification_channels
            
            # 根据配置发送不同类型的通知
            if "email" in notification_channels:
                self._send_email_notification(alert, rule)
            
            if "sms" in notification_channels:
                self._send_sms_notification(alert, rule)
            
            if "webhook" in notification_channels:
                self._send_webhook_notification(alert, rule)
            
            if "in_app" in notification_channels:
                self._send_in_app_notification(alert, rule)
                
        except Exception as e:
            logger.error(f"发送告警通知时出错: {str(e)}")
    
    def _send_email_notification(self, alert: Alert, rule: AlertRule):
        """发送邮件通知"""
        # 这里应该集成实际的邮件服务
        logger.info(f"发送邮件通知: {alert.alert_message}")
        # TODO: 实现邮件发送逻辑
    
    def _send_sms_notification(self, alert: Alert, rule: AlertRule):
        """发送短信通知"""
        # 这里应该集成实际的短信服务
        logger.info(f"发送短信通知: {alert.alert_message}")
        # TODO: 实现短信发送逻辑
    
    def _send_webhook_notification(self, alert: Alert, rule: AlertRule):
        """发送Webhook通知"""
        # 这里应该发送HTTP请求到配置的Webhook URL
        logger.info(f"发送Webhook通知: {alert.alert_message}")
        # TODO: 实现Webhook发送逻辑
    
    def _send_in_app_notification(self, alert: Alert, rule: AlertRule):
        """发送应用内通知"""
        # 这里可以通过WebSocket或其他方式发送实时通知
        logger.info(f"发送应用内通知: {alert.alert_message}")
        # TODO: 实现应用内通知逻辑
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """确认告警"""
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            
            self.db.commit()
            logger.info(f"用户 {user_id} 确认了告警 {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"确认告警时出错: {str(e)}")
            self.db.rollback()
            return False
    
    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """解决告警"""
        try:
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"用户 {user_id} 解决了告警 {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"解决告警时出错: {str(e)}")
            self.db.rollback()
            return False
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """获取活跃告警"""
        try:
            query = self.db.query(Alert).filter(Alert.status == "active")
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            return query.order_by(desc(Alert.triggered_at)).all()
            
        except Exception as e:
            logger.error(f"获取活跃告警时出错: {str(e)}")
            return []
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            return self.db.query(Alert).filter(
                Alert.triggered_at >= start_time
            ).order_by(desc(Alert.triggered_at)).all()
            
        except Exception as e:
            logger.error(f"获取告警历史时出错: {str(e)}")
            return []
    
    def create_alert_rule(self, rule_data: Dict[str, Any]) -> Optional[AlertRule]:
        """创建告警规则"""
        try:
            alert_rule = AlertRule(
                rule_name=rule_data["rule_name"],
                metric_type=rule_data["metric_type"],
                condition_operator=rule_data["condition_operator"],
                threshold_value=rule_data["threshold_value"],
                severity=rule_data.get("severity", "medium"),
                notification_channels=rule_data.get("notification_channels", []),
                description=rule_data.get("description"),
                created_by=rule_data.get("created_by"),
                is_active=rule_data.get("is_active", True)
            )
            
            self.db.add(alert_rule)
            self.db.commit()
            self.db.refresh(alert_rule)
            
            logger.info(f"创建告警规则: {alert_rule.rule_name}")
            return alert_rule
            
        except Exception as e:
            logger.error(f"创建告警规则时出错: {str(e)}")
            self.db.rollback()
            return None
    
    def update_alert_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """更新告警规则"""
        try:
            alert_rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not alert_rule:
                return False
            
            # 更新字段
            for field, value in rule_data.items():
                if hasattr(alert_rule, field):
                    setattr(alert_rule, field, value)
            
            alert_rule.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"更新告警规则: {alert_rule.rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"更新告警规则时出错: {str(e)}")
            self.db.rollback()
            return False
    
    def delete_alert_rule(self, rule_id: int) -> bool:
        """删除告警规则"""
        try:
            alert_rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not alert_rule:
                return False
            
            # 先解决所有相关的活跃告警
            self._resolve_existing_alerts(rule_id)
            
            # 删除规则
            self.db.delete(alert_rule)
            self.db.commit()
            
            logger.info(f"删除告警规则: {alert_rule.rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除告警规则时出错: {str(e)}")
            self.db.rollback()
            return False
    
    def get_alert_rules(self, active_only: bool = True) -> List[AlertRule]:
        """获取告警规则"""
        try:
            query = self.db.query(AlertRule)
            
            if active_only:
                query = query.filter(AlertRule.is_active == True)
            
            return query.order_by(AlertRule.created_at).all()
            
        except Exception as e:
            logger.error(f"获取告警规则时出错: {str(e)}")
            return []
    
    async def run_monitoring_loop(self):
        """运行监控循环"""
        logger.info("启动监控循环")
        
        while self.monitoring_active:
            try:
                # 收集系统指标
                system_metrics = self.collect_system_metrics()
                
                # 收集业务指标
                business_metrics = self.collect_business_metrics()
                
                # 合并所有指标
                all_metrics = {**system_metrics, **business_metrics}
                
                # 评估告警条件
                if all_metrics:
                    triggered_alerts = self.evaluate_alert_conditions(all_metrics)
                    if triggered_alerts:
                        logger.info(f"触发了 {len(triggered_alerts)} 个告警")
                
                # 等待下一次检查
                await asyncio.sleep(self.alert_check_interval)
                
            except Exception as e:
                logger.error(f"监控循环中出错: {str(e)}")
                await asyncio.sleep(self.alert_check_interval)
        
        logger.info("监控循环已停止")


    async def collect_system_metrics_async(self) -> List[Dict[str, Any]]:
        """异步收集系统指标（用于API调用）"""
        try:
            # 收集系统指标
            system_metrics = self.collect_system_metrics()
            
            # 收集业务指标
            business_metrics = self.collect_business_metrics()
            
            # 合并所有指标
            all_metrics = []
            
            # 转换系统指标格式
            for name, value in system_metrics.items():
                all_metrics.append({
                    "name": name,
                    "type": "performance" if "usage" in name else "system",
                    "value": value,
                    "unit": self._get_metric_unit(name),
                    "tags": {"source": "system"}
                })
            
            # 转换业务指标格式
            for name, value in business_metrics.items():
                all_metrics.append({
                    "name": name,
                    "type": "business",
                    "value": value,
                    "unit": self._get_metric_unit(name),
                    "tags": {"source": "business"}
                })
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"异步收集指标时出错: {str(e)}")
            return []
    
    async def check_system_health_async(self) -> Dict[str, Any]:
        """异步检查系统健康状态（用于API调用）"""
        try:
            health_status = self.check_system_health()
            
            return {
                "status": health_status.to_dict(),
                "checks": {
                    "cpu_check": "pass" if health_status.cpu_usage < 70 else "warning" if health_status.cpu_usage < 90 else "fail",
                    "memory_check": "pass" if health_status.memory_usage < 70 else "warning" if health_status.memory_usage < 90 else "fail",
                    "disk_check": "pass" if health_status.disk_usage < 80 else "warning" if health_status.disk_usage < 95 else "fail",
                    "error_rate_check": "pass" if health_status.error_rate < 5 else "warning" if health_status.error_rate < 10 else "fail"
                }
            }
            
        except Exception as e:
            logger.error(f"异步检查系统健康状态时出错: {str(e)}")
            return {
                "status": {"status": "unknown", "error": str(e)},
                "checks": {}
            }
    
    async def get_dashboard_data(self, start_time: datetime, 
                               metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取监控仪表板数据"""
        try:
            dashboard_data = {
                "system_overview": {},
                "performance_metrics": {},
                "business_metrics": {},
                "alerts": {},
                "trends": {}
            }
            
            # 系统概览
            health_status_obj = self.check_system_health()
            dashboard_data["system_overview"] = health_status_obj.to_dict()
            
            # 性能指标
            performance_query = self.db.query(SystemMetric).filter(
                SystemMetric.metric_type == "performance",
                SystemMetric.recorded_at >= start_time
            )
            
            if metrics:
                performance_query = performance_query.filter(
                    SystemMetric.metric_name.in_(metrics)
                )
            
            performance_metrics = performance_query.order_by(
                SystemMetric.recorded_at.desc()
            ).limit(100).all()
            
            # 按指标名称分组
            grouped_metrics = {}
            for metric in performance_metrics:
                if metric.metric_name not in grouped_metrics:
                    grouped_metrics[metric.metric_name] = []
                grouped_metrics[metric.metric_name].append({
                    "timestamp": metric.recorded_at.isoformat(),
                    "value": metric.metric_value
                })
            
            dashboard_data["performance_metrics"] = grouped_metrics
            
            # 业务指标
            business_metrics = self.collect_business_metrics()
            dashboard_data["business_metrics"] = business_metrics
            
            # 活跃告警
            active_alerts = self.get_active_alerts()
            dashboard_data["alerts"] = {
                "active_count": len(active_alerts),
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "message": alert.alert_message,
                        "severity": alert.severity,
                        "triggered_at": alert.triggered_at.isoformat()
                    } for alert in active_alerts[:10]
                ]
            }
            
            # 趋势分析（简单版本）
            dashboard_data["trends"] = await self._calculate_simple_trends(start_time)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"获取仪表板数据时出错: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_simple_trends(self, start_time: datetime) -> Dict[str, Any]:
        """计算简单趋势"""
        try:
            trends = {}
            
            # CPU使用率趋势
            cpu_metrics = self.db.query(SystemMetric).filter(
                SystemMetric.metric_name == "cpu_usage",
                SystemMetric.recorded_at >= start_time
            ).order_by(SystemMetric.recorded_at).all()
            
            if len(cpu_metrics) >= 2:
                recent_avg = sum(m.metric_value for m in cpu_metrics[-5:]) / min(5, len(cpu_metrics))
                earlier_avg = sum(m.metric_value for m in cpu_metrics[:5]) / min(5, len(cpu_metrics))
                
                if recent_avg > earlier_avg * 1.1:
                    trends["cpu_trend"] = "increasing"
                elif recent_avg < earlier_avg * 0.9:
                    trends["cpu_trend"] = "decreasing"
                else:
                    trends["cpu_trend"] = "stable"
            
            # 测试通过率趋势
            recent_evaluations = self.db.query(TestCaseEvaluation).filter(
                TestCaseEvaluation.evaluated_at >= start_time
            ).order_by(TestCaseEvaluation.evaluated_at).all()
            
            if len(recent_evaluations) >= 10:
                recent_scores = [e.total_score for e in recent_evaluations[-10:]]
                earlier_scores = [e.total_score for e in recent_evaluations[:10]]
                
                recent_avg = sum(recent_scores) / len(recent_scores)
                earlier_avg = sum(earlier_scores) / len(earlier_scores)
                
                if recent_avg > earlier_avg * 1.05:
                    trends["quality_trend"] = "improving"
                elif recent_avg < earlier_avg * 0.95:
                    trends["quality_trend"] = "declining"
                else:
                    trends["quality_trend"] = "stable"
            
            return trends
            
        except Exception as e:
            logger.error(f"计算趋势时出错: {str(e)}")
            return {}


def get_monitoring_service(db: Session = None) -> MonitoringService:
    """获取监控服务实例"""
    if db is None:
        db = next(get_db())
    return MonitoringService(db)