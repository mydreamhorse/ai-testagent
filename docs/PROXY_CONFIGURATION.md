# 代理配置说明

## 问题描述

如果您遇到以下错误：
```
Error generating test cases: Using SOCKS proxy, but the 'socksio' package is not installed.
```

这表明系统检测到了SOCKS代理配置，但缺少必要的依赖包。

## 解决方案

### 1. 安装必要的依赖包

已经在 `requirements.txt` 中添加了必要的依赖：

```bash
pip install -r requirements.txt
```

这将自动安装：
- `httpx[socks]` - 支持SOCKS代理的HTTP客户端
- `socksio` - SOCKS代理支持库

### 2. 配置环境变量

创建 `.env` 文件（可以从 `.env.example` 复制）：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件：

```bash
# OpenAI配置
OPENAI_API_KEY=your-openai-api-key-here

# 代理配置
USE_PROXY=true  # 设置为false可以禁用代理

# 如果需要手动配置代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

### 3. 代理问题排查

如果仍然遇到代理问题，可以尝试：

#### 选项1：禁用代理（推荐）
在 `.env` 文件中设置：
```bash
USE_PROXY=false
```

#### 选项2：配置代理环境变量
确保代理配置正确：
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
export NO_PROXY=localhost,127.0.0.1
```

#### 选项3：清除代理配置
如果不需要代理，可以清除环境变量：
```bash
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY
```

### 4. 错误处理机制

系统已经添加了智能错误处理：

1. **自动检测代理错误**：系统会自动识别SOCKS代理相关错误
2. **自动降级**：当OpenAI API不可用时，自动切换到模板生成
3. **详细日志**：提供详细的错误信息和解决建议

### 5. 测试配置

重启后端服务器以应用新配置：

```bash
# 停止现有服务器
pkill -f uvicorn

# 启动服务器
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 系统行为

- ✅ **有OpenAI API Key + 网络正常**：使用LLM生成高质量测试用例
- ✅ **有OpenAI API Key + 代理问题**：自动切换到模板生成
- ✅ **无OpenAI API Key**：直接使用模板生成

无论哪种情况，系统都会正常工作，确保测试用例生成功能可用。

## 常见问题

### Q: 为什么会有代理错误？
A: 系统检测到了环境中的代理配置，但缺少支持SOCKS代理的依赖包。

### Q: 是否必须使用OpenAI API？
A: 不是必须的。系统有完整的备用方案，可以使用内置模板生成测试用例。

### Q: 如何验证修复是否成功？
A: 尝试生成测试用例，如果不再出现SOCKS代理错误，说明修复成功。

### Q: 模板生成的测试用例质量如何？
A: 模板生成的测试用例包含完整的测试结构，涵盖功能、边界、异常、性能、安全等5种测试类型。

## 技术细节

修复包括：
1. 安装 `socksio` 和 `httpx[socks]` 依赖
2. 改进错误处理和日志记录
3. 添加代理配置选项
4. 实现自动降级机制
5. 提供详细的配置文档