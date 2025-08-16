from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Alert, AlertRule, SystemMetric, User, CoverageAnalysis, Defect
from ..schemas import APIResponse
from ..routers.auth import get_current_user
from ..services.monitoring_service import MonitoringService
from ..services.analytics_engine import AnalyticsEngine
from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic schemas for monitoring and analytics
class AlertRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    metric_type: str = Field(..., pattern="^(coverage_rate|defect_rate|execution_time|failure_rate|system_performance)$")
    condition_operator: str = Field(..., pattern="^(>|<|>=|<=|==|!=)$")
    threshold_value: float
    severity: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    notification_channels: List[str] = Field(default=["in_app"])
    description: Optional[str] = None

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    threshold_value: Optional[float] = None
    severity: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AlertRuleResponse(AlertRuleBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        # Handle None notification_channels
        if obj.notification_channels is None:
            obj.notification_channels = []
        return super().from_orm(obj)

class AlertResponse(BaseModel):
    id: int
    rule_id: int
    alert_message: str
    current_value: Optional[float]
    threshold_value: Optional[float]
    severity: str
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    acknowledged_by: Optional[int]

    class Config:
        from_attributes = True

class SystemMetricResponse(BaseModel):
    id: int
    metric_name: str
    metric_type: str
    metric_value: float
    unit: Optional[str]
    tags: Optional[Dict[str, Any]]
    recorded_at: datetime

    class Config:
        from_attributes = True

class AnalyticsQuery(BaseModel):
    metric_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: Optional[str] = Field(None, pattern="^(day|week|month|hour)$")
    aggregation: Optional[str] = Field(default="avg")

class MonitoringDashboardRequest(BaseModel):
    time_range: str = Field(default="24h", pattern="^(1h|6h|24h|7d|30d)$")
    metrics: Optional[List[str]] = None

# Alert Rule Management APIs
@router.get("/alert-rules", response_model=APIResponse)
async def get_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则列表"""
    try:
        query = db.query(AlertRule).filter(AlertRule.created_by == current_user.id)
        
        if is_active is not None:
            query = query.filter(AlertRule.is_active == is_active)
            
        total = query.count()
        rules = query.offset(skip).limit(limit).all()
        
        return APIResponse(
            success=True,
            message="告警规则列表获取成功",
            data={
                "rules": [AlertRuleResponse.from_orm(rule) for rule in rules],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警规则失败: {str(e)}"
        )

@router.post("/alert-rules", response_model=APIResponse)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建告警规则"""
    try:
        db_rule = AlertRule(
            rule_name=rule_data.rule_name,
            metric_type=rule_data.metric_type,
            condition_operator=rule_data.condition_operator,
            threshold_value=rule_data.threshold_value,
            severity=rule_data.severity,
            notification_channels=rule_data.notification_channels,
            description=rule_data.description,
            created_by=current_user.id
        )
        
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        return APIResponse(
            success=True,
            message="告警规则创建成功",
            data=AlertRuleResponse.from_orm(db_rule)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建告警规则失败: {str(e)}"
        )

@router.put("/alert-rules/{rule_id}", response_model=APIResponse)
async def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警规则"""
    try:
        rule = db.query(AlertRule).filter(
            AlertRule.id == rule_id,
            AlertRule.created_by == current_user.id
        ).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警规则不存在"
            )
        
        # 更新字段
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
        
        return APIResponse(
            success=True,
            message="告警规则更新成功",
            data=AlertRuleResponse.from_orm(rule)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新告警规则失败: {str(e)}"
        )

@router.delete("/alert-rules/{rule_id}", response_model=APIResponse)
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除告警规则"""
    try:
        rule = db.query(AlertRule).filter(
            AlertRule.id == rule_id,
            AlertRule.created_by == current_user.id
        ).first()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警规则不存在"
            )
        
        db.delete(rule)
        db.commit()
        
        return APIResponse(
            success=True,
            message="告警规则删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除告警规则失败: {str(e)}"
        )

