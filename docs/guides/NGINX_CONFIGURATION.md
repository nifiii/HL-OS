# Nginx 反向代理配置指南

本文档详细说明如何使用 Nginx 作为 HL-OS 的反向代理，实现统一的入口访问。

---

## 📋 目录

- [配置概述](#配置概述)
- [前置要求](#前置要求)
- [基础配置（HTTP）](#基础配置http)
- [生产配置（HTTPS）](#生产配置https)
- [配置详解](#配置详解)
- [SSL 证书配置](#ssl-证书配置)
- [安全加固](#安全加固)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

---

## 配置概述

### 架构图

```
Internet
    ↓
Nginx (80/443)
    ↓
├─→ Frontend (Streamlit)    → http://localhost:8501
├─→ Backend (FastAPI)       → http://localhost:8000
└─→ AnythingLLM             → http://localhost:3001
```

### URL 路由规则

| 访问路径 | 转发目标 | 说明 |
|---------|---------|------|
| `/` | Frontend (8501) | 主页面和所有 Streamlit 页面 |
| `/api/*` | Backend (8000) | 后端 API 接口 |
| `/docs` | Backend (8000) | API 文档 (Swagger UI) |
| `/redoc` | Backend (8000) | API 文档 (ReDoc) |
| `/anythingllm/*` | AnythingLLM (3001) | RAG 引擎管理界面（可选） |

---

## 前置要求

### 1. 安装 Nginx

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx -y
```

**CentOS/RHEL:**
```bash
sudo yum install nginx -y
```

### 2. 检查 Nginx 状态

```bash
# 检查 Nginx 版本
nginx -v

# 检查 Nginx 状态
sudo systemctl status nginx

# 启动 Nginx
sudo systemctl start nginx

# 设置开机自启
sudo systemctl enable nginx
```

### 3. 检查防火墙

```bash
# Ubuntu (UFW)
sudo ufw allow 'Nginx Full'
sudo ufw status

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 基础配置（HTTP）

适合开发/测试环境或内网部署。

### 🚀 快速配置（推荐）

使用一键配置脚本快速部署：

```bash
# 在项目根目录执行
cd /path/to/HL-OS

# HTTP 配置
sudo bash scripts/setup_nginx.sh your-domain.com

# 查看帮助
sudo bash scripts/setup_nginx.sh --help
```

脚本会自动：
- ✅ 安装 Nginx（如果未安装）
- ✅ 创建配置文件
- ✅ 启用站点
- ✅ 测试配置
- ✅ 重载 Nginx
- ✅ 验证部署

---

### 📝 手动配置步骤

**1. 创建配置文件**

```bash
sudo nano /etc/nginx/sites-available/hlos
```

**2. 添加以下配置**

```nginx
# HL-OS Nginx 配置 - HTTP 版本
# 适用于开发/测试环境

upstream hlos_frontend {
    server localhost:8501;
    keepalive 32;
}

upstream hlos_backend {
    server localhost:8000;
    keepalive 32;
}

upstream hlos_anythingllm {
    server localhost:3001;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;  # 修改为您的域名或服务器 IP

    # 日志配置
    access_log /var/log/nginx/hlos_access.log;
    error_log /var/log/nginx/hlos_error.log;

    # 客户端上传大小限制（用于图片上传）
    client_max_body_size 20M;

    # 前端 - Streamlit (根路径)
    location / {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        # WebSocket 支持（Streamlit 必需）
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 标准反向代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_read_timeout 86400;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;

        # 禁用缓冲（实时更新）
        proxy_buffering off;
    }

    # 后端 API - FastAPI
    location /api/ {
        proxy_pass http://hlos_backend/api/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # API 超时设置
        proxy_read_timeout 300;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
    }

    # API 文档 - Swagger UI
    location /docs {
        proxy_pass http://hlos_backend/docs;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 文档 - ReDoc
    location /redoc {
        proxy_pass http://hlos_backend/redoc;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # AnythingLLM 管理界面（可选，仅管理员访问）
    location /anythingllm/ {
        proxy_pass http://hlos_anythingllm/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 可选：限制访问（需要先配置 htpasswd）
        # auth_basic "Restricted Access";
        # auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://hlos_backend/api/v1/health;
        access_log off;
    }
}
```

**3. 启用配置**

```bash
# 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/hlos /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

**4. 验证配置**

```bash
# 访问前端
curl http://your-domain.com

# 访问 API
curl http://your-domain.com/api/v1/health

# 访问 API 文档
# 浏览器打开: http://your-domain.com/docs
```

---

## 生产配置（HTTPS）

推荐用于生产环境，提供 SSL/TLS 加密。

### 🚀 快速配置（推荐）

使用一键配置脚本快速部署 HTTPS：

```bash
# 在项目根目录执行
cd /path/to/HL-OS

# 1. 配置 HTTPS（会生成配置但证书路径需要后续填充）
sudo bash scripts/setup_nginx.sh your-domain.com yes

# 2. 使用 Certbot 自动配置 SSL 证书
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 完成！访问 https://your-domain.com
```

---

### 📝 手动配置步骤

**1. 获取 SSL 证书**

使用 Let's Encrypt 免费证书（推荐）：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 自动配置 SSL
sudo certbot --nginx -d your-domain.com

# 或手动获取证书
sudo certbot certonly --nginx -d your-domain.com
```

**2. 创建 HTTPS 配置文件**

```bash
sudo nano /etc/nginx/sites-available/hlos-ssl
```

**3. 添加以下配置**

```nginx
# HL-OS Nginx 配置 - HTTPS 版本（生产环境推荐）

upstream hlos_frontend {
    server localhost:8501;
    keepalive 64;
}

upstream hlos_backend {
    server localhost:8000;
    keepalive 64;
}

upstream hlos_anythingllm {
    server localhost:3001;
    keepalive 32;
}

# HTTP 自动跳转到 HTTPS
server {
    listen 80;
    server_name your-domain.com;  # 修改为您的域名

    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 其他所有请求重定向到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 修改为您的域名

    # SSL 证书配置（Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 优化配置
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # 现代化 SSL 协议和加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # HSTS (可选，启用后强制 HTTPS)
    # add_header Strict-Transport-Security "max-age=63072000" always;

    # 其他安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志配置
    access_log /var/log/nginx/hlos_ssl_access.log;
    error_log /var/log/nginx/hlos_ssl_error.log;

    # 客户端上传大小限制
    client_max_body_size 20M;
    client_body_buffer_size 128k;

    # 前端 - Streamlit
    location / {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 反向代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_read_timeout 86400;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;

        # 禁用缓冲
        proxy_buffering off;
        proxy_cache off;
    }

    # 后端 API - FastAPI
    location /api/ {
        proxy_pass http://hlos_backend/api/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # API 超时设置（AI 调用可能较慢）
        proxy_read_timeout 300;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;

        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # API 文档
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://hlos_backend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # AnythingLLM 管理界面（仅限管理员）
    location /anythingllm/ {
        proxy_pass http://hlos_anythingllm/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 限制访问（推荐配置）
        # allow 192.168.1.0/24;  # 允许内网访问
        # deny all;               # 拒绝其他所有

        # 或使用密码认证
        # auth_basic "Administrator Access";
        # auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://hlos_backend/api/v1/health;
        access_log off;
    }

    # 静态文件缓存（如果有）
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg)$ {
        proxy_pass http://hlos_frontend;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

**4. 启用 HTTPS 配置**

```bash
# 禁用 HTTP 配置
sudo rm /etc/nginx/sites-enabled/hlos

# 启用 HTTPS 配置
sudo ln -s /etc/nginx/sites-available/hlos-ssl /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

**5. 设置证书自动续期**

```bash
# Certbot 自动续期
sudo certbot renew --dry-run

# 查看定时任务
sudo systemctl status certbot.timer
```

---

## 配置详解

### WebSocket 支持（重要）

Streamlit 需要 WebSocket 支持才能正常工作：

```nginx
# 必须配置这两个头
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# 禁用缓冲以支持实时更新
proxy_buffering off;
```

### 超时配置

根据不同服务调整超时时间：

```nginx
# Streamlit (长连接)
proxy_read_timeout 86400;  # 24 小时

# Backend API (AI 调用)
proxy_read_timeout 300;    # 5 分钟

# 连接超时
proxy_connect_timeout 60;  # 1 分钟
proxy_send_timeout 60;     # 1 分钟
```

### 文件上传大小

允许上传图片：

```nginx
# 允许上传最大 20MB 的文件
client_max_body_size 20M;
client_body_buffer_size 128k;
```

---

## SSL 证书配置

### 方式 1: Let's Encrypt（推荐，免费）

```bash
# 自动配置（最简单）
sudo certbot --nginx -d your-domain.com

# 手动配置
sudo certbot certonly --nginx -d your-domain.com

# 证书路径
/etc/letsencrypt/live/your-domain.com/fullchain.pem
/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 方式 2: 自签名证书（仅测试）

```bash
# 生成自签名证书
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/hlos.key \
    -out /etc/nginx/ssl/hlos.crt

# 在 Nginx 配置中使用
ssl_certificate /etc/nginx/ssl/hlos.crt;
ssl_certificate_key /etc/nginx/ssl/hlos.key;
```

### 方式 3: 商业证书

```nginx
# 配置商业证书
ssl_certificate /path/to/your/fullchain.crt;
ssl_certificate_key /path/to/your/private.key;
```

---

## 安全加固

### 1. 启用基本认证（保护 AnythingLLM）

```bash
# 创建密码文件
sudo apt install apache2-utils -y
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 在 location 块中启用
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

### 2. IP 白名单

```nginx
# 限制 AnythingLLM 访问
location /anythingllm/ {
    # 仅允许内网访问
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;

    proxy_pass http://hlos_anythingllm/;
    # ... 其他配置
}
```

### 3. 速率限制

```nginx
# 在 http 块中定义
http {
    # 限制 API 调用频率
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        # 应用速率限制
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://hlos_backend/api/;
        }
    }
}
```

### 4. 安全头配置

```nginx
# 防止点击劫持
add_header X-Frame-Options "SAMEORIGIN" always;

# 防止 MIME 类型嗅探
add_header X-Content-Type-Options "nosniff" always;

# XSS 保护
add_header X-XSS-Protection "1; mode=block" always;

# 推荐内容安全策略（根据需要调整）
add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data: https:;" always;
```

---

## 性能优化

### 1. 启用 Gzip 压缩

```nginx
# 在 http 块中配置
http {
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;
    gzip_disable "msie6";
}
```

### 2. 启用缓存

```nginx
# 静态文件缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2)$ {
    expires 7d;
    add_header Cache-Control "public, immutable";
}

# API 响应缓存（谨慎使用）
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/v1/some-cacheable-endpoint {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

### 3. 连接池优化

```nginx
upstream hlos_backend {
    server localhost:8000;
    keepalive 64;              # 保持 64 个空闲连接
    keepalive_timeout 60s;     # 空闲连接超时
    keepalive_requests 100;    # 每个连接最大请求数
}
```

---

## 故障排查

### 1. 检查配置语法

```bash
sudo nginx -t
```

### 2. 查看错误日志

```bash
# 实时查看错误日志
sudo tail -f /var/log/nginx/hlos_error.log

# 查看访问日志
sudo tail -f /var/log/nginx/hlos_access.log
```

### 3. 测试反向代理

```bash
# 测试前端
curl -I http://your-domain.com

# 测试 API
curl http://your-domain.com/api/v1/health

# 测试 HTTPS
curl -k https://your-domain.com/health
```

### 4. 常见问题

**问题 1: 502 Bad Gateway**

```bash
# 检查后端服务是否运行
docker-compose ps

# 检查端口是否监听
netstat -tlnp | grep -E '8000|8501|3001'

# 检查 SELinux（CentOS）
sudo setsebool -P httpd_can_network_connect 1
```

**问题 2: WebSocket 连接失败**

确保配置了以下头：
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_buffering off;
```

**问题 3: 上传文件失败**

检查文件大小限制：
```nginx
client_max_body_size 20M;
```

**问题 4: SSL 证书错误**

```bash
# 检查证书有效期
sudo certbot certificates

# 手动续期
sudo certbot renew

# 测试自动续期
sudo certbot renew --dry-run
```

---

## 完整配置示例

### 快速部署脚本

保存为 `setup_nginx.sh`：

```bash
#!/bin/bash
# HL-OS Nginx 快速配置脚本

DOMAIN="your-domain.com"  # 修改为您的域名

echo "=== HL-OS Nginx 配置脚本 ==="

# 1. 安装 Nginx
if ! command -v nginx &> /dev/null; then
    echo "安装 Nginx..."
    sudo apt update
    sudo apt install nginx -y
fi

# 2. 创建配置文件
echo "创建 Nginx 配置..."
sudo tee /etc/nginx/sites-available/hlos > /dev/null <<'EOF'
# 粘贴上面的完整配置内容
EOF

# 3. 启用站点
sudo ln -sf /etc/nginx/sites-available/hlos /etc/nginx/sites-enabled/

# 4. 测试配置
echo "测试 Nginx 配置..."
sudo nginx -t

# 5. 重载 Nginx
if [ $? -eq 0 ]; then
    echo "重载 Nginx..."
    sudo systemctl reload nginx
    echo "✓ Nginx 配置完成！"
    echo "访问地址: http://$DOMAIN"
else
    echo "✗ 配置文件有误，请检查"
    exit 1
fi
```

---

## 监控和维护

### 日志轮转

```bash
# 配置日志轮转
sudo nano /etc/logrotate.d/hlos-nginx
```

```
/var/log/nginx/hlos*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 性能监控

```bash
# 查看 Nginx 状态
sudo systemctl status nginx

# 查看活动连接
ss -antp | grep :80
ss -antp | grep :443

# 查看资源使用
top -p $(pgrep nginx | tr '\n' ',')
```

---

## 总结

使用 Nginx 作为反向代理的优势：

✅ **统一入口** - 所有服务通过一个域名访问
✅ **SSL/TLS 加密** - 保护数据传输安全
✅ **负载均衡** - 支持水平扩展
✅ **静态文件优化** - 提升性能
✅ **访问控制** - IP 限制、认证保护
✅ **日志管理** - 集中式日志收集

推荐配置组合：
- **开发/测试**: 基础 HTTP 配置
- **生产环境**: HTTPS + 安全加固 + 性能优化

---

**下一步**：
- 配置 SSL 证书自动续期
- 设置监控告警
- 配置日志分析（如 GoAccess、ELK）
- 考虑 CDN 加速（如 Cloudflare）
