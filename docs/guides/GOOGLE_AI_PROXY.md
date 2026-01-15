# Google AI API 代理配置指南

本文档说明如何通过日本服务器的 Nginx 代理访问 Google Gemini API，解决中国大陆访问限制问题。

---

## 📋 架构说明

```
中国大陆用户
    ↓
HL-OS 服务器（主服务器）
    ↓ HTTPS 请求
日本服务器 Nginx 代理
    ↓ HTTPS 请求
Google AI API (generativelanguage.googleapis.com)
```

**目标**: 通过日本服务器作为中间代理，转发 Google AI API 请求。

---

## 🚀 步骤 1: 配置日本服务器 Nginx

### 1.1 创建代理配置文件

在**日本服务器**上执行：

```bash
sudo nano /etc/nginx/conf.d/google-ai-proxy.conf
```

### 1.2 添加以下配置

```nginx
# Google AI API 代理配置
upstream google_ai_api {
    server generativelanguage.googleapis.com:443;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;

    # 如果有域名，建议配置域名；否则使用 IP
    server_name japan-proxy.example.com;  # 替换为您的域名或注释掉此行

    # 日志配置
    access_log /var/log/nginx/google_ai_proxy_access.log;
    error_log /var/log/nginx/google_ai_proxy_error.log;

    # ==================== 安全配置 ====================
    # 只允许您的 HL-OS 服务器 IP 访问（强烈推荐）
    # 替换为您 HL-OS 服务器的公网 IP
    allow YOUR_HLOS_SERVER_PUBLIC_IP;
    deny all;

    # ==================== 代理配置 ====================
    location / {
        # 代理到 Google AI API
        proxy_pass https://google_ai_api;

        # SSL 配置
        proxy_ssl_server_name on;
        proxy_ssl_name generativelanguage.googleapis.com;
        proxy_ssl_protocols TLSv1.2 TLSv1.3;
        proxy_ssl_verify off;  # 如果遇到 SSL 验证问题可以关闭

        # HTTP 版本
        proxy_http_version 1.1;

        # 必需的请求头
        proxy_set_header Host generativelanguage.googleapis.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # 超时设置（AI 请求可能较长）
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;

        # 支持大请求体（图片 OCR）
        client_max_body_size 20M;
    }

    # 健康检查端点（可选）
    location /health {
        access_log off;
        return 200 "Proxy OK\n";
        add_header Content-Type text/plain;
    }
}
```

### 1.3 测试并应用配置

```bash
# 测试 Nginx 配置语法
sudo nginx -t

# 如果测试通过，重载 Nginx
sudo nginx -s reload

# 验证 Nginx 运行状态
sudo systemctl status nginx
```

### 1.4 验证代理工作

在**日本服务器**上测试（需要从 HL-OS 服务器测试，因为有 IP 限制）：

```bash
# 从 HL-OS 服务器执行
curl -I http://YOUR_JAPAN_SERVER_IP/health
# 应该返回: 200 OK

# 测试代理到 Google AI
curl -I http://YOUR_JAPAN_SERVER_IP/v1beta/models
```

---

## 🔐 步骤 2: 安全加固（强烈推荐）

### 2.1 IP 白名单

在上面的配置中已经包含了 IP 限制。确保替换为您的 HL-OS 服务器公网 IP：

```nginx
# 获取 HL-OS 服务器公网 IP
# 在 HL-OS 服务器上执行：
curl ifconfig.me
# 或
curl ip.sb

# 将返回的 IP 填入 Nginx 配置的 allow 指令
```

### 2.2 添加基本认证（可选，额外保护层）

```bash
# 在日本服务器上安装 htpasswd 工具
sudo apt install apache2-utils -y

# 创建认证文件和用户
sudo htpasswd -c /etc/nginx/.google_ai_htpasswd gemini_proxy
# 输入密码（建议使用强密码，如：Gm3Px_2024!@#）
```

在 Nginx 配置中启用认证：

