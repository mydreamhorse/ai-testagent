from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import KnowledgeBase
from ..schemas import (
    KnowledgeBaseCreate, KnowledgeBase as KnowledgeBaseSchema,
    APIResponse
)
from ..routers.auth import get_current_active_user
from ..models import User

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseSchema)
async def create_knowledge(
    knowledge: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_knowledge = KnowledgeBase(**knowledge.model_dump())
    db.add(db_knowledge)
    db.commit()
    db.refresh(db_knowledge)
    return db_knowledge


@router.get("/", response_model=List[KnowledgeBaseSchema])
async def read_knowledge(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    
    if subcategory:
        query = query.filter(KnowledgeBase.subcategory == subcategory)
    
    if search:
        query = query.filter(
            KnowledgeBase.title.contains(search) |
            KnowledgeBase.content.contains(search)
        )
    
    knowledge = query.offset(skip).limit(limit).all()
    return knowledge


@router.get("/{knowledge_id}", response_model=KnowledgeBaseSchema)
async def read_knowledge_item(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    knowledge = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_id,
        KnowledgeBase.is_active == True
    ).first()
    if knowledge is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    # Increment usage count
    knowledge.usage_count += 1
    db.commit()
    
    return knowledge


@router.put("/{knowledge_id}", response_model=KnowledgeBaseSchema)
async def update_knowledge(
    knowledge_id: int,
    knowledge: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
    if db_knowledge is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    for key, value in knowledge.model_dump().items():
        setattr(db_knowledge, key, value)
    
    db.commit()
    db.refresh(db_knowledge)
    return db_knowledge


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    knowledge = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
    if knowledge is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    knowledge.is_active = False
    db.commit()
    return {"message": "Knowledge item deleted successfully"}


@router.get("/categories/list", response_model=List[str])
async def get_knowledge_categories(db: Session = Depends(get_db)):
    categories = db.query(KnowledgeBase.category).filter(
        KnowledgeBase.is_active == True
    ).distinct().all()
    return [category[0] for category in categories]


@router.get("/categories/{category}/subcategories", response_model=List[str])
async def get_knowledge_subcategories(
    category: str,
    db: Session = Depends(get_db)
):
    subcategories = db.query(KnowledgeBase.subcategory).filter(
        KnowledgeBase.category == category,
        KnowledgeBase.is_active == True,
        KnowledgeBase.subcategory.isnot(None)
    ).distinct().all()
    return [subcategory[0] for subcategory in subcategories]


@router.post("/search", response_model=List[KnowledgeBaseSchema])
async def search_knowledge(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # Simple text search - can be enhanced with full-text search or vector search
    search_query = db.query(KnowledgeBase).filter(
        KnowledgeBase.is_active == True
    )
    
    if category:
        search_query = search_query.filter(KnowledgeBase.category == category)
    
    # Search in title and content
    search_query = search_query.filter(
        KnowledgeBase.title.contains(query) |
        KnowledgeBase.content.contains(query)
    )
    
    results = search_query.limit(limit).all()
    return results