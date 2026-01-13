# HL-OS 部署指南

本文档提供 HL-OS 系统的完整部署流程，包括开发环境和生产环境。

## 📋 目录

- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [备份与恢复](#备份与恢复)
- [故障排查](#故障排查)

---

## 快速开始

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git >= 2.30
- 至少 4GB 可用内存
- 至少 20GB 可用磁盘空间

### 5分钟部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd HL-OS

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 3. 一键启动
make dev

# 4. 访问服务
# - 前端: http://localhost:8501
# - 后端 API: http://localhost:8000
# - API 文档: http://localhost:8000/docs
```

---

## 开发环境部署

### 1. 配置环境变量

编辑 `.env` 文件：

```bash
# AI 服务 API 密钥
GOOGLE_AI_STUDIO_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# 应用配置
SECRET_KEY=your-secret-key-here  # 使用 make generate-secret 生成

# 路径配置（开发环境使用相对路径）
OBSIDIAN_VAULT_PATH=./obsidian_vault
UPLOAD_DIR=./uploads

# AnythingLLM 配置
ANYTHINGLLM_URL=http://anythingllm:3001
ANYTHINGLLM_API_KEY=  # 首次启动后自动生成
```

### 2. 生成密钥

```bash
make generate-secret
```

复制输出的密钥到 `.env` 的 `SECRET_KEY` 字段。

### 3. 启动服务

```bash
# 构建并启动所有服务
make dev

# 或者分步执行
make build  # 构建镜像
make up     # 启动服务
```

### 4. 验证部署

```bash
# 检查服务状态
make status

# 查看日志
make logs

# 测试 API 健康检查
curl http://localhost:8000/api/v1/health
```

### 5. 停止服务

```bash
make down  # 停止但保留数据
make clean # 停止并清理所有数据（谨慎使用）
```

---

## 生产环境部署

### 架构概览

```
Internet
    ↓
Nginx (443) - SSL Termination
    ↓
┌─────────────────────────────┐
│  Docker Network             │
│  ┌─────────┬─────────────┐ │
│  │ Backend │  Frontend   │ │
│  │ :8000   │  :8501      │ │
│  └────┬────┴──────┬──────┘ │
│       │           │         │
│  ┌────┴───────────┴──────┐ │
│  │ AnythingLLM   Redis   │ │
│  │ :3001         :6379   │ │
│  └──────────────────────┘ │
└─────────────────────────────┘
```

### 1. 准备 VPS

#### 系统要求

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- 4核 CPU
- 8GB RAM
- 50GB SSD
- 独立公网 IP

#### 安装 Docker

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 部署应用

```bash
# 克隆项目到服务器
cd /opt
sudo git clone <repository-url> HL-OS
cd HL-OS

# 配置环境变量
sudo cp .env.example .env
sudo vim .env  # 填入生产环境 API 密钥
```

### 3. 配置 SSL 证书

#### 方式一：Let's Encrypt（推荐）

```bash
# 安装 Certbot
sudo apt-get update
sudo apt-get install certbot

# 生成证书（替换为您的域名）
sudo certbot certonly --standalone -d hlos.example.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/hlos.example.com/fullchain.pem ./docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/hlos.example.com/privkey.pem ./docker/nginx/ssl/

# 更新 docker/nginx/nginx.conf
# 取消注释 SSL 证书路径配置
```

#### 方式二：自签名证书（仅测试）

```bash
# 在 nginx 容器内生成自签名证书
docker-compose exec nginx /etc/nginx/generate-selfsigned-cert.sh
```

### 4. 更新 Nginx 配置

编辑 `docker/nginx/nginx.conf`：

```nginx
server {
    listen 443 ssl http2;
    server_name hlos.example.com;  # 替换为您的域名

    # 使用 Let's Encrypt 证书
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... 其他配置
}
```

### 5. 启动生产服务

```bash
# 构建镜像
sudo docker-compose build

# 启动服务（后台运行）
sudo docker-compose up -d

# 检查状态
sudo docker-compose ps
sudo docker-compose logs -f
```

### 6. 配置自动备份

```bash
# 添加定时任务
sudo crontab -e

# 每天凌晨 2 点备份 Obsidian
0 2 * * * /opt/HL-OS/docker/backup/backup.sh >> /var/log/hlos-backup.log 2>&1

# 每 6 小时备份 AnythingLLM
0 */6 * * * /opt/HL-OS/docker/backup/backup.sh >> /var/log/hlos-backup.log 2>&1
```

### 7. 配置防火墙

```bash
# 允许 HTTP/HTTPS 流量
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 8. 配置证书自动更新

```bash
# Let's Encrypt 证书自动更新
sudo crontab -e

# 每月 1 号凌晨 3 点更新证书
0 3 1 * * certbot renew --post-hook "docker-compose -f /opt/HL-OS/docker-compose.yml restart nginx" >> /var/log/certbot-renew.log 2>&1
```

---

## 备份与恢复

### 手动备份

```bash
# 备份 Obsidian Vault
./docker/backup/backup.sh

# 备份文件位置
# - Obsidian: ./backups/obsidian/obsidian_backup_YYYYMMDD_HHMMSS.tar.gz
# - AnythingLLM: ./backups/anythingllm/anythingllm_backup_YYYYMMDD_HHMMSS.tar.gz
```

### 恢复数据

```bash
# 恢复 Obsidian Vault
./docker/backup/restore.sh obsidian /app/backups/obsidian/obsidian_backup_20240101_120000.tar.gz

# 恢复 AnythingLLM 数据
./docker/backup/restore.sh anythingllm /app/backups/anythingllm/anythingllm_backup_20240101_120000.tar.gz

# 重启服务
docker-compose restart
```

### 云端备份（可选）

配置 `rclone` 将备份自动上传到云存储：

```bash
# 安装 rclone
curl https://rclone.org/install.sh | sudo bash

# 配置远程存储
rclone config

# 编辑 docker/backup/backup.sh 取消注释云上传部分
```

---

## 监控与维护

### 查看日志

```bash
# 所有服务日志
make logs

# 单个服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f anythingllm
```

### 健康检查

```bash
# API 健康检查
curl https://hlos.example.com/health

# 检查容器状态
docker-compose ps
```

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h
du -sh ./obsidian_vault
du -sh ./anythingllm_data
```

### 日志轮转

创建 `/etc/logrotate.d/hlos`：

```
/var/log/hlos-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
}
```

---

## 故障排查

### 后端无法启动

```bash
# 检查日志
docker-compose logs backend

# 常见问题：
# 1. API 密钥未配置 → 检查 .env 文件
# 2. 端口被占用 → 修改 docker-compose.yml 端口映射
# 3. 内存不足 → 增加服务器内存或减少并发
```

### 前端无法访问

```bash
# 检查 Streamlit 日志
docker-compose logs frontend

# 检查后端连接
docker-compose exec frontend env | grep BACKEND_URL
```

### Nginx SSL 错误

```bash
# 检查证书文件权限
ls -la ./docker/nginx/ssl/

# 重新生成自签名证书
docker-compose exec nginx /etc/nginx/generate-selfsigned-cert.sh

# 重启 Nginx
docker-compose restart nginx
```

### OCR 识别失败

```bash
# 检查 Gemini API 配置
docker-compose exec backend python -c "import os; print(os.getenv('GOOGLE_AI_STUDIO_API_KEY'))"

# 检查图片大小限制
# 最大 10MB，检查 nginx.conf 的 client_max_body_size
```

### 数据库连接失败

```bash
# 检查 Redis 状态
docker-compose ps redis

# 重启 Redis
docker-compose restart redis
```

---

## 性能优化

### 1. 增加并发

编辑 `docker-compose.yml`：

```yaml
services:
  backend:
    deploy:
      replicas: 3  # 3 个后端实例
    environment:
      - WORKERS=4  # 每个实例 4 个 worker
```

### 2. 配置 Redis 缓存

编辑 `.env`：

```bash
REDIS_MAX_MEMORY=2gb
REDIS_EVICTION_POLICY=allkeys-lru
```

### 3. 数据库分片（高级）

按孩子姓名分片存储 Obsidian Vault：

```python
# 在 obsidian_service.py 中实现
def get_shard_vault_path(child_name: str) -> Path:
    shard = hash(child_name) % NUM_SHARDS
    return Path(f"/app/obsidian_vault_shard_{shard}")
```

---

## 更新与升级

### 更新应用代码

```bash
cd /opt/HL-OS
sudo git pull origin main

# 重新构建并重启
sudo docker-compose build
sudo docker-compose up -d
```

### 更新依赖

```bash
# 更新 Python 依赖
cd backend
pip-compile requirements.in

# 重新构建镜像
docker-compose build backend
```

---

## 安全最佳实践

1. **API 密钥管理**
   - 使用环境变量存储密钥
   - 定期轮换 API 密钥
   - 使用密钥管理服务（如 AWS Secrets Manager）

2. **网络安全**
   - 启用 HTTPS（强制）
   - 配置防火墙规则
   - 使用 Fail2ban 防止暴力破解

3. **数据安全**
   - 定期备份（每日）
   - 异地备份（云存储）
   - 加密敏感数据

4. **访问控制**
   - 添加 JWT 认证（未来实现）
   - IP 白名单限制
   - Rate Limiting（已配置在 Nginx）

---

## 支持与帮助

- **文档**: 查看 `docs/` 目录
- **Issue 追踪**: GitHub Issues
- **社区讨论**: GitHub Discussions

---

**祝您部署顺利！**
