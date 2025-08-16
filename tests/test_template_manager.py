"""
模板管理器测试
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.services.template_manager import (
    TemplateManager, TemplateConfig, ValidationResult, RenderedReport,
    TemplateValidationError, TemplateRenderError
)
from backend.models import ReportTemplate, User, Report
from backend.database import get_db


class TestTemplateManager:
    """模板管理器测试类"""
    
    @pytest.fixture
    def db_session(self):
        """数据库会话fixture"""
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def template_manager(self, db_session):
        """模板管理器fixture"""
        return TemplateManager(db_session)
    
    @pytest.fixture
    def test_user(self, db_session):
        """测试用户fixture"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f"test_template_user_{unique_id}",
            email=f"template_{unique_id}@test.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def sample_template_config(self):
        """示例模板配置fixture"""
        return TemplateConfig(
            template_name="测试执行报告模板",
            template_type="execution",
            template_content="""
# 测试执行报告

## 基本信息
- 报告生成时间: {{ report_generated_at }}
- 测试用例总数: {{ total_test_cases }}
- 通过数量: {{ passed_count }}
- 失败数量: {{ failed_count }}
- 通过率: {{ pass_rate | percentage }}

## 详细结果
{% for test_case in test_cases %}
- {{ test_case.title }}: {{ test_case.status | status_badge }}
{% endfor %}
            """.strip(),
            template_config={
                "charts": [
                    {
                        "type": "pie",
                        "title": "测试结果分布",
                        "data_source": "test_results"
                    }
                ],
                "filters": [
                    {
                        "field": "status",
                        "type": "select",
                        "options": ["passed", "failed", "pending"]
                    }
                ]
            },
            description="用于生成测试执行报告的模板"
        )
    
    def test_create_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功创建模板"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        assert template is not None
        assert template.template_name == sample_template_config.template_name
        assert template.template_type == sample_template_config.template_type
        assert template.template_content == sample_template_config.template_content
        assert template.created_by == test_user.id
        assert template.is_active is True
        assert template.usage_count == 0
    
    def test_create_template_duplicate_name(self, template_manager, test_user, sample_template_config):
        """测试创建重复名称的模板"""
        # 创建第一个模板
        template_manager.create_template(sample_template_config, test_user.id)
        
        # 尝试创建同名模板
        with pytest.raises(ValueError, match="模板名称.*已存在"):
            template_manager.create_template(sample_template_config, test_user.id)
    
    def test_create_template_invalid_config(self, template_manager, test_user):
        """测试创建无效配置的模板"""
        invalid_config = TemplateConfig(
            template_name="",  # 空名称
            template_type="execution",
            template_content="{{ invalid_syntax"  # 语法错误
        )
        
        with pytest.raises(TemplateValidationError):
            template_manager.create_template(invalid_config, test_user.id)
    
    def test_update_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功更新模板"""
        # 创建模板
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        # 更新配置
        updated_config = TemplateConfig(
            template_name="更新后的模板名称",
            template_type="execution",
            template_content="# 更新后的内容\n{{ test_data }}",
            description="更新后的描述"
        )
        
        updated_template = template_manager.update_template(template.id, updated_config, test_user.id)
        
        assert updated_template.template_name == "更新后的模板名称"
        assert updated_template.template_content == "# 更新后的内容\n{{ test_data }}"
        assert updated_template.description == "更新后的描述"
    
    def test_update_template_not_found(self, template_manager, test_user):
        """测试更新不存在的模板"""
        config = TemplateConfig(
            template_name="不存在的模板",
            template_type="execution",
            template_content="内容"
        )
        
        with pytest.raises(ValueError, match="模板 ID.*不存在"):
            template_manager.update_template(99999, config, test_user.id)
    
    def test_get_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功获取模板"""
        created_template = template_manager.create_template(sample_template_config, test_user.id)
        retrieved_template = template_manager.get_template(created_template.id)
        
        assert retrieved_template is not None
        assert retrieved_template.id == created_template.id
        assert retrieved_template.template_name == created_template.template_name
    
    def test_get_template_not_found(self, template_manager):
        """测试获取不存在的模板"""
        template = template_manager.get_template(99999)
        assert template is None
    
    def test_get_templates_by_user(self, template_manager, test_user, sample_template_config):
        """测试获取用户的模板列表"""
        # 创建多个模板
        template1 = template_manager.create_template(sample_template_config, test_user.id)
        
        config2 = TemplateConfig(
            template_name="缺陷分析模板",
            template_type="defect_analysis",
            template_content="# 缺陷分析\n{{ defect_data }}"
        )
        template2 = template_manager.create_template(config2, test_user.id)
        
        # 获取所有模板
        all_templates = template_manager.get_templates_by_user(test_user.id)
        assert len(all_templates) == 2
        
        # 按类型过滤
        execution_templates = template_manager.get_templates_by_user(test_user.id, "execution")
        assert len(execution_templates) == 1
        assert execution_templates[0].template_type == "execution"
    
    def test_delete_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功删除模板"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        result = template_manager.delete_template(template.id, test_user.id)
        assert result is True
        
        # 验证模板被软删除
        deleted_template = template_manager.db.query(ReportTemplate).filter(
            ReportTemplate.id == template.id
        ).first()
        assert deleted_template.is_active is False
    
    def test_delete_template_with_reports(self, template_manager, test_user, sample_template_config, db_session):
        """测试删除有报告使用的模板"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        # 创建使用此模板的报告
        report = Report(
            title="测试报告",
            report_type="execution",
            template_id=template.id,
            generated_by=test_user.id,
            status="completed"
        )
        db_session.add(report)
        db_session.commit()
        
        # 尝试删除模板
        with pytest.raises(ValueError, match="无法删除模板.*个报告正在使用"):
            template_manager.delete_template(template.id, test_user.id)
    
    def test_render_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功渲染模板"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        test_data = {
            "total_test_cases": 10,
            "passed_count": 8,
            "failed_count": 2,
            "pass_rate": 0.8,
            "test_cases": [
                {"title": "测试用例1", "status": "passed"},
                {"title": "测试用例2", "status": "failed"}
            ]
        }
        
        rendered_report = template_manager.render_template(template, test_data)
        
        assert isinstance(rendered_report, RenderedReport)
        assert "测试执行报告" in rendered_report.content
        assert "80.0%" in rendered_report.content  # 通过率格式化
        assert "测试用例1" in rendered_report.content
        assert rendered_report.metadata["template_id"] == template.id
        
        # 验证使用计数增加
        template_manager.db.refresh(template)
        assert template.usage_count == 1
    
    def test_render_template_with_filters(self, template_manager, test_user):
        """测试使用过滤器渲染模板"""
        config = TemplateConfig(
            template_name="过滤器测试模板",
            template_type="execution",
            template_content="""
