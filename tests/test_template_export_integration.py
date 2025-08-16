"""
模板管理器和导出管理器集成测试
"""

import pytest
import tempfile
import os
from datetime import datetime

from backend.services.template_manager import TemplateManager, TemplateConfig
from backend.services.export_manager import ExportManager, ExportFormat
from backend.models import User, Report
from backend.database import get_db


class TestTemplateExportIntegration:
    """模板和导出集成测试"""
    
    @pytest.fixture
    def db_session(self):
        """数据库会话fixture"""
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def test_user(self, db_session):
        """测试用户fixture"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f"test_integration_user_{unique_id}",
            email=f"integration_{unique_id}@test.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def template_manager(self, db_session):
        """模板管理器fixture"""
        return TemplateManager(db_session)
    
    @pytest.fixture
    def export_manager(self, db_session):
        """导出管理器fixture"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ExportManager(db=db_session, upload_dir=tmp_dir)
            yield manager
    
    def test_template_creation_and_html_export(self, template_manager, export_manager, test_user, db_session):
        """测试模板创建和HTML导出的完整流程"""
        # 1. 创建模板
        template_config = TemplateConfig(
            template_name="集成测试报告模板",
            template_type="execution",
            template_content="""
# {{ title }}

## 测试摘要
- 总测试用例数: {{ total_test_cases }}
- 通过数量: {{ passed_count }}
- 失败数量: {{ failed_count }}
- 通过率: {{ pass_rate | percentage }}

## 测试结果详情
{% for test_case in test_cases %}
- **{{ test_case.title }}**: {{ test_case.status | status_badge }}
{% endfor %}

## 生成信息
报告生成时间: {{ report_generated_at }}
            """.strip(),
            description="用于集成测试的报告模板"
        )
        
        template = template_manager.create_template(template_config, test_user.id)
        assert template is not None
        
        # 2. 创建测试报告
        report = Report(
            title="集成测试报告",
            report_type="execution",
            template_id=template.id,
            generated_by=test_user.id,
            generation_time=datetime.utcnow(),
            report_data={
                'total_test_cases': 5,
                'passed_count': 4,
                'failed_count': 1,
                'pass_rate': 0.8,
                'test_cases': [
                    {'title': '登录功能测试', 'status': 'passed'},
                    {'title': '数据验证测试', 'status': 'passed'},
                    {'title': '权限检查测试', 'status': 'failed'},
                    {'title': '性能测试', 'status': 'passed'},
                    {'title': '兼容性测试', 'status': 'passed'}
                ]
            },
            status="completed"
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # 3. 使用模板渲染报告内容
        test_data = {
            'title': report.title,
            'total_test_cases': report.report_data['total_test_cases'],
            'passed_count': report.report_data['passed_count'],
            'failed_count': report.report_data['failed_count'],
            'pass_rate': report.report_data['pass_rate'],
            'test_cases': report.report_data['test_cases']
        }
        
        rendered_report = template_manager.render_template(template, test_data)
        assert rendered_report is not None
        assert "集成测试报告" in rendered_report.content
        assert "80.0%" in rendered_report.content  # 通过率
        assert "登录功能测试" in rendered_report.content
        
        # 4. 导出为HTML格式
        task_id = export_manager.export_report(
            report.id,
            ExportFormat.HTML,
            {
                'title': '集成测试HTML导出',
                'content': rendered_report.content
            }
        )
        
        assert task_id is not None
        
        # 5. 检查导出任务状态
        task = export_manager.get_export_status(task_id)
        assert task is not None
        assert task.report_id == report.id
        assert task.format == ExportFormat.HTML
        
        print(f"Integration test completed successfully!")
        print(f"Template ID: {template.id}")
        print(f"Report ID: {report.id}")
        print(f"Export Task ID: {task_id}")
    
    def test_template_validation_and_export_formats(self, template_manager, export_manager, test_user):
        """测试模板验证和导出格式支持"""
        # 1. 测试模板验证
        valid_config = TemplateConfig(
            template_name="验证测试模板",
            template_type="coverage",
            template_content="# {{ title }}\n覆盖率: {{ coverage_rate | percentage }}",
            template_config={
                "charts": [
                    {"type": "pie", "title": "覆盖率分布"}
                ]
            }
        )
        
        validation_result = template_manager.validate_template_config(valid_config)
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # 2. 测试无效模板配置
        invalid_config = TemplateConfig(
            template_name="",  # 空名称
            template_type="invalid_type",
            template_content="{{ invalid syntax"  # 语法错误
        )
        
        validation_result = template_manager.validate_template_config(invalid_config)
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        
        # 3. 测试支持的导出格式
        supported_formats = export_manager.get_supported_formats()
        assert 'html' in supported_formats
        assert len(supported_formats) >= 1
        
        print(f"Supported export formats: {supported_formats}")
    
    def test_template_cloning_and_export(self, template_manager, export_manager, test_user, db_session):
        """测试模板克隆和导出功能"""
        # 1. 创建原始模板
        original_config = TemplateConfig(
            template_name="原始缺陷分析模板",
            template_type="defect_analysis",
            template_content="""
# 缺陷分析报告

## 缺陷统计
- 总缺陷数: {{ total_defects }}
- 严重缺陷: {{ critical_defects }}
- 高优先级缺陷: {{ high_priority_defects }}

## 缺陷列表
{% for defect in defects %}
- {{ defect.description }} ({{ defect.severity }})
{% endfor %}
            """.strip()
        )
        
        original_template = template_manager.create_template(original_config, test_user.id)
        
        # 2. 克隆模板
        cloned_template = template_manager.clone_template(
            original_template.id,
            "克隆的缺陷分析模板",
            test_user.id
        )
        
        assert cloned_template.template_name == "克隆的缺陷分析模板"
        assert cloned_template.template_type == original_template.template_type
        assert cloned_template.template_content == original_template.template_content
        assert "克隆自:" in cloned_template.description
        
        # 3. 使用克隆的模板创建报告
        report = Report(
            title="缺陷分析报告",
            report_type="defect_analysis",
            template_id=cloned_template.id,
            generated_by=test_user.id,
            generation_time=datetime.utcnow(),
            report_data={
                'total_defects': 3,
                'critical_defects': 1,
                'high_priority_defects': 2,
                'defects': [
                    {'description': '登录失败', 'severity': 'critical'},
                    {'description': '数据丢失', 'severity': 'high'},
                    {'description': '界面错位', 'severity': 'medium'}
                ]
            },
            status="completed"
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        # 4. 渲染和导出
        test_data = report.report_data.copy()
        rendered_report = template_manager.render_template(cloned_template, test_data)
        
        assert "缺陷分析报告" in rendered_report.content
        assert "登录失败" in rendered_report.content
        assert "critical" in rendered_report.content
        
        # 5. 导出为HTML
        task_id = export_manager.export_report(
            report.id,
            ExportFormat.HTML,
            {'content': rendered_report.content}
        )
        
        assert task_id is not None
        
        print(f"Template cloning and export test completed!")
        print(f"Original template: {original_template.template_name}")
        print(f"Cloned template: {cloned_template.template_name}")
    
    def test_template_usage_statistics(self, template_manager, test_user, db_session):
        """测试模板使用统计"""
        # 1. 创建模板
        config = TemplateConfig(
            template_name="统计测试模板",
            template_type="trend",
            template_content="# 趋势分析\n数据: {{ data }}"
        )
        
        template = template_manager.create_template(config, test_user.id)
        
        # 2. 模拟使用模板（通过渲染增加使用计数）
        for i in range(3):
            template_manager.render_template(template, {'data': f'test_{i}'})
        
        # 3. 创建使用此模板的报告
        for i in range(2):
            report = Report(
                title=f"趋势报告{i+1}",
                report_type="trend",
                template_id=template.id,
                generated_by=test_user.id,
                status="completed"
            )
            db_session.add(report)
        db_session.commit()
        
        # 4. 获取使用统计
        stats = template_manager.get_template_usage_stats(template.id)
        
        assert stats['template_id'] == template.id
        assert stats['usage_count'] == 3  # 渲染次数
        assert stats['total_reports'] == 2  # 报告数量
        assert 'created_at' in stats
        
        print(f"Template usage statistics: {stats}")
    
    def test_error_handling_integration(self, template_manager, export_manager, test_user):
        """测试错误处理集成"""
        # 1. 测试无效模板渲染
        config = TemplateConfig(
            template_name="错误处理测试模板",
            template_type="execution",
            template_content="{{ undefined_variable.method() }}"
        )
        
        template = template_manager.create_template(config, test_user.id)
        
        # 渲染应该抛出异常
        with pytest.raises(Exception):
            template_manager.render_template(template, {})
        
        # 2. 测试不存在的报告导出
        task_id = export_manager.export_report(
            99999,  # 不存在的报告ID
            ExportFormat.HTML
        )
        
        # 任务应该被创建，但会在处理时失败
        assert task_id is not None
        task = export_manager.get_export_status(task_id)
        assert task is not None
        
        print("Error handling integration test completed!")


if __name__ == "__main__":
    # 可以直接运行此文件进行快速测试
    pytest.main([__file__, "-v"])