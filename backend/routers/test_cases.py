from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from ..database import get_db
from ..models import User, TestCase, TestCaseEvaluation, Requirement
from ..schemas import (
    TestCaseCreate, TestCaseUpdate, TestCase as TestCaseSchema,
    TestCaseEvaluation as TestCaseEvaluationSchema,
    APIResponse
)
from ..routers.auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=TestCaseSchema)
async def create_test_case(
    test_case: TestCaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if requirement exists and belongs to user
    requirement = db.query(Requirement).filter(
        Requirement.id == test_case.requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    db_test_case = TestCase(
        **test_case.dict(),
        user_id=current_user.id,
        generated_by="human"
    )
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


@router.get("/", response_model=List[TestCaseSchema])
async def read_test_cases(
    requirement_id: Optional[int] = None,
    test_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(TestCase).filter(TestCase.user_id == current_user.id)
    
    if requirement_id:
        query = query.filter(TestCase.requirement_id == requirement_id)
    
    if test_type:
        query = query.filter(TestCase.test_type == test_type)
    
    test_cases = query.offset(skip).limit(limit).all()
    return test_cases


@router.get("/{test_case_id}", response_model=TestCaseSchema)
async def read_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.user_id == current_user.id
    ).first()
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@router.put("/{test_case_id}", response_model=TestCaseSchema)
async def update_test_case(
    test_case_id: int,
    test_case: TestCaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.user_id == current_user.id
    ).first()
    if db_test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    for key, value in test_case.dict(exclude_unset=True).items():
        setattr(db_test_case, key, value)
    
    db_test_case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


@router.delete("/{test_case_id}")
async def delete_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.user_id == current_user.id
    ).first()
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    db.delete(test_case)
    db.commit()
    return {"message": "Test case deleted successfully"}


@router.get("/{test_case_id}/evaluation", response_model=TestCaseEvaluationSchema)
async def get_test_case_evaluation(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if test case exists and belongs to user
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.user_id == current_user.id
    ).first()
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    evaluation = db.query(TestCaseEvaluation).filter(
        TestCaseEvaluation.test_case_id == test_case_id
    ).first()
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return evaluation


@router.post("/{test_case_id}/evaluate", response_model=APIResponse)
async def evaluate_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if test case exists and belongs to user
    test_case = db.query(TestCase).filter(
        TestCase.id == test_case_id,
        TestCase.user_id == current_user.id
    ).first()
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    try:
        # Import quality evaluator
        from ..ai.quality_evaluator import QualityEvaluator
        
        # Initialize evaluator and evaluate test case
        evaluator = QualityEvaluator()
        result = evaluator.evaluate_test_case(test_case, db)
        
        return APIResponse(
            success=True,
            message="Test case evaluation completed successfully",
            data={
                "test_case_id": test_case_id,
                "status": "completed",
                "evaluation": {
                    "total_score": result.total_score,
                    "completeness_score": result.completeness_score,
                    "accuracy_score": result.accuracy_score,
                    "executability_score": result.executability_score,
                    "coverage_score": result.coverage_score,
                    "clarity_score": result.clarity_score,
                    "suggestions": result.suggestions
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error evaluating test case {test_case_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating test case: {str(e)}"
        )


@router.post("/batch-evaluate", response_model=APIResponse)
async def batch_evaluate_test_cases(
    test_case_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if all test cases exist and belong to user
    test_cases = db.query(TestCase).filter(
        TestCase.id.in_(test_case_ids),
        TestCase.user_id == current_user.id
    ).all()
    
    if len(test_cases) != len(test_case_ids):
        raise HTTPException(status_code=404, detail="One or more test cases not found")
    
    try:
        # Import quality evaluator
        from ..ai.quality_evaluator import QualityEvaluator
        
        # Initialize evaluator and evaluate all test cases
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
        
        return APIResponse(
            success=True,
            message="Batch evaluation completed successfully",
            data={
                "evaluated_count": len(evaluation_results),
                "average_score": sum(r["total_score"] for r in evaluation_results) / len(evaluation_results),
                "evaluations": evaluation_results
            }
        )
        
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch evaluation: {str(e)}"
        )