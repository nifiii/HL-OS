# HL-OS 快速开始指南

## 🚀 5分钟快速启动

### 步骤1: 克隆项目（如果还没有）

```bash
cd /home/opadm/repo/HL-OS
```

### 步骤2: 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用你喜欢的编辑器
```

**必须配置的API密钥:**

```bash
# 在.env文件中填入：
GOOGLE_AI_STUDIO_API_KEY=你的Google-AI-Studio-API密钥
ANTHROPIC_API_KEY=你的Anthropic-API密钥
```

**如何获取API密钥:**

- **Google AI Studio**: https://makersuite.google.com/app/apikey
- **Anthropic Claude**: https://console.anthropic.com/

### 步骤3: 一键启动

```bash
make dev
```

这个命令会自动：
- ✅ 创建必要的目录
- ✅ 构建Docker镜像
- ✅ 启动所有服务

### 步骤4: 访问系统

等待约1-2分钟让服务完全启动，然后访问：

- **🖥️ 家长控制面板**: http://localhost:8501
- **📖 API文档**: http://localhost:8000/docs
- **🤖 AnythingLLM**: http://localhost:3001

## 📋 常用命令速查

```bash
make help          # 查看所有可用命令
make up            # 启动服务
make down          # 停止服务
make restart       # 重启服务
make logs          # 查看所有日志
make logs-backend  # 仅查看后端日志
make logs-frontend # 仅查看前端日志
make ps            # 查看服务状态
make backup        # 备份Obsidian知识库
make clean         # 清理临时文件
```

## 🎯 第一次使用

### 1. 上传第一张作业图片

1. 访问 http://localhost:8501
2. 点击"开始校验"或侧边栏的"📸 作业校验"
3. 选择孩子姓名和学科
4. 上传作业图片
5. 点击"开始识别"
6. 等待AI识别完成
7. 在"✏️ 校验内容"标签中检查并修正识别结果
8. 点击"确认并保存"

### 2. 查看存储的内容

```bash
# 查看Obsidian vault目录
ls -la obsidian_vault/

# 查看某个孩子的作业
ls -la obsidian_vault/张三/数学/No_Problems/
```

### 3. 生成教学课件

1. 点击侧边栏的"📚 内容生成"
2. 选择知识点
3. 设置难度和风格
4. 点击"生成内容"
5. 预览课件
6. 确认并推送

## 🔧 故障排除

### 问题: 服务无法启动

**解决:**

```bash
# 检查Docker状态
docker ps

# 查看详细日志
make logs

# 重新构建并启动
make clean
make build
make up
```

### 问题: API密钥错误

**解决:**

1. 确认`.env`文件中的API密钥正确
2. 重启服务使配置生效:
   ```bash
   make restart
   ```

### 问题: 端口冲突

**解决:**

如果8000、8501或3001端口被占用：

1. 修改`docker-compose.yml`中的端口映射
2. 或停止占用端口的其他服务

## 📚 目录结构说明

```
HL-OS/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── services/    # 核心服务（Gemini, Claude, Obsidian, AnythingLLM）
│   │   ├── api/         # API端点
│   │   └── models/      # 数据模型
│   └── requirements.txt
│
├── frontend/             # Streamlit前端
│   ├── app.py          # 主页面
│   └── pages/          # 功能页面
│
├── obsidian_vault/      # 知识库（自动创建）
│   └── {孩子姓名}/
│       └── {学科}/
│           ├── No_Problems/     # 作业
│           ├── Wrong_Problems/  # 错题本
│           ├── Cards/           # 知识卡片
│           └── Courses/         # 课件
│
├── uploads/             # 临时上传文件
├── logs/                # 日志文件
└── backups/             # 备份文件
```

## 🎓 下一步学习

1. **阅读完整文档**: `README.md`
2. **查看API文档**: http://localhost:8000/docs
3. **探索代码结构**: 从`backend/app/main.py`开始
4. **自定义提示词**: 修改`backend/app/services/gemini_service.py`和`claude_service.py`

## 💡 提示和技巧

### 提高OCR准确率

- 确保照片光线充足
- 避免倾斜和模糊
- 文字清晰可见
- 使用图片质量检查功能

### 备份重要数据

```bash
# 定期备份
make backup

# 备份文件保存在backups/目录
```

### 监控服务健康

```bash
# 检查所有服务状态
make ps

# 查看后端健康状态
curl http://localhost:8000/health

# 查看API版本
curl http://localhost:8000/api/v1/health
```

## 🆘 获取帮助

- **问题报告**: 在项目仓库创建Issue
- **查看日志**: `make logs`
- **文档**: 查看`README.md`
- **API文档**: http://localhost:8000/docs

---

**祝使用愉快！🎉**
