# API 快速配置指南

**目标**: 5分钟内完成 API 配置并启动系统

---

## ⚡ 快速开始

### 1. 准备 API 密钥

您需要准备以下两个 API 密钥：

#### ✅ Gemini 3 Pro Preview API Key
- **获取地址**: https://makersuite.google.com/app/apikey
- **示例格式**: `AIzaSy...` (以 AIzaSy 开头)

#### ✅ Claude Sonnet 4.5 认证（二选一）

**方式A - 代理接入（推荐中国大陆用户）**:
- Base URL: `https://crs.yidang.net/api`
- Auth Token: `sk-z-...` (从代理服务商获取)

**方式B - 官方API（海外用户）**:
- API Key: `sk-ant-api03-...` (从 https://console.anthropic.com/ 获取)

---

## 🚀 配置步骤

### 方法1: 使用提供的配置（推荐）

如果您使用的是文档中提供的示例配置，可以直接使用：

```bash
# 1. 进入项目目录
cd /home/opadm/repo/HL-OS

# 2. 已自动创建 .env 文件，包含以下配置：
# - Gemini API Key: AI......nk
# - Claude 代理: https://CHANGE.ME
# - Claude Token: sk......fa

# 3. 直接启动服务
make dev

# 4. 等待服务启动（约30-60秒）
# 看到 "✅ All services are up" 即表示成功

# 5. 访问前端
# 浏览器打开: http://localhost:8501
```

### 方法2: 自定义配置

如果您有自己的 API 密钥：

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件
nano .env

# 3. 修改以下配置项：

# Gemini API Key（必填）
GOOGLE_AI_STUDIO_API_KEY=你的Gemini-API-Key

# Claude 配置（二选一）
# 方式A - 使用代理（推荐）
ANTHROPIC_BASE_URL=https://crs.yidang.net/api
ANTHROPIC_AUTH_TOKEN=你的Auth-Token

# 方式B - 使用官方API
# ANTHROPIC_API_KEY=你的Claude-API-Key

# 4. 保存文件（Ctrl+O, 回车, Ctrl+X）

# 5. 启动服务
make dev
```

---

## ✅ 验证配置

### 1. 检查服务状态

```bash
# 查看所有服务是否正常运行
docker-compose ps

# 应该看到以下服务都是 "Up" 状态：
# - backend
# - frontend
# - anythingllm
# - redis
```

### 2. 检查后端日志

```bash
# 查看后端启动日志
make logs-backend | tail -50

# 应该看到：
# ✅ "ClaudeService initialized with proxy: base_url=https://crs.yidang.net/api"
# 或 "ClaudeService initialized with standard API"
# ✅ "GeminiVisionService initialized with model: gemini-3-pro-preview-11-2025"
```

### 3. 访问前端

```bash
# 在浏览器打开
http://localhost:8501

# 应该看到：
# ✅ HL-OS 主页面
# ✅ 左侧边栏有4个导航菜单
# ✅ 中间显示3个功能模块卡片
```

### 4. 测试基础功能

```bash
# 访问 API 文档
http://localhost:8000/docs

# 测试健康检查
curl http://localhost:8000/api/v1/health

# 应该返回:
# {"status": "ok", "timestamp": "..."}
```

---

## 🔧 常见问题

### ❌ 问题1: 服务启动失败

**症状**: `docker-compose up` 报错

**解决方案**:
```bash
# 1. 检查 Docker 是否运行
docker ps

# 2. 检查端口是否被占用
netstat -tlnp | grep -E "8000|8501|3001|6379"

# 3. 清理并重启
make clean
make dev
```

### ❌ 问题2: Claude API 连接失败

**症状**: 日志显示 "401 Unauthorized" 或 "Connection timeout"

**解决方案**:
```bash
# 1. 检查配置
cat .env | grep ANTHROPIC

# 2. 如果使用代理，确保配置正确
ANTHROPIC_BASE_URL=https://crs.yidang.net/api  # 注意没有尾部斜杠
ANTHROPIC_AUTH_TOKEN=sk-z-...  # 确保 token 完整

# 3. 如果使用官方API，检查密钥格式
ANTHROPIC_API_KEY=sk-ant-api03-...  # 确保以 sk-ant-api03- 开头

# 4. 重启服务
make restart
```

### ❌ 问题3: Gemini API 配额超限

**症状**: "Resource has been exhausted" 或 "Quota exceeded"

**解决方案**:
```bash
# 1. 检查 API 配额
# 访问: https://makersuite.google.com/app/apikey

# 2. 降低速率限制
# 编辑 .env:
GEMINI_RPM=15  # 免费层限制为每分钟15次

# 3. 重启服务
make restart
```

### ❌ 问题4: 前端无法访问

**症状**: 浏览器显示 "无法访问此网站"

**解决方案**:
```bash
# 1. 检查 frontend 容器状态
docker-compose ps frontend

# 2. 查看 frontend 日志
make logs-frontend

# 3. 确认端口映射
docker-compose port frontend 8501

# 4. 尝试使用 IP 地址访问
http://127.0.0.1:8501
```

---

## 📚 详细文档

配置完成后，建议阅读以下文档：

- **[API配置指南](docs/guides/API_CONFIGURATION.md)** - 详细的配置说明
- **[开发文档](docs/guides/DEVELOPMENT.md)** - 开发环境搭建
- **[功能测试清单](TESTING_CHECKLIST.md)** - 全面测试系统功能

---

## 🎯 下一步

配置成功后，您可以：

1. **测试OCR功能**
   - 进入"📸 作业校验"页面
   - 上传一张作业图片
   - 查看AI识别结果

2. **测试教学内容生成**
   - 进入"📚 内容生成"页面
   - 选择知识点
   - 生成微课PPT

3. **测试评测引擎**
   - 进入"📝 评测管理"页面
   - 配置题目参数
   - 生成原创题目

4. **执行完整测试**
   ```bash
   # 查看测试清单
   cat TESTING_CHECKLIST.md

   # 按照清单逐项测试
   ```

---

## 🆘 获取帮助

如果遇到其他问题：

1. 查看完整日志：`make logs`
2. 检查配置文件：`cat .env`
3. 重启服务：`make restart`
4. 提交 Issue 并附上错误日志

---

<div align="center">

**配置完成！开始使用 HL-OS 吧！** 🎉

**下一步**: 访问 http://localhost:8501 开始使用

</div>
