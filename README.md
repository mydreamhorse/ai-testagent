# 汽车座椅软件测试智能体

## 项目概述

汽车座椅软件测试智能体是一个基于AI的测试用例生成和质量评估系统，专门针对汽车座椅软件功能测试需求设计。系统能够自动解析需求文档、生成高质量测试用例，并提供专业的质量评估和改进建议。

## 核心特性

### 🔍 智能需求解析
- 支持中文需求文档解析
- 自动识别功能类型（电动调节、记忆、加热、通风、按摩、安全）
- 提取参数约束和依赖关系
- 智能分类和优先级判断

### 🔧 测试用例生成
- 基于模板和规则的生成算法
- 支持多种测试类型：
  - 功能测试：验证基本功能
  - 边界测试：极值条件验证
  - 异常测试：故障场景处理
  - 性能测试：响应时间和效率
  - 安全测试：安全保护机制
- 生成速度：<30秒/用例

### 📊 质量评估系统
- **5维度评估体系**：
  - 完整性（25%）：前置条件、测试步骤、预期结果
  - 准确性（25%）：技术术语、操作描述准确性
  - 可执行性（20%）：操作可行性、结果可验证性
  - 覆盖度（20%）：功能点和场景覆盖
  - 清晰度（10%）：语言表达和结构清晰度
- 自动评分：0-100分制
- 智能建议：提供具体改进方案

### 🎯 质量目标
- 生成质量评分：>85分
- 与专家评价一致性：>90%
- 功能覆盖率：>95%
- 效率提升：90%（相比人工编写）

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104.1
- **数据库**: SQLAlchemy + SQLite/PostgreSQL
- **AI处理**: 
  - jieba：中文分词
  - 正则表达式：参数提取
  - 规则引擎：特征识别
- **认证**: JWT + OAuth2
- **异步**: Celery + Redis

### 前端技术栈
- **框架**: Vue.js 3 + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts + vue-echarts
- **构建**: Vite

### 数据模型设计
```
User (用户)
├── Requirement (需求) [1:N]
│   ├── ParsedFeature (解析特征) [1:N]
│   └── TestCase (测试用例) [1:N]
│       └── TestCaseEvaluation (质量评估) [1:1]
├── TestTemplate (测试模板)
└── KnowledgeBase (知识库)
```

## 项目规则

本项目遵循以下规则和约定：

### 📁 文件组织规则
- **测试文件**：所有 `test_*.py` 文件都放在 `tests` 目录下，使用 pytest 框架编写
- **文档文件**：所有 `*.md` 文件都放在 `docs` 目录下，除了 `README.md` 放在根目录

详细规则请参考：[docs/PROJECT_RULES.md](docs/PROJECT_RULES.md)

## 项目结构

```
mytestagent/
├── README.md                 # 项目概述（根目录）
├── requirements.txt          # Python依赖
├── docs/                     # 文档目录
│   ├── PROJECT_RULES.md      # 项目规则
│   ├── TESTING_GUIDE.md      # 测试指南
│   ├── DEPLOYMENT.md         # 部署指南
│   ├── PRD.md               # 产品需求文档
│   ├── TODO.md              # 开发任务清单
│   └── ...                  # 其他文档
├── backend/                  # 后端代码
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models.py            # 数据模型
│   ├── schemas.py           # Pydantic模式
│   ├── ai/                  # AI核心组件
│   │   ├── requirement_parser.py    # 需求解析器
│   │   ├── test_case_generator.py   # 测试用例生成器
│   │   └── quality_evaluator.py    # 质量评估器
│   └── routers/             # API路由
│       ├── auth.py          # 认证模块
│       ├── requirements.py  # 需求管理
│       ├── test_cases.py    # 测试用例
│       ├── generation.py    # 智能生成
│       ├── templates.py     # 模板管理
│       └── knowledge.py     # 知识库
├── frontend/                 # 前端代码
│   ├── package.json         # 前端依赖
│   ├── vite.config.ts       # Vite配置
│   ├── src/
│   │   ├── main.ts          # 应用入口
│   │   ├── App.vue          # 根组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # 状态管理
│   │   ├── components/      # 组件
│   │   ├── views/           # 页面
│   │   ├── api/             # API调用
│   │   └── types/           # 类型定义
└── tests/                   # 测试代码
    ├── test_frontend_auth.py    # 前端认证测试
    ├── test_sqlalchemy_query.py # 数据库查询测试
    ├── test_fastapi_query.py    # FastAPI查询测试
    └── ...                      # 其他测试文件
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- SQLite/PostgreSQL

### 后端启动
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
cd backend
python main.py

# API文档: http://localhost:8000/docs
```