```nginx
location / {
    # 基本认证
    auth_basic "Google AI Proxy";
    auth_basic_user_file /etc/nginx/.google_ai_htpasswd;

    # ... 其他代理配置 ...
}
```

### 2.3 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow from YOUR_HLOS_SERVER_IP to any port 80
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="YOUR_HLOS_SERVER_IP" port port="80" protocol="tcp" accept'
sudo firewall-cmd --reload
```

---

## ⚙️ 步骤 3: 配置 HL-OS 服务器使用代理

### 方案 A: 使用环境变量（推荐，最简单）

在 HL-OS 服务器的 `.env` 文件中添加：

```bash
# Google AI API 代理配置
# 替换为您日本服务器的 IP 或域名
HTTPS_PROXY=http://YOUR_JAPAN_SERVER_IP:80

# 如果启用了基本认证，使用：
# HTTPS_PROXY=http://username:password@YOUR_JAPAN_SERVER_IP:80

# 可选：只代理 Google AI 请求
# NO_PROXY=localhost,127.0.0.1,anythingllm,redis
```

重启 Backend 容器：

```bash
docker-compose up -d --force-recreate backend
```

验证配置已加载：

```bash
docker exec hlos-backend printenv | grep PROXY
# 应该显示: HTTPS_PROXY=http://YOUR_JAPAN_SERVER_IP:80
```

### 方案 B: 修改代码支持自定义 Base URL（如果方案 A 不work）

**步骤 1**: 在 `.env` 添加配置

```bash
# Google AI API 代理 URL
GEMINI_PROXY_URL=http://YOUR_JAPAN_SERVER_IP
```

**步骤 2**: 更新 `backend/app/config.py`，添加：

```python
# 在 Settings 类中添加
GEMINI_PROXY_URL: Optional[str] = Field(
    default=None,
    description="Gemini API 代理 URL（如通过日本服务器代理）"
)
```

**步骤 3**: 更新 `backend/app/services/gemini_service.py`

修改初始化方法：

```python
def __init__(self):
    """初始化Gemini服务"""
    # 配置代理（如果设置了）
    if settings.GEMINI_PROXY_URL:
        import os
        os.environ['HTTPS_PROXY'] = settings.GEMINI_PROXY_URL
        logger.info(f"Using Gemini proxy: {settings.GEMINI_PROXY_URL}")

    genai.configure(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)
    self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    logger.info(f"GeminiVisionService initialized with model: {settings.GEMINI_MODEL}")
```

**步骤 4**: 重新构建并启动

```bash
docker-compose build --no-cache backend
docker-compose up -d --force-recreate backend
```

---

## ✅ 步骤 4: 验证配置

### 4.1 检查日本服务器代理状态

在日本服务器上：

```bash
# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/google_ai_proxy_access.log

# 查看错误日志
sudo tail -f /var/log/nginx/google_ai_proxy_error.log
```

### 4.2 测试 HL-OS Backend

```bash
# 在 HL-OS 服务器上查看 backend 日志
docker logs hlos-backend --tail 50 | grep -i "gemini\|proxy"

# 测试上传作业图片
# 通过前端上传一张作业图片，查看是否能成功识别
```

### 4.3 验证请求流向

**成功的标志**：

在日本服务器的 Nginx 日志中应该看到：
```
YOUR_HLOS_SERVER_IP - - [15/Jan/2026:15:30:00 +0900] "POST /v1beta/models/gemini-3-pro-preview:generateContent?key=... HTTP/1.1" 200 ...
```

在 HL-OS Backend 日志中应该看到：
```
INFO - GeminiVisionService initialized with model: gemini-3-pro-preview
INFO - Using Gemini proxy: http://YOUR_JAPAN_SERVER_IP  (如果使用方案 B)
```

---

## 🔍 故障排查

### 问题 1: 连接被拒绝 `Connection refused`

**原因**: IP 白名单配置错误或防火墙阻止

**解决方案**:
```bash
# 1. 检查 HL-OS 服务器公网 IP
curl ifconfig.me

