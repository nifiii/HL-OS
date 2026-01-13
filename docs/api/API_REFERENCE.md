# API 参考文档

## 基础信息

**Base URL**: `http://localhost:8000`
**API Version**: `v1`
**Content-Type**: `application/json`
**API Prefix**: `/api/v1`

## 认证

当前版本暂无认证机制（适用于本地部署）。未来版本将支持：
- API Key 认证
- JWT Token 认证

---

## 模块 A: 感知与校验 API

### 1. 上传图片进行 OCR

**Endpoint**: `POST /api/v1/perception/upload`

**描述**: 上传作业/试卷图片，系统自动进行 OCR 识别。

**请求格式**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件（JPG/PNG，≤10MB） |
| child_name | String | 是 | 孩子姓名 |
| subject | String | 是 | 学科名称 |
| content_type | String | 是 | 内容类型：homework/test/textbook/worksheet |

**请求示例**:

```bash
curl -X POST http://localhost:8000/api/v1/perception/upload \
  -F "file=@homework.jpg" \
  -F "child_name=张三" \
  -F "subject=数学" \
  -F "content_type=homework"
```

**响应示例** (200 OK):

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "OCR识别完成"
}
```

**错误响应**:

```json
{
  "error_code": "FILE_UPLOAD_ERROR",
  "message": "文件过大: 12.5MB，最大允许: 10.0MB",
  "details": {
    "filename": "homework.jpg"
  }
}
```

**状态码**:
- `200` - 成功
- `400` - 请求参数错误
- `413` - 文件过大
- `500` - 服务器错误

---

### 2. 获取 OCR 识别结果

**Endpoint**: `GET /api/v1/perception/result/{task_id}`

**描述**: 根据任务 ID 获取 OCR 识别结果。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | String | OCR任务ID |

**请求示例**:

```bash
curl http://localhost:8000/api/v1/perception/result/550e8400-e29b-41d4-a716-446655440000
```

**响应示例** (200 OK):

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "extracted_text": "1. 已知函数 f(x) = 2x + 3，求 f(5) 的值。\n学生答案：13 ✓",
  "structured_data": {
    "problems": [
      {
        "problem_number": "1",
        "question": "已知函数 $f(x) = 2x + 3$，求 $f(5)$ 的值。",
        "student_answer": "13",
        "is_marked_correct": true
      }
    ],
    "metadata": {
      "subject": "数学",
      "page_number": "P45"
    }
  },
  "confidence_score": 0.95,
  "original_image_url": "/uploads/550e8400.jpg",
  "created_at": "2024-01-13T10:30:00Z",
  "error": null
}
```

**状态值**:
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 失败

---

### 3. 图片质量验证

**Endpoint**: `POST /api/v1/perception/validate-quality`

**描述**: 在 OCR 之前检查图片质量。

**请求格式**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |

**响应示例** (200 OK):

```json
{
  "quality_score": 85,
  "is_acceptable": true,
  "issues": [
    {
      "issue_type": "slightly_tilted",
      "severity": "low",
      "description": "图片轻微倾斜，建议重新拍摄"
    }
  ],
  "recommendations": ["使用平整表面", "增加光照"]
}
```

---

### 4. 提交校验结果

**Endpoint**: `POST /api/v1/validation/submit`

**描述**: 家长校验后提交修正的内容。

**请求体**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "corrected_text": "1. 已知函数 f(x) = 2x + 3，求 f(5) 的值。",
  "metadata": {
    "Source": "课后作业 P45",
    "Difficulty": 3,
    "Tags": ["一次函数", "函数值"],
    "Related_Knowledge_Points": ["函数定义", "函数求值"]
  },
  "save_to_obsidian": true,
  "embed_in_anythingllm": true,
  "child_name": "张三",
  "subject": "数学",
  "folder_type": "no_problems",
  "filename": "一次函数作业"
}
```

**响应示例** (200 OK):

```json
{
  "success": true,
  "obsidian_file_path": "/obsidian_vault/张三/数学/No_Problems/20240113_一次函数作业.md",
  "anythingllm_status": "embedded",
  "message": "保存成功"
}
```

---

## 模块 B: 存储管理 API

### 5. 保存到 Obsidian

**Endpoint**: `POST /api/v1/storage/obsidian/save`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "folder_type": "wrong_problems",
  "filename": "二次函数错题",
  "content": "# 题目\n\n已知二次函数...",
  "metadata": {
    "Source": "期中考试",
    "Difficulty": 4,
    "Accuracy": 0.6,
    "Tags": ["待复习", "二次函数"]
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "file_path": "/obsidian_vault/张三/数学/Wrong_Problems/二次函数错题.md",
  "message": "保存成功"
}
```

