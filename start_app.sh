#!/bin/bash

# 汽车座椅软件测试智能体启动脚本

echo "🚀 启动汽车座椅软件测试智能体..."

# 检查Python依赖
echo "📦 检查Python依赖..."
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "❌ Python依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

# 检查Node.js依赖
echo "📦 检查前端依赖..."
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ 前端依赖未安装，正在安装..."
    cd frontend && npm install && cd ..
fi

# 杀掉可能存在的进程
echo "🔄 清理旧进程..."
pkill -f "python.*start_backend.py" 2>/dev/null
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null

# 启动后端
echo "🔧 启动后端服务..."
python start_backend.py &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 测试后端
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

# 测试前端
if curl -s http://localhost:3000/ > /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务启动失败"
    exit 1
fi

echo ""
echo "🎉 汽车座椅软件测试智能体启动成功！"
echo ""
echo "📱 前端应用: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🧪 测试页面: http://localhost:3000/test_frontend.html"
echo ""
echo "按 Ctrl+C 停止服务"

# 保存PID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; echo "✅ 服务已停止"; exit 0' INT

# 保持脚本运行
while true; do
    sleep 1
done 