"""
数据库迁移和初始化模块
"""
import logging
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base, User, ReportTemplate, AlertRule, SystemMetric

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.engine = engine
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    def get_existing_tables(self) -> list:
        """获取现有表列表"""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def create_all_tables(self):
        """创建所有表"""
        try:
            logger.info("开始创建数据库表...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
            return True
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            return False
    
    def drop_all_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            logger.warning("开始删除所有数据库表...")
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("所有数据库表已删除")
            return True
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            return False
    
    def migrate_to_reporting_schema(self):
        """迁移到智能报告模式"""
        try:
            logger.info("开始迁移到智能报告模式...")
            
            # 检查新表是否已存在
            new_tables = [
                'reports', 'defects', 'coverage_analysis', 
                'alert_rules', 'alerts', 'report_templates', 'system_metrics'
            ]
            
            existing_tables = self.get_existing_tables()
            missing_tables = [table for table in new_tables if table not in existing_tables]
            
            if not missing_tables:
                logger.info("智能报告相关表已存在，无需迁移")
                return True
            
            logger.info(f"需要创建的表: {missing_tables}")
            
            # 创建新表
            Base.metadata.create_all(bind=self.engine)
            
            # 验证表创建
            updated_tables = self.get_existing_tables()
            created_tables = [table for table in new_tables if table in updated_tables]
            
            logger.info(f"成功创建表: {created_tables}")
            
            if len(created_tables) == len(new_tables):
                logger.info("智能报告模式迁移完成")
                return True
            else:
                logger.error(f"部分表创建失败，预期: {new_tables}, 实际: {created_tables}")
                return False
                
        except Exception as e:
            logger.error(f"迁移到智能报告模式失败: {e}")
            return False
    
    def initialize_default_data(self):
        """初始化默认数据"""
        try:
            logger.info("开始初始化默认数据...")
            
            # 初始化默认报告模板
            self._create_default_report_templates()
            
            # 初始化默认告警规则
            self._create_default_alert_rules()
            
            # 初始化系统指标记录
            self._create_initial_system_metrics()
            
            logger.info("默认数据初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化默认数据失败: {e}")
            return False
    
    def _create_default_report_templates(self):
        """创建默认报告模板"""
        # 检查是否已有默认模板
        existing_templates = self.session.query(ReportTemplate).filter(
            ReportTemplate.is_default == True
        ).count()
        
        if existing_templates > 0:
            logger.info("默认报告模板已存在，跳过创建")
            return
        
        # 创建默认的系统用户（如果不存在）
        system_user = self.session.query(User).filter(User.username == "system").first()
        if not system_user:
            system_user = User(
                username="system",
                email="system@example.com",
                hashed_password="system_hash",
                is_active=True
            )
            self.session.add(system_user)
            self.session.commit()
            self.session.refresh(system_user)
        
        default_templates = [
            {
                "template_name": "标准测试执行报告",
                "template_type": "execution",
                "template_content": """
                <html>
                <head><title>测试执行报告</title></head>
                <body>
                    <h1>{{title}}</h1>
                    <h2>执行概要</h2>
                    <p>总测试用例: {{total_tests}}</p>
                    <p>通过: {{passed_tests}}</p>
                    <p>失败: {{failed_tests}}</p>
                    <p>通过率: {{pass_rate}}%</p>
                    
                    <h2>详细结果</h2>
                    {{test_details}}
                    
                    <h2>图表分析</h2>
                    {{charts}}
                </body>
                </html>
                """,
                "template_config": {
                    "sections": ["summary", "details", "charts"],
                    "chart_types": ["bar", "pie"],
                    "filters": ["date_range", "test_type", "priority"]
                },
                "description": "标准的测试执行报告模板，包含概要、详情和图表"
            },
            {
                "template_name": "缺陷分析报告",
                "template_type": "defect_analysis",
                "template_content": """
                <html>
                <head><title>缺陷分析报告</title></head>
                <body>
                    <h1>{{title}}</h1>
                    <h2>缺陷统计</h2>
                    <p>总缺陷数: {{total_defects}}</p>
                    <p>严重缺陷: {{critical_defects}}</p>
                    <p>高优先级: {{high_defects}}</p>
                    
                    <h2>缺陷分布</h2>
                    {{defect_distribution}}
                    
                    <h2>趋势分析</h2>
                    {{trend_analysis}}
                </body>
                </html>
                """,
                "template_config": {
                    "sections": ["statistics", "distribution", "trends"],
                    "chart_types": ["line", "bar", "heatmap"],
                    "filters": ["severity", "type", "status"]
                },
                "description": "缺陷分析报告模板，包含统计、分布和趋势"
            },
            {
                "template_name": "覆盖率分析报告",
                "template_type": "coverage",
                "template_content": """
                <html>
                <head><title>测试覆盖率报告</title></head>
                <body>
                    <h1>{{title}}</h1>
                    <h2>覆盖率概览</h2>
                    <p>总体覆盖率: {{overall_coverage}}%</p>
                    <p>功能覆盖率: {{functional_coverage}}%</p>
                    <p>需求覆盖率: {{requirement_coverage}}%</p>
                    
                    <h2>模块覆盖率</h2>
                    {{module_coverage}}
                    
                    <h2>未覆盖区域</h2>
                    {{uncovered_areas}}
                </body>
                </html>
                """,
                "template_config": {
                    "sections": ["overview", "modules", "gaps"],
                    "chart_types": ["heatmap", "bar", "treemap"],
                    "filters": ["module", "requirement_type"]
                },
                "description": "测试覆盖率分析报告模板"
            }
        ]
        
        for template_data in default_templates:
            template = ReportTemplate(
                template_name=template_data["template_name"],
                template_type=template_data["template_type"],
                template_content=template_data["template_content"],
                template_config=template_data["template_config"],
                description=template_data["description"],
                created_by=system_user.id,
                is_default=True,
                is_active=True
            )
            self.session.add(template)
        
        self.session.commit()
        logger.info(f"创建了 {len(default_templates)} 个默认报告模板")
    
    def _create_default_alert_rules(self):
        """创建默认告警规则"""
        # 检查是否已有告警规则
        existing_rules = self.session.query(AlertRule).count()
        
        if existing_rules > 0:
            logger.info("告警规则已存在，跳过创建")
            return
        
        # 获取系统用户
        system_user = self.session.query(User).filter(User.username == "system").first()
        if not system_user:
            logger.warning("系统用户不存在，跳过创建默认告警规则")
            return
        
        default_rules = [
            {
                "rule_name": "测试覆盖率过低告警",
                "metric_type": "coverage_rate",
                "condition_operator": "<",
                "threshold_value": 80.0,
                "severity": "high",
                "notification_channels": ["email", "in_app"],
                "description": "当测试覆盖率低于80%时触发告警"
            },
            {
                "rule_name": "测试失败率过高告警",
                "metric_type": "failure_rate",
                "condition_operator": ">",
                "threshold_value": 10.0,
                "severity": "high",
                "notification_channels": ["email", "in_app"],
                "description": "当测试失败率超过10%时触发告警"
            },
            {
                "rule_name": "严重缺陷数量告警",
                "metric_type": "critical_defects",
                "condition_operator": ">",
                "threshold_value": 0.0,
                "severity": "critical",
                "notification_channels": ["email", "sms", "in_app"],
                "description": "发现严重缺陷时立即告警"
            },
            {
                "rule_name": "测试执行时间过长告警",
                "metric_type": "execution_time",
                "condition_operator": ">",
                "threshold_value": 1800.0,  # 30分钟
                "severity": "medium",
                "notification_channels": ["in_app"],
                "description": "测试执行时间超过30分钟时告警"
            }
        ]
        
        for rule_data in default_rules:
            rule = AlertRule(
                rule_name=rule_data["rule_name"],
                metric_type=rule_data["metric_type"],
                condition_operator=rule_data["condition_operator"],
                threshold_value=rule_data["threshold_value"],
                severity=rule_data["severity"],
                notification_channels=rule_data["notification_channels"],
                description=rule_data["description"],
                created_by=system_user.id,
                is_active=True
            )
            self.session.add(rule)
        
        self.session.commit()
        logger.info(f"创建了 {len(default_rules)} 个默认告警规则")
    
    def _create_initial_system_metrics(self):
        """创建初始系统指标记录"""
        # 创建一些初始的系统指标记录作为示例
        initial_metrics = [
            {
                "metric_name": "system_startup",
                "metric_type": "system",
                "metric_value": 1.0,
                "unit": "count",
                "tags": {"event": "migration", "version": "1.0.0"}
            },
            {
                "metric_name": "database_tables",
                "metric_type": "system",
                "metric_value": len(self.get_existing_tables()),
                "unit": "count",
                "tags": {"migration": "reporting_schema"}
            }
        ]
        
        for metric_data in initial_metrics:
            metric = SystemMetric(
                metric_name=metric_data["metric_name"],
                metric_type=metric_data["metric_type"],
                metric_value=metric_data["metric_value"],
                unit=metric_data["unit"],
                tags=metric_data["tags"]
            )
            self.session.add(metric)
        
        self.session.commit()
        logger.info(f"创建了 {len(initial_metrics)} 个初始系统指标")
    
    def get_migration_status(self) -> dict:
        """获取迁移状态"""
        try:
            existing_tables = self.get_existing_tables()
            
            # 检查核心表
            core_tables = ['users', 'requirements', 'test_cases']
            core_status = all(table in existing_tables for table in core_tables)
            
            # 检查报告相关表
            reporting_tables = [
                'reports', 'defects', 'coverage_analysis', 
                'alert_rules', 'alerts', 'report_templates', 'system_metrics'
            ]
            reporting_status = all(table in existing_tables for table in reporting_tables)
            
            # 检查默认数据（只有在表存在时才查询）
            default_templates = 0
            default_rules = 0
            
            if 'report_templates' in existing_tables:
                try:
                    default_templates = self.session.query(ReportTemplate).filter(
                        ReportTemplate.is_default == True
                    ).count()
                except Exception as e:
                    logger.warning(f"查询默认模板失败: {e}")
            
            if 'alert_rules' in existing_tables:
                try:
                    default_rules = self.session.query(AlertRule).count()
                except Exception as e:
                    logger.warning(f"查询告警规则失败: {e}")
            
            return {
                "core_tables": core_status,
                "reporting_tables": reporting_status,
                "total_tables": len(existing_tables),
                "existing_tables": existing_tables,
                "default_templates": default_templates,
                "alert_rules": default_rules,
                "migration_complete": core_status and reporting_status
            }
            
        except Exception as e:
            logger.error(f"获取迁移状态失败: {e}")
            return {
                "error": str(e),
                "core_tables": False,
                "reporting_tables": False,
                "migration_complete": False
            }


def run_migration():
    """运行数据库迁移"""
    with DatabaseMigration() as migration:
        logger.info("开始数据库迁移...")
        
        # 1. 创建所有表
        if not migration.create_all_tables():
            logger.error("表创建失败，迁移中止")
            return False
        
        # 2. 迁移到报告模式
        if not migration.migrate_to_reporting_schema():
            logger.error("报告模式迁移失败")
            return False
        
        # 3. 初始化默认数据
        if not migration.initialize_default_data():
            logger.error("默认数据初始化失败")
            return False
        
        # 4. 检查迁移状态
        status = migration.get_migration_status()
        if status.get("migration_complete"):
            logger.info("数据库迁移完成")
            logger.info(f"迁移状态: {status}")
            return True
        else:
            logger.error(f"迁移未完全成功: {status}")
            return False


def get_migration_status():
    """获取迁移状态"""
    with DatabaseMigration() as migration:
        return migration.get_migration_status()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行迁移
    success = run_migration()
    if success:
        print("数据库迁移成功完成")
    else:
        print("数据库迁移失败")
        exit(1)