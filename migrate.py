#!/usr/bin/env python3
"""
数据库迁移命令行工具
"""
import sys
import argparse
import logging
from backend.migrations import run_migration, get_migration_status, DatabaseMigration


def setup_logging(verbose=False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_migrate(args):
    """执行迁移"""
    print("开始数据库迁移...")
    success = run_migration()
    if success:
        print("✅ 数据库迁移成功完成")
        return 0
    else:
        print("❌ 数据库迁移失败")
        return 1


def cmd_status(args):
    """显示迁移状态"""
    print("检查数据库迁移状态...")
    status = get_migration_status()
    
    if "error" in status:
        print(f"❌ 获取状态失败: {status['error']}")
        return 1
    
    print("\n📊 数据库状态:")
    print(f"  核心表: {'✅' if status['core_tables'] else '❌'}")
    print(f"  报告表: {'✅' if status['reporting_tables'] else '❌'}")
    print(f"  总表数: {status['total_tables']}")
    print(f"  默认模板: {status['default_templates']}")
    print(f"  告警规则: {status['alert_rules']}")
    print(f"  迁移完成: {'✅' if status['migration_complete'] else '❌'}")
    
    if args.verbose:
        print(f"\n📋 现有表列表:")
        for table in status['existing_tables']:
            print(f"  - {table}")
    
    return 0


def cmd_reset(args):
    """重置数据库（危险操作）"""
    if not args.force:
        print("⚠️  这是一个危险操作，将删除所有数据！")
        print("如果确定要继续，请使用 --force 参数")
        return 1
    
    print("⚠️  开始重置数据库...")
    
    with DatabaseMigration() as migration:
        # 删除所有表
        if migration.drop_all_tables():
            print("✅ 所有表已删除")
            
            # 重新创建表
            if migration.create_all_tables():
                print("✅ 表重新创建完成")
                
                # 初始化默认数据
                if migration.initialize_default_data():
                    print("✅ 默认数据初始化完成")
                    print("✅ 数据库重置成功")
                    return 0
    
    print("❌ 数据库重置失败")
    return 1


def cmd_init_data(args):
    """初始化默认数据"""
    print("初始化默认数据...")
    
    with DatabaseMigration() as migration:
        if migration.initialize_default_data():
            print("✅ 默认数据初始化完成")
            return 0
        else:
            print("❌ 默认数据初始化失败")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python migrate.py migrate          # 执行迁移
  python migrate.py status           # 查看状态
  python migrate.py status -v        # 查看详细状态
  python migrate.py reset --force    # 重置数据库
  python migrate.py init-data        # 初始化默认数据
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # migrate 命令
    migrate_parser = subparsers.add_parser("migrate", help="执行数据库迁移")
    migrate_parser.set_defaults(func=cmd_migrate)
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="显示迁移状态")
    status_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    status_parser.set_defaults(func=cmd_status)
    
    # reset 命令
    reset_parser = subparsers.add_parser("reset", help="重置数据库（危险操作）")
    reset_parser.add_argument(
        "--force",
        action="store_true",
        help="强制执行重置操作"
    )
    reset_parser.set_defaults(func=cmd_reset)
    
    # init-data 命令
    init_parser = subparsers.add_parser("init-data", help="初始化默认数据")
    init_parser.set_defaults(func=cmd_init_data)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 执行命令
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())