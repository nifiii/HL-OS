#!/bin/bash
# HL-OS Nginx 反向代理配置脚本
# 用于快速配置 Nginx 作为 HL-OS 的反向代理

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN="${1:-localhost}"
ENABLE_SSL="${2:-no}"
NGINX_CONF_DIR="/etc/nginx"
SITES_AVAILABLE="$NGINX_CONF_DIR/sites-available"
SITES_ENABLED="$NGINX_CONF_DIR/sites-enabled"
CONF_FILE="$SITES_AVAILABLE/hlos"

echo -e "${BLUE}=== HL-OS Nginx 配置脚本 ===${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 root 或 sudo 运行此脚本${NC}"
    echo "用法: sudo bash $0 [domain] [ssl]"
    exit 1
fi

# 使用说明
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "用法: sudo bash $0 [domain] [ssl]"
    echo ""
    echo "参数:"
    echo "  domain  - 域名或服务器 IP（默认: localhost）"
    echo "  ssl     - 是否启用 SSL (yes/no，默认: no)"
    echo ""
    echo "示例:"
    echo "  sudo bash $0                              # 使用默认配置"
    echo "  sudo bash $0 example.com                  # 配置域名"
    echo "  sudo bash $0 example.com yes              # 配置域名并启用 SSL"
    exit 0
fi

# 检查 Nginx 是否已安装
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx 未安装，正在安装...${NC}"
    apt update
    apt install nginx -y
    systemctl enable nginx
    systemctl start nginx
    echo -e "${GREEN}✓ Nginx 安装完成${NC}"
else
    echo -e "${GREEN}✓ Nginx 已安装${NC}"
fi

# 检查 HL-OS 服务是否运行
echo -e "${BLUE}检查 HL-OS 服务...${NC}"
if ! curl -s http://localhost:8501 > /dev/null; then
    echo -e "${YELLOW}警告: Frontend (8501) 似乎未运行${NC}"
fi
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${YELLOW}警告: Backend (8000) 似乎未运行${NC}"
fi
if ! curl -s http://localhost:3001 > /dev/null; then
    echo -e "${YELLOW}警告: AnythingLLM (3001) 似乎未运行${NC}"
fi

# 创建配置文件
echo -e "${BLUE}创建 Nginx 配置文件...${NC}"

if [ "$ENABLE_SSL" = "yes" ]; then
    # HTTPS 配置
    cat > "$CONF_FILE" <<EOF
# HL-OS Nginx 配置 - HTTPS 版本
# 生成时间: $(date)
# 域名: $DOMAIN

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
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL 证书配置（需要先使用 Certbot 生成证书）
    # 执行: sudo certbot --nginx -d $DOMAIN
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL 优化配置
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志配置
    access_log /var/log/nginx/hlos_ssl_access.log;
    error_log /var/log/nginx/hlos_ssl_error.log;

    # 客户端上传大小限制
    client_max_body_size 20M;

    # 前端 - Streamlit
    location / {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        # WebSocket 支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://hlos_backend/api/;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300;
    }

    # API 文档
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://hlos_backend;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://hlos_backend/api/v1/health;
        access_log off;
    }
}
EOF
else
    # HTTP 配置
    cat > "$CONF_FILE" <<EOF
# HL-OS Nginx 配置 - HTTP 版本
# 生成时间: $(date)
# 域名: $DOMAIN

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
    server_name $DOMAIN;

    # 日志配置
    access_log /var/log/nginx/hlos_access.log;
    error_log /var/log/nginx/hlos_error.log;

    # 客户端上传大小限制
    client_max_body_size 20M;

    # 前端 - Streamlit
    location / {
        proxy_pass http://hlos_frontend;
        proxy_http_version 1.1;

        # WebSocket 支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://hlos_backend/api/;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300;
    }

    # API 文档
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://hlos_backend;
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://hlos_backend/api/v1/health;
        access_log off;
    }
}
EOF
fi

echo -e "${GREEN}✓ 配置文件已创建: $CONF_FILE${NC}"

# 启用站点
echo -e "${BLUE}启用站点配置...${NC}"
if [ -f "$SITES_ENABLED/hlos" ]; then
    rm "$SITES_ENABLED/hlos"
fi
ln -s "$CONF_FILE" "$SITES_ENABLED/hlos"
echo -e "${GREEN}✓ 站点已启用${NC}"

# 测试配置
echo -e "${BLUE}测试 Nginx 配置...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ 配置文件语法正确${NC}"
else
    echo -e "${RED}✗ 配置文件有错误${NC}"
    exit 1
fi

# 重载 Nginx
echo -e "${BLUE}重载 Nginx...${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx 已重载${NC}"

echo ""
echo -e "${GREEN}=== 配置完成！===${NC}"
echo ""
echo -e "访问地址:"
if [ "$ENABLE_SSL" = "yes" ]; then
    echo -e "  前端:     ${BLUE}https://$DOMAIN${NC}"
    echo -e "  API 文档: ${BLUE}https://$DOMAIN/docs${NC}"
    echo -e "  健康检查: ${BLUE}https://$DOMAIN/health${NC}"
    echo ""
    echo -e "${YELLOW}下一步: 配置 SSL 证书${NC}"
    echo -e "执行: ${BLUE}sudo certbot --nginx -d $DOMAIN${NC}"
else
    echo -e "  前端:     ${BLUE}http://$DOMAIN${NC}"
    echo -e "  API 文档: ${BLUE}http://$DOMAIN/docs${NC}"
    echo -e "  健康检查: ${BLUE}http://$DOMAIN/health${NC}"
    echo ""
    echo -e "${YELLOW}提示: 生产环境建议启用 HTTPS${NC}"
    echo -e "重新运行: ${BLUE}sudo bash $0 $DOMAIN yes${NC}"
fi
echo ""

# 验证配置
echo -e "${BLUE}验证配置...${NC}"
sleep 2
if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health | grep -q "200"; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠ 健康检查未通过，请检查 HL-OS 服务是否运行${NC}"
fi

echo ""
echo -e "${GREEN}部署完成！${NC}"
