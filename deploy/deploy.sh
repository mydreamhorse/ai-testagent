#!/bin/bash

# 智能测试报告系统部署脚本

set -e

echo "🚀 开始部署智能测试报告系统..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p ssl
mkdir -p data/prometheus
mkdir -p data/grafana

# 设置权限
echo "🔐 设置目录权限..."
chmod 755 logs
chmod 755 ssl
chmod 755 data/prometheus
chmod 755 data/grafana

# 检查配置文件
echo "📋 检查配置文件..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml文件不存在"
    exit 1
fi

if [ ! -f "nginx.conf" ]; then
    echo "❌ nginx.conf文件不存在"
    exit 1
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down --remove-orphans || true

# 清理旧的镜像（可选）
read -p "是否清理旧的Docker镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理旧镜像..."
    docker system prune -f
fi

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "▶️ 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🏥 执行健康检查..."

# 检查后端服务
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务健康检查失败"
    docker-compose logs backend
    exit 1
fi

# 检查前端服务
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务健康检查失败"
    docker-compose logs frontend
    exit 1
fi

# 检查Redis服务
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis服务运行正常"
else
    echo "❌ Redis服务健康检查失败"
    docker-compose logs redis
    exit 1
fi

# 检查Prometheus服务
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus服务运行正常"
else
    echo "❌ Prometheus服务健康检查失败"
    docker-compose logs prometheus
fi

# 检查Grafana服务
if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
    echo "✅ Grafana服务运行正常"
else
    echo "❌ Grafana服务健康检查失败"
    docker-compose logs grafana
fi

echo ""
echo "🎉 智能测试报告系统部署成功！"
echo ""
echo "📱 应用访问地址:"
echo "   - 主应用: http://localhost"
echo "   - 前端: http://localhost:3000"
echo "   - 后端API: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3001 (admin/admin123)"
echo ""
echo "📊 监控和日志:"
echo "   - 查看服务状态: docker-compose ps"
echo "   - 查看日志: docker-compose logs [service_name]"
echo "   - 停止服务: docker-compose down"
echo ""
echo "📚 更多信息请查看用户手册: docs/USER_MANUAL.md"