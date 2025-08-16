"""
测试智能测试报告相关数据模型
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import (
    Base, User, TestCase, Requirement, 
    Report, Defect, CoverageAnalysis, AlertRule, Alert, ReportTemplate, SystemMetric
)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_user(db_session):
    """创建示例用户"""
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_requirement(db_session, sample_user):
    """创建示例需求"""
    requirement = Requirement(
        title="座椅调节功能",
        description="测试座椅前后调节功能",
        content="座椅应能前后调节30cm",
        user_id=sample_user.id
    )
    db_session.add(requirement)
    db_session.commit()
    db_session.refresh(requirement)
    return requirement


@pytest.fixture
def sample_test_case(db_session, sample_user, sample_requirement):
    """创建示例测试用例"""
    test_case = TestCase(
        requirement_id=sample_requirement.id,
        user_id=sample_user.id,
        title="座椅前后调节测试",
        description="验证座椅前后调节功能",
        test_type="function",
        test_steps="1. 启动系统\n2. 按下前进按钮\n3. 观察座椅移动",
        expected_result="座椅向前移动"
    )
    db_session.add(test_case)
    db_session.commit()
    db_session.refresh(test_case)
    return test_case


class TestReportModel:
    """测试Report模型"""
    
    def test_create_report(self, db_session, sample_user):
        """测试创建报告"""
        report = Report(
            title="测试执行报告",
            report_type="execution",
            generated_by=sample_user.id,
            data_range_start=datetime.utcnow() - timedelta(days=7),
            data_range_end=datetime.utcnow(),
            report_data={"total_tests": 100, "passed": 85, "failed": 15}
        )
        
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.id is not None
        assert report.title == "测试执行报告"
        assert report.report_type == "execution"
        assert report.status == "generating"
        assert report.generated_by == sample_user.id
        assert report.report_data["total_tests"] == 100
    
    def test_report_user_relationship(self, db_session, sample_user):
        """测试报告与用户的关系"""
        report = Report(
            title="缺陷分析报告",
            report_type="defect_analysis",
            generated_by=sample_user.id
        )
        
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.user.username == sample_user.username
        assert report in sample_user.reports


class TestDefectModel:
    """测试Defect模型"""
    
    def test_create_defect(self, db_session, sample_test_case, sample_user):
        """测试创建缺陷"""
        defect = Defect(
            test_case_id=sample_test_case.id,
            defect_type="functional",
            severity="high",
            description="座椅无法正常前进",
            root_cause="电机故障",
            reproduction_steps="1. 启动系统\n2. 按下前进按钮",
            expected_behavior="座椅向前移动",
            actual_behavior="座椅无反应",
            assigned_to=sample_user.id
        )
        
        db_session.add(defect)
        db_session.commit()
        db_session.refresh(defect)
        
        assert defect.id is not None
        assert defect.defect_type == "functional"
        assert defect.severity == "high"
        assert defect.status == "open"
        assert defect.test_case_id == sample_test_case.id
    
    def test_defect_relationships(self, db_session, sample_test_case, sample_user):
        """测试缺陷的关系"""
        defect = Defect(
            test_case_id=sample_test_case.id,
            defect_type="performance",
            severity="medium",
            description="响应时间过长",
            assigned_to=sample_user.id
        )
        
        db_session.add(defect)
        db_session.commit()
        db_session.refresh(defect)
        
        assert defect.test_case.title == sample_test_case.title
        assert defect.assignee.username == sample_user.username
        assert defect in sample_test_case.defects
        assert defect in sample_user.assigned_defects


class TestCoverageAnalysisModel:
    """测试CoverageAnalysis模型"""
    
    def test_create_coverage_analysis(self, db_session, sample_requirement):
        """测试创建覆盖率分析"""
        coverage = CoverageAnalysis(
            requirement_id=sample_requirement.id,
            function_module="seat_adjustment",
            coverage_percentage=85.5,
            covered_test_cases=17,
            total_test_cases=20,
            uncovered_areas=["边界值测试", "异常处理"],
            coverage_details={"unit_tests": 90, "integration_tests": 80}
        )
        
        db_session.add(coverage)
        db_session.commit()
        db_session.refresh(coverage)
        
        assert coverage.id is not None
        assert coverage.function_module == "seat_adjustment"
        assert coverage.coverage_percentage == 85.5
        assert coverage.covered_test_cases == 17
        assert coverage.total_test_cases == 20
        assert "边界值测试" in coverage.uncovered_areas
    
    def test_coverage_requirement_relationship(self, db_session, sample_requirement):
        """测试覆盖率分析与需求的关系"""
        coverage = CoverageAnalysis(
            requirement_id=sample_requirement.id,
            function_module="seat_memory",
            coverage_percentage=75.0,
            covered_test_cases=15,
            total_test_cases=20
        )
        
        db_session.add(coverage)
        db_session.commit()
        db_session.refresh(coverage)
        
        assert coverage.requirement.title == sample_requirement.title
        assert coverage in sample_requirement.coverage_analyses


class TestAlertRuleModel:
    """测试AlertRule模型"""
    
    def test_create_alert_rule(self, db_session, sample_user):
        """测试创建告警规则"""
        alert_rule = AlertRule(
            rule_name="覆盖率低告警",
            metric_type="coverage_rate",
            condition_operator="<",
            threshold_value=80.0,
            severity="high",
            notification_channels=["email", "in_app"],
            description="当覆盖率低于80%时触发告警",
            created_by=sample_user.id
        )
        
        db_session.add(alert_rule)
        db_session.commit()
        db_session.refresh(alert_rule)
        
        assert alert_rule.id is not None
        assert alert_rule.rule_name == "覆盖率低告警"
        assert alert_rule.metric_type == "coverage_rate"
        assert alert_rule.condition_operator == "<"
        assert alert_rule.threshold_value == 80.0
        assert alert_rule.is_active is True
        assert "email" in alert_rule.notification_channels
    
    def test_alert_rule_user_relationship(self, db_session, sample_user):
        """测试告警规则与用户的关系"""
        alert_rule = AlertRule(
            rule_name="缺陷率高告警",
            metric_type="defect_rate",
            condition_operator=">",
            threshold_value=5.0,
            created_by=sample_user.id
        )
        
        db_session.add(alert_rule)
        db_session.commit()
        db_session.refresh(alert_rule)
        
        assert alert_rule.creator.username == sample_user.username
        assert alert_rule in sample_user.alert_rules


class TestAlertModel:
    """测试Alert模型"""
    
    def test_create_alert(self, db_session, sample_user):
        """测试创建告警"""
        # 先创建告警规则
        alert_rule = AlertRule(
            rule_name="执行时间过长告警",
            metric_type="execution_time",
            condition_operator=">",
            threshold_value=300.0,
            created_by=sample_user.id
        )
        db_session.add(alert_rule)
        db_session.commit()
        db_session.refresh(alert_rule)
        
        # 创建告警
        alert = Alert(
            rule_id=alert_rule.id,
            alert_message="测试执行时间超过5分钟",
            current_value=450.0,
            threshold_value=300.0,
            severity="medium"
        )
        
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.alert_message == "测试执行时间超过5分钟"
        assert alert.current_value == 450.0
        assert alert.status == "active"
        assert alert.rule_id == alert_rule.id
    
    def test_alert_relationships(self, db_session, sample_user):
        """测试告警的关系"""
        # 创建告警规则
        alert_rule = AlertRule(
            rule_name="失败率高告警",
            metric_type="failure_rate",
            condition_operator=">",
            threshold_value=10.0,
            created_by=sample_user.id
        )
        db_session.add(alert_rule)
        db_session.commit()
        
        # 创建告警
        alert = Alert(
            rule_id=alert_rule.id,
            alert_message="测试失败率过高",
            current_value=15.0,
            threshold_value=10.0,
            severity="high",
            acknowledged_by=sample_user.id
        )
        
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        assert alert.rule.rule_name == alert_rule.rule_name
        assert alert.acknowledger.username == sample_user.username
        assert alert in alert_rule.alerts
        assert alert in sample_user.acknowledged_alerts


class TestReportTemplateModel:
    """测试ReportTemplate模型"""
    
    def test_create_report_template(self, db_session, sample_user):
        """测试创建报告模板"""
        template = ReportTemplate(
            template_name="标准执行报告模板",
            template_type="execution",
            template_content="<html><body>{{content}}</body></html>",
            template_config={
                "sections": ["summary", "details", "charts"],
                "chart_types": ["bar", "pie"],
                "filters": ["date_range", "test_type"]
            },
            description="标准的测试执行报告模板",
            created_by=sample_user.id,
            is_default=True
        )
        
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        
        assert template.id is not None
        assert template.template_name == "标准执行报告模板"
        assert template.template_type == "execution"
        assert template.is_default is True
        assert template.is_active is True
        assert "summary" in template.template_config["sections"]
    
    def test_template_user_relationship(self, db_session, sample_user):
        """测试模板与用户的关系"""
        template = ReportTemplate(
            template_name="自定义缺陷报告",
            template_type="defect_analysis",
            template_content="{{defect_summary}}",
            created_by=sample_user.id
        )
        
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        
        assert template.creator.username == sample_user.username
        assert template in sample_user.report_templates
    
    def test_template_report_relationship(self, db_session, sample_user):
        """测试模板与报告的关系"""
        template = ReportTemplate(
            template_name="覆盖率报告模板",
            template_type="coverage",
            template_content="{{coverage_data}}",
            created_by=sample_user.id
        )
        db_session.add(template)
        db_session.commit()
        
        report = Report(
            title="覆盖率分析报告",
            report_type="coverage",
            template_id=template.id,
            generated_by=sample_user.id
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.template.template_name == template.template_name
        assert report in template.reports


class TestSystemMetricModel:
    """测试SystemMetric模型"""
    
    def test_create_system_metric(self, db_session):
        """测试创建系统指标"""
        metric = SystemMetric(
            metric_name="test_execution_time",
            metric_type="performance",
            metric_value=125.5,
            unit="seconds",
            tags={"test_suite": "regression", "environment": "staging"}
        )
        
        db_session.add(metric)
        db_session.commit()
        db_session.refresh(metric)
        
        assert metric.id is not None
        assert metric.metric_name == "test_execution_time"
        assert metric.metric_type == "performance"
        assert metric.metric_value == 125.5
        assert metric.unit == "seconds"
        assert metric.tags["test_suite"] == "regression"
    
    def test_multiple_metrics(self, db_session):
        """测试创建多个系统指标"""
        metrics = [
            SystemMetric(
                metric_name="cpu_usage",
                metric_type="system",
                metric_value=75.2,
                unit="percentage"
            ),
            SystemMetric(
                metric_name="memory_usage",
                metric_type="system",
                metric_value=1024.0,
                unit="MB"
            ),
            SystemMetric(
                metric_name="test_pass_rate",
                metric_type="business",
                metric_value=92.5,
                unit="percentage"
            )
        ]
        
        for metric in metrics:
            db_session.add(metric)
        db_session.commit()
        
        # 验证所有指标都已保存
        saved_metrics = db_session.query(SystemMetric).all()
        assert len(saved_metrics) == 3
        
        metric_names = [m.metric_name for m in saved_metrics]
        assert "cpu_usage" in metric_names
        assert "memory_usage" in metric_names
        assert "test_pass_rate" in metric_names


class TestModelConstraints:
    """测试模型约束和验证"""
    
    def test_report_required_fields(self, db_session, sample_user):
        """测试报告必填字段"""
        with pytest.raises(Exception):
            # 缺少title字段
            report = Report(
                report_type="execution",
                generated_by=sample_user.id
            )
            db_session.add(report)
            db_session.commit()
    
    def test_defect_required_fields(self, db_session, sample_test_case):
        """测试缺陷必填字段"""
        with pytest.raises(Exception):
            # 缺少severity字段
            defect = Defect(
                test_case_id=sample_test_case.id,
                defect_type="functional",
                description="测试缺陷"
            )
            db_session.add(defect)
            db_session.commit()
    
    def test_alert_rule_required_fields(self, db_session, sample_user):
        """测试告警规则必填字段"""
        with pytest.raises(Exception):
            # 缺少threshold_value字段
            alert_rule = AlertRule(
                rule_name="测试规则",
                metric_type="coverage_rate",
                condition_operator="<",
                created_by=sample_user.id
            )
            db_session.add(alert_rule)
            db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])