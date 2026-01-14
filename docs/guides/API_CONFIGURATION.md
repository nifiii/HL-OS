# API配置指南

本文档详细说明如何配置 HL-OS 系统的各项 API 密钥和连接方式。

---

## 📋 目录

- [Gemini 3 Pro Preview 配置](#gemini-3-pro-preview-配置)
- [Claude Sonnet 4.5 配置](#claude-sonnet-45-配置)
  - [方式1: 直连官方API](#方式1-直连官方api)
  - [方式2: 代理接入（推荐中国大陆用户）](#方式2-代理接入推荐中国大陆用户)
- [AnythingLLM 配置](#anythingllm-配置)
- [常见问题](#常见问题)

---

## Gemini 3 Pro Preview 配置

### 获取 API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 使用 Google 账号登录
3. 点击 "Create API Key" 创建新密钥
4. 复制生成的 API Key

### 配置到 .env 文件

```bash
GOOGLE_AI_STUDIO_API_KEY=AIzaSy...你的API密钥
GEMINI_MODEL=gemini-3-pro-preview-11-2025
```

### 验证配置

```bash
# 测试 Gemini API 连接
docker-compose exec backend python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_AI_STUDIO_API_KEY'))
model = genai.GenerativeModel('gemini-3-pro-preview-11-2025')
print('✅ Gemini API 配置成功！')
"
```

---

## Claude Sonnet 4.5 配置

Claude 提供两种接入方式，根据您的网络环境选择合适的方式。

### 方式1: 直连官方API

**适用场景**: 海外用户、有稳定国际网络的用户

#### 获取 API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 在 API Keys 页面创建新密钥
4. 复制 API Key

#### 配置到 .env 文件

```bash
# 使用官方 API（注释掉代理配置）
ANTHROPIC_API_KEY=sk-ant-api03-...你的API密钥
# ANTHROPIC_BASE_URL=
# ANTHROPIC_AUTH_TOKEN=

# 模型配置
CLAUDE_MODEL_TEACHING=claude-sonnet-4-5-20250929
CLAUDE_MODEL_GRADING=claude-sonnet-4-5-20250929
```

---

### 方式2: 代理接入（推荐中国大陆用户）

**适用场景**: 中国大陆用户、无法访问 Anthropic 官网的用户

#### 什么是代理接入？

代理接入是通过第三方服务提供商转发 API 请求到 Anthropic 服务器，解决网络访问问题。

#### 配置步骤

1. **获取代理服务**

   常见的代理服务商：
   - [一登科技](https://crs.yidang.net/) - 本项目使用的示例
   - [其他国内代理服务商]

2. **获取认证信息**

   代理服务通常提供：
   - `base_url`: API 基础地址
   - `auth_token`: 认证令牌

3. **配置到 .env 文件**

```bash
# 使用代理接入（注释掉官方 API 配置）
# ANTHROPIC_API_KEY=

# 代理配置
ANTHROPIC_BASE_URL=https://CHANGE.ME
ANTHROPIC_AUTH_TOKEN=sk-z-...你的认证令牌

# 模型配置
CLAUDE_MODEL_TEACHING=claude-sonnet-4-5-20250929
CLAUDE_MODEL_GRADING=claude-sonnet-4-5-20250929
```

#### 示例配置

```bash
# 完整的代理配置示例
ANTHROPIC_BASE_URL=https://CHANGE.ME
ANTHROPIC_AUTH_TOKEN=sk-z-3e74ba887b9b474e809af041f2bff179872f75630869e2f3faa266aee3146dfa
CLAUDE_MODEL_TEACHING=claude-sonnet-4-5-20250929
CLAUDE_MODEL_GRADING=claude-sonnet-4-5-20250929
```

---

### 配置优先级

系统会按照以下优先级选择配置：

1. **优先使用代理**: 如果配置了 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`
2. **备用官方API**: 如果只配置了 `ANTHROPIC_API_KEY`
3. **报错**: 如果两种方式都未配置

### 验证配置

```bash
# 方法1: 查看日志
docker-compose logs backend | grep "ClaudeService initialized"

# 应该看到以下输出之一：
# ✅ 代理方式: "ClaudeService initialized with proxy: base_url=https://CHANGE.ME"
# ✅ 官方方式: "ClaudeService initialized with standard API"

# 方法2: 测试 API 调用
docker-compose exec backend python -c "
from anthropic import Anthropic
import os

if os.getenv('ANTHROPIC_BASE_URL'):
    client = Anthropic(
        base_url=os.getenv('ANTHROPIC_BASE_URL'),
        api_key=os.getenv('ANTHROPIC_AUTH_TOKEN')
    )
    print('✅ 使用代理方式连接成功！')
else:
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    print('✅ 使用官方API连接成功！')

# 测试简单请求
response = client.messages.create(
    model='claude-sonnet-4-5-20250929',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(f'Claude 响应: {response.content[0].text}')
"
```

---

## AnythingLLM 配置

AnythingLLM 使用 Claude Sonnet 4.5 作为底层 LLM，需要配置通用 OpenAI 兼容接口。

### 配置说明

```bash
# AnythingLLM 基础配置
ANYTHINGLLM_URL=http://anythingllm:3001
ANYTHINGLLM_API_KEY=  # 留空使用默认

# 底层 LLM 配置（使用 Claude）
LLM_PROVIDER=generic-openai
GENERIC_OPEN_AI_BASE_PATH=https://api.anthropic.com/v1
GENERIC_OPEN_AI_MODEL_PREF=claude-sonnet-4-5-20250929

# 向量数据库配置
VECTOR_DB=lancedb
EMBEDDING_ENGINE=native
EMBEDDING_MODEL_PREF=nomic-embed-text
```

### 注意事项

- AnythingLLM 的 `GENERIC_OPEN_AI_BASE_PATH` 需要指向 Anthropic API
- 如果使用代理，这里仍然使用官方地址，因为 AnythingLLM 容器内部可能无法访问代理
- 后端服务（Python）直接使用代理配置，AnythingLLM（Node.js）使用官方配置

---

## 常见问题

### Q1: 如何选择直连还是代理？

**A**:
- 海外用户 → 选择**方式1（直连）**
- 中国大陆用户 → 选择**方式2（代理）**
- 如果直连速度慢或连接不稳定 → 选择**方式2（代理）**

### Q2: 代理服务安全吗？

**A**:
- 选择信誉良好的代理服务商
- 避免使用免费的不明来源代理
- 定期更换 auth_token
- 不要在公开仓库提交 `.env` 文件

### Q3: 两种方式可以同时配置吗？

**A**:
- 可以同时配置，系统会优先使用代理方式
- 建议只配置一种，避免混淆

### Q4: 如何切换配置方式？

**A**:
```bash
# 从代理切换到直连
# 1. 注释掉代理配置
# ANTHROPIC_BASE_URL=https://CHANGE.ME
# ANTHROPIC_AUTH_TOKEN=sk-z-...

# 2. 启用官方API配置
ANTHROPIC_API_KEY=sk-ant-api03-...

# 3. 重启服务
make restart
```

### Q5: 遇到 API 错误如何排查？

**A**:
```bash
# 1. 检查配置
cat .env | grep ANTHROPIC

# 2. 查看服务日志
make logs-backend

# 3. 测试连接
docker-compose exec backend python -c "
from anthropic import Anthropic
import os
# ... 运行测试代码
"

# 4. 常见错误：
# - 401 Unauthorized: API Key 或 Token 错误
# - 404 Not Found: base_url 配置错误
# - Connection timeout: 网络问题，尝试使用代理
```

### Q6: Gemini API 有配额限制吗？

**A**:
- 免费层：每分钟 15 次请求
- 付费层：更高配额
- 建议配置速率限制：`GEMINI_RPM=50`

### Q7: 如何监控 API 使用量？

**A**:
- Gemini: 访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 查看
- Claude: 访问 [Anthropic Console](https://console.anthropic.com/) 查看用量
- 代理服务: 登录代理服务商控制台查看

---

## 最佳实践

### 1. 环境隔离

```bash
# 开发环境
cp .env.example .env.dev
# 配置开发用的API密钥

# 生产环境
cp .env.example .env.prod
# 配置生产用的API密钥

# 使用时指定环境文件
docker-compose --env-file .env.dev up
```

### 2. 密钥轮换

```bash
# 定期（建议每月）更换API密钥
# 1. 创建新密钥
# 2. 更新 .env 文件
# 3. 重启服务
# 4. 删除旧密钥
```

### 3. 成本控制

```bash
# 设置速率限制
RATE_LIMIT_ENABLED=true
GEMINI_RPM=50
CLAUDE_RPM=40

# 监控日志中的API调用
make logs-backend | grep "API call"
```

### 4. 安全建议

- ✅ 不要将 `.env` 提交到版本控制
- ✅ 使用环境变量管理密钥
- ✅ 生产环境使用独立密钥
- ✅ 定期检查 API 使用情况
- ✅ 设置合理的速率限制
- ❌ 不要在代码中硬编码密钥
- ❌ 不要在日志中打印密钥

---

## 快速配置检查清单

使用本清单快速验证您的配置：

```bash
# 1. 检查 .env 文件存在
[ ] ls .env

# 2. 检查 Gemini 配置
[ ] grep GOOGLE_AI_STUDIO_API_KEY .env
[ ] grep GEMINI_MODEL .env

# 3. 检查 Claude 配置（二选一）
[ ] grep ANTHROPIC_API_KEY .env  # 或
[ ] grep ANTHROPIC_BASE_URL .env && grep ANTHROPIC_AUTH_TOKEN .env

# 4. 启动服务
[ ] make dev

# 5. 查看日志
[ ] make logs-backend | grep "initialized"

# 6. 测试功能
[ ] 访问 http://localhost:8501
[ ] 上传测试图片
[ ] 查看OCR识别结果
```

---

## 获取帮助

如果您在配置过程中遇到问题：

1. 查看 [开发文档](DEVELOPMENT.md)
2. 查看 [常见问题](#常见问题)
3. 查看容器日志：`make logs-backend`
4. 提交 Issue 描述问题

---

<div align="center">

**配置完成后，您就可以开始使用 HL-OS 了！** 🎉

</div>
