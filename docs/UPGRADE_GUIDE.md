# HL-OS 升级指南

本文档说明如何从旧版本升级到最新版本，以及重要的配置更新。

---

## 2026-01-15 更新 - Streamlit 1.40.2 & Nginx 性能优化

### 📋 更新摘要

本次更新包含两个重要改进：

1. **Streamlit 版本升级**: 1.29.0 → 1.40.2（修复 `page_link` API 错误）
2. **Nginx 性能优化**: 添加 Gzip 压缩和静态资源缓存（速度提升 75-95%）

---

## 🚀 升级步骤

### 步骤 1: 更新代码

```bash
cd /path/to/HL-OS
git pull origin master
```

### 步骤 2: 检查 Streamlit 版本要求

确认 `frontend/requirements.txt` 中的 Streamlit 版本：

```bash
cat frontend/requirements.txt | grep streamlit
# 应该显示: streamlit==1.40.2
```

如果不是 1.40.2，请手动更新：

```bash
echo "streamlit==1.40.2" > frontend/requirements.txt
```

### 步骤 3: 重新构建 Frontend 容器

**重要**: 必须使用 `--no-cache` 确保安装新版本

```bash
# 停止 frontend 容器
docker-compose stop frontend

# 无缓存重新构建
docker-compose build --no-cache frontend

# 强制重新创建所有容器
docker-compose down
docker-compose up -d
```

### 步骤 4: 验证 Streamlit 版本

```bash
# 检查运行中的容器版本
docker exec hlos-frontend pip show streamlit | grep Version

# 应该显示: Version: 1.40.2
```

### 步骤 5: 检查前端日志

```bash
docker logs hlos-frontend

# 应该看到:
#   You can now view your Streamlit app in your browser.
#   URL: http://0.0.0.0:8501
#
# 不应该看到任何 AttributeError
```

---

## ⚡ Nginx 性能优化（可选但强烈推荐）

### 为什么需要优化？

未优化前：
- 主 JS 文件: 4.2 MB（未压缩）
- 每次访问都重新下载所有资源
- 存在字体预加载警告

优化后：
- 主 JS 文件: 1.0 MB（Gzip 压缩，压缩率 77%）
- 静态资源缓存 7 天，字体缓存 365 天
- 首次加载提升 75%，再次访问提升 95%+

### 优化步骤

#### 1. 备份当前配置

```bash
sudo cp /etc/nginx/conf.d/your-domain.conf /etc/nginx/conf.d/your-domain.conf.backup
```

#### 2. 应用性能优化配置

在 Nginx 配置文件的 `server` 块中添加以下内容：

**位置**: `/etc/nginx/conf.d/your-domain.conf` 或 `/etc/nginx/sites-available/your-domain`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # ==================== Gzip 压缩配置 ====================
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;
    gzip_min_length 256;

    # ==================== 静态资源缓存配置 ====================
    # ⚠️ 重要：这些 location 块必须放在 location / 之前

    # Streamlit 静态文件缓存
    location ~* ^/static/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        add_header Cache-Control "public, max-age=604800, immutable";
        expires 7d;
        access_log off;
    }

    # 字体文件特殊缓存
    location ~* \.(woff|woff2|ttf|eot)$ {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        add_header Cache-Control "public, max-age=31536000, immutable";
        add_header Access-Control-Allow-Origin "*";
        expires 365d;
        access_log off;
    }

    # 前端 - Streamlit (根路径)
    location / {
        proxy_pass http://hlos_frontend;
        # ... 其他配置保持不变 ...
    }

    # ... 其他 location 配置 ...
}
```

**完整配置示例**: 参考 [docs/guides/NGINX_CONFIGURATION.md#完整的性能优化配置示例](../guides/NGINX_CONFIGURATION.md#3-完整的性能优化配置示例)

#### 3. 测试并应用配置

```bash
# 测试配置语法
sudo nginx -t

# 如果显示 "syntax is ok" 和 "test is successful"，重载配置
sudo nginx -s reload
```

#### 4. 验证优化效果

```bash
# 测试 Gzip 压缩
curl -I -H "Accept-Encoding: gzip" http://your-domain.com/ | grep -i "content-encoding"
# 应该看到: Content-Encoding: gzip

# 测试静态文件缓存
curl -I http://your-domain.com/static/js/main.xxx.js | grep -i "cache-control"
# 应该看到: Cache-Control: public, max-age=604800, immutable

