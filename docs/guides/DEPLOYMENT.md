# HL-OS 部署指南

本文档提供 HL-OS 系统的完整部署说明，包括环境准备、权限配置和部署步骤。

---

## 📋 目录

- [部署前准备](#部署前准备)
- [用户权限配置](#用户权限配置)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [验证部署](#验证部署)
- [常见问题](#常见问题)

---

## 部署前准备

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux (Ubuntu 18.04+, CentOS 7+) | Ubuntu 20.04 LTS / Ubuntu 22.04 LTS |
| CPU | 2 核 | 4 核或以上 |
| 内存 | 4GB | 8GB 或以上 |
| 磁盘空间 | 10GB | 20GB 或以上 |
| Docker | 20.10+ | 最新稳定版 |
| Docker Compose | 1.29+ | 最新稳定版 |

### 网络要求

- 需要访问以下外部服务（用于 AI 模型调用）：
  - Google AI Studio API (Gemini 3 Pro Preview)
  - Anthropic API / 代理服务 (Claude Sonnet 4.5)
- 端口占用检查：
  - `8000` - Backend API
  - `8501` - Frontend (Streamlit)
  - `3001` - AnythingLLM
  - `6379` - Redis

---

## 用户权限配置

### ⚠️ 重要：选择合适的部署用户

为确保部署过程顺利，**强烈建议**使用以下两种方式之一：

#### 方式 1: Root 用户部署（最简单，适合测试环境）

```bash
# 切换到 root 用户
sudo su -

# 验证当前用户
whoami
# 输出: root

# 进入工作目录
cd /opt  # 或其他合适的目录
```

**优点**：
- ✅ 无需担心权限问题
- ✅ 可以直接执行所有操作

**缺点**：
- ⚠️ 安全风险较高，不推荐在生产环境使用

---

#### 方式 2: 具有完整权限的普通用户（推荐，适合生产环境）

该用户需要满足以下条件：
1. ✅ 具有 **sudo 权限**
2. ✅ 在 **docker 用户组**中

**步骤 1: 检查当前用户权限**

```bash
# 查看当前用户
whoami

# 查看用户所属组
groups

# 检查是否在 docker 组
groups | grep docker
```

**步骤 2: 添加用户到 docker 组（如果需要）**

```bash
# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 或指定用户名
sudo usermod -aG docker your_username

# 查看修改结果
grep docker /etc/group
```

**步骤 3: 使权限生效**

```bash
# 方式 A: 重新登录（推荐）
exit
# 重新 SSH 登录

# 方式 B: 启动新的 shell
newgrp docker

# 验证 docker 权限
docker ps
# 如果不报错，说明配置成功 ✅
```

**步骤 4: 验证 sudo 权限**

```bash
# 测试 sudo 权限
sudo echo "Sudo access OK"

# 如果提示输入密码后执行成功，说明有 sudo 权限 ✅
```

### 权限验证脚本

运行以下脚本快速验证权限配置：

```bash
#!/bin/bash
echo "========== HL-OS 部署权限检查 =========="
echo ""

# 检查当前用户
echo "✓ 当前用户: $(whoami)"

# 检查用户组
echo "✓ 用户组: $(groups)"

# 检查 docker 权限
echo -n "✓ Docker 权限: "
if docker ps &>/dev/null; then
    echo "OK ✅"
else
    echo "FAILED ❌"
    echo "  解决方法: sudo usermod -aG docker $USER 并重新登录"
fi

# 检查 sudo 权限
echo -n "✓ Sudo 权限: "
if sudo -n true 2>/dev/null; then
    echo "OK (无需密码) ✅"
elif sudo -v &>/dev/null; then
    echo "OK (需要密码) ✅"
else
    echo "FAILED ❌"
    echo "  解决方法: 联系系统管理员授予 sudo 权限"
fi

echo ""
echo "=========================================="
```

将上述脚本保存为 `check_permissions.sh`，然后执行：

```bash
bash check_permissions.sh
```

---

## 快速部署

如果您已经配置好用户权限，可以使用以下命令快速部署：

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd HL-OS

# 2. 配置 API 密钥（编辑 .env 文件）
cp .env.example .env
nano .env  # 填入您的 API 密钥

# 3. 一键部署
make dev
# 执行过程中会提示输入 sudo 密码，这是正常的

# 4. 检查服务状态
docker-compose ps

# 5. 访问服务
# 前端: http://your-server-ip:8501
# API文档: http://your-server-ip:8000/docs
```

---

## 详细部署步骤

### 步骤 1: 安装 Docker 和 Docker Compose

**Ubuntu/Debian 系统：**

```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

**CentOS/RHEL 系统：**

```bash
# 安装必要的包
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 步骤 2: 克隆项目

```bash
# 选择合适的目录
cd /opt  # 或 /home/your_user/projects

# 克隆项目
git clone <your-repo-url>
cd HL-OS

# 查看项目结构
ls -la
```

### 步骤 3: 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用 vim

# 必须配置以下内容：
# 1. GOOGLE_AI_STUDIO_API_KEY=<your-gemini-api-key>
# 2. ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN（代理方式）
#    或 ANTHROPIC_API_KEY（官方 API）
```

**示例配置：**

```bash
# Gemini API
GOOGLE_AI_STUDIO_API_KEY=AIzaSyBoew3ufZKE23UGdxHuM-g2iI_3RJweZnk

# Claude API（代理方式）
ANTHROPIC_BASE_URL=https://crs.yidang.net/api
ANTHROPIC_AUTH_TOKEN=sk-z-3e74ba887b9b474e809af041f2bff179872f75630869e2f3faa266aee3146dfa

# 或使用官方 API
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 步骤 4: 初始化并部署

```bash
# 方式 A: 使用 make 命令（推荐）
make dev
# 会提示输入 sudo 密码来设置 AnythingLLM 目录权限

# 方式 B: 使用 docker-compose 命令
make setup  # 初始化目录和权限
docker-compose build
docker-compose up -d
```

### 步骤 5: 等待服务启动

```bash
# 查看所有服务状态
docker-compose ps

# 查看启动日志
docker-compose logs -f

# 等待直到看到类似以下日志：
# hlos-backend    | INFO:     Uvicorn running on http://0.0.0.0:8000
# hlos-frontend   | You can now view your Streamlit app in your browser.
# hlos-anythingllm| [server] info: Server listening on port 3001
```

---

## 验证部署

### 检查服务健康状态

```bash
# 1. 检查所有容器是否运行
docker-compose ps

# 期望输出：所有服务状态为 "running" 或 "running (healthy)"

# 2. 测试 Backend API
curl http://localhost:8000/api/v1/health

# 期望输出：{"status":"healthy","api_version":"v1"}

# 3. 测试 AnythingLLM
curl http://localhost:3001/api/v1/system/status

# 4. 访问前端
# 在浏览器中打开: http://your-server-ip:8501
```

### 查看详细日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs anythingllm
docker-compose logs redis

# 实时跟踪日志
docker-compose logs -f backend
```

---

## 常见问题

### 问题 1: Permission denied 错误

**现象**：
```
docker: Got permission denied while trying to connect to the Docker daemon socket
```

**解决方案**：
```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录
exit
# 重新 SSH 登录
```

### 问题 2: AnythingLLM 启动失败

**现象**：
```
unable to open database file: ../storage/anythingllm.db
```

**解决方案**：
```bash
# 手动设置权限
sudo chown -R 1000:1000 anythingllm_data
chmod -R 755 anythingllm_data

# 重启服务
docker-compose restart anythingllm
```

### 问题 3: 端口被占用

**现象**：
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方案**：
```bash
# 检查端口占用
sudo netstat -tulpn | grep :8000

# 停止占用端口的进程或修改 docker-compose.yml 中的端口映射
```

### 问题 4: Docker 服务未启动

**解决方案**：
```bash
# 启动 Docker 服务
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker
```

---

## 更多帮助

- **部署故障排查**: 参见 [部署故障排查指南](../DEPLOYMENT_TROUBLESHOOTING.md)
- **API 配置**: 参见 [API 配置指南](API_CONFIGURATION.md)
- **开发指南**: 参见 [开发文档](DEVELOPMENT.md)

---

## 生产环境建议

### 安全加固

1. **使用专用的非 root 用户**
2. **配置防火墙规则**，只开放必要端口
3. **使用 HTTPS**（通过 Nginx 反向代理）
4. **定期更新 Docker 镜像**
5. **配置日志轮转**，防止磁盘空间耗尽
6. **定期备份数据**（Obsidian 知识库和 AnythingLLM 数据）

### 性能优化

1. 增加系统资源（CPU、内存）
2. 使用 SSD 存储
3. 配置 Redis 持久化策略
4. 监控容器资源使用情况

### 监控和告警

```bash
# 安装监控工具
docker run -d \
  --name=cadvisor \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --publish=8080:8080 \
  google/cadvisor:latest
```
