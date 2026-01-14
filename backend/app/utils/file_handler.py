"""
文件处理工具函数
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

from app.config import settings
from app.core.exceptions import FileUploadError

logger = logging.getLogger(__name__)


def validate_image_file(filename: str, content_type: str, file_size: int) -> None:
    """
    验证图片文件
    
    Args:
        filename: 文件名
        content_type: MIME类型
        file_size: 文件大小（字节）
    
    Raises:
        FileUploadError: 文件验证失败
    """
    # 检查MIME类型
    allowed_types = settings.ALLOWED_IMAGE_TYPES
    if isinstance(allowed_types, str):
        allowed_types = [t.strip() for t in allowed_types.split(',')]
    
    if content_type not in allowed_types:
        raise FileUploadError(
            f"不支持的文件类型: {content_type}。允许的类型: {', '.join(allowed_types)}",
            filename=filename
        )
    
    # 检查文件大小
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        raise FileUploadError(
            f"文件过大: {actual_size_mb:.2f}MB，最大允许: {max_size_mb:.2f}MB",
            filename=filename
        )
    
    # 检查文件扩展名
    ext = Path(filename).suffix.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in allowed_extensions:
        raise FileUploadError(
            f"不支持的文件扩展名: {ext}。允许的扩展名: {', '.join(allowed_extensions)}",
            filename=filename
        )


def save_upload_file(
    file_content: bytes,
    original_filename: str,
    child_name: Optional[str] = None,
    subject: Optional[str] = None
) -> Path:
    """
    保存上传的文件
    
    Args:
        file_content: 文件内容
        original_filename: 原始文件名
        child_name: 孩子姓名（可选）
        subject: 学科（可选）
    
    Returns:
        Path: 保存的文件路径
    """
    try:
        # 生成安全的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = Path(original_filename).suffix
        safe_filename = f"{timestamp}_{original_filename}"
        
        # 构建保存路径
        upload_dir = Path(settings.UPLOAD_DIR)
        if child_name:
            upload_dir = upload_dir / child_name
        if subject:
            upload_dir = upload_dir / subject
        
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / safe_filename
        
        # 写入文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved upload file: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save upload file: {e}")
        raise FileUploadError(f"保存文件失败: {str(e)}", filename=original_filename)


# Alias for compatibility
save_uploaded_file = save_upload_file


def cleanup_old_uploads(days: int = 7) -> int:
    """
    清理旧的上传文件
    
    Args:
        days: 保留天数
    
    Returns:
        int: 删除的文件数量
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    deleted_count = 0
    
    for file_path in upload_dir.rglob("*"):
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
    
    return deleted_count


def get_file_info(file_path: Path) -> dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        dict: 文件信息
    """
    stat = file_path.stat()
    return {
        "filename": file_path.name,
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": file_path.suffix
    }