---

### 6. 搜索 Obsidian 文件

**Endpoint**: `POST /api/v1/storage/obsidian/search`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "folder_type": "wrong_problems",
  "filters": {
    "Difficulty": 4,
    "Tags": ["待复习"]
  }
}
```

**响应示例**:

```json
{
  "results": [
    {
      "file_path": "/obsidian_vault/张三/数学/Wrong_Problems/二次函数错题.md",
      "metadata": {
        "Source": "期中考试",
        "Difficulty": 4,
        "Accuracy": 0.6,
        "Tags": ["待复习", "二次函数"]
      },
      "content": "# 题目\n\n...",
      "filename": "二次函数错题"
    }
  ],
  "total": 1
}
```

---

### 7. 获取错题列表

**Endpoint**: `POST /api/v1/storage/obsidian/wrong-problems`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "min_difficulty": 3,
  "max_accuracy": 0.7,
  "limit": 10
}
```

**响应示例**:

```json
{
  "problems": [
    {
      "file_path": "...",
      "metadata": {...},
      "content": "...",
      "filename": "二次函数错题"
    }
  ],
  "total": 5
}
```

---

### 8. 嵌入文档到 AnythingLLM

**Endpoint**: `POST /api/v1/storage/anythingllm/embed`

**请求体**:

```json
{
  "workspace_slug": "zhangsan_math_homework",
  "file_path": "/path/to/document.pdf",
  "metadata": {
    "child_name": "张三",
    "subject": "数学",
    "content_type": "homework",
    "difficulty": 3
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "document_name": "document.pdf",
  "workspace_slug": "zhangsan_math_homework",
  "status": "embedded"
}
```

---

### 9. RAG 检索

**Endpoint**: `POST /api/v1/storage/anythingllm/query`

**请求体**:

```json
{
  "workspace_slug": "zhangsan_textbooks",
  "query": "二次函数顶点坐标公式",
  "top_k": 5
}
```

**响应示例**:

```json
{
  "query": "二次函数顶点坐标公式",
  "context": "二次函数的顶点式为 y = a(x - h)² + k，其中 (h, k) 即为顶点坐标...",
  "sources": [
    {
      "text": "二次函数的顶点式...",
      "source": "人教版数学九年级上册 P45",
      "score": 0.89
    }
  ]
}
```

---

## 模块 C: 教学内容生成 API

### 10. 生成教学内容

**Endpoint**: `POST /api/v1/teaching/generate`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "knowledge_points": ["二次函数顶点式", "配方法"],
  "difficulty": 4,
  "style": "启发式",
  "duration_minutes": 30,
  "additional_instructions": "重点讲解配方过程",
  "retrieve_from_textbook": true,
  "retrieve_from_wrong_problems": true
}
```

**响应示例** (200 OK):

```json
{
  "content_id": "c123456",
  "marp_markdown": "---\nmarp: true\n...",
  "preview_url": "/preview/c123456",
  "knowledge_points_used": ["二次函数顶点式", "配方法"],
  "estimated_duration": 28,
  "created_at": "2024-01-13T10:30:00Z"
}
```

---

### 11. 审批教学内容

**Endpoint**: `POST /api/v1/teaching/approve`

**请求体**:

```json
{
  "content_id": "c123456",
  "approved": true,
  "modifications": null
}
```

**响应示例**:

```json
{
  "success": true,
  "saved_path": "/obsidian_vault/张三/数学/Courses/20240113_二次函数顶点式.md",
  "message": "内容已保存并推送"
}
```

---

## 模块 D: 评测引擎 API

### 12. 生成评测题目

**Endpoint**: `POST /api/v1/assessment/generate`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "topic_range": ["二次函数", "一元二次方程"],
  "difficulty_distribution": {
    "1": 2,
    "2": 3,
    "3": 3,
    "4": 2
  },
  "question_types": ["calculation", "short_answer"],
  "total_points": 100
}
```

**响应示例**:

```json
{
  "assessment_id": "a789012",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "已知二次函数 $f(x) = x^2 - 4x + 3$，求其顶点坐标。",
      "question_type": "calculation",
      "difficulty": 3,
      "points": 10,
      "options": null,
      "correct_answer": "(2, -1)",
      "solution": "使用配方法：f(x) = (x - 2)² - 1，顶点为 (2, -1)",
      "grading_rubric": "列式正确2分，配方过程5分，答案3分",
      "knowledge_points": ["二次函数", "配方法", "顶点坐标"],
      "hint": "将函数配方成顶点式"
    }
  ],
  "total_points": 100,
  "created_at": "2024-01-13T10:30:00Z"
}
```

