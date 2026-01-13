"""
HL-OS FastAPI主应用
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.core.exceptions import HLOSException
from app.api.v1 import router as api_v1_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=== HL-OS Backend Starting ===")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 这里可以添加启动时的初始化逻辑
    # 例如：测试外部API连接、初始化数据库等
    
    yield
    
    # 关闭时执行
    logger.info("=== HL-OS Backend Shutting Down ===")
    # 这里可以添加清理逻辑


# 创建FastAPI应用
app = FastAPI(
    title="HL-OS API",
    description="家庭智能学习系统 - Home Learning Operating System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(HLOSException)
async def hlos_exception_handler(request: Request, exc: HLOSException):
    """处理自定义异常"""
    logger.error(f"HLOSException: {exc.message} (code: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误" if not settings.DEBUG else str(exc),
            "details": {}
        }
    )


# 注册API路由
app.include_router(api_v1_router, prefix="/api/v1")


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "HL-OS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
