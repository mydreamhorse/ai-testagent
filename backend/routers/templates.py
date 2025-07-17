from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import TestTemplate
from ..schemas import (
    TestTemplateCreate, TestTemplate as TestTemplateSchema,
    APIResponse
)
from ..routers.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=TestTemplateSchema)
async def create_template(
    template: TestTemplateCreate,
    db: Session = Depends(get_db)
):
    db_template = TestTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/", response_model=List[TestTemplateSchema])
async def read_templates(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(TestTemplate).filter(TestTemplate.is_active == True)
    
    if category:
        query = query.filter(TestTemplate.category == category)
    
    templates = query.offset(skip).limit(limit).all()
    return templates


@router.get("/{template_id}", response_model=TestTemplateSchema)
async def read_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    template = db.query(TestTemplate).filter(
        TestTemplate.id == template_id,
        TestTemplate.is_active == True
    ).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=TestTemplateSchema)
async def update_template(
    template_id: int,
    template: TestTemplateCreate,
    db: Session = Depends(get_db)
):
    db_template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template.dict().items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    template = db.query(TestTemplate).filter(TestTemplate.id == template_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    db.commit()
    return {"message": "Template deleted successfully"}


@router.get("/categories/list", response_model=List[str])
async def get_template_categories(db: Session = Depends(get_db)):
    categories = db.query(TestTemplate.category).filter(
        TestTemplate.is_active == True
    ).distinct().all()
    return [category[0] for category in categories]