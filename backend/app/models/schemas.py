"""
Pydantic数据模型
定义所有API的请求和响应模型
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator


# =============================================================================
# 通用模型
# =============================================================================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool] = {}


class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# =============================================================================
# 模块A: 感知与校验
# =============================================================================

class PhotoUploadRequest(BaseModel):
    """图片上传请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    content_type: Literal["homework", "test", "textbook", "worksheet"] = Field(
        ..., description="内容类型"
    )


class OCRTaskResponse(BaseModel):
    """OCR任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: Literal["processing", "completed", "failed"] = Field(..., description="状态")
    message: str = Field(default="", description="消息")


class OCRResult(BaseModel):
    """OCR识别结果"""
    task_id: str
    status: Literal["processing", "completed", "failed"]
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    original_image_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class ValidationSubmission(BaseModel):
    """家长校验提交"""
    task_id: str = Field(..., description="OCR任务ID")
    corrected_content: str = Field(..., description="校验后的内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据（难度、标签等）")
    save_to_obsidian: bool = Field(default=True, description="是否保存到Obsidian")
    embed_in_anythingllm: bool = Field(default=True, description="是否嵌入AnythingLLM")

    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    folder_type: Literal["No_Problems", "Wrong_Problems", "Cards", "Courses"] = Field(
        ..., description="文件夹类型"
    )
    filename: Optional[str] = Field(None, description="文件名（可选，默认使用task_id）")


class ValidationResponse(BaseModel):
    """校验响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    task_id: str = Field(..., description="任务ID")
    obsidian_file_path: Optional[str] = Field(None, description="Obsidian文件路径")
    embedding_status: Optional[str] = Field(None, description="嵌入状态：queued/skipped/failed")


# =============================================================================
# 模块B: 存储管理
# =============================================================================

class ObsidianSaveRequest(BaseModel):
    """Obsidian保存请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    folder_type: Literal["No_Problems", "Wrong_Problems", "Cards", "Courses"] = Field(
        ..., description="文件夹类型"
    )
    filename: str = Field(..., description="文件名")
    content: str = Field(..., description="内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ObsidianSaveResponse(BaseModel):
    """Obsidian保存响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    file_path: str = Field(..., description="文件路径")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class ObsidianUpdateMetadataRequest(BaseModel):
    """Obsidian更新元数据请求"""
    file_path: str = Field(..., description="文件路径")
    metadata: Dict[str, Any] = Field(..., description="要更新的元数据")


class ObsidianQueryRequest(BaseModel):
    """Obsidian查询请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: Optional[str] = Field(None, description="学科")
    folder_type: Optional[str] = Field(None, description="文件夹类型")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class ObsidianQueryResponse(BaseModel):
    """Obsidian查询响应"""
    total: int = Field(..., description="总数")
    files: List[Dict[str, Any]] = Field(..., description="文件列表")


class ObsidianSearchRequest(BaseModel):
    """Obsidian搜索请求"""
    child_name: str
    subject: Optional[str] = None
    folder_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class ObsidianFileResponse(BaseModel):
    """Obsidian文件响应"""
    metadata: Dict[str, Any]
    content: str
    file_path: str
    filename: str


class WrongProblemsRequest(BaseModel):
    """错题查询请求"""
    child_name: str
    subject: str
    min_difficulty: Optional[int] = Field(None, ge=1, le=5)
    max_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    limit: Optional[int] = Field(None, ge=1, le=100)


# =============================================================================
# 模块C: 教学内容生成
# =============================================================================

class TeachingContentRequest(BaseModel):
    """教学内容生成请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    knowledge_points: List[str] = Field(..., min_items=1, description="知识点列表")
    difficulty: int = Field(..., ge=1, le=5, description="难度等级(1-5)")
    style: Literal["启发式", "费曼式", "详解式"] = Field(..., description="教学风格")
    duration_minutes: int = Field(..., ge=5, le=120, description="目标时长(分钟)")
    additional_requirements: Optional[str] = Field(None, description="额外要求")

    # RAG检索参数
    use_rag: bool = Field(default=True, description="是否使用RAG检索")
    rag_top_k: int = Field(default=5, ge=1, le=20, description="RAG检索top-k数量")


