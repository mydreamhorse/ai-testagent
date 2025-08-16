"""
导出管理器测试
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from backend.services.export_manager import (
    ExportManager, ExportFormat, ExportStatus, ExportTask, ExportResult,
    PDFExporter, ExcelExporter, HTMLExporter, ExportTaskQueue,
    get_export_manager
)
from backend.models import Report, User
from backend.database import get_db


class TestHTMLExporter:
    """HTML导出器测试"""
    
    def test_html_export_success(self):
        """测试HTML导出成功"""
        exporter = HTMLExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            content = "<h1>测试报告</h1><p>这是测试内容</p>"
            options = {'title': '测试HTML导出'}
            
            result = exporter.export(content, tmp_path, options)
            
            assert result.success is True
            assert result.file_path == tmp_path
            assert result.file_size > 0
            assert result.metadata['format'] == 'html'
            
            # 验证文件内容
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert '测试HTML导出' in html_content
                assert '测试报告' in html_content
                assert '这是测试内容' in html_content
                assert 'DOCTYPE html' in html_content
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_html_export_with_complete_html(self):
        """测试导出完整HTML文档"""
        exporter = HTMLExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            complete_html = """<!DOCTYPE html>
<html>
<head><title>完整HTML</title></head>
<body><h1>完整的HTML文档</h1></body>
</html>"""
            
            result = exporter.export(complete_html, tmp_path)
            
            assert result.success is True
            
            # 验证内容未被修改
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert html_content == complete_html
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_html_export_with_custom_css(self):
        """测试带自定义CSS的HTML导出"""
        exporter = HTMLExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            content = "<h1>测试报告</h1>"
            options = {
                'title': '自定义CSS测试',
                'css': 'h1 { color: red; }'
            }
            
            result = exporter.export(content, tmp_path, options)
            
            assert result.success is True
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert 'color: red' in html_content
                assert 'Custom CSS' in html_content
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestExcelExporter:
    """Excel导出器测试"""
    
    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return {
            'title': '测试报告',
            'report_generated_at': '2024-01-15 10:30:00',
            'total_test_cases': 10,
            'passed_count': 8,
            'failed_count': 2,
            'pass_rate': 0.8,
            'test_cases': [
                {
                    'id': 1,
                    'title': '测试用例1',
                    'test_type': 'functional',
                    'status': 'passed',
                    'priority': 'high',
                    'created_at': '2024-01-15 09:00:00'
                },
                {
                    'id': 2,
                    'title': '测试用例2',
                    'test_type': 'boundary',
                    'status': 'failed',
                    'priority': 'medium',
                    'created_at': '2024-01-15 09:30:00'
                }
            ],
            'defects': [
                {
                    'id': 1,
                    'defect_type': 'functional',
                    'severity': 'high',
                    'description': '功能缺陷描述',
                    'status': 'open',
                    'detected_at': '2024-01-15 11:00:00'
                }
            ],
            'coverage_data': [
                {
                    'function_module': '用户管理',
                    'coverage_percentage': 85.5,
                    'covered_test_cases': 17,
                    'total_test_cases': 20,
                    'analysis_date': '2024-01-15'
                }
            ]
        }
    
    def test_excel_export_success(self, sample_data):
        """测试Excel导出成功"""
        try:
            exporter = ExcelExporter()
        except ImportError:
            pytest.skip("openpyxl not available")
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            options = {'title': '测试Excel导出'}
            result = exporter.export(sample_data, tmp_path, options)
            
            assert result.success is True
            assert result.file_path == tmp_path
            assert result.file_size > 0
            assert result.metadata['format'] == 'excel'
            assert result.metadata['sheets'] > 0
            
            # 验证文件存在且可读
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_excel_export_minimal_data(self):
        """测试最小数据的Excel导出"""
        try:
            exporter = ExcelExporter()
        except ImportError:
            pytest.skip("openpyxl not available")
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            minimal_data = {
                'title': '最小报告',
                'total_test_cases': 5
            }
            
            result = exporter.export(minimal_data, tmp_path)
            
            assert result.success is True
            assert os.path.exists(tmp_path)
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestPDFExporter:
    """PDF导出器测试"""
    
    def test_pdf_export_not_available(self):
        """测试PDF导出器在WeasyPrint不可用时的行为"""
        with patch('backend.services.export_manager.WEASYPRINT_AVAILABLE', False):
            with pytest.raises(ImportError, match="WeasyPrint is required"):
                PDFExporter()
    
    @pytest.mark.skipif(not hasattr(pytest, 'weasyprint_available'), reason="WeasyPrint not available")
    def test_pdf_export_success(self):
        """测试PDF导出成功（需要WeasyPrint）"""
        try:
            exporter = PDFExporter()
        except ImportError:
            pytest.skip("WeasyPrint not available")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            content = "<h1>测试PDF报告</h1><p>这是PDF内容</p>"
            options = {'title': '测试PDF导出'}
            
            result = exporter.export(content, tmp_path, options)
            
            assert result.success is True
            assert result.file_path == tmp_path
            assert result.file_size > 0
            assert result.metadata['format'] == 'pdf'
            
            # 验证PDF文件存在
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestExportTaskQueue:
    """导出任务队列测试"""
    
    def test_task_queue_lifecycle(self):
        """测试任务队列生命周期"""
        queue = ExportTaskQueue(max_workers=1)
        
        assert queue.running is False
        
        # 启动队列
        queue.start()
        assert queue.running is True
        assert len(queue.workers) == 1
        
        # 停止队列
        queue.stop()
        assert queue.running is False
        assert len(queue.workers) == 0
    
    def test_add_and_get_task(self):
        """测试添加和获取任务"""
        queue = ExportTaskQueue(max_workers=1)
        
        task = ExportTask(
            id="test-task-1",
            report_id=1,
            format=ExportFormat.HTML,
            options={'content': '<h1>Test</h1>'},
            status=ExportStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # 添加任务
        task_id = queue.add_task(task)
        assert task_id == "test-task-1"
        
        # 获取任务状态
        retrieved_task = queue.get_task_status(task_id)
        assert retrieved_task is not None
        assert retrieved_task.id == task_id
        assert retrieved_task.status == ExportStatus.PENDING
    
    def test_task_processing(self):
        """测试任务处理"""
        queue = ExportTaskQueue(max_workers=1)
        queue.start()
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            task = ExportTask(
                id="test-task-2",
                report_id=1,
                format=ExportFormat.HTML,
                options={
                    'content': '<h1>Test Task Processing</h1>',
                    'output_path': tmp_path
                },
                status=ExportStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            queue.add_task(task)
            
            # 等待任务完成
            import time
            max_wait = 5  # 最多等待5秒
            waited = 0
            while waited < max_wait:
                task_status = queue.get_task_status(task.id)
                if task_status.status in [ExportStatus.COMPLETED, ExportStatus.FAILED]:
                    break
                time.sleep(0.1)
                waited += 0.1
            
            # 验证任务完成
            final_task = queue.get_task_status(task.id)
            assert final_task.status == ExportStatus.COMPLETED
            assert final_task.file_path == tmp_path
            assert os.path.exists(tmp_path)
            
            # 清理
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        finally:
            queue.stop()


class TestExportManager:
    """导出管理器测试"""
    
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
            username=f"test_export_user_{unique_id}",
            email=f"export_{unique_id}@test.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_report(self, db_session, test_user):
        """测试报告fixture"""
        report = Report(
            title="测试导出报告",
            report_type="execution",
            generated_by=test_user.id,
            generation_time=datetime.utcnow(),
            report_data={
                'total_test_cases': 10,
                'passed_count': 8,
                'failed_count': 2
            },
            status="completed"
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        return report
    
    @pytest.fixture
    def export_manager(self, db_session):
        """导出管理器fixture"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ExportManager(db=db_session, upload_dir=tmp_dir)
            yield manager
            # 清理会在临时目录删除时自动完成
    
    def test_export_manager_initialization(self, export_manager):
        """测试导出管理器初始化"""
        assert export_manager.db is not None
        assert export_manager.upload_dir.exists()
        assert export_manager.task_queue is not None
        assert export_manager.task_queue.running is True
    
    def test_get_supported_formats(self, export_manager):
        """测试获取支持的格式"""
        formats = export_manager.get_supported_formats()
        
        assert 'html' in formats
        # PDF和Excel的支持取决于依赖库是否安装
    
    def test_export_report_html(self, export_manager, test_report):
        """测试HTML格式报告导出"""
        task_id = export_manager.export_report(
            test_report.id,
            ExportFormat.HTML,
            {'title': '测试HTML导出'}
        )
        
        assert task_id is not None
        assert len(task_id) > 0
        
        # 获取任务状态
        task = export_manager.get_export_status(task_id)
        assert task is not None
        assert task.report_id == test_report.id
        assert task.format == ExportFormat.HTML
        assert task.status == ExportStatus.PENDING
    
    def test_export_report_excel(self, export_manager, test_report):
        """测试Excel格式报告导出"""
        task_id = export_manager.export_report(
            test_report.id,
            ExportFormat.EXCEL,
            {'title': '测试Excel导出'}
        )
        
        assert task_id is not None
        
        task = export_manager.get_export_status(task_id)
        assert task is not None
        assert task.format == ExportFormat.EXCEL
    
    def test_get_export_status_not_found(self, export_manager):
        """测试获取不存在的导出状态"""
        task = export_manager.get_export_status("non-existent-task")
        assert task is None
    
    def test_generate_filename(self, export_manager):
        """测试文件名生成"""
        filename = export_manager._generate_filename(
            123,
            ExportFormat.HTML,
            {'filename_prefix': 'custom_report'}
        )
        
        assert filename.startswith('custom_report_')
        assert filename.endswith('.html')
        assert len(filename) > 20  # 包含时间戳
    
    def test_generate_filename_excel(self, export_manager):
        """测试Excel文件名生成"""
        filename = export_manager._generate_filename(
            456,
            ExportFormat.EXCEL,
            {}
        )
        
        assert filename.startswith('report_456_')
        assert filename.endswith('.xlsx')
    
    def test_get_report_data(self, export_manager, test_report):
        """测试获取报告数据"""
        data = export_manager._get_report_data(test_report.id)
        
        assert data['id'] == test_report.id
        assert data['title'] == test_report.title
        assert data['report_type'] == test_report.report_type
        assert 'report_data' in data
        assert 'report_generated_at' in data
    
    def test_get_report_data_not_found(self, export_manager):
        """测试获取不存在的报告数据"""
        data = export_manager._get_report_data(99999)
        assert data == {}
    
    def test_render_report_content(self, export_manager):
        """测试渲染报告内容"""
        report_data = {
            'title': '测试报告',
            'report_type': 'execution',
            'report_generated_at': '2024-01-15 10:30:00'
        }
        
        content = export_manager._render_report_content(report_data, {})
        
        assert '测试报告' in content
        assert 'execution' in content
        assert '2024-01-15 10:30:00' in content
        assert '<h1>' in content
        assert '<h2>' in content
    
    def test_cleanup_old_files(self, export_manager):
        """测试清理旧文件"""
        # 创建一个旧文件
        old_file = export_manager.upload_dir / "old_report.html"
        old_file.write_text("old content")
        
        # 修改文件时间为7天前
        old_time = datetime.utcnow() - timedelta(days=8)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        # 创建一个新文件
        new_file = export_manager.upload_dir / "new_report.html"
        new_file.write_text("new content")
        
        assert old_file.exists()
        assert new_file.exists()
        
        # 清理旧文件
        export_manager.cleanup_old_files(days=7)
        
        # 验证旧文件被删除，新文件保留
        assert not old_file.exists()
        assert new_file.exists()


