# 汽车座椅软件测试智能体 - 部署指南

## 系统概述

本系统是一个基于AI的汽车座椅软件测试用例生成和质量评估平台，包含以下核心功能：

- 📋 **需求管理**: 上传和管理测试需求文档
- 🔍 **智能解析**: AI解析需求文档，提取关键特征
- 🧪 **用例生成**: 基于AI模型自动生成多种类型的测试用例
- 📊 **质量评估**: 多维度评估测试用例质量（完整性、准确性、可执行性、覆盖度、清晰度）
- 📈 **数据分析**: 可视化展示测试数据和质量趋势

## 系统架构

### 后端 (FastAPI + Python)
- **框架**: FastAPI 0.104.1
- **数据库**: SQLAlchemy + SQLite/PostgreSQL
- **认证**: JWT Token 认证
- **AI组件**: 
  - 需求解析器 (jieba + spaCy)
  - 测试用例生成器 (模板+规则引擎)
  - 质量评估器 (多维度评分算法)

### 前端 (Vue.js 3 + TypeScript)
- **框架**: Vue 3 + Composition API
- **UI库**: Element Plus
- **状态管理**: Pinia
- **数据可视化**: ECharts
- **构建工具**: Vite

### 数据库设计
- **用户表**: 用户管理和认证
- **需求表**: 需求文档存储
- **特征表**: 解析后的需求特征
- **测试用例表**: 生成的测试用例
- **评估表**: 质量评估结果
- **知识库表**: 领域知识存储
- **生成日志表**: 操作历史记录

## 部署步骤

### 1. 环境准备

```bash
# Python 3.10+
python --version

# Node.js 16+
node --version
npm --version

# Git
git --version
```

### 2. 获取代码

```bash
git clone <repository-url>
cd mytestagent
```

### 3. 后端部署

```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量 (可选)
cp .env.example .env
# 编辑 .env 文件设置数据库URL、Secret Key等

# 初始化数据库
python -c "
from backend.database import engine
from backend.models import Base
Base.metadata.create_all(bind=engine)
print('Database initialized successfully!')
"

# 启动后端服务
python start_server.py
# 或者直接运行
cd backend && python main.py
```

### 4. 前端部署

```bash
# 安装Node.js依赖
cd frontend
npm install

# 开发模式运行
npm run dev

# 生产构建
npm run build

# 预览生产版本
npm run preview
```

### 5. 验证部署

```bash
# 运行系统测试
python final_test.py

# 运行API测试
python test_api.py

# 运行工作流测试
python test_workflow.py
```

## 配置说明

### 后端配置 (backend/config.py)

```python
# 数据库配置
database_url = "sqlite:///./test.db"  # 开发环境
# database_url = "postgresql://user:password@localhost/dbname"  # 生产环境

# Redis配置 (可选)
redis_url = "redis://localhost:6379"

# 安全配置
secret_key = "your-secret-key-here"  # 生产环境请更换
algorithm = "HS256"
access_token_expire_minutes = 30

# 文件上传配置
upload_dir = "uploads"
max_file_size = 10 * 1024 * 1024  # 10MB

# AI模型配置
model_cache_dir = "models"
```

### 前端配置

前端会自动连接到 `http://localhost:8000` 的后端API。
如需修改，请编辑 `frontend/src/api/index.ts`。

## API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取用户信息

### 需求管理
- `GET /api/v1/requirements/` - 获取需求列表
- `POST /api/v1/requirements/` - 创建需求
- `GET /api/v1/requirements/{id}` - 获取需求详情
- `POST /api/v1/requirements/{id}/parse` - 解析需求
- `POST /api/v1/requirements/upload` - 上传需求文件

### 测试用例管理
- `GET /api/v1/test-cases/` - 获取测试用例列表
- `POST /api/v1/test-cases/` - 创建测试用例
- `GET /api/v1/test-cases/{id}` - 获取测试用例详情
- `POST /api/v1/test-cases/{id}/evaluate` - 评估测试用例
- `POST /api/v1/test-cases/batch-evaluate` - 批量评估

### AI生成
- `POST /api/v1/generation/test-cases` - 生成测试用例
- `POST /api/v1/generation/evaluation` - 质量评估
- `GET /api/v1/generation/history` - 生成历史

## 使用指南

### 1. 用户注册和登录
1. 访问系统首页
2. 点击注册创建账户
3. 使用用户名和密码登录

### 2. 需求管理
1. 进入"需求管理"页面
2. 点击"新建需求"
3. 填写需求标题、描述和详细内容
4. 保存后点击"解析"按钮进行AI解析

### 3. 测试用例生成
1. 选择已解析的需求
2. 进入"AI生成"页面
3. 选择"测试用例生成"
4. 选择需要生成的测试类型
5. 点击"开始生成"

### 4. 质量评估
1. 在测试用例列表中选择需要评估的用例
2. 点击"评估"按钮进行单个评估
3. 或选择多个用例进行批量评估
4. 查看详细的评分结果和改进建议

### 5. 数据分析
1. 进入"数据分析"页面
2. 查看系统总体统计数据
3. 分析质量分数分布和趋势
4. 查看测试类型和优先级统计

## 性能优化

### 数据库优化
- 生产环境建议使用PostgreSQL
- 设置合适的数据库连接池大小
- 为经常查询的字段添加索引

### 缓存优化
- 配置Redis缓存常用查询结果
- 缓存AI模型推理结果
- 实现合理的缓存失效策略

### 前端优化
- 启用代码分割和懒加载
- 压缩静态资源
- 使用CDN加速

## 监控和维护

### 日志监控
- 后端日志位置: `logs/`
- 关键指标: 请求响应时间、错误率、AI推理耗时
- 建议集成ELK或类似日志分析系统

### 数据备份
- 定期备份数据库
- 备份用户上传的文件
- 备份AI模型和配置

### 系统更新
- 定期更新依赖包
- 监控安全漏洞
- 测试新版本兼容性

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串配置
   - 确认网络连通性

2. **AI模型加载失败**
   - 检查模型文件是否存在
   - 验证模型缓存目录权限
   - 确认依赖包版本

3. **前端连接后端失败**
   - 检查后端服务是否启动
   - 验证API端点配置
   - 检查CORS设置

4. **文件上传失败**
   - 检查上传目录权限
   - 验证文件大小限制
   - 确认支持的文件格式

### 调试命令

```bash
# 检查系统健康状态
curl http://localhost:8000/health

# 验证API认证
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass"

# 运行完整测试套件
python -m pytest tests/ -v

# 查看详细日志
tail -f logs/app.log
```

## 联系和支持

- 技术文档: 查看项目README.md
- 问题反馈: 提交GitHub Issue
- 开发团队: 查看CONTRIBUTORS.md

---

**最后更新**: 2025-07-15  
**版本**: v1.0.0  
**状态**: 生产就绪 ✅