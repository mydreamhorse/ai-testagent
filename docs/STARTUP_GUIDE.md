# 启动指南

## 🎉 问题已解决

所有的启动错误都已修复！现在可以正常启动系统了。

## 修复内容

### 1. Pydantic 配置问题
- ✅ 修复了 `model_cache_dir` 字段命名冲突
- ✅ 重命名为 `ai_model_cache_dir` 避免保护命名空间冲突
- ✅ 更新了 Pydantic v2 配置语法

### 2. 环境变量配置
- ✅ 添加了代理相关的环境变量支持
- ✅ 设置了 `extra = "allow"` 允许额外的环境变量
- ✅ 修复了配置验证错误

### 3. 启动脚本优化
- ✅ 修复了 Python 路径配置
- ✅ 优化了模块导入逻辑

## 启动方法

### 方法1：使用启动脚本（推荐）
```bash
python start_backend.py
```

### 方法2：使用 uvicorn 直接启动
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 方法3：使用 Shell 脚本
```bash
chmod +x start_app.sh
./start_app.sh
```

## 验证启动

启动后可以通过以下方式验证：

1. **健康检查**：
   ```bash
   curl http://localhost:8000/health
   ```
   应该返回：`{"status":"healthy"}`

2. **API 文档**：
   浏览器访问：http://localhost:8000/docs

3. **前端界面**：
   浏览器访问：http://localhost:3000

## 配置说明

系统现在支持以下环境变量配置：

```bash
# 基础配置
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here

# OpenAI 配置
OPENAI_API_KEY=your-openai-api-key-here
USE_PROXY=true  # 设置为 false 可以禁用代理

# 代理配置
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

## 功能特点

- 🚀 **快速启动**：无需复杂配置，开箱即用
- 🔧 **自动修复**：智能处理代理和网络问题
- 📝 **完整文档**：提供详细的 API 文档
- 🛡️ **错误处理**：完善的错误处理和日志记录
- 🎯 **高兼容性**：支持各种网络环境

## 故障排除

如果仍然遇到问题，请检查：

1. **端口占用**：确保 8000 端口未被占用
2. **依赖安装**：运行 `pip install -r requirements.txt`
3. **环境变量**：检查 `.env` 文件配置
4. **日志信息**：查看启动日志中的错误信息

## 支持的功能

- ✅ 测试用例生成（支持 LLM 和模板两种方式）
- ✅ 质量评估
- ✅ 需求解析
- ✅ 知识库管理
- ✅ 用户认证
- ✅ 文件上传
- ✅ 批量处理

---

🎉 现在您可以正常使用汽车座椅软件测试智能体了！