数值: {{ value | number_format }}
百分比: {{ percentage | percentage }}
日期: {{ date | datetime_format }}
状态: {{ status | status_badge }}
            """.strip()
        )
        
        template = template_manager.create_template(config, test_user.id)
        
        test_data = {
            "value": 1234.567,
            "percentage": 85.5,
            "date": "2024-01-15T10:30:00",
            "status": "passed"
        }
        
        rendered_report = template_manager.render_template(template, test_data)
        
        assert "1,234.57" in rendered_report.content
        assert "85.5%" in rendered_report.content
        assert "2024-01-15" in rendered_report.content
        assert "badge-success" in rendered_report.content
    
    def test_render_template_error(self, template_manager, test_user):
        """测试模板渲染错误"""
        config = TemplateConfig(
            template_name="错误模板",
            template_type="execution",
            template_content="{{ undefined_variable.nonexistent_method() }}"
        )
        
        template = template_manager.create_template(config, test_user.id)
        
        with pytest.raises(TemplateRenderError):
            template_manager.render_template(template, {})
    
    def test_validate_template_success(self, template_manager, test_user, sample_template_config):
        """测试模板验证成功"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        validation_result = template_manager.validate_template(template)
        
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
    
    def test_validate_template_syntax_error(self, template_manager, test_user):
        """测试模板语法错误验证"""
        config = TemplateConfig(
            template_name="语法错误模板",
            template_type="execution",
            template_content="{{ invalid syntax"
        )
        
        template = template_manager.create_template(config, test_user.id)
        validation_result = template_manager.validate_template(template)
        
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        assert "模板语法错误" in validation_result.errors[0]
    
    def test_validate_template_config_success(self, template_manager, sample_template_config):
        """测试模板配置验证成功"""
        validation_result = template_manager.validate_template_config(sample_template_config)
        
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
    
    def test_validate_template_config_missing_fields(self, template_manager):
        """测试模板配置缺少必填字段"""
        invalid_config = TemplateConfig(
            template_name="",  # 空名称
            template_type="",  # 空类型
            template_content=""  # 空内容
        )
        
        validation_result = template_manager.validate_template_config(invalid_config)
        
        assert validation_result.is_valid is False
        assert len(validation_result.errors) >= 3
        assert any("模板名称不能为空" in error for error in validation_result.errors)
        assert any("模板类型不能为空" in error for error in validation_result.errors)
        assert any("模板内容不能为空" in error for error in validation_result.errors)
    
    def test_clone_template_success(self, template_manager, test_user, sample_template_config):
        """测试成功克隆模板"""
        original_template = template_manager.create_template(sample_template_config, test_user.id)
        
        cloned_template = template_manager.clone_template(
            original_template.id, 
            "克隆的模板", 
            test_user.id
        )
        
        assert cloned_template.template_name == "克隆的模板"
        assert cloned_template.template_type == original_template.template_type
        assert cloned_template.template_content == original_template.template_content
        assert cloned_template.template_config == original_template.template_config
        assert "克隆自:" in cloned_template.description
        assert cloned_template.is_default is False
    
    def test_get_template_usage_stats(self, template_manager, test_user, sample_template_config, db_session):
        """测试获取模板使用统计"""
        template = template_manager.create_template(sample_template_config, test_user.id)
        
        # 创建使用此模板的报告
        report1 = Report(
            title="报告1",
            report_type="execution",
            template_id=template.id,
            generated_by=test_user.id,
            status="completed"
        )
        report2 = Report(
            title="报告2",
            report_type="execution",
            template_id=template.id,
            generated_by=test_user.id,
            status="completed"
        )
        db_session.add_all([report1, report2])
        db_session.commit()
        
        # 模拟使用计数
        template.usage_count = 5
        db_session.commit()
        
        stats = template_manager.get_template_usage_stats(template.id)
        
        assert stats["template_id"] == template.id
        assert stats["template_name"] == template.template_name
        assert stats["usage_count"] == 5
        assert stats["total_reports"] == 2
        assert "created_at" in stats
        assert "updated_at" in stats
    
    def test_get_default_templates(self, template_manager, test_user):
        """测试获取默认模板"""
        # 创建默认模板
        default_config = TemplateConfig(
            template_name="默认执行报告模板",
            template_type="execution",
            template_content="# 默认模板\n{{ data }}",
            is_default=True
        )
        template_manager.create_template(default_config, test_user.id)
        
        # 创建非默认模板
        normal_config = TemplateConfig(
            template_name="普通模板",
            template_type="execution",
            template_content="# 普通模板\n{{ data }}"
        )
        template_manager.create_template(normal_config, test_user.id)
        
        default_templates = template_manager.get_default_templates()
        assert len(default_templates) == 1
        assert default_templates[0].is_default is True
        
        # 按类型过滤
        execution_defaults = template_manager.get_default_templates("execution")
        assert len(execution_defaults) == 1
        assert execution_defaults[0].template_type == "execution"
    
    def test_data_transformations(self, template_manager, test_user):
        """测试数据转换功能"""
        config = TemplateConfig(
            template_name="数据转换测试",
            template_type="execution",
            template_content="转换后的值: {{ transformed_value }}",
            template_config={
                "data_transformations": [
                    {
                        "type": "percentage",
                        "source": "raw_value",
                        "target": "transformed_value"
                    }
                ]
            }
        )
        
        template = template_manager.create_template(config, test_user.id)
        
        test_data = {"raw_value": 0.85}
        rendered_report = template_manager.render_template(template, test_data)
        
        assert "85.0%" in rendered_report.content
    
    def test_template_config_validation_charts(self, template_manager):
        """测试图表配置验证"""
        config = TemplateConfig(
            template_name="图表配置测试",
            template_type="execution",
            template_content="内容",
            template_config={
                "charts": [
                    {"type": "bar", "title": "测试图表"},
                    {"title": "缺少类型的图表"},  # 缺少type字段
                    "invalid_chart"  # 不是对象
                ]
            }
        )
        
        validation_result = template_manager.validate_template_config(config)
        
        assert validation_result.is_valid is False
        assert any("缺少type字段" in error for error in validation_result.errors)
        assert any("必须是对象" in error for error in validation_result.errors)
    
    def test_template_config_validation_filters(self, template_manager):
        """测试过滤器配置验证"""
        config = TemplateConfig(
            template_name="过滤器配置测试",
            template_type="execution",
            template_content="内容",
            template_config={
                "filters": [
                    {"field": "status", "type": "select"},
                    {"field": "date"},  # 缺少type字段
                ]
            }
        )
        
        validation_result = template_manager.validate_template_config(config)
        
        assert validation_result.is_valid is False
        assert any("缺少type字段" in error for error in validation_result.errors)


