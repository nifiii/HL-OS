# 开发指南

## 环境准备

### 必需软件

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Git** >= 2.30
- **Python** >= 3.11 (本地开发)
- **Make** (可选，用于快捷命令)

### API密钥

开发前请准备以下API密钥：

1. **Google AI Studio API Key**
   - 访问：https://makersuite.google.com/app/apikey
   - 注册Google账号
   - 创建新项目并启用Gemini API
   - 复制API密钥

2. **Anthropic API Key**
   - 访问：https://console.anthropic.com/
   - 注册账号
   - 在Account Settings创建API Key
   - 复制API密钥

## 项目设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd HL-OS
```

### 2. 配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑.env文件
nano .env
```

填入你的API密钥：
```env
GOOGLE_AI_STUDIO_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
SECRET_KEY=your-secret-key-here
```

生成SECRET_KEY：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 初始化项目

```bash
make setup
```

这会自动创建必要的目录：
- `obsidian_vault/`
- `uploads/`
- `logs/`
- `backups/`
- `anythingllm_data/`

## 本地开发

### 启动开发环境

```bash
# 一键启动（构建+运行）
make dev

# 或分步执行
make build  # 构建镜像
make up     # 启动服务
```

### 访问服务

- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs (Swagger UI)
- **前端界面**: http://localhost:8501
- **AnythingLLM**: http://localhost:3001
- **Redis**: localhost:6379

### 查看日志

```bash
# 所有服务日志
make logs

# 仅后端日志
make logs-backend

# 仅前端日志
make logs-frontend

# AnythingLLM日志
make logs-anythingllm
```

### 停止服务

```bash
make down
```

## 代码结构

### 后端结构

```
backend/app/
├── main.py                 # FastAPI应用入口
├── config.py               # 配置管理
├── api/v1/                 # API端点
│   ├── router.py          # 路由聚合
│   └── endpoints/         # 各模块端点
│       ├── perception.py
│       ├── validation.py
│       ├── storage.py
│       ├── teaching.py
│       └── assessment.py
├── services/               # 业务逻辑层
│   ├── gemini_service.py
│   ├── claude_service.py
│   ├── obsidian_service.py
│   └── anythingllm_service.py
├── models/                 # 数据模型
│   └── schemas.py
├── core/                   # 核心模块
│   └── exceptions.py
└── utils/                  # 工具函数
    ├── file_handler.py
    └── retry_utils.py
```

### 前端结构

```
frontend/
├── app.py                  # 主页面
├── pages/                  # 功能页面
│   ├── 1_📸_Validation.py
│   ├── 2_📚_Content.py
│   └── 3_📝_Assessment.py
├── components/             # 可复用组件
└── utils/                  # 工具函数
    └── api_client.py
```

## 开发规范

### 代码风格

#### Python (PEP 8)

```python
# 使用类型提示
def process_image(image_path: str, task_id: str) -> Dict[str, Any]:
    """
    处理图片并返回结果

    Args:
        image_path: 图片文件路径
        task_id: 任务ID

    Returns:
        Dict: 处理结果
    """
    ...

# 使用async/await
async def fetch_data(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

#### 命名规范

```python
# 类名: PascalCase
class ObsidianService:
    pass

# 函数名: snake_case
def save_markdown():
    pass

# 常量: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 10485760

# 私有方法: 前缀下划线
def _internal_helper():
    pass
```

### Git提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```bash
# 格式
<type>(<scope>): <subject>

# 示例
feat(api): add perception upload endpoint
fix(obsidian): correct metadata update logic
docs(readme): update installation instructions
style(backend): format code with ruff
refactor(services): extract common retry logic
test(api): add tests for validation endpoint
chore(deps): update dependencies
```

**Type类型**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具链

### 代码审查清单

提交PR前检查：

- [ ] 代码符合PEP 8规范
- [ ] 添加了类型提示
- [ ] 编写了文档字符串
- [ ] 添加了单元测试
- [ ] 测试全部通过
- [ ] 无敏感信息（API密钥）
- [ ] 更新了相关文档

## 测试

### 运行测试

```bash
# 所有测试
make test

# 带覆盖率
make test-cov

# 查看覆盖率报告
open htmlcov/index.html
```

### 编写测试

#### 单元测试

```python
# tests/unit/test_obsidian_service.py
import pytest
from pathlib import Path
from app.services.obsidian_service import ObsidianService

@pytest.fixture
def obsidian_service(tmp_path):
    service = ObsidianService()
    service.vault_path = tmp_path
    return service

def test_save_markdown(obsidian_service, tmp_path):
    file_path = obsidian_service.save_markdown(
        child_name="测试",
        subject="数学",
        folder_type="cards",
        filename="测试卡片",
        content="# 测试内容",
        metadata={"Difficulty": 3}
    )

    assert file_path.exists()
    assert "测试卡片" in file_path.name
```

#### 集成测试

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_photo():
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/api/v1/perception/upload",
            files={"file": f},
            data={
                "child_name": "测试",
                "subject": "数学",
                "content_type": "homework"
            }
        )

    assert response.status_code == 200
    assert "task_id" in response.json()
```

