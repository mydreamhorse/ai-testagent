from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Report, ReportTemplate, User, Defect, CoverageAnalysis
from ..schemas import APIResponse
from ..routers.auth import get_current_user
from ..services.report_generator import ReportGenerator
from ..services.export_manager import ExportManager
from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic schemas for report management
class ReportBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    report_type: str = Field(..., pattern="^(execution|defect_analysis|coverage|trend|custom)$")
    template_id: Optional[int] = None
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None

class ReportCreate(ReportBase):
    report_data: Optional[Dict[str, Any]] = None

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    report_data: Optional[Dict[str, Any]] = None

class ReportResponse(ReportBase):
    id: int
    generated_by: int
    generation_time: datetime
    report_data: Optional[Dict[str, Any]]
    file_path: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportGenerationRequest(BaseModel):
    report_type: str = Field(..., pattern="^(execution|defect_analysis|coverage|trend|custom)$")
    title: str = Field(..., min_length=1, max_length=200)
    template_id: Optional[int] = None
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    export_format: Optional[str] = Field(None, pattern="^(pdf|excel|html)$")

class ReportShareRequest(BaseModel):
    report_id: int
    share_with_users: Optional[List[int]] = None
    share_via_email: Optional[List[str]] = None
    share_via_link: bool = False
    expiry_date: Optional[datetime] = None

# Report CRUD operations
@router.get("/", response_model=APIResponse)
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告列表"""
    try:
        query = db.query(Report).filter(Report.generated_by == current_user.id)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        if status:
            query = query.filter(Report.status == status)
            
        total = query.count()
        reports = query.offset(skip).limit(limit).all()
        
        return APIResponse(
            success=True,
            message="报告列表获取成功",
            data={
                "reports": [ReportResponse.from_orm(report) for report in reports],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告列表失败: {str(e)}"
        )

@router.get("/{report_id}", response_model=APIResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个报告详情"""
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
            
        return APIResponse(
            success=True,
            message="报告详情获取成功",
            data=ReportResponse.from_orm(report)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告详情失败: {str(e)}"
        )

@router.post("/", response_model=APIResponse)
async def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新报告"""
    try:
        # 验证模板是否存在
        if report_data.template_id:
            template = db.query(ReportTemplate).filter(
                ReportTemplate.id == report_data.template_id,
                ReportTemplate.is_active == True
            ).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="报告模板不存在"
                )
        
        # 创建报告记录
        db_report = Report(
            title=report_data.title,
            report_type=report_data.report_type,
            template_id=report_data.template_id,
            generated_by=current_user.id,
            data_range_start=report_data.data_range_start,
            data_range_end=report_data.data_range_end,
            report_data=report_data.report_data,
            status="created"
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return APIResponse(
            success=True,
            message="报告创建成功",
            data=ReportResponse.from_orm(db_report)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建报告失败: {str(e)}"
        )

@router.put("/{report_id}", response_model=APIResponse)
async def update_report(
    report_id: int,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报告"""
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        # 更新字段
        update_data = report_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(report, field, value)
        
        report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
        
        return APIResponse(
            success=True,
            message="报告更新成功",
            data=ReportResponse.from_orm(report)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新报告失败: {str(e)}"
        )

