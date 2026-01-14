# 部署故障排查指南

本文档记录 HL-OS 部署过程中常见问题及解决方案。

---

## 1. AnythingLLM 容器启动失败：无法打开数据库文件

### 问题现象

```
Error: Schema engine error:
SQLite database error
unable to open database file: ../storage/anythingllm.db
```

### 问题原因

AnythingLLM 需要写入 SQLite 数据库到挂载的 volume 目录，但：
1. `anythingllm_data` 目录不存在
2. 目录权限不正确（UID/GID 不匹配）
3. 容器以 UID=1000, GID=1000 运行，需要对应的目录权限

### 解决方案

**方案 1：使用初始化脚本（推荐）**

```bash
# 在项目根目录执行
cd /path/to/HL-OS
bash scripts/init_anythingllm.sh
```

**方案 2：手动创建目录**

```bash
# 在项目根目录执行
cd /path/to/HL-OS

# 创建目录结构
mkdir -p anythingllm_data/storage
mkdir -p anythingllm_data/documents
mkdir -p anythingllm_data/vector-cache

# 设置权限（UID=1000, GID=1000）
sudo chown -R 1000:1000 anythingllm_data
chmod -R 755 anythingllm_data

# 启动服务
docker-compose up -d anythingllm
```

**方案 3：让 Docker 自动创建（可能有权限问题）**

如果不想手动创建目录，可以修改 `docker-compose.yml` 中 AnythingLLM 的配置：

```yaml
anythingllm:
  image: mintplexlabs/anythingllm:latest
  user: "1000:1000"  # 添加这一行，显式指定用户
  volumes:
    - ./anythingllm_data/storage:/app/server/storage
    - ./anythingllm_data/documents:/app/collector/hotdir
    - ./anythingllm_data/vector-cache:/app/server/storage/vector-cache
```

但建议使用方案 1 或方案 2，提前创建目录并设置权限。

### 验证修复

```bash
# 检查目录权限
ls -la anythingllm_data/

# 应该看到类似输出：
# drwxr-xr-x 5 1000 1000   58 Jan 14 20:19 .
# drwxr-xr-x 2 1000 1000    6 Jan 14 20:19 documents
# drwxr-xr-x 5 1000 1000   76 Jan 14 20:19 storage
# drwxr-xr-x 2 1000 1000    6 Jan 14 20:19 vector-cache

# 重启 AnythingLLM 容器
docker-compose restart anythingllm

# 检查日志
docker logs hlos-anythingllm --tail 50

# 应该看到类似成功启动的日志：
# [server] info: Server listening on port 3001
```

---

## 2. Backend 容器启动失败：ImportError

### 问题现象

```
ImportError: cannot import name 'XXX' from 'app.models.schemas'
```

### 问题原因

缺少必要的 Pydantic schema 类或异常类定义。

### 解决方案

确保使用最新代码，所有必需的 schema 类和异常类已添加到：
- `backend/app/models/schemas.py`
- `backend/app/core/exceptions.py`

如果仍有问题，清理缓存并重新构建：

```bash
# 清理 Python 缓存
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# 完全重建 backend
docker-compose down backend
docker rmi hl-os_backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

## 3. SECRET_KEY 未配置

### 问题现象

```
ValidationError: SECRET_KEY Field required
```

### 解决方案

确保 `.env` 文件中有有效的 `SECRET_KEY`：

```bash
# 生成安全的 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 将生成的密钥添加到 .env 文件
# SECRET_KEY=<生成的密钥>
```

---

## 4. 检查所有服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 查看特定服务日志
docker logs hlos-backend --tail 100
docker logs hlos-frontend --tail 100
docker logs hlos-anythingllm --tail 100
docker logs hlos-redis --tail 100

# 检查健康状态
curl http://localhost:8000/api/v1/health
```

---

## 5. 完整重新部署流程

如果遇到无法解决的问题，可以完全重新部署：

```bash
# 1. 停止并删除所有容器
docker-compose down

# 2. 清理数据（警告：会删除所有数据！）
# sudo rm -rf anythingllm_data obsidian_vault uploads logs

# 3. 初始化 AnythingLLM 数据目录
bash scripts/init_anythingllm.sh

# 4. 创建其他必要目录
mkdir -p obsidian_vault uploads logs

# 5. 确保 .env 配置正确
cp .env.example .env
# 编辑 .env 文件，填入正确的 API 密钥

# 6. 构建并启动所有服务
docker-compose build --no-cache
docker-compose up -d

# 7. 检查服务状态
docker-compose ps
docker-compose logs -f
```

---

## 常用调试命令

```bash
# 进入容器内部
docker exec -it hlos-backend bash
docker exec -it hlos-frontend bash
docker exec -it hlos-anythingllm bash

# 查看容器资源占用
docker stats

# 查看容器详细信息
docker inspect hlos-backend

# 查看网络连接
docker network inspect hl-os_hlos-network

# 测试容器间网络连通性
docker exec hlos-frontend ping backend
docker exec hlos-backend ping anythingllm
```

---

## 获取帮助

如果以上方案都无法解决问题：

1. 收集完整的错误日志：`docker-compose logs > debug.log`
2. 检查系统资源：`docker stats`
3. 查看系统日志：`sudo journalctl -u docker --since "1 hour ago"`
4. 提交 Issue 时附带上述信息