### Mock外部API

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch('app.services.gemini_service.genai.GenerativeModel')
async def test_ocr_with_mock(mock_model):
    # Mock Gemini API
    mock_response = AsyncMock()
    mock_response.text = '{"problems": []}'
    mock_model.return_value.generate_content_async.return_value = mock_response

    service = GeminiVisionService()
    result = await service.extract_from_image("test.jpg", "homework")

    assert result["success"] == True
```

## 调试技巧

### 1. 使用Python调试器

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用ipdb（更友好）
import ipdb; ipdb.set_trace()
```

### 2. 日志调试

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug信息")
logger.info("Info信息")
logger.warning("Warning信息")
logger.error("Error信息")
```

### 3. Docker调试

```bash
# 进入后端容器
make shell-backend

# 手动运行Python
python -m app.main

# 查看环境变量
env | grep API_KEY
```

### 4. API调试

使用Swagger UI：
- 访问 http://localhost:8000/docs
- 选择端点
- 点击 "Try it out"
- 输入参数并执行

使用curl：
```bash
curl -X POST http://localhost:8000/api/v1/perception/upload \
  -F "file=@test.jpg" \
  -F "child_name=测试" \
  -F "subject=数学" \
  -F "content_type=homework" \
  -v
```

## 添加新功能

### 示例：添加新的API端点

#### 1. 定义数据模型

```python
# backend/app/models/schemas.py
class NewFeatureRequest(BaseModel):
    param1: str = Field(..., description="参数1")
    param2: int = Field(..., ge=1, le=10, description="参数2")

class NewFeatureResponse(BaseModel):
    result: str
    success: bool
```

#### 2. 实现服务逻辑

```python
# backend/app/services/new_service.py
class NewService:
    async def process(self, request: NewFeatureRequest) -> Dict:
        # 业务逻辑
        return {"result": "processed", "success": True}
```

#### 3. 创建API端点

```python
# backend/app/api/v1/endpoints/new_feature.py
from fastapi import APIRouter
from app.models.schemas import NewFeatureRequest, NewFeatureResponse
from app.services.new_service import NewService

router = APIRouter()
service = NewService()

@router.post("/process", response_model=NewFeatureResponse)
async def process_feature(request: NewFeatureRequest):
    result = await service.process(request)
    return result
```

#### 4. 注册路由

```python
# backend/app/api/v1/router.py
from app.api.v1.endpoints import new_feature

router.include_router(
    new_feature.router,
    prefix="/new-feature",
    tags=["新功能"]
)
```

#### 5. 编写测试

```python
# tests/unit/test_new_service.py
def test_new_service():
    service = NewService()
    request = NewFeatureRequest(param1="test", param2=5)
    result = await service.process(request)
    assert result["success"] == True
```

#### 6. 更新文档

- 在 `docs/api/API_REFERENCE.md` 添加端点文档
- 更新 `README.md` 功能列表

## 性能优化

### 1. 分析性能瓶颈

```python
# 使用line_profiler
@profile
def slow_function():
    ...

# 或使用cProfile
import cProfile
cProfile.run('slow_function()')
```

### 2. 异步优化

```python
# Bad: 串行执行
result1 = await service1.call()
result2 = await service2.call()

# Good: 并行执行
results = await asyncio.gather(
    service1.call(),
    service2.call()
)
```

### 3. 缓存优化

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param: str) -> str:
    # 耗时计算
    return result
```

## 常见问题

### Q: ModuleNotFoundError

```bash
# 确保在正确的环境中
docker-compose exec backend python -m pip install -r requirements.txt
```

### Q: API调用失败

```bash
# 检查API密钥
docker-compose exec backend printenv | grep API_KEY

# 测试API连接
docker-compose exec backend python -c "
from app.services.gemini_service import GeminiVisionService
service = GeminiVisionService()
print(await service.test_connection())
"
```

### Q: 端口冲突

```bash
# 查看端口占用
lsof -i :8000
lsof -i :8501

# 修改docker-compose.yml中的端口映射
ports:
  - "8001:8000"  # 改为8001
```

## 贡献流程

1. Fork项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'feat: add amazing feature'`
4. 推送到分支: `git push origin feature/amazing-feature`
5. 开启Pull Request
6. 等待代码审查
7. 合并到main分支

## 参考资源

### 官方文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Streamlit文档](https://docs.streamlit.io/)
- [Gemini API文档](https://ai.google.dev/docs)
- [Claude API文档](https://docs.anthropic.com/)
- [Pydantic文档](https://docs.pydantic.dev/)

### 工具链
- [Docker文档](https://docs.docker.com/)
- [Pytest文档](https://docs.pytest.org/)
- [Ruff (Linter)](https://beta.ruff.rs/)
- [MyPy (Type Checker)](https://mypy.readthedocs.io/)

### 社区
- [GitHub Discussions](链接)
- [Discord频道](链接)
- [开发者Wiki](链接)