class TestTemplateConfig:
    """模板配置类测试"""
    
    def test_template_config_creation(self):
        """测试模板配置创建"""
        config = TemplateConfig(
            template_name="测试模板",
            template_type="execution",
            template_content="模板内容",
            template_config={"key": "value"},
            description="测试描述",
            is_default=True
        )
        
        assert config.template_name == "测试模板"
        assert config.template_type == "execution"
        assert config.template_content == "模板内容"
        assert config.template_config == {"key": "value"}
        assert config.description == "测试描述"
        assert config.is_default is True
    
    def test_template_config_defaults(self):
        """测试模板配置默认值"""
        config = TemplateConfig(
            template_name="测试模板",
            template_type="execution",
            template_content="模板内容"
        )
        
        assert config.template_config == {}
        assert config.description is None
        assert config.is_default is False


class TestValidationResult:
    """验证结果类测试"""
    
    def test_validation_result_valid(self):
        """测试有效的验证结果"""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_validation_result_invalid(self):
        """测试无效的验证结果"""
        errors = ["错误1", "错误2"]
        warnings = ["警告1"]
        result = ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        assert result.is_valid is False
        assert result.errors == errors
        assert result.warnings == warnings


class TestRenderedReport:
    """渲染报告类测试"""
    
    def test_rendered_report_creation(self):
        """测试渲染报告创建"""
        content = "渲染后的内容"
        metadata = {"key": "value"}
        report = RenderedReport(content=content, metadata=metadata)
        
        assert report.content == content
        assert report.metadata == metadata
        assert isinstance(report.rendered_at, datetime)
    
    def test_rendered_report_defaults(self):
        """测试渲染报告默认值"""
        report = RenderedReport("内容")
        
        assert report.content == "内容"
        assert report.metadata == {}
        assert isinstance(report.rendered_at, datetime)