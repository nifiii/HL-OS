# 存储分级策略

**文档版本**: v1.0
**最后更新**: 2024-01-13

---

## 📋 目录

- [策略概述](#策略概述)
- [分级详情](#分级详情)
- [代码实现](#代码实现)
- [使用示例](#使用示例)

---

## 策略概述

HL-OS 系统采用分级存储策略，根据内容类型在 AnythingLLM 和 Obsidian 之间合理分配存储职责：

### 设计原则

1. **Obsidian**: 永久存储结构化知识，支持双向链接和知识图谱
2. **AnythingLLM**: RAG检索引擎，存储教材全文和内容索引

### 存储分级表

| 内容类型 | AnythingLLM | Obsidian | 说明 |
|---------|-------------|----------|------|
| 电子教材 | ✅ 全量存储（Hot/可搜索） | ❌ 仅存MOC索引 | RAG检索用 |
| 原始图片 | ✅ 全量存储（Cold/不搜索） | ❌ | 存证备份 |
| 校验后作业 | 索引链接 | ✅ 永久存储 | `No_Problems/` |
| 校验后错题 | 索引链接 | ✅ 永久存储 | `Wrong_Problems/` |
| 知识卡片 | 索引链接 | ✅ 永久存储 | `Cards/` |
| 完成的课件 | 索引链接 | ✅ 永久存储 | `Courses/` |

---

## 分级详情

### 1. 全量存储（Hot/可搜索）

**适用内容**: 电子教材

**特点**:
- 完整的向量嵌入，支持语义搜索
- 可进行RAG检索
- 用于教学内容生成时的上下文检索

**实现方式**:
```python
# 全量嵌入（默认方式）
await anythingllm_service.embed_document(
    workspace_slug="textbooks",
    file_path="/path/to/textbook.pdf",
    metadata={"type": "textbook"},
    index_only=False  # 全量嵌入
)
```

### 2. 全量存储（Cold/不搜索）

**适用内容**: 原始图片

**特点**:
- 存储原始文件，但不进行向量嵌入
- 用于存证和备份
- 不参与RAG检索

**实现方式**:
```python
# 仅上传存储，不嵌入
await anythingllm_service.upload_document(
    file_path="/path/to/image.jpg",
    metadata={"type": "original_image"}
)
# 注意：不调用 embed_document
```

### 3. 索引链接

**适用内容**: 校验后作业、错题、知识卡片、完成的课件

**特点**:
- 在 Obsidian 中存储完整内容
- 在 AnythingLLM 中仅存储轻量级元数据和文件链接
- 通过元数据支持基础检索，但不嵌入完整内容

**优势**:
- 节省 AnythingLLM 存储空间和向量计算资源
- Obsidian 作为主要知识库，保持数据完整性
- 支持通过元数据检索（如知识点、难度、日期）

**实现方式**:
```python
# 创建索引链接
await anythingllm_service.embed_document(
    workspace_slug="homework",
    file_path="/path/to/obsidian/file.md",
    metadata={
        "type": "homework",
        "knowledge_points": ["二次函数"],
        "difficulty": 3
    },
    index_only=True  # 仅索引，不全量嵌入
)
```

**索引文档示例**:
```markdown
# 📄 二次函数_20240113

**文件路径**: `/obsidian_vault/小明/数学/Wrong_Problems/二次函数_20240113.md`
**创建时间**: 2024-01-13T10:30:00

## 元数据

- **Knowledge_Points**: ['二次函数']
- **Difficulty**: 3
- **Tags**: ['待复习']

## 说明

这是一个索引链接文档，指向实际存储在 Obsidian 中的完整内容。

**实际文件位置**: `/obsidian_vault/小明/数学/Wrong_Problems/二次函数_20240113.md`

---
*此文档仅用于索引和检索，完整内容请查看 Obsidian 知识库*
```

---

## 代码实现

### AnythingLLM 服务

**文件**: `backend/app/services/anythingllm_service.py`

#### 主要方法

```python
class AnythingLLMService:
    async def embed_document(
        self,
        workspace_slug: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        index_only: bool = False  # 关键参数
    ) -> Dict[str, Any]:
        """
        嵌入文档到工作区

        Args:
            workspace_slug: 工作区slug
            file_path: 文件路径
            metadata: 元数据
            index_only: 是否仅创建索引链接（不全量嵌入）

        Returns:
            嵌入结果
        """
        if index_only:
            # 索引链接模式
            return await self._embed_index_only(
                workspace_slug,
                file_path,
                metadata
            )

        # 全量嵌入模式
        upload_result = await self.upload_document(file_path, metadata)
        # ... 向量嵌入逻辑
```

#### 索引链接实现

```python
async def _embed_index_only(
    self,
    workspace_slug: str,
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    仅创建索引链接，不嵌入完整文档内容

    策略：
    1. 创建轻量级的元数据文档
    2. 包含文件路径、关键元数据
    3. 上传但不进行向量嵌入
    """
    # 创建索引文档（仅元数据）
    index_content = f"""# 📄 {path.stem}
**文件路径**: `{file_path}`
**创建时间**: {created_at}

## 元数据
{metadata_lines}

**实际文件位置**: `{file_path}`
"""

    # 上传索引文档
    # 注意：不调用 update-embeddings API
    upload_result = await self.upload_document(
        tmp_index_file,
        {**metadata, "is_index_only": True}
    )

    return {
        "status": "index_created",
        "index_only": True,
        "original_file_path": str(file_path)
    }
```

### 校验模块集成

**文件**: `backend/app/api/v1/endpoints/validation.py`

```python
async def _embed_to_anythingllm(
    workspace_slug: str,
    file_path: Path,
    metadata: Dict[str, Any],
    task_id: str
):
    """后台任务：将校验内容嵌入到 AnythingLLM"""

    # 根据存储分级策略：
    # 校验后作业、错题、知识卡片都使用"索引链接"方式
    result = await anythingllm_service.embed_document(
        workspace_slug=workspace_slug,
        file_path=str(file_path),
        metadata={
            **metadata,
            "task_id": task_id
        },
        index_only=True  # 仅创建索引链接
    )
```

### 教学内容模块集成

**文件**: `backend/app/api/v1/endpoints/teaching.py`

```python
async def approve_teaching_content(
    request: TeachingContentApprovalRequest
):
    """审批教学内容并保存"""

    # 1. 保存到 Obsidian
    file_path = obsidian_service.save_markdown(
        child_name=preview.child_name,
        subject=preview.subject,
        folder_type="Courses",
        filename=filename,
        content=final_content,
        metadata=metadata
    )

    # 2. 创建索引链接到 AnythingLLM
    workspace_slug = f"{child_name}_{subject}_courses"

    await anythingllm_service.embed_document(
        workspace_slug=workspace_slug,
        file_path=str(file_path),
        metadata=metadata,
        index_only=True  # 关键：仅索引，不全量嵌入
    )
```

---

## 使用示例

### 示例1: 上传电子教材（全量存储）

```python
# 用户上传数学教材PDF
textbook_path = "/uploads/math_textbook.pdf"

# 创建教材工作区
workspace_slug = "xiaoming_math_textbooks"
await anythingllm_service.ensure_workspace(
    slug=workspace_slug,
    name="小明 - 数学教材",
    child_name="小明",
    subject="数学"
)

# 全量嵌入教材（支持RAG检索）
result = await anythingllm_service.embed_document(
    workspace_slug=workspace_slug,
    file_path=textbook_path,
    metadata={
        "type": "textbook",
        "title": "初中数学九年级上册",
        "publisher": "人教版"
    },
    index_only=False  # 全量嵌入
)

# 结果：
# - AnythingLLM: 完整PDF内容向量化，支持语义搜索
# - Obsidian: 仅创建MOC索引（可选）
```

### 示例2: 保存错题（索引链接）

```python
# 学生作业识别后，发现错题
# 1. 保存到 Obsidian
obsidian_path = obsidian_service.save_markdown(
    child_name="小明",
    subject="数学",
    folder_type="Wrong_Problems",
    filename="二次函数_20240113",
    content=corrected_content,
    metadata={
        "Knowledge_Points": ["二次函数", "顶点式"],
        "Difficulty": 3,
        "Tags": ["待复习"],
        "Accuracy": 0.6
    }
)

# 2. 创建索引链接到 AnythingLLM
workspace_slug = "xiaoming_math_homework"
await anythingllm_service.embed_document(
    workspace_slug=workspace_slug,
    file_path=str(obsidian_path),
    metadata={
        "type": "wrong_problem",
        "Knowledge_Points": ["二次函数", "顶点式"],
        "Difficulty": 3,
        "file_path": str(obsidian_path)
    },
    index_only=True  # 仅索引
)

# 结果：
# - Obsidian: 完整错题内容、解析、反思
# - AnythingLLM: 轻量级元数据文档，包含文件路径和关键信息
```

### 示例3: 生成教学课件（索引链接）

```python
# Claude 生成 Marp 课件后，家长审批通过
# 1. 保存到 Obsidian
course_path = obsidian_service.save_markdown(
    child_name="小明",
    subject="数学",
    folder_type="Courses",
    filename="二次函数专题_20240113",
    content=marp_content,
    metadata={
        "Knowledge_Points": ["二次函数"],
        "Difficulty": 3,
        "Style": "启发式",
        "Duration_Minutes": 30
    }
)

# 2. 创建索引链接到 AnythingLLM
workspace_slug = "xiaoming_math_courses"
await anythingllm_service.embed_document(
    workspace_slug=workspace_slug,
    file_path=str(course_path),
    metadata={
        "type": "course",
        "Knowledge_Points": ["二次函数"],
        "file_path": str(course_path)
    },
    index_only=True  # 仅索引
)

# 结果：
# - Obsidian: 完整 Marp 课件内容
# - AnythingLLM: 课件索引，支持按知识点检索历史课件
```

---

## 工作区规划

根据存储策略，AnythingLLM 工作区按以下方式组织：

### 工作区命名规则

```
{child_name}_{subject}_{type}
```

### 工作区类型

| 类型 | Slug示例 | 内容 | 存储方式 |
|-----|---------|------|---------|
| textbooks | `xiaoming_math_textbooks` | 电子教材 | 全量存储 |
| homework | `xiaoming_math_homework` | 作业、错题 | 索引链接 |
| cards | `xiaoming_math_cards` | 知识卡片 | 索引链接 |
| courses | `xiaoming_math_courses` | 教学课件 | 索引链接 |
| images | `xiaoming_math_images` | 原始图片 | Cold存储 |

---

## 迁移指南

### 从旧版本迁移

如果您的系统之前使用全量嵌入所有内容，可以通过以下步骤迁移：

#### 1. 识别需要转换的文档

```python
# 查找所有 homework、cards、courses 工作区
workspaces = await anythingllm_service.list_workspaces()

migration_targets = [
    ws for ws in workspaces
    if any(t in ws['slug'] for t in ['homework', 'cards', 'courses'])
]
```

#### 2. 移除旧的全量嵌入

```python
for workspace in migration_targets:
    documents = await anythingllm_service.list_documents(workspace['slug'])

    for doc in documents:
        if not doc.get('metadata', {}).get('is_index_only'):
            # 移除全量嵌入的文档
            await anythingllm_service.remove_document(
                workspace['slug'],
                doc['name']
            )
```

#### 3. 重新创建为索引链接

```python
# 从 Obsidian 读取文件列表
obsidian_files = obsidian_service.list_files(
    child_name="小明",
    subject="数学",
    folder_type="Wrong_Problems"
)

for file_path in obsidian_files:
    # 读取元数据
    metadata = obsidian_service.get_metadata(file_path)

    # 创建索引链接
    await anythingllm_service.embed_document(
        workspace_slug="xiaoming_math_homework",
        file_path=str(file_path),
        metadata=metadata,
        index_only=True
    )
```

---

## 性能对比

### 存储空间

| 文档类型 | 全量嵌入 | 索引链接 | 节省比例 |
|---------|---------|---------|---------|
| 1个错题（2KB） | ~500KB（含向量） | ~1KB | 99.8% |
| 1个课件（10KB） | ~2MB（含向量） | ~1KB | 99.95% |
| 100个错题 | ~50MB | ~100KB | 99.8% |

### 检索性能

| 操作 | 全量嵌入 | 索引链接 | 说明 |
|-----|---------|---------|------|
| 语义搜索 | ✅ 支持 | ❌ 不支持 | 索引链接不支持向量搜索 |
| 元数据检索 | ✅ 支持 | ✅ 支持 | 都支持按元数据筛选 |
| 检索速度 | 中等 | 快速 | 索引文档小，查询更快 |

---

## 最佳实践

### 1. 合理选择存储方式

✅ **使用全量嵌入**：
- 需要语义搜索的教材
- 需要RAG检索的参考资料
- 用于生成上下文的背景知识

✅ **使用索引链接**：
- 已结构化的知识（错题、卡片）
- 生成的内容（课件）
- 个人学习记录

### 2. 元数据设计

为索引链接文档设计良好的元数据：

```python
metadata = {
    # 必要字段
    "type": "wrong_problem",  # 文档类型
    "file_path": "/path/to/file.md",  # 原始文件路径

    # 检索字段
    "Knowledge_Points": ["二次函数", "顶点式"],  # 支持知识点检索
    "Difficulty": 3,  # 支持难度筛选
    "Tags": ["待复习", "易错"],  # 支持标签检索

    # 时间字段
    "created_at": "2024-01-13T10:30:00",  # 创建时间
    "reviewed_at": None,  # 复习时间

    # 状态字段
    "is_index_only": True,  # 标识为索引文档
    "accuracy": 0.6  # 准确率等业务指标
}
```

### 3. 定期维护

```python
# 定期清理无效索引
async def cleanup_invalid_indices():
    """清理指向不存在文件的索引"""

    workspaces = await anythingllm_service.list_workspaces()

    for ws in workspaces:
        docs = await anythingllm_service.list_documents(ws['slug'])

        for doc in docs:
            if doc.get('metadata', {}).get('is_index_only'):
                file_path = doc['metadata'].get('file_path')

                # 检查文件是否存在
                if not Path(file_path).exists():
                    logger.warning(f"索引指向的文件不存在，清理: {file_path}")
                    await anythingllm_service.remove_document(
                        ws['slug'],
                        doc['name']
                    )
```

---

## 故障排查

### 问题1: 索引链接检索不到内容

**原因**: 索引文档不包含完整内容，无法进行语义搜索

**解决方案**: 使用元数据检索
```python
# ❌ 错误：尝试语义搜索索引文档
result = await anythingllm_service.query(
    workspace_slug="xiaoming_math_homework",
    query="二次函数的顶点式是什么？"  # 语义搜索
)

# ✅ 正确：使用元数据检索
result = await anythingllm_service.query(
    workspace_slug="xiaoming_math_homework",
    query="knowledge_points:二次函数"  # 元数据检索
)
```

### 问题2: 索引文档占用空间过大

**原因**: 元数据过多或包含冗余信息

**解决方案**: 精简元数据
```python
# ❌ 包含完整内容（错误）
metadata = {
    "full_content": marp_content,  # 不要在元数据中包含完整内容
    ...
}

# ✅ 仅包含必要元数据
metadata = {
    "Knowledge_Points": ["二次函数"],
    "Difficulty": 3,
    "file_path": "/path/to/file.md",  # 通过路径引用
    ...
}
```

---

## 总结

HL-OS 的存储分级策略实现了：

✅ **高效存储**: 索引链接节省99%+存储空间
✅ **快速检索**: 轻量级索引文档提升检索速度
✅ **数据完整性**: Obsidian保持完整内容，支持知识图谱
✅ **灵活扩展**: 支持全量嵌入和索引链接两种模式

通过合理的存储策略，系统在保证功能完整的同时，大幅优化了性能和成本。

---

<div align="center">

**存储分级策略文档** v1.0

**HL-OS - 智能家庭学习系统**

</div>
