"""
AnythingLLM服务
负责与AnythingLLM RAG引擎的交互，实现文档嵌入和检索功能
"""

import httpx
from typing import List, Dict, Any, Optional
import logging
import json
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class AnythingLLMService:
    """AnythingLLM RAG服务"""

    def __init__(self):
        """初始化AnythingLLM服务"""
        self.base_url = settings.ANYTHINGLLM_URL
        self.api_key = settings.ANYTHINGLLM_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=60.0
        )
        logger.info(f"AnythingLLMService initialized with base URL: {self.base_url}")

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

    # =========================================================================
    # 工作区管理
    # =========================================================================

    async def create_workspace(
        self,
        name: str,
        child_name: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        创建工作区

        Args:
            name: 工作区名称
            child_name: 孩子姓名
            subject: 学科

        Returns:
            Dict: 工作区信息
        """
        try:
            slug = f"{child_name.lower().replace(' ', '-')}_{subject.lower()}"

            response = await self.client.post(
                "/api/workspace/new",
                json={
                    "name": name,
                    "slug": slug
                }
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Created workspace: {slug}")
            return result.get("workspace", {})

        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            raise

    async def get_workspace(self, slug: str) -> Optional[Dict[str, Any]]:
        """获取工作区信息"""
        try:
            response = await self.client.get(f"/api/workspace/{slug}")
            if response.status_code == 200:
                return response.json().get("workspace")
            return None
        except Exception as e:
            logger.error(f"Failed to get workspace {slug}: {e}")
            return None

    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """列出所有工作区"""
        try:
            response = await self.client.get("/api/workspaces")
            response.raise_for_status()
            return response.json().get("workspaces", [])
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            return []

    async def ensure_workspace(
        self,
        slug: str,
        name: Optional[str] = None,
        child_name: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        确保工作区存在，不存在则创建

        Args:
            slug: 工作区slug
            name: 工作区名称（创建时使用）
            child_name: 孩子姓名（创建时使用）
            subject: 学科（创建时使用）

        Returns:
            Dict: 工作区信息
        """
        workspace = await self.get_workspace(slug)
        if workspace:
            return workspace

        if not all([name, child_name, subject]):
            raise ValueError("Workspace does not exist and creation parameters are incomplete")

        return await self.create_workspace(name, child_name, subject)

    # =========================================================================
    # 文档管理
    # =========================================================================

    async def upload_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        上传文档到AnythingLLM

        Args:
            file_path: 文件路径
            metadata: 文档元数据

        Returns:
            Dict: 上传结果
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(path, 'rb') as f:
                files = {'file': (path.name, f, 'application/octet-stream')}
                data = {}
                if metadata:
                    data['metadata'] = json.dumps(metadata)

                response = await self.client.post(
                    "/api/document/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()

            result = response.json()
            logger.info(f"Uploaded document: {path.name}")
            return result

        except Exception as e:
            logger.error(f"Failed to upload document {file_path}: {e}")
            raise

    async def embed_document(
        self,
        workspace_slug: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        上传并嵌入文档到工作区

        Args:
            workspace_slug: 工作区slug
            file_path: 文件路径
            metadata: 元数据

        Returns:
            Dict: 嵌入结果
        """
        try:
            # 1. 上传文档
            upload_result = await self.upload_document(file_path, metadata)
            document_name = upload_result.get("document", {}).get("location")

            if not document_name:
                raise ValueError("Failed to get document location from upload result")

            # 2. 添加到工作区
            response = await self.client.post(
                f"/api/workspace/{workspace_slug}/update-embeddings",
                json={"adds": [document_name]}
            )
            response.raise_for_status()

            logger.info(f"Embedded document {document_name} into workspace {workspace_slug}")
            return {
                "document_name": document_name,
                "workspace_slug": workspace_slug,
                "status": "embedded"
            }

        except Exception as e:
            logger.error(f"Failed to embed document: {e}")
            raise

    async def remove_document(
        self,
        workspace_slug: str,
        document_name: str
    ) -> None:
        """从工作区移除文档"""
        try:
            response = await self.client.post(
                f"/api/workspace/{workspace_slug}/update-embeddings",
                json={"deletes": [document_name]}
            )
            response.raise_for_status()
            logger.info(f"Removed document {document_name} from workspace {workspace_slug}")

        except Exception as e:
            logger.error(f"Failed to remove document: {e}")
            raise

    # =========================================================================
    # RAG检索和对话
    # =========================================================================

    async def query(
        self,
        workspace_slug: str,
        query: str,
        mode: str = "query",
        top_k: int = 5,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        查询工作区（RAG检索）

        Args:
            workspace_slug: 工作区slug
            query: 查询内容
            mode: 模式 ("query"仅检索, "chat"对话)
            top_k: 返回top K个结果
            temperature: LLM温度参数

        Returns:
            Dict: 检索结果
        """
        try:
            response = await self.client.post(
                f"/api/workspace/{workspace_slug}/{mode}",
                json={
                    "message": query,
                    "mode": mode,
                    "topK": top_k,
                    "temperature": temperature
                }
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Queried workspace {workspace_slug}: {query[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to query workspace: {e}")
            raise

    async def retrieve_context(
        self,
        workspace_slug: str,
        query: str,
        top_k: int = 5
    ) -> str:
        """
        检索相关上下文（用于RAG）

        Args:
            workspace_slug: 工作区slug
            query: 查询内容
            top_k: 返回数量

        Returns:
            str: 检索到的上下文文本
        """
        result = await self.query(
            workspace_slug=workspace_slug,
            query=query,
            mode="query",
            top_k=top_k
        )

        # 提取文本内容
        if result.get("textResponse"):
            return result["textResponse"]

        # 或从sources中提取
        sources = result.get("sources", [])
        context = "\n\n".join([
            source.get("text", "")
            for source in sources
            if source.get("text")
        ])

        return context or "未找到相关内容"

    # =========================================================================
    # 工作区配置的工作区规划
    # =========================================================================

    @staticmethod
    def get_workspace_slug(child_name: str, content_type: str, subject: Optional[str] = None) -> str:
        """
        获取标准化的工作区slug

        Args:
            child_name: 孩子姓名
            content_type: 内容类型 (textbooks/homework/test/cards)
            subject: 学科（可选）

        Returns:
            str: 工作区slug
        """
        child_slug = child_name.lower().replace(" ", "-")

        if content_type == "textbooks":
            return f"{child_slug}_textbooks"
        elif subject:
            return f"{child_slug}_{subject.lower()}_{content_type}"
        else:
            return f"{child_slug}_{content_type}"

    # =========================================================================
    # 批量操作
    # =========================================================================

    async def batch_embed_documents(
        self,
        workspace_slug: str,
        file_paths: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """批量嵌入文档"""
        import asyncio

        if metadata_list and len(metadata_list) != len(file_paths):
            raise ValueError("metadata_list length must match file_paths length")

        tasks = []
        for i, file_path in enumerate(file_paths):
            metadata = metadata_list[i] if metadata_list else None
            tasks.append(
                self.embed_document(workspace_slug, file_path, metadata)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to embed {file_paths[i]}: {result}")
                processed_results.append({
                    "success": False,
                    "file_path": file_paths[i],
                    "error": str(result)
                })
            else:
                result["file_path"] = file_paths[i]
                result["success"] = True
                processed_results.append(result)

        return processed_results

    # =========================================================================
    # 辅助方法
    # =========================================================================

    async def test_connection(self) -> bool:
        """测试AnythingLLM连接"""
        try:
            response = await self.client.get("/api/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"AnythingLLM connection test failed: {e}")
            return False


# =========================================================================
# 便捷函数
# =========================================================================

def get_anythingllm_service() -> AnythingLLMService:
    """获取AnythingLLM服务实例（依赖注入）"""
    return AnythingLLMService()
