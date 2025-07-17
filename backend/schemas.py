from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestType(str, Enum):
    FUNCTION = "function"
    BOUNDARY = "boundary"
    EXCEPTION = "exception"
    PERFORMANCE = "performance"
    SECURITY = "security"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Requirement schemas
class RequirementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class RequirementCreate(RequirementBase):
    content: str = Field(..., min_length=1)
    file_path: Optional[str] = None
    file_type: Optional[str] = None


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    status: Optional[Status] = None


class Requirement(RequirementBase):
    id: int
    content: str
    file_path: Optional[str]
    file_type: Optional[str]
    status: Status
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ParsedFeature schemas
class ParsedFeatureBase(BaseModel):
    feature_name: str = Field(..., min_length=1, max_length=200)
    feature_type: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None
    priority: Priority = Priority.MEDIUM


class ParsedFeatureCreate(ParsedFeatureBase):
    requirement_id: int


class ParsedFeature(ParsedFeatureBase):
    id: int
    requirement_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# TestCase schemas
class TestCaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    test_type: TestType
    preconditions: Optional[str] = None
    test_steps: str = Field(..., min_length=1)
    expected_result: str = Field(..., min_length=1)
    priority: Priority = Priority.MEDIUM


class TestCaseCreate(TestCaseBase):
    requirement_id: int
    template_id: Optional[str] = None


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[TestType] = None
    preconditions: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[str] = None


class TestCase(TestCaseBase):
    id: int
    requirement_id: int
    user_id: int
    status: str
    generated_by: str
    template_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# TestCaseEvaluation schemas
class TestCaseEvaluationBase(BaseModel):
    completeness_score: float = Field(..., ge=0, le=100)
    accuracy_score: float = Field(..., ge=0, le=100)
    executability_score: float = Field(..., ge=0, le=100)
    coverage_score: float = Field(..., ge=0, le=100)
    clarity_score: float = Field(..., ge=0, le=100)
    total_score: float = Field(..., ge=0, le=100)
    evaluation_details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    evaluator_type: str = "ai"


class TestCaseEvaluationCreate(TestCaseEvaluationBase):
    test_case_id: int


class TestCaseEvaluation(TestCaseEvaluationBase):
    id: int
    test_case_id: int
    evaluated_at: datetime
    
    class Config:
        from_attributes = True


# TestTemplate schemas
class TestTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str
    description: Optional[str] = None
    template_content: str = Field(..., min_length=1)
    variables: Optional[Dict[str, Any]] = None


class TestTemplateCreate(TestTemplateBase):
    pass


class TestTemplate(TestTemplateBase):
    id: int
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# KnowledgeBase schemas
class KnowledgeBaseBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0, le=1)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBase(KnowledgeBaseBase):
    id: int
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API Response schemas
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class GenerationRequest(BaseModel):
    requirement_id: int
    generation_type: str  # "test_cases", "evaluation"
    options: Optional[Dict[str, Any]] = None


class GenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None  # seconds


class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: datetime


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None