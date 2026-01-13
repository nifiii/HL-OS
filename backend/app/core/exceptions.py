"""
自定义异常类
"""

from typing import Optional, Dict, Any


class HLOSException(Exception):
    """HL-OS基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ExternalAPIError(HLOSException):
    """外部API调用失败"""
    
    def __init__(self, message: str, service: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            status_code=503,
            details={"service": service, **kwargs}
        )


class ObsidianError(HLOSException):
    """Obsidian文件操作错误"""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="OBSIDIAN_ERROR",
            status_code=500,
            details={"file_path": file_path} if file_path else {}
        )


class ValidationError(HLOSException):
    """数据验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {}
        )


class FileUploadError(HLOSException):
    """文件上传错误"""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=400,
            details={"filename": filename} if filename else {}
        )


class ResourceNotFoundError(HLOSException):
    """资源未找到"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type} if resource_type else {}
        )


class RateLimitError(HLOSException):
    """速率限制错误"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after} if retry_after else {}
        )
