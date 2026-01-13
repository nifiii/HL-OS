# HL-OS 架构设计文档

## 架构概览

HL-OS 采用分层架构设计，从上到下分为：用户层、API层、服务层、AI引擎层和存储层。

```
┌─────────────────────────────────────────────────────────┐
│                     用户层 (User Layer)                  │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │  Streamlit Web   │    │   Student View   │          │
│  │  (家长控制端)     │    │   (学生查看端)   │          │
│  └──────────────────┘    └──────────────────┘          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────┴──────────────────────────────────┐
│                 API层 (API Layer)                        │
│  ┌───────────────────────────────────────────────┐     │
│  │         FastAPI Application                    │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐         │     │
│  │  │Perception│ │ Storage │ │Teaching │ ...     │     │
│  │  │Endpoints │ │Endpoints│ │Endpoints│         │     │
│  │  └─────────┘ └─────────┘ └─────────┘         │     │
│  └───────────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────────┐     │
│  │   Middleware (CORS, Auth, Logging, etc.)      │     │
│  └───────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│               服务层 (Service Layer)                     │
│  ┌───────────┐ ┌───────────┐ ┌────────────┐           │
│  │  Gemini   │ │  Claude   │ │ AnythingLLM│           │
│  │  Service  │ │  Service  │ │  Service   │           │
│  └───────────┘ └───────────┘ └────────────┘           │
│  ┌───────────┐ ┌───────────┐ ┌────────────┐           │
│  │ Obsidian  │ │   File    │ │   Retry    │           │
│  │  Service  │ │  Handler  │ │   Utils    │           │
│  └───────────┘ └───────────┘ └────────────┘           │
└──────────────────────┬──────────────────────────────────┘
                       │ API Calls
┌──────────────────────┴──────────────────────────────────┐
│              AI引擎层 (AI Engine Layer)                  │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ Gemini 3 Pro     │    │Claude Sonnet 4.5 │          │
│  │  Preview         │    │   (Anthropic)    │          │
│  │  (Google AI)     │    │                  │          │
│  └──────────────────┘    └──────────────────┘          │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                存储层 (Storage Layer)                    │
│  ┌─────────────────────┐  ┌──────────────────────┐     │
│  │   AnythingLLM       │  │   Obsidian Vault     │     │
│  │  ┌──────────────┐   │  │  ┌────────────────┐ │     │
│  │  │  LanceDB     │   │  │  │ Markdown Files │ │     │
│  │  │ (Vectors)    │   │  │  │ + Frontmatter  │ │     │
│  │  └──────────────┘   │  │  └────────────────┘ │     │
│  └─────────────────────┘  └──────────────────────┘     │
│  ┌─────────────────────┐  ┌──────────────────────┐     │
│  │      Redis          │  │    File System       │     │
│  │   (Cache/Queue)     │  │   (Uploads/Logs)     │     │
│  └─────────────────────┘  └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 设计原则

### 1. 关注点分离 (Separation of Concerns)

每一层只关注自己的职责：
- **用户层**：仅处理UI和用户交互
- **API层**：仅处理HTTP请求/响应和路由
- **服务层**：包含所有业务逻辑
- **AI引擎层**：仅负责AI推理
- **存储层**：仅负责数据持久化

### 2. 依赖倒置 (Dependency Inversion)

高层模块不依赖低层模块，都依赖抽象：
```python
# 抽象接口
class OCRService(ABC):
    @abstractmethod
    async def extract_from_image(self, image_path: str) -> Dict: pass

# 具体实现
class GeminiVisionService(OCRService):
    async def extract_from_image(self, image_path: str) -> Dict:
        # Gemini specific implementation
        ...

# API层依赖抽象，不依赖具体实现
@router.post("/upload")
async def upload(ocr_service: OCRService = Depends(get_ocr_service)):
    result = await ocr_service.extract_from_image(...)
```

### 3. 单一职责 (Single Responsibility)

每个服务/模块只有一个变化的理由：
- `ObsidianService` 只负责文件操作
- `GeminiService` 只负责视觉识别
- `ClaudeService` 只负责内容生成和批改
- `AnythingLLMService` 只负责RAG检索

### 4. 开闭原则 (Open-Closed)

对扩展开放，对修改关闭：
```python
# 添加新的OCR引擎，无需修改现有代码
class TesseractOCRService(OCRService):
    async def extract_from_image(self, image_path: str) -> Dict:
        # Tesseract specific implementation
        ...

# 使用工厂模式选择OCR引擎
def get_ocr_service(engine: str = "gemini") -> OCRService:
    if engine == "gemini":
        return GeminiVisionService()
    elif engine == "tesseract":
        return TesseractOCRService()
```

## 数据流设计

### 作业上传与校验流程

```
[用户] → [Streamlit] → [FastAPI] → [Gemini Service] → [Gemini API]
                            ↓
                    [File Handler] → [File System]
                            ↓
                    [Redis] (Task Queue)
                            ↓
            [Streamlit Poll] ← [Task Result]
                            ↓
                    [User Validation]
                            ↓
                  ┌─────────┴─────────┐
                  ↓                   ↓
        [Obsidian Service]   [AnythingLLM Service]
                  ↓                   ↓
          [Markdown File]        [Vector DB]
```

### 教学内容生成流程

```
[用户配置] → [Streamlit] → [FastAPI Teaching Endpoint]
                                    ↓
                      [AnythingLLM Service Query]
                                    ↓
                          [Retrieve Context]
                                    ↓
                         [Claude Service Generate]
                                    ↓
                            [Claude API]
                                    ↓
                         [Marp Markdown]
                                    ↓
                      [User Preview & Approve]
                                    ↓
                        [Obsidian Service Save]
