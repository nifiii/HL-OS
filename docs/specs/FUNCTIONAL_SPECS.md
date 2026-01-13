# 功能规格说明

## 模块 A: 感知与校验 (Perception & Validation)

### A.1 图片上传

**功能描述**：家长通过手机拍照或选择相册中的作业/试卷图片上传到系统。

**输入**：
- 图片文件（JPG/PNG，最大10MB）
- 孩子姓名
- 学科
- 内容类型（作业/试卷/教材/练习）

**处理流程**：
1. 验证文件类型和大小
2. 保存到临时目录 `uploads/{child_name}/{subject}/`
3. 生成唯一任务ID
4. 返回任务ID给前端

**输出**：
- 任务ID
- 上传状态
- 文件保存路径

**错误处理**：
- 文件格式不支持 → 400 错误
- 文件过大 → 413 错误
- 服务器错误 → 500 错误

**性能要求**：
- 上传响应时间 < 3秒
- 支持并发上传数 ≥ 5

---

### A.2 OCR 识别

**功能描述**：调用 Gemini Vision API 识别图片中的文字和数学公式。

**输入**：
- 图片文件路径
- 内容类型（决定使用哪个提示词模板）

**处理流程**：
1. 读取图片文件
2. 根据内容类型选择提示词
3. 调用 Gemini API
4. 解析返回的 JSON 结果
5. 计算置信度分数

**输出**：
```json
{
  "task_id": "uuid",
  "status": "completed",
  "extracted_text": "原始文本",
  "structured_data": {
    "problems": [
      {
        "problem_number": "1",
        "question": "题目内容（LaTeX格式）",
        "student_answer": "学生答案",
        "is_marked_correct": true
      }
    ]
  },
  "confidence_score": 0.95
}
```

**提示词模板**：
- **作业模板**：提取题号、题目、学生答案、批改标记
- **试卷模板**：提取题目、题型、分值、标准答案
- **教材模板**：提取章节、知识点、例题、公式
- **练习模板**：提取题目、难度、提示

**质量保证**：
- LaTeX 公式准确率 > 85%
- 题号识别准确率 > 95%
- 整体文字识别准确率 > 90%

**错误处理**：
- API 调用失败 → 自动重试3次（指数退避）
- JSON 解析失败 → 返回原始文本
- 置信度过低 → 标记需人工复核

---

### A.3 图片质量检查

**功能描述**：在 OCR 之前检查图片质量，提前发现问题。

**检查项**：
- [ ] 图片清晰度
- [ ] 光线充足性
- [ ] 是否倾斜
- [ ] 是否有遮挡

**输出**：
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

**阈值设定**：
- quality_score < 60 → 拒绝处理
- quality_score 60-75 → 警告但允许
- quality_score > 75 → 正常处理

---

### A.4 人工校验界面

**功能描述**：三栏式界面展示原图、AI识别结果和编辑框，供家长校验。

**界面布局**：
```
┌────────────────┬────────────────┬────────────────┐
│   原始图片     │  AI识别结果    │   编辑修正     │
│   (只读展示)   │  (只读展示)    │   (可编辑)     │
│                │                │                │
│   [图片预览]   │  题目1: ...    │  [文本编辑框]  │
│                │  学生答案: ... │                │
│                │  题目2: ...    │  难度: ★★★☆☆  │
│                │                │  标签: [...]   │
└────────────────┴────────────────┴────────────────┘
             [取消]  [确认并保存]
```

**元数据配置**：
- **难度等级**：1-5星滑动条
- **标签**：多选（待复习/已掌握/重难点等）
- **知识点**：文本输入
- **来源**：自动填充或手动修改

**保存选项**：
- [ ] 保存到 Obsidian（默认勾选）
- [ ] 嵌入 AnythingLLM（默认勾选）
- 文件夹类型：下拉选择（作业/错题/卡片）

**交互要求**：
- 实时预览编辑效果
- 支持快捷键（Ctrl+S 保存）
- 自动保存草稿（每30秒）

---

### A.5 数据分流保存

**功能描述**：根据家长配置将校验后的数据保存到不同位置。

**保存到 Obsidian**：
```
路径: obsidian_vault/{child_name}/{subject}/{folder_type}/{timestamp}_{filename}.md
格式: Markdown + YAML Frontmatter
```

