"""
模块C - 教学内容生成端点

基于 RAG 检索和 Claude 生成个性化教学内容（Marp 格式课件）
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime

from app.models.schemas import (
    TeachingContentRequest,
    TeachingContentResponse,
    TeachingContentApprovalRequest,
    TeachingContentApprovalResponse,
    TeachingContentPreview
)
from app.services.claude_service import ClaudeService
from app.services.anythingllm_service import AnythingLLMService
from app.services.obsidian_service import ObsidianService
from app.core.exceptions import (
    ClaudeServiceError,
    RAGServiceError,
    ObsidianStorageError,
    HLOSException
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 服务实例
claude_service = ClaudeService()
anythingllm_service = AnythingLLMService()
obsidian_service = ObsidianService()

# 内存缓存用于预览（生产环境应使用 Redis）
preview_cache: Dict[str, TeachingContentPreview] = {}


@router.post("/generate", response_model=TeachingContentResponse)
async def generate_teaching_content(request: TeachingContentRequest):
    """
    生成教学内容（Marp 格式课件）

    工作流程：
    1. 根据知识点从 AnythingLLM 检索相关教材内容（RAG）
    2. 使用 Claude 生成 Marp 格式的教学课件
    3. 返回预览 ID 供家长审批

    Args:
        request: 教学内容生成请求

    Returns:
        TeachingContentResponse: 生成结果和预览 ID
    """
    logger.info(
        f"生成教学内容 - knowledge_points: {request.knowledge_points}, "
        f"difficulty: {request.difficulty}, style: {request.style}"
    )

    try:
        # 1. RAG 检索相关教材内容
        context_from_rag = ""
        if request.use_rag:
            try:
                # 构建工作区 slug（教材通常存储在 textbooks 工作区）
                workspace_slug = f"{request.child_name}_textbooks".lower().replace(" ", "_")

                # 构建检索查询
                rag_query = f"查找关于以下知识点的教材内容：{', '.join(request.knowledge_points)}"

                logger.info(f"RAG 检索 - workspace: {workspace_slug}, query: {rag_query}")

                rag_result = await anythingllm_service.query(
                    workspace_slug=workspace_slug,
                    query=rag_query,
                    top_k=request.rag_top_k
                )

                context_from_rag = rag_result.get("context", "")
                logger.info(f"RAG 检索完成 - 上下文长度: {len(context_from_rag)} 字符")

            except Exception as e:
                logger.warning(f"RAG 检索失败（将继续生成但无上下文）: {str(e)}")
                context_from_rag = ""

        # 2. 使用 Claude 生成教学内容
        try:
            marp_content = await claude_service.generate_teaching_content(
                knowledge_points=request.knowledge_points,
                context_from_rag=context_from_rag,
                difficulty=request.difficulty,
                style=request.style,
                duration_minutes=request.duration_minutes,
                additional_requirements=request.additional_requirements
            )

            logger.info(f"教学内容生成完成 - 长度: {len(marp_content)} 字符")

        except Exception as e:
            logger.error(f"Claude 生成失败: {str(e)}", exc_info=True)
            raise ClaudeServiceError(
                f"教学内容生成失败: {str(e)}",
                details={
                    "knowledge_points": request.knowledge_points,
                    "difficulty": request.difficulty
                }
            )

        # 3. 创建预览 ID 并缓存内容
        preview_id = f"teaching_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.child_name}"

        preview = TeachingContentPreview(
            preview_id=preview_id,
            child_name=request.child_name,
            subject=request.subject,
            knowledge_points=request.knowledge_points,
            difficulty=request.difficulty,
            style=request.style,
            duration_minutes=request.duration_minutes,
            marp_content=marp_content,
            rag_context_used=context_from_rag != "",
            created_at=datetime.now().isoformat()
        )

        preview_cache[preview_id] = preview
        logger.info(f"预览已缓存 - preview_id: {preview_id}")

        # 4. 返回响应
        return TeachingContentResponse(
            success=True,
            message="教学内容生成成功，请预览并审批",
            preview_id=preview_id,
            knowledge_points=request.knowledge_points,
            estimated_duration=request.duration_minutes,
            preview_url=f"/api/v1/teaching/preview/{preview_id}"
        )

    except ClaudeServiceError:
        raise
    except Exception as e:
        logger.error(f"生成教学内容失败: {str(e)}", exc_info=True)
        raise HLOSException(
            message=f"生成教学内容失败: {str(e)}",
            error_code="TEACHING_GENERATION_ERROR",
            status_code=500,
            details={"knowledge_points": request.knowledge_points}
        )


@router.get("/preview/{preview_id}", response_model=TeachingContentPreview)
async def get_teaching_preview(preview_id: str):
    """
    获取教学内容预览

    Args:
        preview_id: 预览 ID

    Returns:
        TeachingContentPreview: 预览内容
    """
    logger.info(f"获取教学内容预览 - preview_id: {preview_id}")

    if preview_id not in preview_cache:
        logger.warning(f"预览不存在或已过期: {preview_id}")
        raise HTTPException(
            status_code=404,
            detail=f"预览不存在或已过期: {preview_id}"
        )

    return preview_cache[preview_id]


@router.post("/approve", response_model=TeachingContentApprovalResponse)
async def approve_teaching_content(request: TeachingContentApprovalRequest):
    """
    家长审批教学内容并保存到 Obsidian

    工作流程：
    1. 从缓存中获取预览内容
    2. 可选地应用家长的修改意见
    3. 保存到 Obsidian 的 Courses 文件夹
    4. 清除预览缓存

    Args:
        request: 审批请求

    Returns:
        TeachingContentApprovalResponse: 审批结果
    """
    logger.info(
        f"审批教学内容 - preview_id: {request.preview_id}, "
        f"approved: {request.approved}"
    )

    # 1. 获取预览内容
    if request.preview_id not in preview_cache:
        raise HTTPException(
            status_code=404,
            detail=f"预览不存在或已过期: {request.preview_id}"
        )

    preview = preview_cache[request.preview_id]

    # 2. 如果未通过审批，只返回结果不保存
    if not request.approved:
        logger.info(f"教学内容未通过审批: {request.preview_id}")
        return TeachingContentApprovalResponse(
            success=True,
            message="教学内容已拒绝",
            preview_id=request.preview_id,
            approved=False,
            rejection_reason=request.rejection_reason
        )

    try:
        # 3. 应用修改意见（如果有）
        final_content = preview.marp_content
        if request.modifications:
            logger.info(f"应用修改意见: {request.modifications[:100]}...")
            # TODO: 可以使用 Claude 来应用修改意见
            # 当前直接附加修改说明
            final_content += f"\n\n---\n\n## 家长修改意见\n\n{request.modifications}"

        # 4. 保存到 Obsidian
        filename = f"{'_'.join(preview.knowledge_points)}_{datetime.now().strftime('%Y%m%d')}"

        metadata = {
            "Knowledge_Points": preview.knowledge_points,
            "Difficulty": preview.difficulty,
            "Style": preview.style,
            "Duration_Minutes": preview.duration_minutes,
            "RAG_Context_Used": preview.rag_context_used,
            "Approved_At": datetime.now().isoformat(),
            "Approved_By": "家长"
        }

        file_path = obsidian_service.save_markdown(
            child_name=preview.child_name,
            subject=preview.subject,
            folder_type="Courses",
            filename=filename,
            content=final_content,
            metadata=metadata
        )

        logger.info(f"教学内容已保存到 Obsidian: {file_path}")

        # 5. 清除预览缓存
        del preview_cache[request.preview_id]

        return TeachingContentApprovalResponse(
            success=True,
            message="教学内容已审批并保存",
            preview_id=request.preview_id,
            approved=True,
            obsidian_file_path=str(file_path)
        )

    except Exception as e:
        logger.error(f"审批处理失败: {str(e)}", exc_info=True)
        raise ObsidianStorageError(
            f"保存教学内容失败: {str(e)}",
            details={"preview_id": request.preview_id}
        )


@router.delete("/preview/{preview_id}", response_model=Dict[str, Any])
async def delete_teaching_preview(preview_id: str):
    """
    删除教学内容预览（取消生成）

    Args:
        preview_id: 预览 ID

    Returns:
        删除结果
    """
    logger.info(f"删除教学内容预览 - preview_id: {preview_id}")

    if preview_id in preview_cache:
        del preview_cache[preview_id]
        return {
            "success": True,
            "message": "预览已删除",
            "preview_id": preview_id
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"预览不存在: {preview_id}"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_teaching_history(
    child_name: str,
    subject: Optional[str] = None,
    limit: int = 20
):
    """
    获取教学内容历史记录

    Args:
        child_name: 孩子姓名
        subject: 可选的学科过滤
        limit: 返回数量限制

    Returns:
        历史记录列表
    """
    logger.info(f"获取教学历史 - child: {child_name}, subject: {subject}")

    try:
        # TODO: 从 Obsidian Courses 文件夹读取历史记录
        # 当前为占位实现

        return {
            "success": True,
            "child_name": child_name,
            "subject": subject,
            "total_count": 0,
            "history": [],
            "message": "历史记录功能开发中"
        }

    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
