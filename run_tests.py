#!/usr/bin/env python3
"""
测试运行脚本
"""

import subprocess
import sys
import os

def run_pytest(category=None, verbose=False):
    """运行pytest测试"""
    cmd = ["python", "-m", "pytest"]
    
    if category:
        cmd.extend(["-m", category])
    
    if verbose:
        cmd.append("-v")
    
    print(f"运行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

def main():
    """主函数"""
    args = sys.argv[1:]
    category = None
    verbose = True
    
    # 解析参数
    i = 0
    while i < len(args):
        if args[i] in ["-v", "--verbose"]:
            verbose = True
            args.pop(i)
        elif args[i] == "-m" and i + 1 < len(args):
            category = args[i + 1]
            args.pop(i)  # 移除 -m
            args.pop(i)  # 移除类别参数
        else:
            i += 1
    
    print("=== 运行测试 ===")
    
    if category:
        print(f"测试类别: {category}")
    else:
        print("运行所有测试")
    
    exit_code = run_pytest(category, verbose)
    
    if exit_code == 0:
        print("\n✅ 所有测试通过")
    else:
        print(f"\n❌ 测试失败，退出码: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 