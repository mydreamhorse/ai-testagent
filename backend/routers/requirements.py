from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import logging
from datetime import datetime

from ..database import get_db
from ..models import User, Requirement, ParsedFeature
from ..schemas import (
    RequirementCreate, RequirementUpdate, Requirement as RequirementSchema,
    ParsedFeature as ParsedFeatureSchema, APIResponse, FileUploadResponse
)
from ..routers.auth import get_current_active_user
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=RequirementSchema)
async def create_requirement(
    requirement: RequirementCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_requirement = Requirement(
        **requirement.model_dump(),
        user_id=current_user.id
    )
    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


@router.get("/", response_model=List[RequirementSchema])
async def read_requirements(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    requirements = db.query(Requirement).filter(
        Requirement.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    # Seed a default requirement for the current user if none exist
    if not requirements:
        seed_requirement = Requirement(
            title="示例需求",
            description="这是为当前用户自动创建的示例需求，用于初始化数据。",
            content="座椅应能够通过电动方式进行前后、上下、靠背角度调节。",
            user_id=current_user.id,
            status="pending",
        )
        db.add(seed_requirement)
        db.commit()
        db.refresh(seed_requirement)
        requirements = [seed_requirement]
    return requirements


@router.get("/{requirement_id}", response_model=RequirementSchema)
async def read_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.put("/{requirement_id}", response_model=RequirementSchema)
async def update_requirement(
    requirement_id: int,
    requirement: RequirementUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if db_requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    for key, value in requirement.dict(exclude_unset=True).items():
        setattr(db_requirement, key, value)
    
    db_requirement.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


@router.delete("/{requirement_id}")
async def delete_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    db.delete(requirement)
    db.commit()
    return {"message": "Requirement deleted successfully"}


@router.post("/upload", response_model=FileUploadResponse)
async def upload_requirement_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    # Check file type
    allowed_types = ['.txt', '.pdf', '.doc', '.docx']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, filename)
    
    # Save file with size limit enforcement
    bytes_written = 0
    try:
        with open(file_path, "wb") as buffer:
            chunk_size = 1024 * 1024  # 1MB
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > settings.max_file_size:
                    # Remove partially written file
                    buffer.close()
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
                    )
                buffer.write(chunk)
    finally:
        await file.close()
    
    return FileUploadResponse(
        filename=file.filename,
        file_path=file_path,
        file_size=bytes_written,
        file_type=file_extension,
        upload_time=datetime.utcnow()
    )


@router.get("/{requirement_id}/features", response_model=List[ParsedFeatureSchema])
async def get_requirement_features(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if requirement exists and belongs to user
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    features = db.query(ParsedFeature).filter(
        ParsedFeature.requirement_id == requirement_id
    ).all()
    return features


@router.post("/{requirement_id}/parse", response_model=APIResponse)
async def parse_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if requirement exists and belongs to user
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    if requirement is None:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    try:
        # Import requirement parser
        from ..ai.requirement_parser import RequirementParser
        
        # Initialize parser and parse requirement
        parser = RequirementParser()
        features = parser.parse_requirement(requirement, db)
        
        # Update requirement status
        requirement.status = "completed"
        db.commit()
        
        return APIResponse(
            success=True,
            message="Requirement parsing completed successfully",
            data={
                "requirement_id": requirement_id, 
                "status": "completed",
                "features_count": len(features),
                "features": [
                    {
                        "name": f.name,
                        "type": f.type,
                        "priority": f.priority
                    } for f in features
                ]
            }
        )
    except Exception as e:
        # Update requirement status to failed
        requirement.status = "failed"
        db.commit()
        
        logger.error(f"Error parsing requirement {requirement_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing requirement: {str(e)}"
        )