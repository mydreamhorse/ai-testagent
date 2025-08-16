# 智能测试报告系统部署指南

## 目录
1. [部署概述](#部署概述)
2. [系统要求](#系统要求)
3. [部署方式](#部署方式)
4. [配置说明](#配置说明)
5. [监控设置](#监控设置)
6. [故障排除](#故障排除)
7. [维护指南](#维护指南)

## 部署概述

智能测试报告系统支持多种部署方式，推荐使用Docker容器化部署以确保环境一致性和便于管理。

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Frontend      │    │   Backend       │
│   (反向代理)     │────│   (Vue.js)      │────│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Redis         │    │   SQLite        │
         └──────────────│   (缓存)        │    │   (数据库)      │
                        └─────────────────┘    └─────────────────┘
```

## 系统要求

### 硬件要求

**最低配置:**
- CPU: 2核心
- 内存: 4GB RAM
- 磁盘: 20GB 可用空间
- 网络: 100Mbps

**推荐配置:**
- CPU: 4核心
- 内存: 8GB RAM
- 磁盘: 50GB SSD
- 网络: 1Gbps

### 软件要求

**Docker部署:**
- Docker 20.10+
- Docker Compose 2.0+
- Linux/macOS/Windows

**本地部署:**
- Python 3.11+
- Node.js 18+
- Redis 6.0+
- Nginx 1.20+ (可选)

## 部署方式

### 方式一：Docker部署（推荐）

#### 1. 准备部署文件

```bash
# 克隆项目
git clone <repository-url>
cd intelligent-test-reporting

# 进入部署目录
cd deploy
```

#### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./test.db

# Redis配置
REDIS_URL=redis://redis:6379

# 应用配置
LOG_LEVEL=INFO
MONITORING_ENABLED=true

# 邮件配置（可选）
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@example.com

# 告警配置（可选）
WEBHOOK_URL=https://hooks.slack.com/your-webhook-url
```

#### 3. 执行部署

```bash
# 运行部署脚本
./deploy.sh
```

部署脚本会自动：
- 构建Docker镜像
- 启动所有服务
- 执行健康检查
- 显示访问地址

#### 4. 验证部署

访问以下地址验证部署：
- 主应用: http://localhost
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

### 方式二：本地开发部署

#### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install && cd ..

# 启动Redis（如果未安装）
# Ubuntu/Debian: sudo apt install redis-server
# macOS: brew install redis
# Windows: 下载并安装Redis
```

#### 2. 初始化数据库

```bash
# 运行数据库迁移
python migrate.py
```

#### 3. 启动服务

```bash
# 使用启动脚本
./start_app.sh

# 或手动启动
# 终端1: 启动后端
python start_backend.py

# 终端2: 启动前端
cd frontend && npm run dev
```

### 方式三：生产环境部署

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建应用用户
sudo useradd -m -s /bin/bash appuser
sudo usermod -aG docker appuser
```

#### 2. 部署应用

```bash
# 切换到应用用户
sudo su - appuser

# 克隆代码
git clone <repository-url> /opt/intelligent-test-reporting
cd /opt/intelligent-test-reporting

# 配置生产环境变量
cp deploy/.env.example deploy/.env
# 编辑 deploy/.env 文件，设置生产环境配置

# 执行部署
cd deploy && ./deploy.sh
```

#### 3. 配置系统服务

创建systemd服务文件：

```bash
sudo tee /etc/systemd/system/intelligent-test-reporting.service > /dev/null <<EOF
[Unit]
Description=Intelligent Test Reporting System
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/intelligent-test-reporting/deploy
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=appuser
Group=appuser

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable intelligent-test-reporting
sudo systemctl start intelligent-test-reporting
```

## 配置说明

### 数据库配置

#### SQLite（默认）
```python
DATABASE_URL = "sqlite:///./test.db"
```

#### PostgreSQL（推荐生产环境）
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/testdb"
```

#### MySQL
```python
DATABASE_URL = "mysql://user:password@localhost:3306/testdb"
```

### Redis配置

```python
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,  # 如果设置了密码
    "max_connections": 20
}
```

### 日志配置

```python
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "filename": "logs/application.log",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        },
        "console": {
            "stream": "stdout"
        }
    }
}
```

### Nginx配置

生产环境建议使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API请求
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 监控设置

### Prometheus配置

编辑 `deploy/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:3000']
```

### Grafana仪表板

1. 访问 http://localhost:3001
2. 使用 admin/admin123 登录
3. 导入预配置的仪表板
4. 配置告警通知渠道

### 告警规则

编辑 `deploy/alert_rules.yml` 添加自定义告警：

```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: CustomMetricHigh
        expr: custom_metric > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "自定义指标过高"
```

## 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs [service_name]

# 重启服务
docker-compose restart [service_name]
```

#### 2. 数据库连接问题

```bash
# 检查数据库文件权限
ls -la test.db

# 测试数据库连接
python -c "from backend.database import engine; print('数据库连接正常')"
```

#### 3. 端口冲突

```bash
# 检查端口占用
netstat -tulpn | grep :8000
lsof -i :8000

# 修改端口配置
# 编辑 docker-compose.yml 或环境变量
```

#### 4. 内存不足

```bash
# 检查内存使用
free -h
docker stats

# 清理Docker资源
docker system prune -f
```

### 日志分析

#### 应用日志位置
- 容器内: `/app/logs/`
- 主机映射: `./logs/`

#### 常用日志命令
```bash
# 实时查看日志
docker-compose logs -f backend

# 查看最近100行日志
docker-compose logs --tail=100 backend

# 搜索错误日志
docker-compose logs backend | grep ERROR
```

## 维护指南

### 定期维护任务

#### 每日检查
- [ ] 检查服务运行状态
- [ ] 查看错误日志
- [ ] 监控系统资源使用

#### 每周维护
- [ ] 清理旧日志文件
- [ ] 检查磁盘空间
- [ ] 更新系统补丁

#### 每月维护
- [ ] 备份数据库
- [ ] 清理临时文件
- [ ] 性能优化检查

### 备份策略

#### 数据库备份
```bash
# SQLite备份
cp test.db backup/test_$(date +%Y%m%d).db

# PostgreSQL备份
pg_dump -h localhost -U user testdb > backup/testdb_$(date +%Y%m%d).sql
```

#### 配置文件备份
```bash
# 备份配置文件
tar -czf backup/config_$(date +%Y%m%d).tar.gz deploy/ docs/
```

#### 自动备份脚本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp test.db $BACKUP_DIR/test_$DATE.db

# 备份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz deploy/ docs/

# 清理7天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

### 更新升级

#### 应用更新
```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose down && docker-compose up -d
```

#### 数据库迁移
```bash
# 运行数据库迁移
python migrate.py

# 验证迁移结果
python -c "from backend.database import engine; print('迁移完成')"
```

### 性能优化

#### 数据库优化
```sql
-- 添加索引
CREATE INDEX idx_reports_created_at ON reports(created_at);
CREATE INDEX idx_test_cases_status ON test_cases(status);

-- 清理历史数据
DELETE FROM reports WHERE created_at < DATE('now', '-90 days');
```

#### 缓存优化
```python
# Redis缓存配置优化
REDIS_CONFIG = {
    "max_connections": 50,
    "connection_pool_kwargs": {
        "max_connections": 50,
        "retry_on_timeout": True
    }
}
```

### 安全加固

#### 系统安全
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

#### 应用安全
- 定期更新依赖包
- 使用强密码
- 启用HTTPS
- 配置访问控制

## 技术支持

### 联系方式
- 邮箱: support@example.com
- 文档: https://docs.example.com
- 问题反馈: https://github.com/example/issues

### 紧急联系
- 24/7技术支持: +86-xxx-xxxx-xxxx
- 紧急邮箱: emergency@example.com

---

*部署指南最后更新时间: 2024年1月*