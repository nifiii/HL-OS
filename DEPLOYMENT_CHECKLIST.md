# HL-OS 部署检查清单

在开始部署 HL-OS 之前，请使用此检查清单确保所有前提条件已满足。

---

## 📋 部署前检查清单

### ✅ 1. 用户权限检查

- [ ] **已确认使用 root 用户** 或 **具有完整权限的普通用户**
- [ ] **已验证 Docker 权限**（能够执行 `docker ps` 命令）
- [ ] **已验证 sudo 权限**（能够执行 `sudo echo "test"` 命令）

**验证命令：**
```bash
# 检查当前用户
whoami

# 检查用户组（应包含 docker）
groups

# 测试 Docker 权限
docker ps

# 测试 sudo 权限
sudo echo "Sudo access OK"
```

---

### ✅ 2. 系统环境检查

- [ ] **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)
- [ ] **Docker 版本** >= 20.10
- [ ] **Docker Compose 版本** >= 1.29
- [ ] **可用磁盘空间** >= 10GB
- [ ] **可用内存** >= 4GB

**验证命令：**
```bash
# 检查操作系统
cat /etc/os-release

# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker-compose --version

# 检查磁盘空间
df -h .

# 检查内存
free -h
```

---

### ✅ 3. Docker 服务检查

- [ ] **Docker 服务已启动**
- [ ] **Docker 服务已设置为开机自启**
- [ ] **当前用户可以运行 Docker 命令（无需 sudo）**

**验证命令：**
```bash
# 检查 Docker 服务状态
sudo systemctl status docker

# 检查是否开机自启
sudo systemctl is-enabled docker

# 测试 Docker 命令（不使用 sudo）
docker run hello-world
```

---

### ✅ 4. 网络和端口检查

- [ ] **端口 8000 未被占用**（Backend API）
- [ ] **端口 8501 未被占用**（Frontend）
- [ ] **端口 3001 未被占用**（AnythingLLM）
- [ ] **端口 6379 未被占用**（Redis）
- [ ] **可以访问外部 API 服务**（Gemini、Claude）

**验证命令：**
```bash
# 检查端口占用
sudo netstat -tulpn | grep -E ':(8000|8501|3001|6379)'

# 如果以上命令无输出，说明端口未被占用 ✅

# 测试外部网络连接
curl -I https://generativelanguage.googleapis.com
curl -I https://api.anthropic.com
```

---

### ✅ 5. API 密钥准备

- [ ] **已获取 Gemini 3 Pro Preview API 密钥**
- [ ] **已配置 Claude Sonnet 4.5 访问方式**（代理 或 官方 API）
- [ ] **API 密钥已验证可用**（有足够的配额）

**获取 API 密钥：**
- Gemini API: https://makersuite.google.com/app/apikey
- Claude 代理配置: 参见 [API配置指南](docs/guides/API_CONFIGURATION.md)
- Claude 官方 API: https://console.anthropic.com/

---

### ✅ 6. 项目代码准备

- [ ] **已克隆项目代码**
- [ ] **已复制 `.env.example` 为 `.env`**
- [ ] **已在 `.env` 文件中填写 API 密钥**
- [ ] **已检查 `.env` 文件格式正确**

**验证命令：**
```bash
# 进入项目目录
cd /path/to/HL-OS

# 检查项目文件
ls -la

# 检查 .env 文件
cat .env | grep -E 'GOOGLE_AI_STUDIO_API_KEY|ANTHROPIC'
```

---

## 🚀 开始部署

如果以上所有检查项都已完成 ✅，可以开始部署：

### 快速部署命令

```bash
# 确保在项目根目录
cd /path/to/HL-OS

# 一键部署
make dev

# 等待所有服务启动（约 1-2 分钟）
```

### 部署过程中的预期提示

1. **创建目录和文件**
   ```
   初始化HL-OS项目...
   已创建.env文件，请填入你的API密钥
   ```

2. **设置 AnythingLLM 权限**（会要求输入 sudo 密码）
   ```
   设置AnythingLLM目录权限（需要sudo）...
   [sudo] password for user:
   ```
   👉 **这是正常的，请输入您的 sudo 密码**

3. **构建 Docker 镜像**
   ```
   构建Docker镜像...
   [+] Building 45.2s (12/12) FINISHED
   ```

4. **启动服务**
   ```
   启动HL-OS服务...
   Container hlos-redis  Running
   Container hlos-anythingllm  Running
   Container hlos-backend  Running
   Container hlos-frontend  Running
   ```

---

## ✅ 部署后验证

部署完成后，进行以下验证：

### 1. 检查容器状态

```bash
docker-compose ps
```

**预期输出：** 所有服务状态为 `running` 或 `running (healthy)`

### 2. 检查 API 健康状态

```bash
curl http://localhost:8000/api/v1/health
```

**预期输出：** `{"status":"healthy","api_version":"v1"}`

### 3. 访问前端界面

在浏览器中打开：`http://your-server-ip:8501`

**预期结果：** 能够看到 HL-OS 主页面

### 4. 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看 Backend 日志
docker-compose logs backend | tail -50

# 查看 AnythingLLM 日志
docker-compose logs anythingllm | tail -50
```

**预期日志：**
- Backend: `INFO:     Uvicorn running on http://0.0.0.0:8000`
- Frontend: `You can now view your Streamlit app in your browser`
- AnythingLLM: `[server] info: Server listening on port 3001`

---

## ❌ 部署失败？

如果部署过程中遇到问题，请参考：

1. **[部署故障排查指南](docs/DEPLOYMENT_TROUBLESHOOTING.md)** - 详细的问题诊断和解决方案
2. **[完整部署指南](docs/guides/DEPLOYMENT.md)** - 详细的部署步骤和配置说明

### 常见问题快速索引

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Permission denied` | Docker 权限不足 | `sudo usermod -aG docker $USER` 并重新登录 |
| `unable to open database file` | AnythingLLM 目录权限 | `sudo chown -R 1000:1000 anythingllm_data` |
| `port is already allocated` | 端口被占用 | 检查并停止占用端口的程序 |
| `API 调用失败` | API 密钥配置错误 | 检查 `.env` 文件中的密钥配置 |

---

## 📞 获取帮助

如果仍然遇到问题：

1. 查看日志: `docker-compose logs > debug.log`
2. 收集环境信息: `docker-compose ps` 和 `docker version`
3. 查阅文档: [docs/DEPLOYMENT_TROUBLESHOOTING.md](docs/DEPLOYMENT_TROUBLESHOOTING.md)
4. 提交 Issue（附带日志和环境信息）

---

## ✨ 部署成功！

如果所有验证通过，恭喜您成功部署 HL-OS！🎉

### 下一步

1. 阅读 [功能测试清单](TESTING_CHECKLIST.md) 进行功能测试
2. 查看 [API 参考手册](docs/api/API_REFERENCE.md) 了解 API 使用方法
3. 访问前端界面开始使用系统

---

**最后更新**: 2026-01-14