@router.delete("/{report_id}", response_model=APIResponse)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报告"""
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        # 删除关联文件
        if report.file_path:
            try:
                import os
                if os.path.exists(report.file_path):
                    os.remove(report.file_path)
            except Exception as e:
                print(f"删除报告文件失败: {e}")
        
        db.delete(report)
        db.commit()
        
        return APIResponse(
            success=True,
            message="报告删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除报告失败: {str(e)}"
        )

# Report generation and processing
@router.post("/generate", response_model=APIResponse)
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成报告（异步）"""
    try:
        # 创建报告记录
        db_report = Report(
            title=request.title,
            report_type=request.report_type,
            template_id=request.template_id,
            generated_by=current_user.id,
            data_range_start=request.data_range_start,
            data_range_end=request.data_range_end,
            status="generating"
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        # 添加后台任务生成报告
        background_tasks.add_task(
            _generate_report_task,
            db_report.id,
            request.dict(),
            current_user.id
        )
        
        return APIResponse(
            success=True,
            message="报告生成任务已启动",
            data={
                "report_id": db_report.id,
                "status": "generating",
                "estimated_time": 30  # 预估30秒
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动报告生成失败: {str(e)}"
        )

@router.get("/{report_id}/export", response_model=APIResponse)
async def export_report(
    report_id: int,
    format: str = Query(..., pattern="^(pdf|excel|html)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出报告"""
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.generated_by == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        if report.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="报告尚未生成完成"
            )
        
        # 使用导出管理器导出报告
        from ..services.export_manager import ExportManager, ExportFormat
        export_manager = ExportManager()
        
        # 转换格式字符串为枚举
        format_enum = ExportFormat(format)
        task_id = export_manager.export_report(report.id, format_enum)
        
        # 等待导出完成（简化版本，实际应该异步处理）
        import time
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            task_status = export_manager.get_export_status(task_id)
            if task_status and task_status.status.value == "completed":
                file_path = task_status.options.get('output_path')
                break
            elif task_status and task_status.status.value == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"导出失败: {task_status.error_message}"
                )
            time.sleep(1)
            wait_time += 1
        
        if wait_time >= max_wait:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="导出超时"
            )
        
        return APIResponse(
            success=True,
            message="报告导出成功",
            data={
                "file_path": file_path,
                "format": format,
                "download_url": f"/api/v1/reports/{report_id}/download?format={format}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出报告失败: {str(e)}"
        )

@router.post("/share", response_model=APIResponse)
async def share_report(
    request: ReportShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分享报告"""
    try:
        report = db.query(Report).filter(
            Report.id == request.report_id,
            Report.generated_by == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )
        
        # 实现分享逻辑
        share_info = {
            "report_id": request.report_id,
            "shared_by": current_user.id,
            "shared_at": datetime.utcnow().isoformat(),
            "expiry_date": request.expiry_date.isoformat() if request.expiry_date else None
        }
        
        if request.share_via_link:
            # 生成分享链接
            import uuid
            share_token = str(uuid.uuid4())
            share_info["share_token"] = share_token
            share_info["share_url"] = f"/shared/reports/{share_token}"
        
        return APIResponse(
            success=True,
            message="报告分享成功",
            data=share_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分享报告失败: {str(e)}"
        )

# Background task for report generation
async def _generate_report_task(report_id: int, request_data: dict, user_id: int):
    """后台报告生成任务"""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return
        
        # 使用报告生成器生成报告
        report_generator = ReportGenerator(db)
        
        if report.report_type == "execution":
            # 生成测试执行报告数据
            report_data = report_generator.data_collector.collect_execution_data(
                user_id=user_id
            )
        elif report.report_type == "defect_analysis":
            # 生成缺陷分析报告数据
            report_data = report_generator.data_collector.collect_defect_data()
        elif report.report_type == "coverage":
            # 生成覆盖率报告数据
            report_data = report_generator.data_collector.collect_coverage_data()
        else:
            report_data = {"message": "报告类型暂不支持"}
        
        # 更新报告状态和数据
        report.report_data = report_data
        report.status = "completed"
        report.updated_at = datetime.utcnow()
        
        # 如果需要导出文件
        export_format = request_data.get("export_format")
        if export_format:
            export_manager = ExportManager()
            file_path = await export_manager.export_report(report, export_format)
            report.file_path = file_path
        
        db.commit()
        
    except Exception as e:
        # 更新报告状态为失败
        if report:
            report.status = "failed"
            report.report_data = {"error": str(e)}
            report.updated_at = datetime.utcnow()
            db.commit()
        print(f"报告生成失败: {e}")
    finally:
        db.close()