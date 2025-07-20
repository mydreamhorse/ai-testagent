# 测试说明

本项目使用 pytest 框架进行测试，所有测试文件都放在 `tests` 目录下。

## 测试文件结构

```
tests/
├── test_frontend_auth.py      # 前端认证和API测试
├── test_sqlalchemy_query.py   # SQLAlchemy数据库查询测试
├── test_fastapi_query.py      # FastAPI查询逻辑测试
├── test_api_responses.py      # API响应测试
├── test_frontend_detail.py    # 前端详情测试
├── test_testcase_detail.py    # 测试用例详情测试
├── test_workflow.py           # 工作流测试
└── test_system.py             # 系统集成测试

docs/
└── TESTING_GUIDE.md           # 本文件
```

## 运行测试

### 运行所有测试
```bash
python -m pytest
```

### 运行特定测试文件
```bash
python -m pytest tests/test_frontend_auth.py
```

### 运行特定测试函数
```bash
python -m pytest tests/test_frontend_auth.py::test_login
```

### 使用测试运行脚本
```bash
python run_tests.py                    # 运行所有测试
python run_tests.py api               # 运行API测试
python run_tests.py database          # 运行数据库测试
python run_tests.py --verbose         # 详细输出
```

## 测试分类

### API测试 (`@pytest.mark.api`)
- 测试API端点的响应
- 测试认证和授权
- 测试数据格式和验证

### 数据库测试 (`@pytest.mark.database`)
- 测试SQLAlchemy查询
- 测试数据模型
- 测试数据库连接

### 前端测试 (`@pytest.mark.frontend`)
- 测试前端组件
- 测试用户界面
- 测试前端路由

### 集成测试 (`@pytest.mark.integration`)
- 测试端到端功能
- 测试系统集成
- 测试工作流

### 单元测试 (`@pytest.mark.unit`)
- 测试单个函数
- 测试模块功能
- 测试工具函数

## 测试标记

使用 pytest 标记来分类和组织测试：

```python
@pytest.mark.api
def test_api_endpoint():
    """API测试"""
    pass

@pytest.mark.database
def test_database_query():
    """数据库测试"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """慢速测试"""
    pass
```

## 运行特定类型的测试

```bash
# 运行API测试
python -m pytest -m api

# 运行数据库测试
python -m pytest -m database

# 运行除慢速测试外的所有测试
python -m pytest -m "not slow"

# 运行集成测试
python -m pytest -m integration
```

## 测试配置

pytest 配置文件：`pytest.ini`

主要配置：
- 测试路径：`tests/`
- 测试文件模式：`test_*.py`
- 测试函数模式：`test_*`
- 详细输出：`-v`
- 颜色输出：`--color=yes`

## 测试最佳实践

1. **测试命名**：使用描述性的测试名称
2. **测试隔离**：每个测试应该独立运行
3. **使用 fixtures**：共享测试数据和设置
4. **断言消息**：提供清晰的失败消息
5. **测试覆盖**：确保关键功能有测试覆盖

## 示例测试

```python
import pytest
import requests

@pytest.fixture
def auth_token():
    """获取认证token"""
    response = requests.post("/api/v1/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]

@pytest.mark.api
def test_get_user_info(auth_token):
    """测试获取用户信息"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["username"] == "admin"
```

## 故障排除

### 常见问题

1. **导入错误**：确保 Python 路径正确设置
2. **数据库连接**：确保数据库文件存在且可访问
3. **API服务**：确保后端服务正在运行
4. **依赖问题**：确保所有依赖已安装

### 调试测试

```bash
# 详细输出
python -m pytest -v

# 显示本地变量
python -m pytest -l

# 停止在第一个失败
python -m pytest -x

# 显示最慢的测试
python -m pytest --durations=10
``` 