# Nginx 反向代理快速开始

一页纸快速配置指南 - 5 分钟完成 Nginx 配置。

---

## 前提条件

- ✅ HL-OS 服务已部署并运行（`make dev` 已执行）
- ✅ 有可用的域名（或使用服务器 IP）
- ✅ 具有 root/sudo 权限

---

## 快速配置（3 步完成）

### 开发/测试环境（HTTP）

```bash
# 1. 进入项目目录
cd /path/to/HL-OS

# 2. 运行配置脚本
sudo bash scripts/setup_nginx.sh your-domain.com

# 3. 访问服务
# http://your-domain.com
```

**完成！** 🎉

---

### 生产环境（HTTPS）

```bash
# 1. 进入项目目录
cd /path/to/HL-OS

# 2. 配置 Nginx 和 SSL
sudo bash scripts/setup_nginx.sh your-domain.com yes
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 3. 访问服务
# https://your-domain.com
```

**完成！** 🎉

---

## 配置后访问地址

| 服务 | 原始地址 | Nginx 代理后 |
|------|----------|--------------|
| **前端** | http://localhost:8501 | http://your-domain.com |
| **API 文档** | http://localhost:8000/docs | http://your-domain.com/docs |
| **API 接口** | http://localhost:8000/api/* | http://your-domain.com/api/* |
| **健康检查** | http://localhost:8000/api/v1/health | http://your-domain.com/health |

---

## 验证配置

```bash
# 1. 检查 Nginx 状态
sudo systemctl status nginx

# 2. 测试健康检查
curl http://your-domain.com/health

# 3. 访问前端
# 浏览器打开: http://your-domain.com

# 4. 查看日志
sudo tail -f /var/log/nginx/hlos_access.log
```

---

## 常用命令

```bash
# 重载配置（修改配置后）
sudo nginx -t && sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 查看错误日志
sudo tail -f /var/log/nginx/hlos_error.log

# 查看访问日志
sudo tail -f /var/log/nginx/hlos_access.log
```

---

## 防火墙配置

### Ubuntu (UFW)
```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### CentOS (firewalld)
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 故障排查

### 问题 1: 502 Bad Gateway

**原因**: HL-OS 服务未运行

**解决方案**:
```bash
cd /path/to/HL-OS
docker-compose ps
docker-compose up -d
```

---

### 问题 2: Nginx 配置测试失败

**解决方案**:
```bash
# 查看详细错误
sudo nginx -t

# 检查配置文件
sudo cat /etc/nginx/sites-available/hlos
```

---

### 问题 3: SSL 证书获取失败

**原因**: 域名未正确解析或防火墙阻止

**解决方案**:
```bash
# 检查域名解析
nslookup your-domain.com

# 检查 80 端口是否开放
sudo netstat -tlnp | grep :80

# 手动获取证书
sudo certbot certonly --standalone -d your-domain.com
```

---

### 问题 4: WebSocket 连接失败（前端无法加载）

**原因**: 缺少 WebSocket 配置

**解决方案**: 确保配置文件包含以下内容
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_buffering off;
```

---

## 高级配置

需要更多配置？参考：

- **[完整 Nginx 配置指南](NGINX_CONFIGURATION.md)** - 详细的配置说明和优化
- **[部署指南](DEPLOYMENT.md)** - 生产环境部署最佳实践
- **[故障排查](../DEPLOYMENT_TROUBLESHOOTING.md)** - 常见问题解决方案

---

## 安全建议

### 最小配置（10 秒）

```bash
# 1. 限制 AnythingLLM 访问（编辑配置文件）
sudo nano /etc/nginx/sites-available/hlos

# 2. 在 location /anythingllm/ 块中添加：
# allow 192.168.1.0/24;  # 允许内网
# deny all;               # 拒绝其他

# 3. 重载配置
sudo nginx -t && sudo systemctl reload nginx
```

### 推荐配置

- ✅ 使用 HTTPS (SSL/TLS)
- ✅ 配置防火墙只开放 80/443 端口
- ✅ 限制 AnythingLLM 管理界面访问
- ✅ 配置速率限制（防止 API 滥用）
- ✅ 定期更新 SSL 证书（Certbot 自动续期）

---

## 性能优化

### 快速优化（可选）

编辑 `/etc/nginx/nginx.conf`，在 `http` 块中添加：

```nginx
# Gzip 压缩
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;

# 连接优化
keepalive_timeout 65;
keepalive_requests 100;
```

重载配置：
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 监控访问日志

### 实时查看访问

```bash
# 查看所有访问
sudo tail -f /var/log/nginx/hlos_access.log

# 仅查看 API 调用
sudo tail -f /var/log/nginx/hlos_access.log | grep '/api/'

# 仅查看错误
sudo tail -f /var/log/nginx/hlos_error.log
```

### 分析访问统计

```bash
# 安装 GoAccess（Web 日志分析）
sudo apt install goaccess -y

# 生成报告
sudo goaccess /var/log/nginx/hlos_access.log -o /var/www/html/report.html --log-format=COMBINED

# 访问报告: http://your-domain.com/report.html
```

---

## 下一步

- [ ] 配置 SSL 证书自动续期
- [ ] 设置日志轮转
- [ ] 配置监控告警
- [ ] 优化缓存策略
- [ ] 配置 CDN（可选）

---

**需要帮助？**

- 📖 [完整配置文档](NGINX_CONFIGURATION.md)
- 🔧 [故障排查指南](../DEPLOYMENT_TROUBLESHOOTING.md)
- 💬 提交 Issue
