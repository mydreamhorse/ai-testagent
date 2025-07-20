# 文档规则更新记录

## 更新概述

本次更新增加了新的项目规则：**所有 `*.md` 文件都直接创建到根目录的 `docs` 目录下，除了 `README.md` 放在根目录下**。

## 更新内容

### 1. 新增项目规则

**规则**：所有 `*.md` 文件都直接创建到根目录的 `docs` 目录下，除了 `README.md` 放在根目录下

**目的**：
- 保持项目根目录整洁
- 集中管理所有文档
- 提高项目结构的可维护性

### 2. 文件移动

#### 移动的文件
- `tests/README.md` → `docs/TESTING_GUIDE.md`
- `CLAUDE.md` → `docs/CLAUDE.md`

#### 保留的文件
- `README.md` - 保留在根目录（项目主文档）

### 3. 文档更新

#### 更新的文件
1. **docs/TESTING_GUIDE.md**
   - 更新了文件结构说明
   - 修正了路径引用

2. **README.md**
   - 添加了项目规则说明
   - 更新了项目结构图
   - 添加了文档目录说明

3. **docs/PROJECT_RULES.md**（新建）
   - 创建了完整的项目规则文档
   - 包含文件组织、代码规范、测试规范等

## 最终目录结构

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
│   ├── CLAUDE.md            # Claude相关文档
│   ├── TEST_MIGRATION_SUMMARY.md  # 测试迁移总结
│   ├── TEST_CASE_VISIBILITY_FIX.md # 测试用例可见性修复
│   ├── TIMEOUT_FIX.md       # 超时修复
│   ├── STARTUP_GUIDE.md     # 启动指南
│   ├── PROXY_CONFIGURATION.md # 代理配置
│   └── DOCUMENTATION_RULES_UPDATE.md # 本文档
├── backend/                  # 后端代码
├── frontend/                 # 前端代码
└── tests/                   # 测试代码
    ├── test_frontend_auth.py
    ├── test_sqlalchemy_query.py
    ├── test_fastapi_query.py
    └── ...
```

## 项目规则总结

### 当前项目规则

1. **测试文件规则**
   - 所有 `test_*.py` 文件都放在 `tests` 目录下
   - 使用 pytest 框架编写
   - 作为回归测试脚本使用

2. **文档文件规则**
   - 所有 `*.md` 文件都放在 `docs` 目录下
   - 除了 `README.md` 放在根目录下
   - 保持项目根目录整洁

### 规则执行

- ✅ 所有测试文件都在 `tests` 目录下
- ✅ 所有文档文件都在 `docs` 目录下（除 README.md）
- ✅ 项目根目录保持整洁
- ✅ 文档结构清晰有序

## 使用指南

### 创建新文档
```bash
# 创建新的文档文件
touch docs/NEW_DOCUMENT.md

# 编辑文档
vim docs/NEW_DOCUMENT.md
```

### 文档命名规范
- 使用大写字母和下划线
- 文件名应该描述文档内容
- 使用 `.md` 扩展名

### 文档链接
在代码或其他文档中引用文档时，使用相对路径：
```markdown
详细规则请参考：[docs/PROJECT_RULES.md](docs/PROJECT_RULES.md)
```

## 验证结果

### 文件位置验证
```bash
# 检查根目录的 .md 文件
find . -maxdepth 1 -name "*.md" -type f
# 结果：只有 README.md

# 检查 docs 目录的 .md 文件
ls docs/*.md
# 结果：所有其他 .md 文件都在 docs 目录下
```

### 规则遵守验证
- ✅ 根目录只有 `README.md`
- ✅ 所有其他 `.md` 文件都在 `docs` 目录下
- ✅ 测试文件都在 `tests` 目录下
- ✅ 项目结构清晰有序

## 后续维护

### 定期检查
- 定期检查是否有新的 `.md` 文件创建在错误位置
- 确保新创建的文档遵循命名规范
- 更新文档索引和链接

### 团队培训
- 向团队成员介绍新的文档规则
- 确保所有成员都了解文件组织规范
- 在代码审查中检查规则遵守情况

---

**更新时间**：2025年1月18日  
**更新人**：AI Assistant  
**规则版本**：v1.0 