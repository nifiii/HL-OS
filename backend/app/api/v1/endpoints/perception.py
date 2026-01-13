"""
模块A: 感知与OCR API端点
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
import logging

from app.models.schemas import OCRTaskResponse, OCRResult
from app.services.gemini_service import GeminiVisionService
from app.utils.file_handler import validate_image_file, save_upload_file

router = APIRouter()
logger = logging.getLogger(__name__)

# 全局服务实例（简化版，生产环境建议使用依赖注入）
gemini_service = GeminiVisionService()


@router.post("/upload", response_model=OCRTaskResponse)
async def upload_photo_for_ocr(
    file: UploadFile = File(..., description="图片文件"),
    child_name: str = Form(..., description="孩子姓名"),
    subject: str = Form(..., description="学科"),
    content_type: str = Form(..., description="内容类型 (homework/test/textbook/worksheet)")
):
    """
    上传图片进行OCR识别
    
    流程:
    1. 验证文件类型和大小
    2. 保存文件到临时目录
    3. 调用Gemini Vision进行OCR
    4. 返回任务ID和初步结果
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件
        validate_image_file(
            filename=file.filename,
            content_type=file.content_type,
            file_size=len(file_content)
        )
        
        # 保存文件
        file_path = save_upload_file(
            file_content=file_content,
            original_filename=file.filename,
            child_name=child_name,
            subject=subject
        )
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 调用OCR服务（这里简化为同步，实际应该异步处理）
        try:
            ocr_result = await gemini_service.extract_from_image(
                image_path=str(file_path),
                content_type=content_type
            )
            
            if ocr_result.get("success"):
                status = "completed"
                message = "OCR识别完成"
            else:
                status = "failed"
                message = f"OCR识别失败: {ocr_result.get('error')}"
                
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            status = "failed"
            message = f"OCR处理失败: {str(e)}"
        
        return OCRTaskResponse(
            task_id=task_id,
            status=status,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{task_id}", response_model=OCRResult)
async def get_ocr_result(task_id: str):
    """
    获取OCR识别结果
    
    注意: 这是简化版实现，生产环境应该使用Redis或数据库存储任务状态
    """
    # TODO: 从缓存/数据库中获取OCR结果
    # 这里返回示例数据
    return OCRResult(
        task_id=task_id,
        status="completed",
        extracted_text="示例提取文本",
        structured_data={"problems": []},
        confidence_score=0.95,
        original_image_url=f"/uploads/{task_id}.jpg",
        error=None
    )


@router.post("/validate-quality")
async def validate_image_quality(file: UploadFile = File(...)):
    """
    验证图片质量（在OCR之前）
    """
    try:
        file_content = await file.read()
        
        # 保存临时文件
        file_path = save_upload_file(
            file_content=file_content,
            original_filename=file.filename
        )
        
        # 检查质量
        quality_result = await gemini_service.validate_image_quality(str(file_path))
        
        return quality_result
        
    except Exception as e:
        logger.error(f"Quality validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
