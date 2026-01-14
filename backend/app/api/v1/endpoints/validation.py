"""
模块A - 家长校验端点

提供人工校验后的数据提交功能，将校验后的内容保存到 Obsidian 和 AnythingLLM
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pathlib import Path

from app.models.schemas import ValidationSubmission, ValidationResponse
from app.services.obsidian_service import ObsidianService
from app.services.anythingllm_service import AnythingLLMService
from app.core.exceptions import (
    HLOSException,
    ObsidianStorageError,
    RAGServiceError
)
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# 服务实例
obsidian_service = ObsidianService()
anythingllm_service = AnythingLLMService()


@router.post("/submit", response_model=ValidationResponse)
async def submit_validation(
    submission: ValidationSubmission,
    background_tasks: BackgroundTasks
):
    """
    提交家长校验后的数据

    工作流程：
    1. 保存到 Obsidian（带 Frontmatter 元数据）
    2. 嵌入到 AnythingLLM（后台异步任务）
    3. 返回保存结果

    Args:
        submission: 校验提交数据
        background_tasks: FastAPI 后台任务

    Returns:
        ValidationResponse: 保存结果，包含文件路径和嵌入状态
    """
    logger.info(
        f"收到校验提交请求 - task_id: {submission.task_id}, "
        f"child: {submission.child_name}, subject: {submission.subject}"
    )

    try:
        # 1. 保存到 Obsidian
        obsidian_file_path = None
        if submission.save_to_obsidian:
            try:
                obsidian_file_path = obsidian_service.save_markdown(
                    child_name=submission.child_name,
                    subject=submission.subject,
                    folder_type=submission.folder_type,
                    filename=submission.filename or f"task_{submission.task_id}",
                    content=submission.corrected_content,
                    metadata=submission.metadata
                )
                logger.info(f"成功保存到 Obsidian: {obsidian_file_path}")
            except Exception as e:
                logger.error(f"保存到 Obsidian 失败: {str(e)}", exc_info=True)
                raise ObsidianStorageError(
                    f"保存到 Obsidian 失败: {str(e)}",
                    details={"task_id": submission.task_id}
                )

        # 2. 嵌入到 AnythingLLM（后台任务，避免阻塞响应）
        embedding_status = "skipped"
        if submission.embed_in_anythingllm and obsidian_file_path:
            try:
                # 确定工作区 slug
                workspace_slug = _get_workspace_slug(
                    submission.child_name,
                    submission.subject,
                    submission.folder_type
                )

                # 添加后台任务
                background_tasks.add_task(
                    _embed_to_anythingllm,
                    workspace_slug=workspace_slug,
                    file_path=obsidian_file_path,
                    metadata=submission.metadata,
                    task_id=submission.task_id
                )
                embedding_status = "queued"
                logger.info(f"已添加 AnythingLLM 嵌入任务: {workspace_slug}")
            except Exception as e:
                logger.warning(f"添加嵌入任务失败（非致命错误）: {str(e)}")
                embedding_status = "failed"

        # 3. 返回响应
        return ValidationResponse(
            success=True,
            message="校验数据已成功保存",
            task_id=submission.task_id,
            obsidian_file_path=str(obsidian_file_path) if obsidian_file_path else None,
            embedding_status=embedding_status
        )

    except ObsidianStorageError:
        raise
    except Exception as e:
        logger.error(f"校验提交处理失败: {str(e)}", exc_info=True)
        raise HLOSException(
            message=f"校验提交处理失败: {str(e)}",
            error_code="VALIDATION_SUBMIT_ERROR",
            status_code=500,
            details={"task_id": submission.task_id}
        )


@router.post("/batch-submit", response_model=Dict[str, Any])
async def batch_submit_validation(
    submissions: list[ValidationSubmission],
    background_tasks: BackgroundTasks
):
    """
    批量提交校验数据（用于多题目场景）

    Args:
        submissions: 多个校验提交数据
        background_tasks: FastAPI 后台任务

    Returns:
        批量处理结果统计
    """
    logger.info(f"收到批量校验提交请求 - 数量: {len(submissions)}")

    results = {
        "total": len(submissions),
        "success": 0,
        "failed": 0,
        "details": []
    }

    for submission in submissions:
        try:
            response = await submit_validation(submission, background_tasks)
            results["success"] += 1
            results["details"].append({
                "task_id": submission.task_id,
                "status": "success",
                "file_path": response.obsidian_file_path
            })
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "task_id": submission.task_id,
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"批量提交中的单项失败 - task_id: {submission.task_id}, error: {str(e)}")

    logger.info(
        f"批量校验提交完成 - 成功: {results['success']}, 失败: {results['failed']}"
    )

    return results


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_validation_status(task_id: str):
    """
    查询校验任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    # TODO: 实现基于 Redis 的任务状态查询
    # 当前为占位实现
    logger.info(f"查询校验状态 - task_id: {task_id}")

    return {
        "task_id": task_id,
        "status": "completed",
        "message": "任务状态查询功能开发中"
    }


# ========== 辅助函数 ==========

def _get_workspace_slug(child_name: str, subject: str, folder_type: str) -> str:
    """
    根据内容类型确定 AnythingLLM 工作区 slug

    规则：
    - No_Problems, Wrong_Problems → {child_name}_{subject}_homework
    - Cards → {child_name}_{subject}_cards
    - Courses → {child_name}_{subject}_courses
    - 其他 → {child_name}_{subject}_general
    """
    folder_type_mapping = {
        "No_Problems": "homework",
        "Wrong_Problems": "homework",
        "Cards": "cards",
        "Courses": "courses"
    }

    workspace_type = folder_type_mapping.get(folder_type, "general")
    slug = f"{child_name}_{subject}_{workspace_type}".lower().replace(" ", "_")

    return slug


async def _embed_to_anythingllm(
    workspace_slug: str,
    file_path: Path,
    metadata: Dict[str, Any],
    task_id: str
):
    """
    后台任务：将文件嵌入到 AnythingLLM

    Args:
        workspace_slug: 工作区 slug
        file_path: 文件路径
        metadata: 元数据
        task_id: 任务ID
    """
    try:
        logger.info(f"开始嵌入任务 - task_id: {task_id}, workspace: {workspace_slug}")

        # 1. 确保工作区存在
        try:
            await anythingllm_service.get_workspace(workspace_slug)
        except Exception:
            # 工作区不存在，创建新工作区
            logger.info(f"工作区不存在，正在创建: {workspace_slug}")
            await anythingllm_service.create_workspace(
                name=workspace_slug.replace("_", " ").title(),
                child_name=metadata.get("child_name", ""),
                subject=metadata.get("subject", "")
            )

        # 2. 嵌入文档（使用索引链接方式）
        # 根据存储分级策略：校验后作业、错题、知识卡片都使用"索引链接"方式
        result = await anythingllm_service.embed_document(
            workspace_slug=workspace_slug,
            file_path=str(file_path),
            metadata={
                **metadata,
                "task_id": task_id,
                "embedded_at": "auto_generated"
            },
            index_only=True  # 仅创建索引链接，不全量嵌入
        )

        logger.info(f"索引链接创建完成 - task_id: {task_id}, result: {result}")

    except Exception as e:
        logger.error(
            f"嵌入任务失败 - task_id: {task_id}, error: {str(e)}",
            exc_info=True
        )
        # 后台任务失败不抛出异常，只记录日志