# 查看压缩效果
echo "压缩前大小:"
curl -s http://your-domain.com/static/js/main.xxx.js 2>/dev/null | wc -c
echo "压缩后大小:"
curl -s -H "Accept-Encoding: gzip" http://your-domain.com/static/js/main.xxx.js 2>/dev/null | wc -c
```

---

## 🔍 验证更新成功

### 1. 检查 Streamlit 版本

```bash
docker exec hlos-frontend pip show streamlit | grep Version
# 期望输出: Version: 1.40.2
```

### 2. 检查前端无错误

```bash
docker logs hlos-frontend --tail 50
# 不应该看到任何 AttributeError
```

### 3. 访问前端页面

访问 http://your-domain.com，确认：
- ✅ 页面正常加载
- ✅ 导航菜单正常显示（使用 `st.page_link`）
- ✅ 无 JavaScript 错误（F12 打开开发者工具检查）

### 4. 检查性能优化

访问 http://your-domain.com，打开浏览器开发者工具（F12）：

**Network 标签**:
- 查看 `main.xxx.js` 文件大小应该约为 1.0 MB（而非 4.2 MB）
- Response Headers 应该包含 `Content-Encoding: gzip`
- 静态资源的 Response Headers 应该包含 `Cache-Control: public, max-age=604800, immutable`

**Console 标签**:
- 不应该有字体预加载警告
- 不应该有 `st.page_link` 相关错误

---

## 🎯 用户操作建议

### 清除浏览器缓存

更新后首次访问，建议用户清除浏览器缓存以获得最佳体验：

**Chrome/Edge**:
1. 按 F12 打开开发者工具
2. 右键点击刷新按钮
3. 选择「清空缓存并硬性重新加载」

**Firefox**:
1. 按 Ctrl+F5（Windows）或 Cmd+Shift+R（Mac）

**或者**:
- 按 Ctrl+Shift+Delete（Windows）或 Cmd+Shift+Delete（Mac）
- 选择「缓存的图片和文件」
- 点击「清除数据」

---

## ❌ 常见问题

### Q1: 升级后前端仍然报错 `AttributeError: page_link`

**原因**: Docker 使用了旧镜像

**解决方案**:
```bash
# 删除旧容器和镜像
docker-compose down
docker rmi hl-os_frontend

# 无缓存重新构建
docker-compose build --no-cache frontend
docker-compose up -d

# 验证版本
docker exec hlos-frontend pip show streamlit | grep Version
```

### Q2: Nginx 配置后仍然没有压缩

**原因**: 可能是配置位置不对或语法错误

**解决方案**:
```bash
# 检查配置语法
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 确认 Gzip 配置在 server 块中，不是 http 块
```

### Q3: 静态资源缓存不生效

**原因**: location 规则顺序错误

**解决方案**:
- 确保静态资源的 `location ~*` 规则放在 `location /` **之前**
- Nginx 按顺序匹配，更具体的规则要放在前面

### Q4: 浏览器缓存了旧版本

**原因**: 浏览器使用了旧的缓存资源

**解决方案**:
```bash
# 强制清除缓存并重新加载
# Chrome/Edge: Ctrl+Shift+R 或 F12 → 右键刷新按钮 → 清空缓存并硬性重新加载
# Firefox: Ctrl+F5
```

---

## 📚 参考文档

- [Nginx 完整配置指南](../guides/NGINX_CONFIGURATION.md)
- [性能优化详细说明](../guides/NGINX_CONFIGURATION.md#性能优化)
- [故障排查指南](../guides/DEPLOYMENT_TROUBLESHOOTING.md)
- [变更日志](../../CHANGELOG.md)

---

## 🔄 回滚步骤

如果升级后出现问题，可以回滚到之前的版本：

### 回滚 Streamlit 版本

```bash
# 1. 修改 requirements.txt
echo "streamlit==1.29.0" > frontend/requirements.txt

# 2. 重新构建
docker-compose build --no-cache frontend
docker-compose up -d
```

### 回滚 Nginx 配置

```bash
# 恢复备份的配置
sudo cp /etc/nginx/conf.d/your-domain.conf.backup /etc/nginx/conf.d/your-domain.conf

# 测试并重载
sudo nginx -t
sudo nginx -s reload
```

---

## 💬 获取帮助

如果在升级过程中遇到问题：

1. 查看 [故障排查文档](../guides/DEPLOYMENT_TROUBLESHOOTING.md)
2. 查看 [变更日志](../../CHANGELOG.md) 了解详细变更
3. 提交 GitHub Issue 并附上：
   - 错误日志（`docker logs hlos-frontend`）
   - Nginx 错误日志（`sudo tail -f /var/log/nginx/error.log`）
   - 系统信息（操作系统、Docker 版本等）

---

**最后更新**: 2026-01-15
