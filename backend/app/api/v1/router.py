"""
API v1路由聚合
"""

from fastapi import APIRouter
from app.api.v1.endpoints import perception, validation, storage, teaching, assessment

router = APIRouter()

# 注册各模块路由
router.include_router(perception.router, prefix="/perception", tags=["感知与OCR"])
router.include_router(validation.router, prefix="/validation", tags=["家长校验"])
router.include_router(storage.router, prefix="/storage", tags=["存储管理"])
router.include_router(teaching.router, prefix="/teaching", tags=["教学内容生成"])
router.include_router(assessment.router, prefix="/assessment", tags=["评测引擎"])


# 健康检查端点
@router.get("/health", tags=["系统"])
async def api_health():
    """API健康检查"""
    return {
        "status": "healthy",
        "api_version": "v1"
    }
