#!/bin/bash
# AnythingLLM 数据目录初始化脚本
# 用于在新服务器部署时创建必要的目录结构和权限

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==== AnythingLLM 数据目录初始化 ===="
echo "项目目录: $PROJECT_DIR"

# 创建目录结构
echo "创建目录结构..."
mkdir -p "$PROJECT_DIR/anythingllm_data/storage"
mkdir -p "$PROJECT_DIR/anythingllm_data/documents"
mkdir -p "$PROJECT_DIR/anythingllm_data/vector-cache"

# 设置权限（UID=1000, GID=1000 对应 docker-compose.yml 中的配置）
echo "设置目录权限..."
sudo chown -R 1000:1000 "$PROJECT_DIR/anythingllm_data"
chmod -R 755 "$PROJECT_DIR/anythingllm_data"

# 显示结果
echo ""
echo "目录结构："
ls -la "$PROJECT_DIR/anythingllm_data/"
echo ""
echo "✅ AnythingLLM 数据目录初始化完成！"
echo ""
echo "现在可以启动服务："
echo "  cd $PROJECT_DIR"
echo "  docker-compose up -d anythingllm"