### 前端启动
```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 前端应用: http://localhost:3000
```

### 核心功能验证
```bash
# 运行核心功能验证
python verify_core.py

# 运行简化测试
python simple_test.py
```

## API接口

### 认证模块
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取用户信息

### 需求管理
- `POST /api/v1/requirements/` - 创建需求
- `GET /api/v1/requirements/` - 获取需求列表
- `GET /api/v1/requirements/{id}` - 获取需求详情
- `POST /api/v1/requirements/{id}/parse` - 解析需求

### 测试用例
- `POST /api/v1/test-cases/` - 创建测试用例
- `GET /api/v1/test-cases/` - 获取测试用例列表
- `POST /api/v1/test-cases/{id}/evaluate` - 评估测试用例

### 智能生成
- `POST /api/v1/generation/test-cases` - 生成测试用例
- `POST /api/v1/generation/evaluation` - 生成质量评估
- `GET /api/v1/generation/status/{task_id}` - 获取任务状态

## 使用示例

### 1. 需求解析示例
```python
# 输入需求
requirement = """
座椅记忆功能要求：
1. 支持3组记忆位置存储
2. 记忆内容包括前后位置0-250mm、上下位置0-80mm、靠背角度90-160度
3. 调节到记忆位置时间不超过5秒
"""

# 解析结果
features = [
    {
        "name": "记忆功能",
        "type": "记忆功能", 
        "parameters": {"min_value": 0, "max_value": 250},
        "priority": "high"
    }
]
```

### 2. 测试用例生成示例
```python
# 生成的测试用例
test_case = {
    "title": "记忆功能基本功能测试",
    "test_type": "function",
    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置",
    "test_steps": """1. 打开记忆功能控制界面
2. 选择记忆位置1
3. 调整座椅到期望位置
4. 点击存储按钮""",
    "expected_result": "座椅位置成功存储，系统显示存储成功提示"
}
```

### 3. 质量评估示例
```python
# 评估结果
evaluation = {
    "total_score": 87.5,
    "completeness_score": 90.0,
    "accuracy_score": 85.0,
    "executability_score": 88.0,
    "coverage_score": 86.0,
    "clarity_score": 89.0,
    "suggestions": [
        "建议增加异常情况的测试步骤",
        "可以添加更具体的验证点"
    ]
}
```

## 开发进度

### ✅ 第一阶段：基础架构搭建（已完成）
- [x] 项目目录结构创建
- [x] 开发环境配置
- [x] 数据库设计和实现（6个核心模型）
- [x] FastAPI后端框架搭建
- [x] Vue.js前端项目初始化

### ✅ 第二阶段：核心功能开发（已完成）
- [x] 需求解析器实现
  - [x] 中文分词和句子分割
  - [x] 功能类型识别（6种座椅功能）
  - [x] 参数和约束提取
  - [x] 优先级和依赖关系识别
- [x] 测试用例生成器开发
  - [x] 多类型测试用例生成（功能、边界、异常、性能、安全）
  - [x] 基于模板的用例生成系统
  - [x] 智能优先级分配
- [x] 质量评估器实现
  - [x] 5维度评估体系（完整性、准确性、可执行性、覆盖度、清晰度）
  - [x] 自动评分算法（0-100分制）
  - [x] 智能改进建议生成
- [x] 前端界面开发
  - [x] Vue3 + TypeScript + Element Plus架构
  - [x] 用户认证和权限管理
  - [x] 需求管理、测试用例管理界面
  - [x] 质量评估和数据可视化界面
- [x] API接口集成
  - [x] 完整的RESTful API设计（4个模块，15+个端点）
  - [x] 异步任务处理
  - [x] 错误处理和日志记录
- [x] 系统集成测试
  - [x] 核心功能验证脚本
  - [x] 端到端工作流程测试
  - [x] 数据库模型和API测试

### 🔄 第三阶段：模型训练和优化（进行中）
- [x] 基于规则的评估算法实现
- [x] 测试数据生成和验证
- [ ] 大规模数据收集和标注
- [ ] 深度学习模型训练
- [ ] 模型性能优化和校准

### 🔄 第四阶段：测试和部署（待完成）
- [ ] 系统压力测试
- [ ] 性能优化
- [ ] 用户接受测试
- [ ] 生产环境部署配置

## 贡献指南

1. Fork项目仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者：mydreamhorse@gmail.com
- 技术支持：请提交Issue到GitHub仓库

---

*本项目基于PRD.md设计开发，旨在提升汽车座椅软件测试的效率和质量。*