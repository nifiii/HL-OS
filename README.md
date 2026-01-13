# HL-OS (Home-Learning Operating System)
# 家庭智能学习系统

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**一个"前轻后重"的AI驱动的家庭智能学习系统**

[快速开始](#快速开始) • [功能特性](#核心特性) • [文档](#文档) • [API参考](docs/api/API_REFERENCE.md) • [架构设计](docs/architecture/ARCHITECTURE.md)

</div>

---

## 概述

HL-OS 是一个以**质量优先**、**知识资产化**、**隐私保护**为核心理念的AI家庭学习系统。通过强制人工校验机制确保数据100%可靠，采用Obsidian标准化存储实现知识资产终身保存，本地优先架构保障数据完全自主可控。

### 核心理念

- **质量优先**: 所有AI识别结果须经家长校验后才能保存
- **知识资产化**: 使用Obsidian Frontmatter元数据标准，数据永久可导出
- **隐私保护**: 核心数据本地存储，仅API调用使用外部服务

## 目录

- [概述](#概述)
- [系统架构](#系统架构)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [文档](#文档)
- [项目状态](#项目状态)
- [开发指南](#开发指南)
- [备份策略](#备份策略)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [支持与反馈](#支持与反馈)
- [许可证](#许可证)

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
├──────────────┬──────────────────────────────────────────────┤
│ 家长端       │ 学生端                                        │
│ (Streamlit)  │ (Web/PDF查看)                                │
└──────────────┴───────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────┐
│              FastAPI中控层（业务逻辑）                       │
├───────────────┬──────────────┬──────────────┬───────────────┤
│ 感知与校验    │ RAG处理     │ 内容生成     │ 评测引擎       │
│ (Gemini OCR) │ (AnythingLLM)│ (Claude)     │ (Claude)      │
└───────────────┴──────────────┴──────────────┴───────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────┐
│                      存储层                                  │
├──────────────────────┬──────────────────────────────────────┤
│ AnythingLLM         │ Obsidian                              │
│ (海量原始资料检索)   │ (个人精华知识资产库)                  │
└──────────────────────┴──────────────────────────────────────┘
```

## 核心特性

### 🎯 模块A: 感知与人工校验
- **拍照上传**: 手机拍摄作业/试卷，系统自动接收
- **AI OCR识别**: Gemini 3 Pro Preview提取题目和答案（支持LaTeX数学公式）
- **家长校验**: 三栏式界面（原图 | AI识别 | 编辑框），确保100%准确

### 📚 模块B: RAG处理与存储分级
- **AnythingLLM**: 存储教材、原始图片，用于智能检索
- **Obsidian**: 存储校验后的作业、错题、知识卡片、教学课件
- **标准化元数据**: 自动注入难度、准确率、标签等信息

### 🎓 模块C: 教学内容生成
- **个性化课件**: 家长选择知识点、难度、风格，Claude Sonnet 4.5生成Marp PPT
- **RAG增强**: 从AnythingLLM检索教材内容作为生成背景
- **人工审批**: 家长预览确认后才推送给学生

### 📝 模块D: 评测引擎
- **智能出题**: Claude Sonnet 4.5生成原创题目（防止学生搜索到答案）
- **自动批改**: 学生答题拍照 → Gemini 3 Pro Preview OCR → Claude Sonnet 4.5批改 → 更新元数据
- **学情分析**: 实时追踪准确率，自动标记薄弱知识点

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Google AI Studio API密钥（[获取地址](https://makersuite.google.com/app/apikey)）
- Anthropic API密钥（[获取地址](https://console.anthropic.com/)）

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo-url>
cd HL-OS
```

2. **初始化环境**
```bash
make setup
```

3. **配置API密钥**
编辑 `.env` 文件，填入你的API密钥：
```bash
GOOGLE_AI_STUDIO_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

4. **启动服务**
```bash
make dev
```

首次启动会自动：
- 构建Docker镜像
- 创建必要的目录
- 启动所有服务

5. **访问服务**
- **前端界面**: http://localhost:8501 (家长控制面板)
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs (Swagger UI)
- **AnythingLLM**: http://localhost:3001

6. **开始功能测试**

系统已完成所有核心功能开发（v1.0），现在可以进行全面的功能测试：

```bash
# 查看功能测试清单
cat TESTING_CHECKLIST.md

# 或在浏览器中打开
# 推荐使用Markdown预览工具查看
```

**测试清单包含**：
- ✅ 150+ 详细测试项
- 📋 10大测试模块（系统基础、前端、移动端、业务功能、API、数据、集成、性能、安全、部署）
- 🔍 完整的测试步骤和预期结果
- 🛠️ 问题诊断命令和解决方案

**建议的测试顺序**：
1. **快速验证**（5分钟）- 确保所有服务启动
2. **移动端测试**（15分钟）- 在手机/平板上测试响应式布局
3. **核心功能测试**（30-45分钟）- 完整测试3大业务流程
4. **全面测试**（2-3小时）- 执行所有测试项并记录问题

详细的测试指南请参阅：[功能测试清单](TESTING_CHECKLIST.md)

## 常用命令

```bash
make help           # 查看所有可用命令
make dev            # 一键启动开发环境
make up             # 启动所有服务
make down           # 停止所有服务
make restart        # 重启所有服务
make logs           # 查看所有服务日志
make logs-backend   # 仅查看后端日志
make logs-frontend  # 仅查看前端日志
make test           # 运行测试套件
make test-cov       # 生成测试覆盖率报告
make backup         # 备份Obsidian知识库
make clean          # 清理临时文件和缓存
```

完整命令列表请运行 `make help`

## 项目结构

```
HL-OS/
├── backend/                       # FastAPI后端
│   ├── app/
│   │   ├── config.py             # 配置管理
│   │   ├── main.py               # FastAPI入口
│   │   ├── core/                 # 核心模块
│   │   │   └── exceptions.py    # 异常处理
│   │   ├── services/             # 核心服务层
│   │   │   ├── obsidian_service.py    # Obsidian文件操作
│   │   │   ├── gemini_service.py      # Gemini Vision OCR
│   │   │   ├── claude_service.py      # Claude教学和批改
│   │   │   └── anythingllm_service.py # AnythingLLM集成
│   │   ├── api/v1/endpoints/     # API端点
│   │   │   ├── perception.py    # 模块A: 感知与校验
│   │   │   ├── validation.py    # 模块A: 人工校验
│   │   │   ├── storage.py       # 模块B: 存储管理
│   │   │   ├── teaching.py      # 模块C: 教学内容生成
│   │   │   └── assessment.py    # 模块D: 评测引擎
│   │   ├── models/               # 数据模型
│   │   │   └── schemas.py       # Pydantic schemas
│   │   └── utils/                # 工具函数
│   │       ├── file_handler.py  # 文件处理
│   │       └── retry_utils.py   # 重试逻辑
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                      # Streamlit前端
│   ├── app.py                    # 主页面
│   ├── pages/                    # 功能页面
│   │   ├── 1_📸_Validation.py    # 人工校验界面
│   │   ├── 2_📚_Content.py       # 内容生成界面
│   │   └── 3_📝_Assessment.py    # 评测配置界面
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/                          # 文档 (spec_kit标准)
│   ├── specs/                    # 规格说明
│   │   ├── SYSTEM_OVERVIEW.md   # 系统概述
│   │   └── FUNCTIONAL_SPECS.md  # 功能规格
│   ├── architecture/             # 架构设计
│   │   └── ARCHITECTURE.md      # 架构文档
│   ├── api/                      # API文档
│   │   └── API_REFERENCE.md     # API参考手册
│   └── guides/                   # 开发指南
│       └── DEVELOPMENT.md       # 开发文档
│
├── obsidian_vault/               # Obsidian知识库
│   └── {孩子姓名}/
│       └── {学科}/
│           ├── No_Problems/      # 已校验作业
│           ├── Wrong_Problems/   # 错题本
│           ├── Cards/            # 知识卡片
│           └── Courses/          # 教学课件
│
├── anythingllm_data/             # AnythingLLM存储
│   ├── documents/                # 原始文档
│   ├── storage/                  # 数据库
│   └── vector-cache/             # 向量缓存
│
├── uploads/                      # 临时上传文件
├── logs/                         # 应用日志
├── backups/                      # 备份文件
│
├── docker-compose.yml            # 容器编排
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git忽略规则
├── Makefile                      # 常用命令
└── README.md                     # 本文档
```

## Obsidian文件标准格式

每个Markdown文件包含Frontmatter元数据和内容：

```markdown
---
Source: "人教版数学九年级上册 P45 - 二次函数顶点式"
Difficulty: 4
Accuracy: 0.6
Last_Modified: 2024-10-20
Last_Attempted: 2024-10-20
Attempts: 3
Tags:
  - 待复习
  - 二次函数
  - 顶点式
Related_Knowledge_Points:
  - 配方法
  - 函数图像平移
---

# 题目内容

已知二次函数 $y = 2(x-3)^2 + 1$，求其顶点坐标。

## 正确答案

顶点坐标为 $(3, 1)$

## 错误记录 - 2024-10-20

**学生答案:** $(3, -1)$
**错误原因:** 将常数项符号看错
```

## 存储分级策略

| 内容类型 | AnythingLLM | Obsidian | 说明 |
|---------|-------------|----------|------|
| 电子教材 | ✅ 全量存储（Hot/可搜索） | ❌ 仅存MOC索引 | RAG检索用 |
| 原始图片 | ✅ 全量存储（Cold/不搜索） | ❌ | 存证备份 |
| 校验后作业 | 索引链接 | ✅ 永久存储 | `No_Problems/` |
| 校验后错题 | 索引链接 | ✅ 永久存储 | `Wrong_Problems/` |
| 知识卡片 | 索引链接 | ✅ 永久存储 | `Cards/` |
| 完成的课件 | ❌ | ✅ 永久存储 | `Courses/` |

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| **后端框架** | FastAPI | 0.109+ |
| **Python** | Python | 3.11+ |
| **视觉识别** | Gemini 3 Pro Preview | 11-2025 |
| **教学引擎** | Claude Sonnet 4.5 | 20250929 |
| **RAG引擎** | AnythingLLM | Latest |
| **向量数据库** | LanceDB | Embedded |
| **知识库** | Obsidian | 文件系统 |
| **缓存** | Redis | 7-alpine |
| **容器化** | Docker Compose | 3.8 |

## 开发指南

完整的开发指南请参阅 **[开发文档](docs/guides/DEVELOPMENT.md)**，包含：

- 环境准备和项目设置
- 代码风格规范 (PEP 8)
- Git 提交规范 (Conventional Commits)
- 测试编写和运行
- 调试技巧
- 添加新功能的步骤
- 性能优化建议

### 快速参考

#### 添加新的API端点

1. 在 `backend/app/models/schemas.py` 定义数据模型
2. 在 `backend/app/api/v1/endpoints/` 创建端点文件
3. 在 `backend/app/api/v1/router.py` 注册路由
4. 编写单元测试

#### 运行测试

```bash
# 运行所有测试
make test

# 生成覆盖率报告
make test-cov

# 代码检查
make lint
```

详细说明请参阅 [开发文档 - 添加新功能](docs/guides/DEVELOPMENT.md#添加新功能)

## 备份策略

系统采用三级备份：

- **Critical（Obsidian）**: 每小时备份 + 90天保留 + 云端异地
- **Important（AnythingLLM）**: 每日备份 + 30天保留
- **Temporary（uploads）**: 每周备份 + 7天保留

手动备份：
```bash
make backup
```

## 故障排除

### 问题: 容器无法启动

**解决方案:**
```bash
# 查看日志
make logs

# 检查环境变量
cat .env

# 重新构建
make clean
make build
make up
```

### 问题: API密钥无效

**解决方案:**
1. 检查`.env`文件中的API密钥是否正确
2. 确认API密钥有效且有足够额度
3. 重启服务: `make restart`

### 问题: Obsidian文件权限错误

**解决方案:**
```bash
# 修复权限
sudo chown -R $USER:$USER obsidian_vault/
chmod -R 755 obsidian_vault/
```

## 文档

完整的文档结构遵循 GitHub spec_kit 标准，所有文档位于 `docs/` 目录：

### 📖 规格说明

- **[系统概述](docs/specs/SYSTEM_OVERVIEW.md)** - 项目定位、核心理念、四大模块详解
- **[功能规格](docs/specs/FUNCTIONAL_SPECS.md)** - 详细功能需求和性能指标

### 🏗️ 架构文档

- **[架构设计](docs/architecture/ARCHITECTURE.md)** - 分层架构、设计原则、数据流、安全策略

### 🔌 API文档

- **[API参考手册](docs/api/API_REFERENCE.md)** - 完整的REST API文档，包含17个端点的详细说明

### 👨‍💻 开发指南

- **[开发文档](docs/guides/DEVELOPMENT.md)** - 环境准备、代码规范、测试、调试技巧

### 🧪 测试文档

- **[功能测试清单](TESTING_CHECKLIST.md)** - 完整的功能测试清单（150+测试项，10大测试模块）

## 项目状态

### ✅ 已完成 (v1.0 - 功能完整版)

#### 核心基础设施
- [x] 核心服务实现 (Gemini, Claude, Obsidian, AnythingLLM)
- [x] 配置管理系统 (Pydantic Settings)
- [x] Docker容器化 (docker-compose.yml + 优化配置)
- [x] 数据模型定义 (完整的Pydantic schemas)
- [x] 异常处理机制 (统一错误处理)
- [x] 工具函数库 (文件处理、重试逻辑)
- [x] Makefile自动化命令
- [x] 完整文档体系 (spec_kit标准)

#### 后端API (100%完成)
- [x] **模块A - 感知与校验**
  - [x] POST /perception/upload - 图片上传与OCR识别
  - [x] POST /perception/quality-check - 图片质量检查
  - [x] POST /validation/submit - 人工校验数据提交
- [x] **模块B - 存储管理**
  - [x] POST /storage/obsidian/save - 保存到Obsidian
  - [x] GET /storage/obsidian/list - 列出知识库文件
  - [x] GET /storage/obsidian/content - 获取文件内容
  - [x] POST /storage/obsidian/update-metadata - 更新元数据
  - [x] POST /storage/anythingllm/embed - 文档嵌入
  - [x] POST /storage/anythingllm/query - RAG检索
- [x] **模块C - 教学内容生成**
  - [x] POST /teaching/generate - 生成教学内容
  - [x] GET /teaching/preview/{id} - 预览生成内容
  - [x] POST /teaching/approve - 批准并保存
  - [x] POST /teaching/reject - 拒绝内容
  - [x] GET /teaching/knowledge-points - 获取可选知识点
- [x] **模块D - 评测引擎**
  - [x] POST /assessment/generate - 生成评测题目
  - [x] POST /assessment/grade - 自动批改答案
  - [x] POST /assessment/analytics - 学情分析
  - [x] GET /assessment/history - 历史记录

#### 前端界面 (100%完成)
- [x] **主页面** - 系统概览和导航 (app.py)
- [x] **作业校验页面** - 三栏式人工校验界面 (1_📸_Validation.py)
  - [x] 图片上传与OCR识别
  - [x] 人工校验与修正
  - [x] 元数据配置与保存
- [x] **教学内容生成页面** - Claude智能微课生成 (2_📚_Content.py)
  - [x] 知识点选择（错题本/自定义）
  - [x] 参数配置（难度/风格/时长）
  - [x] RAG增强检索
  - [x] 内容预览与审批
- [x] **评测引擎页面** - 智能出题与批改 (3_📝_Assessment.py)
  - [x] 题目生成配置
  - [x] 自动批改功能
  - [x] 学情分析报告

#### 移动端适配 (100%完成)
- [x] **响应式布局** - 所有页面支持平板/手机访问
  - [x] 768px断点（平板）
  - [x] 480px断点（手机）
- [x] **触摸优化** - 按钮最小48px，交互反馈
- [x] **自适应组件** - 图片、表单、卡片全面适配
- [x] **侧边栏优化** - 移动端自动折叠

#### 文档与测试
- [x] 完整的API文档 (Swagger UI + ReDoc)
- [x] 系统架构文档
- [x] 开发指南
- [x] **功能测试清单** (150+测试项，10大测试模块)

### 🔄 待完成 (v1.1 - 生产就绪版)

#### 部署与运维
- [ ] 生产环境部署配置
  - [ ] Nginx反向代理配置
  - [ ] SSL/HTTPS证书配置
  - [ ] 域名配置
  - [ ] 防火墙规则
- [ ] 自动化备份脚本 (cron定时任务)
- [ ] 日志轮转配置
- [ ] 监控告警配置

#### 测试与优化
- [ ] 完整的功能测试执行 (参考TESTING_CHECKLIST.md)
- [ ] 性能压测与优化
- [ ] 安全性测试与加固
- [ ] 单元测试覆盖率提升 (目标>80%)

### 📅 未来规划 (v2.0+)

- [ ] 学情分析可视化看板 (图表、趋势分析)
- [ ] CI/CD自动化流程
- [ ] 多孩子账户管理 (用户系统)
- [ ] 学习进度跟踪 (时间轴、成就系统)
- [ ] 移动端原生应用 (iOS/Android)
- [ ] 数据导出与备份管理界面
- [ ] 自定义模板库 (题目模板、课件模板)
- [ ] 社区分享功能 (匿名化知识分享)

## 贡献指南

欢迎贡献！在开始之前，请先阅读 **[开发文档](docs/guides/DEVELOPMENT.md)** 了解代码规范和开发流程。

### 贡献流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 遵循代码规范 (PEP 8, 类型提示, 文档字符串)
4. 编写测试并确保通过 (`make test`)
5. 提交更改，使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式
   ```bash
   feat(api): add perception upload endpoint
   fix(obsidian): correct metadata update logic
   docs(readme): update installation instructions
   ```
6. 推送到分支 (`git push origin feature/AmazingFeature`)
7. 开启 Pull Request

### 代码审查清单

提交 PR 前请确保：

- [ ] 代码符合 PEP 8 规范
- [ ] 添加了类型提示
- [ ] 编写了文档字符串
- [ ] 添加了单元测试
- [ ] 测试全部通过
- [ ] 无敏感信息（API密钥）
- [ ] 更新了相关文档

## 支持与反馈

### 获取帮助

- 📖 查看 [开发文档](docs/guides/DEVELOPMENT.md) 中的常见问题解答
- 📧 提交 Issue 反馈问题或建议
- 💬 在 Discussions 中讨论功能和想法

### 问题报告

提交 Issue 时请包含：

- 系统环境（操作系统、Docker版本）
- 错误日志 (`make logs`)
- 复现步骤
- 预期行为和实际行为

## 许可证

本项目采用 **MIT 许可证**。详见 [LICENSE](LICENSE) 文件。

## 致谢

感谢以下开源项目和服务提供商：

- [Anthropic](https://www.anthropic.com/) - Claude 3.5 Sonnet API
- [Google AI](https://ai.google.dev/) - Gemini 2.0 Flash API
- [AnythingLLM](https://useanything.com/) - 本地化 RAG 引擎
- [Obsidian](https://obsidian.md/) - 知识管理工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [Streamlit](https://streamlit.io/) - 快速构建数据应用
- [Pydantic](https://docs.pydantic.dev/) - 数据验证库

## 免责声明

⚠️ **重要提示**:

- 本项目是一个**教育辅助工具**，旨在帮助家长更高效地辅导孩子学习
- **不能替代**正规学校教育和专业教师指导
- AI 生成的内容可能存在错误，请务必经过人工审核
- 使用外部 API 服务产生的费用由用户自行承担
- 请遵守相关法律法规，保护学生隐私

---

<div align="center">

**Built with ❤️ for better home learning**

如果这个项目对你有帮助，欢迎 ⭐ Star 支持

</div>