**Frontmatter 标准**：
```yaml
---
Source: "来源信息"
Difficulty: 4
Accuracy: null  # 初始为null，批改后更新
Last_Modified: "2024-01-13T10:30:00"
Tags: ["待复习", "二次函数"]
Related_Knowledge_Points: ["配方法", "顶点式"]
Original_Image: "/uploads/path/to/image.jpg"
OCR_Confidence: 0.95
---
```

**嵌入到 AnythingLLM**：
```
Workspace: {child_name}_{subject}_homework
Metadata: {
  child_name: "张三",
  subject: "数学",
  difficulty: 4,
  timestamp: "2024-01-13"
}
```

**原子性保证**：
- Obsidian 保存失败 → 回滚，不嵌入 AnythingLLM
- AnythingLLM 失败 → 记录日志，但不影响 Obsidian
- 使用事务确保数据一致性

---

## 模块 B: RAG 处理与存储 (Storage & Retrieval)

### B.1 文档嵌入

**功能描述**：将教材、作业等文档嵌入到 AnythingLLM 向量数据库。

**支持的文档类型**：
- PDF（教材、试卷）
- Markdown（笔记、卡片）
- 图片（OCR后嵌入）

**嵌入流程**：
```
文档上传 → 文本提取 → 分块(Chunking) → 向量化 → 存储到LanceDB
```

**分块策略**：
- 教材：按章节分块（~500 tokens）
- 作业：按题目分块
- 卡片：整个文件作为一块

**元数据标记**：
```json
{
  "doc_type": "textbook",
  "subject": "数学",
  "chapter": "第三章",
  "grade": "九年级",
  "keywords": ["二次函数", "抛物线"]
}
```

---

### B.2 智能检索

**功能描述**：根据查询语句检索相关文档片段。

**检索模式**：
- **语义检索**：基于向量相似度
- **关键词检索**：基于BM25算法
- **混合检索**：结合语义和关键词

**查询增强**：
```python
原始查询: "二次函数顶点"
增强后: "二次函数的顶点坐标公式推导过程示例"
```

**结果排序**：
1. 相关度分数（向量距离）
2. 文档权重（教材 > 笔记 > 作业）
3. 时间新鲜度

**返回格式**：
```json
{
  "query": "二次函数顶点",
  "results": [
    {
      "content": "检索到的文本片段",
      "source": "人教版数学九年级上册 P45",
      "score": 0.89,
      "metadata": {...}
    }
  ]
}
```

---

### B.3 Obsidian 操作

**B.3.1 文件创建**

```python
obsidian_service.save_markdown(
    child_name="张三",
    subject="数学",
    folder_type="wrong_problems",
    filename="二次函数顶点式错题",
    content=markdown_content,
    metadata={
        "Source": "期中考试",
        "Difficulty": 4,
        "Tags": ["待复习", "二次函数"]
    }
)
```

**B.3.2 元数据更新**

```python
# 批改后更新准确率
obsidian_service.update_metadata(
    file_path=Path("..."),
    metadata_updates={
        "Accuracy": 0.6,
        "Attempts": 3,
        "Last_Attempted": "2024-01-13"
    }
)
```

**B.3.3 错题查询**

```python
# 查询准确率低于60%、难度4星以上的错题
wrong_problems = obsidian_service.get_wrong_problems(
    child_name="张三",
    subject="数学",
    min_difficulty=4,
    max_accuracy=0.6,
    limit=10
)
```

**B.3.4 知识卡片创建**

```python
obsidian_service.create_knowledge_card(
    child_name="张三",
    subject="数学",
    knowledge_point="二次函数顶点式",
    explanation="...",
    examples=["例1", "例2"],
    related_problems=["题目1", "题目2"],
    metadata={...}
)
```

---

## 模块 C: 教学内容生成 (Content Generation)

### C.1 课件生成

**输入参数**：
```json
{
  "child_name": "张三",
  "subject": "数学",
  "knowledge_points": ["二次函数顶点式", "配方法"],
  "difficulty": 4,
  "style": "启发式",
  "duration_minutes": 30,
  "additional_instructions": "重点讲解配方过程"
}
```

