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
    corrected_text: str = Field(..., description="校验后的文本")
    metadata: Dict[str, Any] = Field(..., description="元数据（难度、标签等）")
    save_to_obsidian: bool = Field(default=True, description="是否保存到Obsidian")
    embed_in_anythingllm: bool = Field(default=True, description="是否嵌入AnythingLLM")
    
    child_name: str = Field(..., description="孩子姓名")
    subject: str = Field(..., description="学科")
    folder_type: Literal["no_problems", "wrong_problems", "cards", "courses"] = Field(
        ..., description="文件夹类型"
    )
    filename: str = Field(..., description="文件名")


class ValidationResponse(BaseModel):
    """校验响应"""
    success: bool
    obsidian_file_path: Optional[str] = None
    anythingllm_status: Optional[str] = None
    message: str


# =============================================================================
# 模块B: 存储管理
# =============================================================================

class ObsidianSaveRequest(BaseModel):
    """Obsidian保存请求"""
    child_name: str
    subject: str
    folder_type: Literal["no_problems", "wrong_problems", "cards", "courses"]
    filename: str
    content: str
    metadata: Dict[str, Any]


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
    additional_instructions: Optional[str] = Field(None, description="额外指示")
    
    # RAG检索参数
    retrieve_from_textbook: bool = Field(default=True, description="是否从教材检索")
    retrieve_from_wrong_problems: bool = Field(default=True, description="是否从错题检索")


class TeachingContentResponse(BaseModel):
    """教学内容响应"""
    content_id: str = Field(..., description="内容ID")
    marp_markdown: str = Field(..., description="Marp Markdown内容")
    preview_url: Optional[str] = Field(None, description="预览URL")
    knowledge_points_used: List[str] = Field(..., description="使用的知识点")
    estimated_duration: int = Field(..., description="预估时长(分钟)")
    created_at: datetime = Field(default_factory=datetime.now)


class TeachingContentApproval(BaseModel):
    """教学内容审批"""
    content_id: str = Field(..., description="内容ID")
    approved: bool = Field(..., description="是否批准")
    modifications: Optional[str] = Field(None, description="修改意见")


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
    total_points: int = Field(default=100, ge=1, le=200, description="总分")
    
    @validator('difficulty_distribution')
    def validate_difficulty_distribution(cls, v):
        for difficulty in v.keys():
            if not (1 <= difficulty <= 5):
                raise ValueError("难度必须在1-5之间")
        return v


class Question(BaseModel):
    """题目模型"""
    question_id: str
    question_text: str
    question_type: Literal["multiple_choice", "short_answer", "calculation", "proof"]
    difficulty: int = Field(..., ge=1, le=5)
    points: int
    options: Optional[List[str]] = None  # 仅选择题
    correct_answer: str
    solution: str
    grading_rubric: str
    knowledge_points: List[str]
    hint: Optional[str] = None


class AssessmentResponse(BaseModel):
    """评测响应"""
    assessment_id: str
    questions: List[Question]
    total_points: int
    created_at: datetime = Field(default_factory=datetime.now)


class GradingRequest(BaseModel):
    """批改请求"""
    assessment_id: str = Field(..., description="评测ID")
    question_id: str = Field(..., description="题目ID")
    student_answer: str = Field(..., description="学生答案")
    show_detailed_feedback: bool = Field(default=True, description="是否显示详细反馈")


class GradingResult(BaseModel):
    """批改结果"""
    question_id: str
    score: float
    max_score: int
    is_correct: bool
    correctness_rate: float = Field(..., ge=0.0, le=1.0)
    feedback: str
    detailed_feedback: Optional[Dict[str, Any]] = None
    knowledge_gaps: List[str]


class BatchGradingRequest(BaseModel):
    """批量批改请求"""
    assessment_id: str
    answers: List[Dict[str, str]]  # [{question_id: ..., student_answer: ...}]


# =============================================================================
# AnythingLLM模型
# =============================================================================

class EmbedDocumentRequest(BaseModel):
    """文档嵌入请求"""
    workspace_slug: str = Field(..., description="工作区slug")
    file_path: str = Field(..., description="文件路径")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


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