class TeachingContentResponse(BaseModel):
    """教学内容响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    preview_id: str = Field(..., description="预览ID")
    knowledge_points: List[str] = Field(..., description="知识点")
    estimated_duration: int = Field(..., description="预估时长(分钟)")
    preview_url: str = Field(..., description="预览URL")


class TeachingContentApproval(BaseModel):
    """教学内容审批"""
    content_id: str = Field(..., description="内容ID")
    approved: bool = Field(..., description="是否批准")
    modifications: Optional[str] = Field(None, description="修改意见")


class TeachingContentPreview(BaseModel):
    """教学内容预览"""
    preview_id: str = Field(..., description="预览ID")
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    knowledge_points: List[str] = Field(..., description="知识点列表")
    difficulty: int = Field(..., description="难度等级")
    style: str = Field(..., description="教学风格")
    duration_minutes: int = Field(..., description="目标时长")
    marp_content: str = Field(..., description="Marp内容")
    rag_context_used: bool = Field(default=False, description="是否使用了RAG上下文")
    created_at: str = Field(..., description="创建时间")


class TeachingContentApprovalRequest(BaseModel):
    """教学内容审批请求"""
    preview_id: str = Field(..., description="预览ID")
    approved: bool = Field(..., description="是否批准")
    modifications: Optional[str] = Field(None, description="修改意见")
    rejection_reason: Optional[str] = Field(None, description="拒绝原因")


class TeachingContentApprovalResponse(BaseModel):
    """教学内容审批响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    preview_id: str = Field(..., description="预览ID")
    approved: bool = Field(..., description="是否批准")
    obsidian_file_path: Optional[str] = Field(None, description="Obsidian文件路径")
    rejection_reason: Optional[str] = Field(None, description="拒绝原因")
    embedding_status: Optional[str] = Field(None, description="嵌入状态：index_created/failed/not_attempted")


# =============================================================================
# 模块D: 评测引擎
# =============================================================================

class AssessmentGenerationRequest(BaseModel):
    """评测生成请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    topic_range: List[str] = Field(..., min_items=1, description="考察范围")
    difficulty_distribution: Dict[int, int] = Field(
        ..., description="难度分布 {难度: 题数}"
    )
    question_types: List[Literal["multiple_choice", "short_answer", "calculation", "proof"]] = Field(
        ..., min_items=1, description="题型"
    )
    total_problems: int = Field(..., ge=1, le=50, description="题目总数")
    prevent_search: bool = Field(default=True, description="防搜索（生成原创题目）")
    include_detailed_solution: bool = Field(default=True, description="包含详细解答")

    @validator('difficulty_distribution')
    def validate_difficulty_distribution(cls, v):
        for difficulty in v.keys():
            if not (1 <= difficulty <= 5):
                raise ValueError("难度必须在1-5之间")
        return v


class Problem(BaseModel):
    """题目模型"""
    problem_id: str = Field(..., description="题目ID")
    problem_text: str = Field(..., description="题目内容")
    problem_type: Literal["multiple_choice", "short_answer", "calculation", "proof"] = Field(
        ..., description="题型"
    )
    difficulty: int = Field(..., ge=1, le=5, description="难度等级")
    points: int = Field(..., description="分值")
    options: Optional[List[str]] = Field(None, description="选项（仅选择题）")
    correct_answer: str = Field(..., description="正确答案")
    solution: str = Field(..., description="详细解答")
    grading_rubric: str = Field(..., description="评分标准")
    knowledge_points: List[str] = Field(..., description="知识点")
    hint: Optional[str] = Field(None, description="提示")


class AssessmentGenerationResponse(BaseModel):
    """评测生成响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    assessment_id: str = Field(..., description="评测ID")
    problems: List[Problem] = Field(..., description="题目列表")
    total_problems: int = Field(..., description="题目总数")
    created_at: str = Field(..., description="创建时间")


class AssessmentGradingRequest(BaseModel):
    """评测批改请求"""
    assessment_id: str = Field(..., description="评测ID")
    problem_id: str = Field(..., description="题目ID")
    student_answer_text: Optional[str] = Field(None, description="学生答案文本")
    student_answer_image: Optional[str] = Field(None, description="学生答案图片路径")
    show_detailed_feedback: bool = Field(default=True, description="是否显示详细反馈")


