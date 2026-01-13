"""
模块B - 存储管理端点

提供 Obsidian 和 AnythingLLM 的存储操作接口
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path

from app.models.schemas import (
    ObsidianSaveRequest,
    ObsidianSaveResponse,
    ObsidianUpdateMetadataRequest,
    ObsidianQueryRequest,
    ObsidianQueryResponse,
    EmbedDocumentRequest,
    EmbedDocumentResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    RAGQueryRequest,
    RAGQueryResponse
)
from app.services.obsidian_service import ObsidianService
from app.services.anythingllm_service import AnythingLLMService
from app.core.exceptions import (
    ObsidianStorageError,
    RAGServiceError,
    HLOSException
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 服务实例
obsidian_service = ObsidianService()
anythingllm_service = AnythingLLMService()


# ========== Obsidian 存储端点 ==========

@router.post("/obsidian/save", response_model=ObsidianSaveResponse)
async def save_to_obsidian(request: ObsidianSaveRequest):
    """
    保存内容到 Obsidian Vault

    支持四种文件夹类型：
    - No_Problems: 已校验的作业
    - Wrong_Problems: 错题本
    - Cards: 知识卡片
    - Courses: 教学课件

    Args:
        request: Obsidian 保存请求

    Returns:
        ObsidianSaveResponse: 保存结果，包含文件路径
    """
    logger.info(
        f"保存到 Obsidian - child: {request.child_name}, "
        f"subject: {request.subject}, folder: {request.folder_type}"
    )

    try:
        file_path = obsidian_service.save_markdown(
            child_name=request.child_name,
            subject=request.subject,
            folder_type=request.folder_type,
            filename=request.filename,
            content=request.content,
            metadata=request.metadata
        )

        logger.info(f"成功保存到 Obsidian: {file_path}")

        return ObsidianSaveResponse(
            success=True,
            message="成功保存到 Obsidian",
            file_path=str(file_path),
            absolute_path=str(file_path.absolute())
        )

    except Exception as e:
        logger.error(f"保存到 Obsidian 失败: {str(e)}", exc_info=True)
        raise ObsidianStorageError(
            f"保存到 Obsidian 失败: {str(e)}",
            details={
                "child_name": request.child_name,
                "subject": request.subject,
                "folder_type": request.folder_type
            }
        )


@router.put("/obsidian/metadata", response_model=Dict[str, Any])
async def update_obsidian_metadata(request: ObsidianUpdateMetadataRequest):
    """
    更新 Obsidian 文件的 Frontmatter 元数据

    Args:
        request: 元数据更新请求

    Returns:
        更新结果
    """
    logger.info(f"更新 Obsidian 元数据 - file: {request.file_path}")

    try:
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise ObsidianStorageError(
                f"文件不存在: {request.file_path}",
                error_code="FILE_NOT_FOUND",
                status_code=404
            )

        obsidian_service.update_metadata(file_path, request.metadata_updates)

        logger.info(f"成功更新元数据: {request.file_path}")

        return {
            "success": True,
            "message": "元数据更新成功",
            "file_path": str(file_path),
            "updated_fields": list(request.metadata_updates.keys())
        }

    except ObsidianStorageError:
        raise
    except Exception as e:
        logger.error(f"更新元数据失败: {str(e)}", exc_info=True)
        raise ObsidianStorageError(
            f"更新元数据失败: {str(e)}",
            details={"file_path": request.file_path}
        )


@router.post("/obsidian/query", response_model=ObsidianQueryResponse)
async def query_obsidian(request: ObsidianQueryRequest):
    """
    查询 Obsidian 中的文件（按元数据筛选）

    Args:
        request: 查询请求

    Returns:
        ObsidianQueryResponse: 查询结果列表
    """
    logger.info(
        f"查询 Obsidian - child: {request.child_name}, "
        f"subject: {request.subject}, folder: {request.folder_type}"
    )

    try:
        # 根据查询类型调用不同方法
        if request.folder_type == "Wrong_Problems":
            results = obsidian_service.get_wrong_problems(
                child_name=request.child_name,
                subject=request.subject,
                min_difficulty=request.filters.get("min_difficulty"),
                max_accuracy=request.filters.get("max_accuracy")
            )
        else:
            # 通用查询（未来实现）
            results = []
            logger.warning(f"通用查询功能尚未实现: {request.folder_type}")

        logger.info(f"查询完成 - 找到 {len(results)} 条结果")

        return ObsidianQueryResponse(
            success=True,
            total_count=len(results),
            results=results
        )

    except Exception as e:
        logger.error(f"查询失败: {str(e)}", exc_info=True)
        raise ObsidianStorageError(
            f"查询失败: {str(e)}",
            details={
                "child_name": request.child_name,
                "subject": request.subject
            }
        )


# ========== AnythingLLM (RAG) 端点 ==========

@router.post("/anythingllm/workspace", response_model=WorkspaceResponse)
async def create_workspace(request: WorkspaceCreateRequest):
    """
    创建 AnythingLLM 工作区

    Args:
        request: 工作区创建请求

    Returns:
        WorkspaceResponse: 工作区信息
    """
    logger.info(f"创建工作区 - name: {request.name}")

    try:
        workspace = await anythingllm_service.create_workspace(
            name=request.name,
            child_name=request.child_name,
            subject=request.subject
        )

        logger.info(f"工作区创建成功 - slug: {workspace.get('slug')}")

        return WorkspaceResponse(
            success=True,
            message="工作区创建成功",
            workspace=workspace
        )

    except Exception as e:
        logger.error(f"创建工作区失败: {str(e)}", exc_info=True)
        raise RAGServiceError(
            f"创建工作区失败: {str(e)}",
            details={"name": request.name}
        )


@router.get("/anythingllm/workspace/{slug}", response_model=WorkspaceResponse)
async def get_workspace(slug: str):
    """
    获取工作区信息

    Args:
        slug: 工作区 slug

    Returns:
        WorkspaceResponse: 工作区信息
    """
    logger.info(f"获取工作区信息 - slug: {slug}")

    try:
        workspace = await anythingllm_service.get_workspace(slug)

        return WorkspaceResponse(
            success=True,
            message="获取工作区信息成功",
            workspace=workspace
        )

    except Exception as e:
        logger.error(f"获取工作区失败: {str(e)}", exc_info=True)
        raise RAGServiceError(
            f"获取工作区失败: {str(e)}",
            error_code="WORKSPACE_NOT_FOUND",
            status_code=404,
            details={"slug": slug}
        )


@router.post("/anythingllm/embed", response_model=EmbedDocumentResponse)
async def embed_document(request: EmbedDocumentRequest):
    """
    将文档嵌入到 AnythingLLM 工作区

    Args:
        request: 嵌入请求

    Returns:
        EmbedDocumentResponse: 嵌入结果
    """
    logger.info(
        f"嵌入文档 - workspace: {request.workspace_slug}, "
        f"file: {request.file_path}"
    )

    try:
        # 确保工作区存在
        try:
            await anythingllm_service.get_workspace(request.workspace_slug)
        except Exception:
            logger.info(f"工作区不存在，正在创建: {request.workspace_slug}")
            await anythingllm_service.create_workspace(
                name=request.workspace_slug.replace("_", " ").title(),
                child_name=request.metadata.get("child_name", ""),
                subject=request.metadata.get("subject", "")
            )

        # 嵌入文档
        result = await anythingllm_service.embed_document(
            workspace_slug=request.workspace_slug,
            file_path=request.file_path,
            metadata=request.metadata
        )

        logger.info(f"文档嵌入成功: {request.file_path}")

        return EmbedDocumentResponse(
            success=True,
            message="文档嵌入成功",
            workspace_slug=request.workspace_slug,
            document_id=result.get("document_id"),
            embedding_status=result.get("status", "completed")
        )

    except Exception as e:
        logger.error(f"文档嵌入失败: {str(e)}", exc_info=True)
        raise RAGServiceError(
            f"文档嵌入失败: {str(e)}",
            details={
                "workspace_slug": request.workspace_slug,
                "file_path": request.file_path
            }
        )


@router.post("/anythingllm/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """
    在 AnythingLLM 工作区中进行 RAG 检索

    Args:
        request: RAG 查询请求

    Returns:
        RAGQueryResponse: 检索结果
    """
    logger.info(
        f"RAG 检索 - workspace: {request.workspace_slug}, "
        f"query: {request.query[:50]}..."
    )

    try:
        result = await anythingllm_service.query(
            workspace_slug=request.workspace_slug,
            query=request.query,
            top_k=request.top_k
        )

        logger.info(
            f"RAG 检索完成 - 返回 {len(result.get('sources', []))} 条结果"
        )

        return RAGQueryResponse(
            success=True,
            query=request.query,
            response=result.get("response", ""),
            sources=result.get("sources", []),
            context=result.get("context", "")
        )

    except Exception as e:
        logger.error(f"RAG 检索失败: {str(e)}", exc_info=True)
        raise RAGServiceError(
            f"RAG 检索失败: {str(e)}",
            details={
                "workspace_slug": request.workspace_slug,
                "query": request.query
            }
        )


# ========== 统计与健康检查 ==========

@router.get("/stats", response_model=Dict[str, Any])
async def get_storage_stats(
    child_name: Optional[str] = Query(None, description="孩子姓名"),
    subject: Optional[str] = Query(None, description="学科")
):
    """
    获取存储统计信息

    Args:
        child_name: 可选的孩子姓名过滤
        subject: 可选的学科过滤

    Returns:
        存储统计数据
    """
    logger.info(f"获取存储统计 - child: {child_name}, subject: {subject}")

    try:
        # Obsidian 统计
        obsidian_stats = {
            "total_files": 0,
            "by_folder_type": {},
            "total_size_bytes": 0
        }

        # TODO: 实现实际统计逻辑
        # 需要遍历 Obsidian Vault 并统计文件数量

        # AnythingLLM 统计
        anythingllm_stats = {
            "total_workspaces": 0,
            "total_documents": 0
        }

        # TODO: 调用 AnythingLLM API 获取统计

        return {
            "success": True,
            "obsidian": obsidian_stats,
            "anythingllm": anythingllm_stats,
            "filters": {
                "child_name": child_name,
                "subject": subject
            }
        }

    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
