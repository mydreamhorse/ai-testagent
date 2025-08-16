from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirements = relationship(
        "Requirement",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    test_cases = relationship(
        "TestCase",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assigned_defects = relationship(
        "Defect",
        back_populates="assignee",
        foreign_keys="Defect.assigned_to"
    )
    alert_rules = relationship(
        "AlertRule",
        back_populates="creator",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    acknowledged_alerts = relationship(
        "Alert",
        back_populates="acknowledger",
        foreign_keys="Alert.acknowledged_by"
    )
    report_templates = relationship(
        "ReportTemplate",
        back_populates="creator",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Requirement(Base):
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="requirements")
    test_cases = relationship(
        "TestCase",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    parsed_features = relationship(
        "ParsedFeature",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    coverage_analyses = relationship(
        "CoverageAnalysis",
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ParsedFeature(Base):
    __tablename__ = "parsed_features"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    feature_name = Column(String(200), nullable=False)
    feature_type = Column(String(50))  # function, performance, security, etc.
    description = Column(Text)
    parameters = Column(JSON)
    constraints = Column(JSON)
    dependencies = Column(JSON)
    priority = Column(String(20), default="medium")  # high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    requirement = relationship("Requirement", back_populates="parsed_features")


class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    test_type = Column(String(50))  # function, boundary, exception, performance, security
    preconditions = Column(Text)
    test_steps = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="active")  # active, inactive, deprecated
    generated_by = Column(String(50), default="ai")  # ai, human, template
    template_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirement = relationship("Requirement", back_populates="test_cases")
    user = relationship("User", back_populates="test_cases")
    evaluations = relationship(
        "TestCaseEvaluation",
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    defects = relationship(
        "Defect",
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TestCaseEvaluation(Base):
    __tablename__ = "test_case_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    
    # Quality scores (0-100)
    completeness_score = Column(Float, default=0)
    accuracy_score = Column(Float, default=0)
    executability_score = Column(Float, default=0)
    coverage_score = Column(Float, default=0)
    clarity_score = Column(Float, default=0)
    total_score = Column(Float, default=0)
    
    # Detailed evaluation
    evaluation_details = Column(JSON)
    suggestions = Column(JSON)
    evaluator_type = Column(String(50), default="ai")  # ai, human, hybrid
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="evaluations")


class TestTemplate(Base):
    __tablename__ = "test_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # function, boundary, exception, performance, security
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    variables = Column(JSON)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)  # seat_functions, test_standards, failure_modes
    subcategory = Column(String(100))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON)
    source = Column(String(200))
    confidence = Column(Float, default=1.0)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationLog(Base):
    __tablename__ = "generation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    generation_type = Column(String(50))  # requirement_parsing, test_generation, quality_evaluation
    input_data = Column(JSON)
    output_data = Column(JSON)
    model_used = Column(String(100))
    processing_time = Column(Float)  # seconds
    tokens_used = Column(Integer)
    cost = Column(Float)
    status = Column(String(20))  # success, failed, partial
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Intelligent Test Reporting Models

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # execution, defect_analysis, coverage, trend, custom
    template_id = Column(Integer, ForeignKey("report_templates.id"))
    generated_by = Column(Integer, ForeignKey("users.id"))
    generation_time = Column(DateTime, default=datetime.utcnow)
    data_range_start = Column(DateTime)
    data_range_end = Column(DateTime)
    report_data = Column(JSON)
    file_path = Column(String(500))
    status = Column(String(20), default="generating")  # generating, completed, failed, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = relationship("ReportTemplate", back_populates="reports")
    user = relationship("User", back_populates="reports")


class Defect(Base):
    __tablename__ = "defects"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    defect_type = Column(String(50), nullable=False)  # functional, performance, security, usability, compatibility
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    description = Column(Text, nullable=False)
    root_cause = Column(Text)
    reproduction_steps = Column(Text)
    expected_behavior = Column(Text)
    actual_behavior = Column(Text)
    environment_info = Column(JSON)
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed, rejected
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="defects")
    assignee = relationship("User", back_populates="assigned_defects")


class CoverageAnalysis(Base):
    __tablename__ = "coverage_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    function_module = Column(String(100), nullable=False)
    coverage_percentage = Column(Float, nullable=False, default=0.0)
    covered_test_cases = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    uncovered_areas = Column(JSON)  # List of uncovered functionality
    coverage_details = Column(JSON)  # Detailed coverage breakdown
    analysis_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirement = relationship("Requirement", back_populates="coverage_analyses")


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # coverage_rate, defect_rate, execution_time, failure_rate
    condition_operator = Column(String(10), nullable=False)  # >, <, >=, <=, ==, !=
    threshold_value = Column(Float, nullable=False)
    severity = Column(String(20), default="medium")  # critical, high, medium, low
    notification_channels = Column(JSON)  # email, sms, webhook, in_app
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="alert_rules")
    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))
    alert_message = Column(Text, nullable=False)
    current_value = Column(Float)
    threshold_value = Column(Float)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    acknowledger = relationship("User", back_populates="acknowledged_alerts")


class ReportTemplate(Base):
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    template_type = Column(String(50), nullable=False)  # execution, defect_analysis, coverage, trend, custom
    template_content = Column(Text, nullable=False)  # Template structure/layout definition
    template_config = Column(JSON)  # Configuration for charts, filters, sections
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="report_templates")
    reports = relationship("Report", back_populates="template")


class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # performance, business, system
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20))  # percentage, seconds, count, bytes
    tags = Column(JSON)  # Additional metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)