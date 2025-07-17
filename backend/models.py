from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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
    requirements = relationship("Requirement", back_populates="user")
    test_cases = relationship("TestCase", back_populates="user")


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
    test_cases = relationship("TestCase", back_populates="requirement")
    parsed_features = relationship("ParsedFeature", back_populates="requirement")


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
    evaluations = relationship("TestCaseEvaluation", back_populates="test_case")


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