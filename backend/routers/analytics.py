from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models import Requirement, TestCase, ParsedFeature, TestCaseEvaluation, User
from ..routers.auth import get_current_active_user


router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
async def get_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    requirements_count = (
        db.query(Requirement).filter(Requirement.user_id == current_user.id).count()
    )
    test_cases_count = (
        db.query(TestCase).filter(TestCase.user_id == current_user.id).count()
    )
    features_count = (
        db.query(ParsedFeature)
        .join(Requirement, ParsedFeature.requirement_id == Requirement.id)
        .filter(Requirement.user_id == current_user.id)
        .count()
    )
    # Average score from all evaluations for this user (simplified)
    evaluations = (
        db.query(TestCaseEvaluation.total_score)
        .join(TestCase, TestCaseEvaluation.test_case_id == TestCase.id)
        .filter(TestCase.user_id == current_user.id)
        .all()
    )
    avg_score = (
        sum(e.total_score for e in evaluations) / len(evaluations) if evaluations else 0
    )
    return {
        "requirements_count": requirements_count,
        "test_cases_count": test_cases_count,
        "features_count": features_count,
        "average_score": avg_score,
    }


@router.get("/breakdown", response_model=Dict[str, Any])
async def get_breakdown(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    status_rows = (
        db.query(Requirement.status, func.count(Requirement.id))
        .filter(Requirement.user_id == current_user.id)
        .group_by(Requirement.status)
        .all()
    )
    requirement_status = {status: count for status, count in status_rows}

    priority_rows = (
        db.query(TestCase.priority, func.count(TestCase.id))
        .filter(TestCase.user_id == current_user.id)
        .group_by(TestCase.priority)
        .all()
    )
    test_case_priority = {priority: count for priority, count in priority_rows}

    type_rows = (
        db.query(TestCase.test_type, func.count(TestCase.id))
        .filter(TestCase.user_id == current_user.id)
        .group_by(TestCase.test_type)
        .all()
    )
    test_type = {name: count for name, count in type_rows}

    return {
        "requirement_status": requirement_status,
        "test_case_priority": test_case_priority,
        "test_type": test_type,
    }