```

## 服务间通信

### 同步通信
- HTTP/REST API（FastAPI ↔ Streamlit）
- 函数调用（Service层内部）

### 异步通信
- Redis任务队列（长时间OCR任务）
- WebSocket（实时进度更新，未来实现）

### 错误处理策略

```python
# 1. 重试机制（指数退避）
@retry_with_exponential_backoff(max_retries=3)
async def call_external_api():
    ...

# 2. 熔断器（防止级联失败）
if circuit_breaker.is_open():
    raise ServiceUnavailableError()

# 3. 优雅降级
try:
    result = await gemini_service.extract()
except ExternalAPIError:
    result = fallback_ocr_service.extract()
```

## 缓存策略

### Redis缓存层次

```
L1: 任务状态缓存 (TTL: 1小时)
    - OCR任务结果
    - 内容生成状态

L2: RAG检索缓存 (TTL: 24小时)
    - 常用查询结果
    - 教材内容片段

L3: 会话缓存 (TTL: 会话结束)
    - 用户配置
    - 临时草稿
```

### 缓存失效策略

- **主动失效**：数据更新时清除相关缓存
- **被动失效**：TTL到期自动清除
- **LRU淘汰**：内存不足时淘汰最少使用

## 安全架构

### 1. 输入验证

```python
# Pydantic模型自动验证
class UploadRequest(BaseModel):
    child_name: str = Field(..., min_length=1, max_length=50)
    subject: str = Field(..., pattern="^[a-zA-Z\u4e00-\u9fa5]+$")
    file_size: int = Field(..., le=10485760)  # 10MB
```

### 2. 文件安全

```python
# 文件类型白名单
ALLOWED_TYPES = ["image/jpeg", "image/png"]

# 文件名清理
safe_filename = slugify(filename)

# 路径遍历防护
if ".." in file_path:
    raise SecurityError()
```

### 3. API密钥管理

```python
# 环境变量存储
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 密钥轮换支持
def get_api_key(service: str) -> str:
    return key_vault.get(service, version="latest")
```

### 4. 日志脱敏

```python
logger.info(f"User uploaded file: {safe_log(filename)}")
# 自动移除敏感信息：API密钥、个人身份信息等
```

## 可扩展性设计

### 水平扩展

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3  # 3个后端实例

  nginx:
    # 负载均衡配置
    upstream backend {
      server backend_1:8000;
      server backend_2:8000;
      server backend_3:8000;
    }
```

### 垂直扩展

```yaml
# 增加资源限制
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### 数据库分片（未来）

```python
# 按child_name分片
def get_shard(child_name: str) -> int:
    return hash(child_name) % NUM_SHARDS

vault_path = f"vault_shard_{get_shard(child_name)}"
```

## 监控与可观测性

### 日志层次

```python
# 结构化日志
logger.info(
    "OCR completed",
    task_id=task_id,
    duration_ms=elapsed,
    confidence=score
)
```

### 指标收集

```python
# Prometheus metrics
ocr_requests_total.inc()
ocr_duration_seconds.observe(elapsed)
ocr_confidence_score.set(score)
```

### 分布式追踪

```python
# OpenTelemetry
with tracer.start_as_current_span("ocr_process") as span:
    span.set_attribute("task_id", task_id)
    result = await gemini_service.extract()
```

## 容灾设计

### 1. 数据备份

```bash
# 自动备份策略
0 2 * * * /backup/obsidian_backup.sh  # 每日2am
0 */6 * * * /backup/anythingllm_backup.sh  # 每6小时
```

### 2. 故障恢复

```python
# 服务健康检查
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "gemini_api": await check_gemini(),
        "claude_api": await check_claude()
    }

    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(503, detail=checks)
```

### 3. 降级方案

```python
# 服务降级优先级
if gemini_unavailable:
    # 降级方案1: 使用本地Tesseract OCR
    result = tesseract_ocr(image)

if claude_unavailable:
    # 降级方案2: 返回模板内容
    result = get_template_content(topic)
```

## 性能优化

### 1. 异步IO

```python
# 所有IO操作异步化
async def process_batch(images: List[str]):
    tasks = [process_image(img) for img in images]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 连接池

```python
# HTTP连接池
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)
```

### 3. 批处理

```python
# 批量嵌入文档
async def batch_embed(documents: List[str], batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await anythingllm_service.embed_batch(batch)
```

## 部署架构

### 开发环境

```
Developer Machine
├── Docker Desktop
│   ├── Backend Container
│   ├── Frontend Container
│   ├── AnythingLLM Container
│   └── Redis Container
└── Local Obsidian Vault
```

### 生产环境

```
VPS/Cloud Server
├── Docker Compose
│   ├── Nginx (Reverse Proxy + SSL)
│   ├── Backend (×3 replicas)
│   ├── Frontend (×2 replicas)
│   ├── AnythingLLM
│   └── Redis (Master-Slave)
├── Persistent Volumes
│   ├── Obsidian Vault (mounted)
│   └── AnythingLLM Data (mounted)
└── Backup Server (remote)
```

## 技术债务

### 当前已知限制

1. **无认证系统** - 适用于单机部署，多用户需添加认证
2. **Redis单点** - 生产环境应使用主从或集群
3. **同步OCR** - 大文件应改为异步任务队列
4. **无分布式锁** - 并发写入Obsidian可能冲突

### 改进路线图

- [ ] Q1 2024: 添加JWT认证
- [ ] Q2 2024: OCR异步任务队列
- [ ] Q3 2024: Redis哨兵模式
- [ ] Q4 2024: 分布式文件锁

## 参考架构

- **Clean Architecture** (Robert C. Martin)
- **Hexagonal Architecture** (Alistair Cockburn)
- **Microservices Patterns** (Chris Richardson)