**生成流程**：
```
1. RAG检索 → 从AnythingLLM检索相关教材内容
2. 构建Prompt → 组合参数生成详细提示词
3. 调用Claude → 生成Marp Markdown
4. 后处理 → 验证格式、添加页码
5. 返回预览 → 生成预览URL
```

**Marp 输出格式**：
```markdown
---
marp: true
theme: default
paginate: true
---

# 二次函数顶点式

难度: ★★★★☆
时长: 30分钟

---

## 引入：为什么要学顶点式？

<!-- presenter notes: 从实际问题引入 -->
...
```

**质量检查**：
- [ ] 格式正确（YAML + Markdown）
- [ ] 页数适中（10-20页）
- [ ] LaTeX 语法正确
- [ ] 难度匹配设定

---

### C.2 内容审批

**预览功能**：
- Marp渲染后的PDF预览
- 幻灯片逐页浏览
- 讲解备注查看

**修改选项**：
- 重新生成（调整参数）
- 人工编辑（直接修改Markdown）
- 添加批注

**批准后操作**：
```
保存到: obsidian_vault/{child_name}/{subject}/Courses/{timestamp}_{topic}.md
推送方式: 生成分享链接 / 导出PDF / 发送到学生端
```

---

## 模块 D: 评测引擎 (Assessment Engine)

### D.1 题目生成

**输入配置**：
```json
{
  "child_name": "张三",
  "subject": "数学",
  "topic_range": ["二次函数", "一元二次方程"],
  "difficulty_distribution": {
    "1": 2,  // 基础题2道
    "2": 3,  // 中档题3道
    "3": 3,  // 标准题3道
    "4": 2   // 提高题2道
  },
  "question_types": ["calculation", "short_answer"],
  "total_points": 100
}
```

**生成策略**：
- **原创性保证**：
  - 改变数据范围
  - 调整问题场景
  - 组合多个知识点
- **防搜索设计**：
  - 避免经典例题
  - 修改表述方式
  - 使用新颖背景

**输出格式**：
```json
{
  "assessment_id": "uuid",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "已知...",
      "question_type": "calculation",
      "difficulty": 3,
      "points": 10,
      "correct_answer": "...",
      "solution": "详细步骤",
      "grading_rubric": "列式2分，计算过程5分，答案3分",
      "knowledge_points": ["配方法", "顶点坐标"]
    }
  ]
}
```

---

### D.2 自动批改

**批改流程**：
```
学生答题图片 → Gemini OCR → 提取答案
    ↓
答案 + 标准答案 + 评分标准 → Claude批改
    ↓
返回分数、反馈、改进建议
```

**批改维度**：
1. **正确性**（60%）：答案是否正确
2. **过程性**（30%）：解题步骤是否完整
3. **规范性**（10%）：书写是否规范

**反馈格式**：
```json
{
  "score": 8,
  "max_score": 10,
  "is_correct": false,
  "feedback": "解题思路正确，但计算时将3写成了-3",
  "detailed_feedback": {
    "strengths": ["正确应用配方法", "步骤完整"],
    "errors": ["第三步计算错误"],
    "suggestions": ["注意符号", "验算结果"]
  },
  "knowledge_gaps": ["有理数运算"]
}
```

---

### D.3 学情分析

**数据收集**：
- 历史答题记录
- 准确率变化趋势
- 薄弱知识点统计
- 错题类型分布

**分析维度**：
```json
{
  "mastery_level": 75,
  "weak_points": ["配方法符号", "根的判别式"],
  "progress_trend": "improving",
  "recommendations": [
    "加强有理数运算练习",
    "复习配方法的符号规则"
  ],
  "focus_areas": ["基础计算", "公式记忆"]
}
```

**可视化展示**：
- 准确率折线图
- 知识点雷达图
- 难度分布饼图
- 错题分类柱状图

---

## 非功能性需求

### 性能要求
- OCR识别响应 < 10秒
- 内容生成响应 < 30秒
- 批改单题响应 < 5秒
- 系统并发用户 ≥ 10

### 可靠性要求
- 系统可用性 > 99%
- 数据不丢失
- 自动故障恢复
- 完整的日志记录

### 安全性要求
- API密钥加密存储
- 文件上传安全检查
- 防止注入攻击
- 访问权限控制

### 可维护性要求
- 代码注释覆盖率 > 80%
- 模块化设计
- 完整的单元测试
- API文档完整
