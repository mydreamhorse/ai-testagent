#!/bin/bash

echo "🚀 汽车座椅软件测试智能体系统"
echo "=================================="
echo ""
echo "📱 前端应用: http://localhost:3002/"
echo "🔧 后端API: http://localhost:8000/"
echo "📚 API文档: http://localhost:8000/docs"
echo "📊 ReDoc文档: http://localhost:8000/redoc"
echo ""
echo "🎯 快速测试账户:"
echo "用户名: admin"
echo "密码: admin123"
echo ""
echo "💡 使用提示:"
echo "1. 先注册用户账户或使用测试账户登录"
echo "2. 创建需求并上传需求文档内容"
echo "3. 解析需求提取特征"
echo "4. 生成测试用例"
echo "5. 评估测试用例质量"
echo "6. 查看数据分析和可视化"
echo ""

# 打开前端应用
if command -v xdg-open > /dev/null; then
    echo "🌐 正在打开前端应用..."
    xdg-open http://localhost:3002/
elif command -v open > /dev/null; then
    echo "🌐 正在打开前端应用..."
    open http://localhost:3002/
else
    echo "请手动在浏览器中打开: http://localhost:3002/"
fi