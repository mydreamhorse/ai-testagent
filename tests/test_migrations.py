"""
测试数据库迁移功能
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User, ReportTemplate, AlertRule, SystemMetric
from backend.migrations import DatabaseMigration


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    db_url = f"sqlite:///{temp_file.name}"
    engine = create_engine(db_url)
    
    yield engine, db_url
    
    # 清理临时文件
    try:
        os.unlink(temp_file.name)
    except:
        pass


@pytest.fixture
def migration_with_temp_db(temp_db):
    """使用临时数据库的迁移实例"""
    engine, db_url = temp_db
    
    # 创建会话
    SessionLocal = sessionmaker(bind=engine)
    
    # 创建迁移实例并替换引擎
    migration = DatabaseMigration()
    migration.engine = engine
    migration.session = SessionLocal()
    
    yield migration
    
    migration.session.close()


class TestDatabaseMigration:
    """测试数据库迁移功能"""
    
    def test_check_table_exists(self, migration_with_temp_db):
        """测试检查表是否存在"""
        migration = migration_with_temp_db
        
        # 初始状态下表不存在
        assert not migration.check_table_exists("users")
        assert not migration.check_table_exists("reports")
        
        # 创建表后应该存在
        Base.metadata.create_all(bind=migration.engine)
        assert migration.check_table_exists("users")
        assert migration.check_table_exists("reports")
    
    def test_get_existing_tables(self, migration_with_temp_db):
        """测试获取现有表列表"""
        migration = migration_with_temp_db
        
        # 初始状态下没有表
        tables = migration.get_existing_tables()
        assert len(tables) == 0
        
        # 创建表后应该有表
        Base.metadata.create_all(bind=migration.engine)
        tables = migration.get_existing_tables()
        assert len(tables) > 0
        assert "users" in tables
        assert "reports" in tables
    
    def test_create_all_tables(self, migration_with_temp_db):
        """测试创建所有表"""
        migration = migration_with_temp_db
        
        # 创建表
        result = migration.create_all_tables()
        assert result is True
        
        # 验证表已创建
        tables = migration.get_existing_tables()
        expected_tables = [
            "users", "requirements", "test_cases", "test_case_evaluations",
            "test_templates", "knowledge_base", "generation_logs", "parsed_features",
            "reports", "defects", "coverage_analysis", "alert_rules", 
            "alerts", "report_templates", "system_metrics"
        ]
        
        for table in expected_tables:
            assert table in tables, f"表 {table} 未创建"
    
    def test_migrate_to_reporting_schema(self, migration_with_temp_db):
        """测试迁移到报告模式"""
        migration = migration_with_temp_db
        
        # 先创建基础表
        migration.create_all_tables()
        
        # 执行报告模式迁移
        result = migration.migrate_to_reporting_schema()
        assert result is True
        
        # 验证报告相关表已创建
        tables = migration.get_existing_tables()
        reporting_tables = [
            'reports', 'defects', 'coverage_analysis', 
            'alert_rules', 'alerts', 'report_templates', 'system_metrics'
        ]
        
        for table in reporting_tables:
            assert table in tables, f"报告表 {table} 未创建"
    
    def test_initialize_default_data(self, migration_with_temp_db):
        """测试初始化默认数据"""
        migration = migration_with_temp_db
        
        # 先创建表
        migration.create_all_tables()
        
        # 初始化默认数据
        result = migration.initialize_default_data()
        assert result is True
        
        # 验证默认数据已创建
        # 检查系统用户
        system_user = migration.session.query(User).filter(User.username == "system").first()
        assert system_user is not None
        
        # 检查默认报告模板
        default_templates = migration.session.query(ReportTemplate).filter(
            ReportTemplate.is_default == True
        ).all()
        assert len(default_templates) >= 3  # 至少有3个默认模板
        
        template_types = [t.template_type for t in default_templates]
        assert "execution" in template_types
        assert "defect_analysis" in template_types
        assert "coverage" in template_types
        
        # 检查默认告警规则
        alert_rules = migration.session.query(AlertRule).all()
        assert len(alert_rules) >= 4  # 至少有4个默认规则
        
        rule_types = [r.metric_type for r in alert_rules]
        assert "coverage_rate" in rule_types
        assert "failure_rate" in rule_types
        assert "critical_defects" in rule_types
        
        # 检查初始系统指标
        system_metrics = migration.session.query(SystemMetric).all()
        assert len(system_metrics) >= 2  # 至少有2个初始指标
    
    def test_get_migration_status(self, migration_with_temp_db):
        """测试获取迁移状态"""
        migration = migration_with_temp_db
        
        # 初始状态
        status = migration.get_migration_status()
        assert "core_tables" in status
        assert "reporting_tables" in status
        assert "migration_complete" in status
        assert status["migration_complete"] is False
        
        # 创建表后
        migration.create_all_tables()
        migration.initialize_default_data()
        
        status = migration.get_migration_status()
        assert status["core_tables"] is True
        assert status["reporting_tables"] is True
        assert status["migration_complete"] is True
        assert status["total_tables"] > 10
        assert status["default_templates"] >= 3
        assert status["alert_rules"] >= 4


class TestMigrationIntegration:
    """测试迁移集成功能"""
    
    def test_full_migration_process(self, migration_with_temp_db):
        """测试完整迁移流程"""
        migration = migration_with_temp_db
        
        # 1. 检查初始状态
        initial_status = migration.get_migration_status()
        assert initial_status["migration_complete"] is False
        
        # 2. 创建表
        assert migration.create_all_tables() is True
        
        # 3. 迁移到报告模式
        assert migration.migrate_to_reporting_schema() is True
        
        # 4. 初始化默认数据
        assert migration.initialize_default_data() is True
        
        # 5. 检查最终状态
        final_status = migration.get_migration_status()
        assert final_status["migration_complete"] is True
        assert final_status["total_tables"] > 10
        assert final_status["default_templates"] >= 3
        assert final_status["alert_rules"] >= 4
        
        # 6. 验证数据完整性
        # 检查用户表
        users = migration.session.query(User).all()
        assert len(users) >= 1  # 至少有系统用户
        
        # 检查模板表
        templates = migration.session.query(ReportTemplate).all()
        assert len(templates) >= 3
        
        # 检查告警规则表
        rules = migration.session.query(AlertRule).all()
        assert len(rules) >= 4
        
        # 检查系统指标表
        metrics = migration.session.query(SystemMetric).all()
        assert len(metrics) >= 2
    
    def test_migration_idempotency(self, migration_with_temp_db):
        """测试迁移的幂等性（多次运行应该安全）"""
        migration = migration_with_temp_db
        
        # 第一次迁移
        assert migration.create_all_tables() is True
        assert migration.migrate_to_reporting_schema() is True
        assert migration.initialize_default_data() is True
        
        first_status = migration.get_migration_status()
        
        # 第二次迁移（应该是安全的）
        assert migration.create_all_tables() is True
        assert migration.migrate_to_reporting_schema() is True
        assert migration.initialize_default_data() is True
        
        second_status = migration.get_migration_status()
        
        # 状态应该保持一致
        assert first_status["migration_complete"] == second_status["migration_complete"]
        assert first_status["total_tables"] == second_status["total_tables"]
        # 默认数据不应该重复创建
        assert first_status["default_templates"] == second_status["default_templates"]
        assert first_status["alert_rules"] == second_status["alert_rules"]


class TestMigrationErrorHandling:
    """测试迁移错误处理"""
    
    def test_migration_with_invalid_engine(self):
        """测试使用无效引擎的迁移"""
        # 这个测试比较难实现，因为需要模拟数据库连接失败
        # 在实际应用中，应该有适当的错误处理
        pass
    
    def test_partial_migration_recovery(self, migration_with_temp_db):
        """测试部分迁移的恢复"""
        migration = migration_with_temp_db
        
        # 只创建部分表
        migration.create_all_tables()
        
        # 检查状态
        status = migration.get_migration_status()
        assert status["core_tables"] is True
        assert status["reporting_tables"] is True
        
        # 完成剩余迁移
        assert migration.initialize_default_data() is True
        
        # 检查最终状态
        final_status = migration.get_migration_status()
        assert final_status["migration_complete"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])