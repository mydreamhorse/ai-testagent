from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from ..database import get_db
from ..models import User, Requirement, TestCase, GenerationLog
from ..schemas import (
    GenerationRequest, GenerationResponse, APIResponse
)
from ..routers.auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/test-cases", response_model=GenerationResponse)
async def generate_test_cases(
    request: GenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if requirement exists and belongs to user
    requirement = db.query(Requirement).filter(
        Requirement.id == request.requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create generation log
    log = GenerationLog(
        requirement_id=request.requirement_id,
        user_id=current_user.id,
        generation_type="test_generation",
        input_data=request.model_dump(),
        status="processing"
    )
    db.add(log)
    db.commit()
    
    try:
        # Import test case generator
        from ..ai.test_case_generator import TestCaseGenerator
        
        # Initialize generator and generate test cases
        generator = TestCaseGenerator()
        test_cases = generator.generate_test_cases(requirement, db)
        
        # Update log with success
        log.status = "completed"
        log.output_data = {
            "test_cases_count": len(test_cases),
            "test_cases": [
                {
                    "title": tc.title,
                    "test_type": tc.test_type,
                    "priority": tc.priority
                } for tc in test_cases
            ]
        }
        db.commit()
        
        return GenerationResponse(
            task_id=task_id,
            status="completed",
            message=f"Generated {len(test_cases)} test cases successfully",
            estimated_time=0
        )
        
    except Exception as e:
        # Update log with failure
        log.status = "failed"
        log.error_message = str(e)
        db.commit()
        
        logger.error(f"Error generating test cases for requirement {request.requirement_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating test cases: {str(e)}"
        )


@router.post("/evaluation", response_model=GenerationResponse)
async def generate_evaluation(
    request: GenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if requirement exists and belongs to user
    requirement = db.query(Requirement).filter(
        Requirement.id == request.requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create generation log
    log = GenerationLog(
        requirement_id=request.requirement_id,
        user_id=current_user.id,
        generation_type="quality_evaluation",
        input_data=request.model_dump(),
        status="processing"
    )
    db.add(log)
    db.commit()
    
    try:
        # Import quality evaluator
        from ..ai.quality_evaluator import QualityEvaluator
        
        # Get test cases for this requirement
        test_cases = db.query(TestCase).filter(
            TestCase.requirement_id == request.requirement_id,
            TestCase.user_id == current_user.id
        ).all()
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No test cases found for this requirement")
        
        # Initialize evaluator and evaluate test cases
        evaluator = QualityEvaluator()
        evaluation_results = []
        
        for test_case in test_cases:
            result = evaluator.evaluate_test_case(test_case, db)
            evaluation_results.append({
                "test_case_id": test_case.id,
                "total_score": result.total_score,
                "completeness_score": result.completeness_score,
                "accuracy_score": result.accuracy_score,
                "executability_score": result.executability_score,
                "coverage_score": result.coverage_score,
                "clarity_score": result.clarity_score
            })
        
        # Update log with success
        log.status = "completed"
        log.output_data = {
            "evaluated_count": len(evaluation_results),
            "average_score": sum(r["total_score"] for r in evaluation_results) / len(evaluation_results),
            "evaluations": evaluation_results
        }
        db.commit()
        
        return GenerationResponse(
            task_id=task_id,
            status="completed",
            message=f"Evaluated {len(evaluation_results)} test cases successfully",
            estimated_time=0
        )
        
    except Exception as e:
        # Update log with failure
        log.status = "failed"
        log.error_message = str(e)
        db.commit()
        
        logger.error(f"Error evaluating test cases for requirement {request.requirement_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating test cases: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=APIResponse)
async def get_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # TODO: Implement task status checking
    # For now, return a placeholder response
    return APIResponse(
        success=True,
        message="Task status retrieved",
        data={
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "result": "Task completed successfully"
        }
    )


@router.get("/history", response_model=List[dict])
async def get_generation_history(
    generation_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(GenerationLog).filter(GenerationLog.user_id == current_user.id)
    
    if generation_type:
        query = query.filter(GenerationLog.generation_type == generation_type)
    
    logs = query.order_by(GenerationLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "requirement_id": log.requirement_id,
            "generation_type": log.generation_type,
            "status": log.status,
            "processing_time": log.processing_time,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.post("/history", response_model=dict)
async def create_generation_history(
    history_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建生成历史记录"""
    try:
        # 检查需求是否存在
        requirement = db.query(Requirement).filter(
            Requirement.id == history_data.get("requirement_id"),
            Requirement.user_id == current_user.id
        ).first()
        
        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        # 创建生成日志
        log = GenerationLog(
            requirement_id=history_data.get("requirement_id"),
            user_id=current_user.id,
            generation_type=history_data.get("generation_type", "test_cases"),
            status=history_data.get("status", "completed"),
            processing_time=history_data.get("processing_time", 0),
            created_at=datetime.fromisoformat(history_data.get("created_at")) if history_data.get("created_at") else datetime.utcnow()
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return {
            "id": log.id,
            "requirement_id": log.requirement_id,
            "generation_type": log.generation_type,
            "status": log.status,
            "processing_time": log.processing_time,
            "created_at": log.created_at
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create generation history: {str(e)}")