class AssessmentGradingResponse(BaseModel):
    """评测批改响应"""
    success: bool = Field(..., description="是否成功")
    problem_id: str = Field(..., description="题目ID")
    score: float = Field(..., description="得分")
    max_score: int = Field(..., description="满分")
    is_correct: bool = Field(..., description="是否正确")
    correctness_rate: float = Field(..., ge=0.0, le=1.0, description="正确率")
    feedback: str = Field(..., description="反馈")
    detailed_feedback: Optional[Dict[str, Any]] = Field(None, description="详细反馈")
    knowledge_gaps: List[str] = Field(default_factory=list, description="知识漏洞")


class LearningAnalyticsRequest(BaseModel):
    """学情分析请求"""
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    time_range_days: int = Field(default=30, ge=1, le=365, description="时间范围（天）")


class LearningAnalyticsResponse(BaseModel):
    """学情分析响应"""
    success: bool = Field(..., description="是否成功")
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    total_problems_attempted: int = Field(..., description="尝试题目总数")
    correct_count: int = Field(..., description="正确数量")
    wrong_count: int = Field(..., description="错误数量")
    average_score: float = Field(..., description="平均分")
    mastery_level: float = Field(..., ge=0.0, le=100.0, description="掌握程度(%)")
    weak_points: List[str] = Field(..., description="薄弱知识点")
    progress_trend: Literal["improving", "stable", "declining"] = Field(..., description="进步趋势")
    recommendations: List[str] = Field(..., description="学习建议")


# =============================================================================
# AnythingLLM模型
# =============================================================================

class EmbedDocumentRequest(BaseModel):
    """文档嵌入请求"""
    workspace_slug: str = Field(..., description="工作区slug")
    file_path: str = Field(..., description="文件路径")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    index_only: bool = Field(default=False, description="仅创建索引链接，不全量嵌入")


class EmbedDocumentResponse(BaseModel):
    """文档嵌入响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    document_id: Optional[str] = Field(None, description="文档ID")
    workspace_slug: str = Field(..., description="工作区slug")


class WorkspaceCreateRequest(BaseModel):
    """工作区创建请求"""
    name: str = Field(..., description="工作区名称")
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")


class WorkspaceResponse(BaseModel):
    """工作区响应"""
    slug: str = Field(..., description="工作区slug")
    name: str = Field(..., description="工作区名称")
    created_at: Optional[str] = Field(None, description="创建时间")
    documents_count: Optional[int] = Field(None, description="文档数量")


class RAGQueryRequest(BaseModel):
    """RAG检索请求"""
    workspace_slug: str = Field(..., description="工作区slug")
    query: str = Field(..., description="查询内容")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量")


class RAGQueryResponse(BaseModel):
    """RAG检索响应"""
    query: str = Field(..., description="查询内容")
    context: str = Field(..., description="检索到的上下文")
    sources: List[Dict[str, Any]] = Field(..., description="来源列表")


class QueryRequest(BaseModel):
    """RAG检索请求"""
    workspace_slug: str = Field(..., description="工作区slug")
    query: str = Field(..., description="查询内容")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量")


class QueryResponse(BaseModel):
    """RAG检索响应"""
    query: str
    context: str
    sources: List[Dict[str, Any]]


# =============================================================================
# 统计与分析
# =============================================================================

class LearningStatistics(BaseModel):
    """学习统计"""
    child_name: str
    subject: str
    total_problems: int
    wrong_problems: int
    knowledge_cards: int
    courses_completed: int
    average_accuracy: float
    difficulty_distribution: Dict[int, int]
    weak_points: List[str]
    recent_progress: List[Dict[str, Any]]


class AnalysisRequest(BaseModel):
    """学情分析请求"""
    child_name: str
    subject: str
    knowledge_point: str
    time_range_days: int = Field(default=30, ge=1, le=365)


class AnalysisResponse(BaseModel):
    """学情分析响应"""
    mastery_level: float = Field(..., ge=0.0, le=100.0, description="掌握程度(%)")
    weak_points: List[str]
    progress_trend: Literal["improving", "stable", "declining"]
    recommendations: List[str]
    focus_areas: List[str]