class TestExportTask:
    """导出任务测试"""
    
    def test_export_task_creation(self):
        """测试导出任务创建"""
        task = ExportTask(
            id="test-task",
            report_id=1,
            format=ExportFormat.PDF,
            options={'title': 'Test'},
            status=ExportStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        assert task.id == "test-task"
        assert task.report_id == 1
        assert task.format == ExportFormat.PDF
        assert task.status == ExportStatus.PENDING
        assert task.started_at is None
        assert task.completed_at is None
        assert task.progress == 0.0


class TestExportResult:
    """导出结果测试"""
    
    def test_export_result_success(self):
        """测试成功的导出结果"""
        result = ExportResult(
            success=True,
            file_path="/path/to/file.pdf",
            file_size=1024,
            metadata={'format': 'pdf'}
        )
        
        assert result.success is True
        assert result.file_path == "/path/to/file.pdf"
        assert result.file_size == 1024
        assert result.error_message is None
        assert result.metadata['format'] == 'pdf'
    
    def test_export_result_failure(self):
        """测试失败的导出结果"""
        result = ExportResult(
            success=False,
            error_message="Export failed"
        )
        
        assert result.success is False
        assert result.file_path is None
        assert result.file_size is None
        assert result.error_message == "Export failed"


class TestGlobalExportManager:
    """全局导出管理器测试"""
    
    def test_get_export_manager_singleton(self):
        """测试全局导出管理器单例"""
        manager1 = get_export_manager()
        manager2 = get_export_manager()
        
        assert manager1 is manager2  # 应该是同一个实例
        assert isinstance(manager1, ExportManager)


class TestExportFormats:
    """导出格式测试"""
    
    def test_export_format_enum(self):
        """测试导出格式枚举"""
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.EXCEL.value == "excel"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
    
    def test_export_status_enum(self):
        """测试导出状态枚举"""
        assert ExportStatus.PENDING.value == "pending"
        assert ExportStatus.IN_PROGRESS.value == "in_progress"
        assert ExportStatus.COMPLETED.value == "completed"
        assert ExportStatus.FAILED.value == "failed"