#!/bin/bash

# 智能测试报告系统验收测试脚本

set -e

echo "🧪 开始执行智能测试报告系统验收测试..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装"
    exit 1
fi

# 检查pytest
if ! python -c "import pytest" 2>/dev/null; then
    echo "❌ pytest未安装，正在安装..."
    pip install pytest pytest-asyncio
fi

# 检查requests
if ! python -c "import requests" 2>/dev/null; then
    echo "❌ requests未安装，正在安装..."
    pip install requests
fi

# 创建测试结果目录
mkdir -p test_results

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查后端服务
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务未运行，请先启动服务"
    echo "提示: 运行 ./start_app.sh 或 docker-compose up"
    exit 1
fi

# 检查前端服务
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务未运行，请先启动服务"
    echo "提示: 运行 ./start_app.sh 或 docker-compose up"
    exit 1
fi

# 运行验收测试
echo "🚀 开始执行验收测试..."

# 基础功能测试
echo "📋 执行基础功能测试..."
python -m pytest tests/test_acceptance.py::TestReportGeneration -v --tb=short --junitxml=test_results/report_generation.xml

# 数据分析测试
echo "📊 执行数据分析测试..."
python -m pytest tests/test_acceptance.py::TestDataAnalytics -v --tb=short --junitxml=test_results/data_analytics.xml

# 监控功能测试
echo "📈 执行监控功能测试..."
python -m pytest tests/test_acceptance.py::TestMonitoring -v --tb=short --junitxml=test_results/monitoring.xml

# 模板管理测试
echo "📝 执行模板管理测试..."
python -m pytest tests/test_acceptance.py::TestTemplateManagement -v --tb=short --junitxml=test_results/template_management.xml

# 前端集成测试
echo "🎨 执行前端集成测试..."
python -m pytest tests/test_acceptance.py::TestFrontendIntegration -v --tb=short --junitxml=test_results/frontend_integration.xml

# 性能测试
echo "⚡ 执行性能测试..."
python -m pytest tests/test_acceptance.py::TestPerformance -v --tb=short --junitxml=test_results/performance.xml

# 数据完整性测试
echo "🔒 执行数据完整性测试..."
python -m pytest tests/test_acceptance.py::TestDataIntegrity -v --tb=short --junitxml=test_results/data_integrity.xml

# 生成测试报告
echo "📄 生成测试报告..."

# 创建HTML测试报告
if command -v pytest-html &> /dev/null; then
    python -m pytest tests/test_acceptance.py -v --html=test_results/acceptance_test_report.html --self-contained-html
else
    echo "⚠️  pytest-html未安装，跳过HTML报告生成"
fi

# 统计测试结果
echo ""
echo "📊 测试结果统计:"
echo "=================="

total_tests=0
passed_tests=0
failed_tests=0

for xml_file in test_results/*.xml; do
    if [ -f "$xml_file" ]; then
        # 使用python解析XML文件统计结果
        result=$(python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$xml_file')
    root = tree.getroot()
    tests = int(root.get('tests', 0))
    failures = int(root.get('failures', 0))
    errors = int(root.get('errors', 0))
    passed = tests - failures - errors
    print(f'{tests},{passed},{failures + errors}')
except:
    print('0,0,0')
")
        IFS=',' read -r tests passed failed <<< "$result"
        total_tests=$((total_tests + tests))
        passed_tests=$((passed_tests + passed))
        failed_tests=$((failed_tests + failed))
    fi
done

echo "总测试数: $total_tests"
echo "通过测试: $passed_tests"
echo "失败测试: $failed_tests"

if [ $failed_tests -eq 0 ]; then
    echo ""
    echo "🎉 所有验收测试通过！"
    echo ""
    echo "✅ 系统功能验证完成，可以投入使用"
    echo ""
    echo "📋 测试报告位置:"
    echo "   - XML报告: test_results/*.xml"
    if [ -f "test_results/acceptance_test_report.html" ]; then
        echo "   - HTML报告: test_results/acceptance_test_report.html"
    fi
    echo ""
    echo "🚀 系统已准备就绪！"
    exit 0
else
    echo ""
    echo "❌ 验收测试失败，发现 $failed_tests 个问题"
    echo ""
    echo "请检查测试报告并修复问题后重新测试"
    echo ""
    echo "📋 测试报告位置:"
    echo "   - XML报告: test_results/*.xml"
    if [ -f "test_results/acceptance_test_report.html" ]; then
        echo "   - HTML报告: test_results/acceptance_test_report.html"
    fi
    exit 1
fi