---

### 13. 批改答案

**Endpoint**: `POST /api/v1/assessment/grade`

**请求体**:

```json
{
  "assessment_id": "a789012",
  "question_id": "q1",
  "student_answer": "(2, -1)",
  "show_detailed_feedback": true
}
```

**响应示例**:

```json
{
  "question_id": "q1",
  "score": 10,
  "max_score": 10,
  "is_correct": true,
  "correctness_rate": 1.0,
  "feedback": "完全正确！配方过程清晰，答案准确。",
  "detailed_feedback": {
    "strengths": ["配方法应用正确", "计算准确"],
    "errors": [],
    "suggestions": ["保持这种解题思路"]
  },
  "knowledge_gaps": []
}
```

---

### 14. 批量批改

**Endpoint**: `POST /api/v1/assessment/batch-grade`

**请求体**:

```json
{
  "assessment_id": "a789012",
  "answers": [
    {
      "question_id": "q1",
      "student_answer": "(2, -1)"
    },
    {
      "question_id": "q2",
      "student_answer": "x = 1 或 x = 3"
    }
  ]
}
```

**响应示例**:

```json
{
  "results": [
    {
      "question_id": "q1",
      "score": 10,
      "is_correct": true,
      ...
    },
    {
      "question_id": "q2",
      "score": 8,
      "is_correct": false,
      ...
    }
  ],
  "total_score": 18,
  "total_max_score": 20,
  "overall_accuracy": 0.9
}
```

---

### 15. 学情分析

**Endpoint**: `POST /api/v1/assessment/analyze`

**请求体**:

```json
{
  "child_name": "张三",
  "subject": "数学",
  "knowledge_point": "二次函数",
  "time_range_days": 30
}
```

**响应示例**:

```json
{
  "mastery_level": 75.5,
  "weak_points": ["配方法符号处理", "根的判别式"],
  "progress_trend": "improving",
  "recommendations": [
    "加强有理数运算练习",
    "复习配方法的符号规则",
    "多做综合应用题"
  ],
  "focus_areas": ["基础计算", "公式记忆"]
}
```

---

## 系统 API

### 16. 健康检查

**Endpoint**: `GET /health`

**响应示例**:

```json
{
  "status": "healthy",
  "environment": "development"
}
```

---

### 17. API 版本信息

**Endpoint**: `GET /api/v1/health`

**响应示例**:

```json
{
  "status": "healthy",
  "api_version": "v1"
}
```

---

## 错误处理

### 统一错误响应格式

```json
{
  "error_code": "ERROR_CODE",
  "message": "错误描述信息",
  "details": {
    "field": "具体字段",
    "value": "错误值"
  },
  "timestamp": "2024-01-13T10:30:00Z"
}
```

### 错误码列表

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| FILE_UPLOAD_ERROR | 400 | 文件上传错误 |
| RESOURCE_NOT_FOUND | 404 | 资源未找到 |
| RATE_LIMIT_EXCEEDED | 429 | 超过速率限制 |
| EXTERNAL_API_ERROR | 503 | 外部API调用失败 |
| OBSIDIAN_ERROR | 500 | Obsidian操作失败 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 速率限制

| 端点类别 | 限制 |
|---------|------|
| OCR上传 | 10次/分钟 |
| 内容生成 | 5次/分钟 |
| 批改 | 20次/分钟 |
| 查询 | 60次/分钟 |

超过限制返回 `429 Too Many Requests`。

---

## SDK 示例

### Python

```python
import requests

class HLOSClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def upload_homework(self, file_path, child_name, subject):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'child_name': child_name,
                'subject': subject,
                'content_type': 'homework'
            }
            response = requests.post(
                f"{self.base_url}/api/v1/perception/upload",
                files=files,
                data=data
            )
            return response.json()

# 使用示例
client = HLOSClient()
result = client.upload_homework("homework.jpg", "张三", "数学")
print(result['task_id'])
```

### JavaScript

```javascript
class HLOSClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async uploadHomework(file, childName, subject) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('child_name', childName);
    formData.append('subject', subject);
    formData.append('content_type', 'homework');

    const response = await fetch(`${this.baseURL}/api/v1/perception/upload`, {
      method: 'POST',
      body: formData
    });

    return response.json();
  }
}

// 使用示例
const client = new HLOSClient();
const result = await client.uploadHomework(fileInput.files[0], '张三', '数学');
console.log(result.task_id);
```

---

## 变更日志

### v1.0.0 (2024-01-13)
- 初始版本发布
- 实现模块A感知与校验API
- 实现基础存储管理API
- 提供健康检查端点