# 2. 确认日本服务器 Nginx 配置中的 allow 指令正确
sudo nano /etc/nginx/conf.d/google-ai-proxy.conf

# 3. 检查防火墙规则
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 4. 测试从 HL-OS 到日本服务器的连接
curl -I http://YOUR_JAPAN_SERVER_IP/health
```

### 问题 2: SSL 验证失败

**错误**: `SSL certificate problem`

**解决方案**:
```nginx
# 在日本服务器 Nginx 配置中设置
proxy_ssl_verify off;
```

### 问题 3: 502 Bad Gateway

**原因**: 日本服务器无法连接到 Google AI

**解决方案**:
```bash
# 在日本服务器上测试连接 Google AI
curl -I https://generativelanguage.googleapis.com

# 检查 DNS 解析
nslookup generativelanguage.googleapis.com

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/google_ai_proxy_error.log
```

### 问题 4: 504 Gateway Timeout

**原因**: 超时设置太短

**解决方案**:
```nginx
# 增加超时时间
proxy_connect_timeout 120s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### 问题 5: HTTPS_PROXY 环境变量不生效

**原因**: Docker 容器未正确加载环境变量

**解决方案**:
```bash
# 1. 确认 .env 文件中有配置
grep HTTPS_PROXY .env

# 2. 必须使用 --force-recreate 重新创建容器
docker-compose up -d --force-recreate backend

# 3. 验证环境变量已加载
docker exec hlos-backend printenv | grep PROXY
```

---

## 📊 性能监控

### 监控代理请求

```bash
# 在日本服务器上
# 实时查看请求数
sudo tail -f /var/log/nginx/google_ai_proxy_access.log | grep -E "POST|GET"

# 统计请求数量
sudo cat /var/log/nginx/google_ai_proxy_access.log | grep "generateContent" | wc -l

# 查看响应时间（如果配置了 $request_time）
sudo cat /var/log/nginx/google_ai_proxy_access.log | awk '{print $NF}' | sort -n
```

### 添加自定义日志格式（可选）

在日本服务器 `/etc/nginx/nginx.conf` 的 `http` 块中添加：

```nginx
log_format proxy_timing '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_user_agent" '
                        'rt=$request_time uct="$upstream_connect_time" '
                        'uht="$upstream_header_time" urt="$upstream_response_time"';

# 然后在 google-ai-proxy.conf 中使用
access_log /var/log/nginx/google_ai_proxy_access.log proxy_timing;
```

---

## 🔒 安全建议

1. **必须配置 IP 白名单**: 只允许 HL-OS 服务器访问
2. **建议使用 HTTPS**: 配置 SSL 证书保护传输安全
3. **定期更新密钥**: 如使用基本认证，定期更换密码
4. **监控访问日志**: 检测异常访问模式
5. **限制请求速率**: 防止滥用

```nginx
# 添加速率限制（可选）
http {
    limit_req_zone $binary_remote_addr zone=gemini_proxy:10m rate=10r/s;
}

server {
    location / {
        limit_req zone=gemini_proxy burst=20;
        # ... 其他配置 ...
    }
}
```

---

## 📝 配置检查清单

部署前确认：

- [ ] 日本服务器 Nginx 配置正确
- [ ] IP 白名单已设置（允许 HL-OS 服务器 IP）
- [ ] 防火墙规则已配置
- [ ] HL-OS `.env` 文件已添加 HTTPS_PROXY
- [ ] Backend 容器已重新创建（`--force-recreate`）
- [ ] 环境变量已加载（`docker exec ... printenv`）
- [ ] 日志中无错误信息
- [ ] 能够成功上传并识别作业图片

---

## 🔗 相关资源

- [Google Generative AI API 文档](https://ai.google.dev/api)
- [Nginx 反向代理配置](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [HL-OS 部署指南](DEPLOYMENT.md)

---

**最后更新**: 2026-01-15
**适用版本**: HL-OS Latest
