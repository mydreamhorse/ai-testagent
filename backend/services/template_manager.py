"""
模板管理服务
负责报告模板的创建、管理、渲染和验证
"""

import json
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from jinja2 import Environment, BaseLoader, Template as Jinja2Template, TemplateError
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models import ReportTemplate, User, Report
from backend.database import get_db


class TemplateValidationError(Exception):
    """模板验证错误"""
    pass


class TemplateRenderError(Exception):
    """模板渲染错误"""
    pass


class TemplateConfig:
    """模板配置类"""
    
    def __init__(self, 
                 template_name: str,
                 template_type: str,
                 template_content: str,
                 template_config: Dict[str, Any] = None,
                 description: str = None,
                 is_default: bool = False):
        self.template_name = template_name
        self.template_type = template_type
        self.template_content = template_content
        self.template_config = template_config or {}
        self.description = description
        self.is_default = is_default


class ValidationResult:
    """验证结果类"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class RenderedReport:
    """渲染后的报告类"""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.rendered_at = datetime.utcnow()


class TemplateVersion:
    """模板版本类"""
    
    def __init__(self, version: str, template: ReportTemplate, changes: str = None):
        self.version = version
        self.template = template
        self.changes = changes
        self.created_at = template.updated_at


class StringTemplateLoader(BaseLoader):
    """字符串模板加载器"""
    
    def __init__(self, template_string: str):
        self.template_string = template_string
    
    def get_source(self, environment, template):
        return self.template_string, None, lambda: True


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 注册自定义过滤器
        self._register_custom_filters()
        
        # 预定义的模板类型
        self.template_types = {
            'execution': '测试执行报告',
            'defect_analysis': '缺陷分析报告',
            'coverage': '覆盖率分析报告',
            'trend': '趋势分析报告',
            'custom': '自定义报告'
        }
    
    def _register_custom_filters(self):
        """注册自定义Jinja2过滤器"""
        
        def percentage_filter(value, decimals=1):
            """百分比格式化"""
            if value is None:
                return "N/A"
            try:
                # Convert to percentage (multiply by 100 if value is between 0 and 1)
                float_value = float(value)
                if 0 <= float_value <= 1:
                    float_value *= 100
                return f"{float_value:.{decimals}f}%"
            except (ValueError, TypeError):
                return "N/A"
        
        def datetime_format_filter(value, format='%Y-%m-%d %H:%M:%S'):
            """日期时间格式化"""
            if value is None:
                return "N/A"
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    return value
            return value.strftime(format)
        
        def number_format_filter(value, decimals=2):
            """数字格式化"""
            if value is None:
                return "N/A"
            try:
                return f"{float(value):,.{decimals}f}"
            except (ValueError, TypeError):
                return str(value)
        
        def status_badge_filter(status):
            """状态徽章"""
            status_colors = {
                'passed': 'success',
                'failed': 'danger',
                'pending': 'warning',
                'skipped': 'secondary',
                'active': 'primary',
                'resolved': 'success',
                'open': 'warning'
            }
            color = status_colors.get(str(status).lower(), 'secondary')
            return f'<span class="badge badge-{color}">{status}</span>'
        
        # Register filters
        self.jinja_env.filters['percentage'] = percentage_filter
        self.jinja_env.filters['datetime_format'] = datetime_format_filter
        self.jinja_env.filters['number_format'] = number_format_filter
        self.jinja_env.filters['status_badge'] = status_badge_filter
    
    def create_template(self, template_config: TemplateConfig, created_by: int) -> ReportTemplate:
        """创建新模板"""
        try:
            # 验证模板配置
            validation_result = self.validate_template_config(template_config)
            if not validation_result.is_valid:
                raise TemplateValidationError(f"模板验证失败: {', '.join(validation_result.errors)}")
            
            # 检查模板名称是否已存在
            existing_template = self.db.query(ReportTemplate).filter(
                and_(
                    ReportTemplate.template_name == template_config.template_name,
                    ReportTemplate.created_by == created_by,
                    ReportTemplate.is_active == True
                )
            ).first()
            
            if existing_template:
                raise ValueError(f"模板名称 '{template_config.template_name}' 已存在")
            
            # 创建新模板
            template = ReportTemplate(
                template_name=template_config.template_name,
                template_type=template_config.template_type,
                template_content=template_config.template_content,
                template_config=template_config.template_config,
                description=template_config.description,
                created_by=created_by,
                is_default=template_config.is_default,
                is_active=True,
                usage_count=0
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            return template
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_template(self, template_id: int, template_config: TemplateConfig, updated_by: int) -> ReportTemplate:
        """更新模板"""
        try:
            template = self.db.query(ReportTemplate).filter(
                and_(
                    ReportTemplate.id == template_id,
                    ReportTemplate.created_by == updated_by,
                    ReportTemplate.is_active == True
                )
            ).first()
            
            if not template:
                raise ValueError(f"模板 ID {template_id} 不存在或无权限修改")
            
            # 验证新的模板配置
            validation_result = self.validate_template_config(template_config)
            if not validation_result.is_valid:
                raise TemplateValidationError(f"模板验证失败: {', '.join(validation_result.errors)}")
            
            # 更新模板
            template.template_name = template_config.template_name
            template.template_type = template_config.template_type
            template.template_content = template_config.template_content
            template.template_config = template_config.template_config
            template.description = template_config.description
            template.is_default = template_config.is_default
            template.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(template)
            
            return template
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_template(self, template_id: int) -> Optional[ReportTemplate]:
        """获取模板"""
        return self.db.query(ReportTemplate).filter(
            and_(
                ReportTemplate.id == template_id,
                ReportTemplate.is_active == True
            )
        ).first()
    
    def get_templates_by_user(self, user_id: int, template_type: str = None) -> List[ReportTemplate]:
        """获取用户的模板列表"""
        query = self.db.query(ReportTemplate).filter(
            and_(
                ReportTemplate.created_by == user_id,
                ReportTemplate.is_active == True
            )
        )
        
        if template_type:
            query = query.filter(ReportTemplate.template_type == template_type)
        
        return query.order_by(ReportTemplate.updated_at.desc()).all()
    
    def get_default_templates(self, template_type: str = None) -> List[ReportTemplate]:
        """获取默认模板列表"""
        query = self.db.query(ReportTemplate).filter(
            and_(
                ReportTemplate.is_default == True,
                ReportTemplate.is_active == True
            )
        )
        
        if template_type:
            query = query.filter(ReportTemplate.template_type == template_type)
        
        return query.order_by(ReportTemplate.template_name).all()
    
    def delete_template(self, template_id: int, user_id: int) -> bool:
        """删除模板（软删除）"""
        try:
            template = self.db.query(ReportTemplate).filter(
                and_(
                    ReportTemplate.id == template_id,
                    ReportTemplate.created_by == user_id,
                    ReportTemplate.is_active == True
                )
            ).first()
            
            if not template:
                return False
            
            # 检查是否有报告正在使用此模板
            reports_using_template = self.db.query(Report).filter(
                and_(
                    Report.template_id == template_id,
                    Report.status.in_(['generating', 'completed'])
                )
            ).count()
            
            if reports_using_template > 0:
                raise ValueError(f"无法删除模板，有 {reports_using_template} 个报告正在使用此模板")
            
            # 软删除
            template.is_active = False
            template.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def render_template(self, template: ReportTemplate, data: Dict[str, Any]) -> RenderedReport:
        """渲染模板"""
        try:
            # 准备模板数据
            template_data = self._prepare_template_data(data, template.template_config)
            
            # 创建Jinja2模板
            jinja_template = self.jinja_env.from_string(template.template_content)
            
            # 渲染模板
            rendered_content = jinja_template.render(**template_data)
            
            # 更新使用计数
            template.usage_count += 1
            self.db.commit()
            
            # 创建渲染结果
            metadata = {
                'template_id': template.id,
                'template_name': template.template_name,
                'template_type': template.template_type,
                'data_keys': list(template_data.keys())
            }
            
            return RenderedReport(content=rendered_content, metadata=metadata)
            
        except TemplateError as e:
            raise TemplateRenderError(f"模板渲染失败: {str(e)}")
        except Exception as e:
            raise TemplateRenderError(f"渲染过程中发生错误: {str(e)}")
    
    def _prepare_template_data(self, data: Dict[str, Any], template_config: Dict[str, Any]) -> Dict[str, Any]:
        """准备模板数据"""
        template_data = data.copy()
        
        # 添加通用数据
        template_data.update({
            'current_time': datetime.utcnow(),
            'report_generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'template_config': template_config
        })
        
        # 处理配置中的数据转换
        if 'data_transformations' in template_config:
            for transformation in template_config['data_transformations']:
                self._apply_data_transformation(template_data, transformation)
        
        return template_data
    
    def _apply_data_transformation(self, data: Dict[str, Any], transformation: Dict[str, Any]):
        """应用数据转换"""
        transform_type = transformation.get('type')
        source_field = transformation.get('source')
        target_field = transformation.get('target')
        
        if not all([transform_type, source_field, target_field]):
            return
        
        source_value = data.get(source_field)
        if source_value is None:
            return
        
        try:
            if transform_type == 'percentage':
                data[target_field] = f"{float(source_value) * 100:.1f}%"
            elif transform_type == 'round':
                decimals = transformation.get('decimals', 2)
                data[target_field] = round(float(source_value), decimals)
            elif transform_type == 'format_number':
                data[target_field] = f"{float(source_value):,.2f}"
            elif transform_type == 'format_date':
                date_format = transformation.get('format', '%Y-%m-%d')
                if isinstance(source_value, str):
                    source_value = datetime.fromisoformat(source_value.replace('Z', '+00:00'))
                data[target_field] = source_value.strftime(date_format)
        except (ValueError, TypeError, AttributeError):
            # 转换失败时保持原值
            data[target_field] = source_value
    
    def validate_template(self, template: ReportTemplate) -> ValidationResult:
        """验证模板"""
        errors = []
        warnings = []
        
        try:
            # 验证模板内容语法
            self.jinja_env.from_string(template.template_content)
        except TemplateError as e:
            errors.append(f"模板语法错误: {str(e)}")
        
        # 验证模板配置
        if template.template_config:
            config_validation = self._validate_template_config_structure(template.template_config)
            errors.extend(config_validation.get('errors', []))
            warnings.extend(config_validation.get('warnings', []))
        
        # 验证模板类型
        if template.template_type not in self.template_types:
            warnings.append(f"未知的模板类型: {template.template_type}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def validate_template_config(self, template_config: TemplateConfig) -> ValidationResult:
        """验证模板配置"""
        errors = []
        warnings = []
        
        # 验证必填字段
        if not template_config.template_name:
            errors.append("模板名称不能为空")
        elif len(template_config.template_name) > 100:
            errors.append("模板名称长度不能超过100个字符")
        
        if not template_config.template_type:
            errors.append("模板类型不能为空")
        elif template_config.template_type not in self.template_types:
            warnings.append(f"未知的模板类型: {template_config.template_type}")
        
        if not template_config.template_content:
            errors.append("模板内容不能为空")
        else:
            # 验证模板语法
            try:
                self.jinja_env.from_string(template_config.template_content)
            except TemplateError as e:
                errors.append(f"模板语法错误: {str(e)}")
        
        # 验证模板配置结构
        if template_config.template_config:
            config_validation = self._validate_template_config_structure(template_config.template_config)
            errors.extend(config_validation.get('errors', []))
            warnings.extend(config_validation.get('warnings', []))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def _validate_template_config_structure(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证模板配置结构"""
        errors = []
        warnings = []
        
        # 验证图表配置
        if 'charts' in config:
            if not isinstance(config['charts'], list):
                errors.append("charts配置必须是数组")
            else:
                for i, chart in enumerate(config['charts']):
                    if not isinstance(chart, dict):
                        errors.append(f"charts[{i}]必须是对象")
                        continue
                    
                    if 'type' not in chart:
                        errors.append(f"charts[{i}]缺少type字段")
                    elif chart['type'] not in ['bar', 'line', 'pie', 'table', 'heatmap']:
                        warnings.append(f"charts[{i}]使用了未知的图表类型: {chart['type']}")
        
        # 验证过滤器配置
        if 'filters' in config:
            if not isinstance(config['filters'], list):
                errors.append("filters配置必须是数组")
            else:
                for i, filter_config in enumerate(config['filters']):
                    if not isinstance(filter_config, dict):
                        errors.append(f"filters[{i}]必须是对象")
                        continue
                    
                    required_fields = ['field', 'type']
                    for field in required_fields:
                        if field not in filter_config:
                            errors.append(f"filters[{i}]缺少{field}字段")
        
        # 验证数据转换配置
        if 'data_transformations' in config:
            if not isinstance(config['data_transformations'], list):
                errors.append("data_transformations配置必须是数组")
            else:
                for i, transformation in enumerate(config['data_transformations']):
                    if not isinstance(transformation, dict):
                        errors.append(f"data_transformations[{i}]必须是对象")
                        continue
                    
                    required_fields = ['type', 'source', 'target']
                    for field in required_fields:
                        if field not in transformation:
                            errors.append(f"data_transformations[{i}]缺少{field}字段")
        
        return {'errors': errors, 'warnings': warnings}
    
    def manage_template_versions(self, template_id: int) -> List[TemplateVersion]:
        """管理模板版本（简化版本，基于更新时间）"""
        template = self.get_template(template_id)
        if not template:
            return []
        
        # 简化版本管理，只返回当前版本
        # 在实际应用中，可以扩展为完整的版本控制系统
        current_version = TemplateVersion(
            version="1.0",
            template=template,
            changes="当前版本"
        )
        
        return [current_version]
    
    def clone_template(self, template_id: int, new_name: str, user_id: int) -> ReportTemplate:
        """克隆模板"""
        try:
            original_template = self.get_template(template_id)
            if not original_template:
                raise ValueError(f"模板 ID {template_id} 不存在")
            
            # 创建克隆配置
            clone_config = TemplateConfig(
                template_name=new_name,
                template_type=original_template.template_type,
                template_content=original_template.template_content,
                template_config=original_template.template_config,
                description=f"克隆自: {original_template.template_name}",
                is_default=False
            )
            
            return self.create_template(clone_config, user_id)
            
        except Exception as e:
            raise e
    
    def get_template_usage_stats(self, template_id: int) -> Dict[str, Any]:
        """获取模板使用统计"""
        template = self.get_template(template_id)
        if not template:
            return {}
        
        # 统计使用此模板的报告数量
        total_reports = self.db.query(Report).filter(Report.template_id == template_id).count()
        recent_reports = self.db.query(Report).filter(
            and_(
                Report.template_id == template_id,
                Report.created_at >= datetime.utcnow().replace(day=1)  # 本月
            )
        ).count()
        
        return {
            'template_id': template_id,
            'template_name': template.template_name,
            'usage_count': template.usage_count,
            'total_reports': total_reports,
            'recent_reports': recent_reports,
            'created_at': template.created_at,
            'updated_at': template.updated_at
        }