# Alert Management APIs
@router.get("/alerts", response_model=APIResponse)
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警列表"""
    try:
        # 只获取当前用户创建的告警规则产生的告警
        query = db.query(Alert).join(AlertRule).filter(
            AlertRule.created_by == current_user.id
        )
        
        if status_filter:
            query = query.filter(Alert.status == status_filter)
        if severity:
            query = query.filter(Alert.severity == severity)
            
        total = query.count()
        alerts = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit).all()
        
        return APIResponse(
            success=True,
            message="告警列表获取成功",
            data={
                "alerts": [AlertResponse.from_orm(alert) for alert in alerts],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警列表失败: {str(e)}"
        )

@router.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认告警"""
    try:
        alert = db.query(Alert).join(AlertRule).filter(
            Alert.id == alert_id,
            AlertRule.created_by == current_user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
        
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = current_user.id
        
        db.commit()
        db.refresh(alert)
        
        return APIResponse(
            success=True,
            message="告警确认成功",
            data=AlertResponse.from_orm(alert)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认告警失败: {str(e)}"
        )

@router.post("/alerts/{alert_id}/resolve", response_model=APIResponse)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解决告警"""
    try:
        alert = db.query(Alert).join(AlertRule).filter(
            Alert.id == alert_id,
            AlertRule.created_by == current_user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
        
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        if not alert.acknowledged_by:
            alert.acknowledged_by = current_user.id
            alert.acknowledged_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        return APIResponse(
            success=True,
            message="告警解决成功",
            data=AlertResponse.from_orm(alert)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解决告警失败: {str(e)}"
        )

# System Metrics APIs
@router.get("/metrics", response_model=APIResponse)
async def get_system_metrics(
    metric_types: Optional[str] = Query(None, description="逗号分隔的指标类型"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统指标数据"""
    try:
        query = db.query(SystemMetric)
        
        if metric_types:
            types_list = [t.strip() for t in metric_types.split(",")]
            query = query.filter(SystemMetric.metric_type.in_(types_list))
        
        if start_time:
            query = query.filter(SystemMetric.recorded_at >= start_time)
        if end_time:
            query = query.filter(SystemMetric.recorded_at <= end_time)
            
        metrics = query.order_by(SystemMetric.recorded_at.desc()).limit(limit).all()
        
        return APIResponse(
            success=True,
            message="系统指标获取成功",
            data={
                "metrics": [SystemMetricResponse.from_orm(metric) for metric in metrics],
                "count": len(metrics)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统指标失败: {str(e)}"
        )

@router.post("/metrics/collect", response_model=APIResponse)
async def collect_current_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发指标收集"""
    try:
        monitoring_service = MonitoringService(db)
        metrics = await monitoring_service.collect_system_metrics_async()
        
        # 保存指标到数据库
        for metric_data in metrics:
            db_metric = SystemMetric(
                metric_name=metric_data["name"],
                metric_type=metric_data["type"],
                metric_value=metric_data["value"],
                unit=metric_data.get("unit"),
                tags=metric_data.get("tags", {})
            )
            db.add(db_metric)
        
        db.commit()
        
        return APIResponse(
            success=True,
            message="指标收集成功",
            data={"collected_metrics": len(metrics)}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"收集指标失败: {str(e)}"
        )

# Analytics APIs
@router.post("/analytics/query", response_model=APIResponse)
async def query_analytics(
    query: AnalyticsQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询分析数据"""
    try:
        analytics_engine = AnalyticsEngine(db)
        
        # 设置默认时间范围
        if not query.start_date:
            query.start_date = datetime.utcnow() - timedelta(days=7)
        if not query.end_date:
            query.end_date = datetime.utcnow()
        
        # 执行分析查询
        results = await analytics_engine.query_analytics(
            metric_types=query.metric_types,
            start_date=query.start_date,
            end_date=query.end_date,
            group_by=query.group_by,
            aggregation=query.aggregation
        )
        
        return APIResponse(
            success=True,
            message="分析查询成功",
            data=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析查询失败: {str(e)}"
        )

@router.get("/analytics/coverage", response_model=APIResponse)
async def get_coverage_analytics(
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取覆盖率分析数据"""
    try:
        # 计算时间范围
        days = int(time_range.replace("d", ""))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取覆盖率数据
        coverage_data = db.query(CoverageAnalysis).filter(
            CoverageAnalysis.analysis_date >= start_date
        ).all()
        
        analytics_engine = AnalyticsEngine(db)
        analysis_result = await analytics_engine.analyze_coverage_trends(coverage_data)
        
        return APIResponse(
            success=True,
            message="覆盖率分析获取成功",
            data=analysis_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取覆盖率分析失败: {str(e)}"
        )

@router.get("/analytics/defects", response_model=APIResponse)
async def get_defect_analytics(
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取缺陷分析数据"""
    try:
        # 计算时间范围
        days = int(time_range.replace("d", ""))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取缺陷数据
        defects = db.query(Defect).filter(
            Defect.detected_at >= start_date
        ).all()
        
        analytics_engine = AnalyticsEngine(db)
        analysis_result = await analytics_engine.analyze_defect_patterns(defects)
        
        return APIResponse(
            success=True,
            message="缺陷分析获取成功",
            data=analysis_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缺陷分析失败: {str(e)}"
        )

@router.get("/dashboard", response_model=APIResponse)
async def get_monitoring_dashboard(
    request: MonitoringDashboardRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取监控仪表板数据"""
    try:
        # 解析时间范围
        time_mapping = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        start_time = datetime.utcnow() - time_mapping[request.time_range]
        
        monitoring_service = MonitoringService(db)
        dashboard_data = await monitoring_service.get_dashboard_data(
            start_time=start_time,
            metrics=request.metrics
        )
        
        return APIResponse(
            success=True,
            message="仪表板数据获取成功",
            data=dashboard_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表板数据失败: {str(e)}"
        )

@router.get("/health", response_model=APIResponse)
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统健康状态"""
    try:
        monitoring_service = MonitoringService(db)
        health_status = await monitoring_service.check_system_health_async()
        
        return APIResponse(
            success=True,
            message="系统健康状态获取成功",
            data=health_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统健康状态失败: {str(e)}"
        )