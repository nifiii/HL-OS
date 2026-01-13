"""
Gemini Vision服务
使用Google Gemini 3 Pro Preview进行图片OCR和结构化提取
"""

import google.generativeai as genai
from PIL import Image
from typing import Dict, Any, Optional, List
import json
import logging
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """Gemini Vision OCR服务"""

    def __init__(self):
        """初始化Gemini服务"""
        genai.configure(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info(f"GeminiVisionService initialized with model: {settings.GEMINI_MODEL}")

    # =========================================================================
    # 提示词模板
    # =========================================================================

    HOMEWORK_PROMPT = """
你是一个专业的OCR识别助手，专门用于提取学生作业图片中的内容。

**任务：**
仔细分析这张作业图片，提取所有题目和学生答案。

**输出格式（严格遵循JSON格式）：**
```json
{
    "problems": [
        {
            "problem_number": "题号（如：1、2、3或1.1、1.2）",
            "question": "题目内容（数学公式用LaTeX语法，如：$x^2+3x+2=0$）",
            "student_answer": "学生手写的答案（如果有）",
            "is_marked_correct": true/false（如果老师已批改）,
            "teacher_comment": "老师的批注（如果有）"
        }
    ],
    "metadata": {
        "subject": "学科名称（数学/语文/英语等）",
        "page_number": "页码或题目范围（如：P45、第3章）",
        "date": "作业日期（如果图片中有）",
        "total_score": "总分（如果有）",
        "student_score": "学生得分（如果有）"
    },
    "image_quality": {
        "is_clear": true/false,
        "issues": ["光线问题", "模糊", "遮挡"等问题列表]
    }
}
```

**特别注意：**
1. 数学公式必须使用LaTeX语法（如：分数用\\frac{分子}{分母}，根号用\\sqrt{}）
2. 准确识别学生的手写答案，即使字迹潦草
3. 如果老师已经批改，标记哪些题目是对的（is_marked_correct）
4. 如果图片质量不佳，在image_quality中说明问题

请开始识别：
"""

    TEST_PROMPT = """
你是一个专业的OCR识别助手，专门用于提取考试试卷图片中的内容。

**任务：**
仔细分析这张试卷图片，提取所有题目、学生答案和评分信息。

**输出格式（严格遵循JSON格式）：**
```json
{
    "questions": [
        {
            "number": "题号",
            "question_text": "题目内容（数学公式用LaTeX）",
            "question_type": "multiple_choice（选择题）/short_answer（简答题）/calculation（计算题）/essay（作文题）",
            "options": ["A选项", "B选项", "C选项", "D选项"]（仅选择题）,
            "student_answer": "学生的答案",
            "correct_answer": "标准答案（如果试卷上有）",
            "points": 分值,
            "score_given": 实际得分（如果已批改）
        }
    ],
    "exam_info": {
        "exam_name": "考试名称",
        "subject": "学科",
        "total_points": 总分,
        "student_total_score": 学生总分（如果已批改）,
        "exam_date": "考试日期"
    }
}
```

**特别注意：**
1. 区分题目类型（选择题、填空题、计算题等）
2. 准确提取学生的答案和得分
3. 如果有标准答案，一并提取

请开始识别：
"""

    TEXTBOOK_PROMPT = """
你是一个专业的OCR识别助手，专门用于提取教材页面中的教学内容。

**任务：**
仔细分析这张教材图片，提取知识点、例题、公式等教学内容。

**输出格式（严格遵循JSON格式）：**
```json
{
    "content_sections": [
        {
            "section_type": "concept（概念）/theorem（定理）/example（例题）/practice（练习）",
            "title": "章节标题",
            "body": "正文内容（数学公式用LaTeX）",
            "examples": ["例题1", "例题2"],
            "formulas": ["公式1（LaTeX格式）", "公式2"],
            "key_points": ["要点1", "要点2"]
        }
    ],
    "page_info": {
        "page_number": "页码",
        "chapter": "章节名称",
        "subject": "学科",
        "grade_level": "年级"
    },
    "diagrams": [
        {
            "description": "图表描述（如：二次函数图像、三角形示意图）",
            "caption": "图注"
        }
    ]
}
```

**特别注意：**
1. 准确提取知识点和核心概念
2. 数学公式必须使用LaTeX语法
3. 识别图表并描述其含义

请开始识别：
"""

    WORKSHEET_PROMPT = """
你是一个专业的OCR识别助手，专门用于提取练习卷/习题集图片中的内容。

**任务：**
仔细分析这张习题图片，提取所有题目。

**输出格式（严格遵循JSON格式）：**
```json
{
    "exercises": [
        {
            "number": "题号",
            "question": "题目内容（数学公式用LaTeX）",
            "difficulty": 1-5（根据题目判断难度，1最简单，5最难）,
            "knowledge_points": ["知识点1", "知识点2"],
            "hints": ["提示1（如果有）"]
        }
    ],
    "worksheet_info": {
        "title": "练习卷标题",
        "subject": "学科",
        "topic": "主题（如：二次函数、三角形）"
    }
}
```

请开始识别：
"""

    # =========================================================================
    # 核心方法
    # =========================================================================

    async def extract_from_image(
        self,
        image_path: str,
        content_type: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从图片中提取结构化内容

        Args:
            image_path: 图片文件路径
            content_type: 内容类型 (homework/test/textbook/worksheet)
            custom_prompt: 自定义提示词（可选）

        Returns:
            Dict: 结构化的OCR结果
        """
        try:
            # 加载图片
            image = Image.open(image_path)

            # 选择提示词模板
            prompt = custom_prompt or self._get_prompt_for_type(content_type)

            # 调用Gemini API（同步调用，在asyncio中运行）
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )

            # 解析响应
            result = self._parse_response(response, content_type)

            logger.info(f"Successfully extracted content from image: {image_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to extract from image {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": None,
                "structured_data": None
            }

    def _get_prompt_for_type(self, content_type: str) -> str:
        """根据内容类型选择提示词"""
        prompts = {
            "homework": self.HOMEWORK_PROMPT,
            "test": self.TEST_PROMPT,
            "textbook": self.TEXTBOOK_PROMPT,
            "worksheet": self.WORKSHEET_PROMPT
        }
        return prompts.get(content_type, self.HOMEWORK_PROMPT)

    def _parse_response(self, response: Any, content_type: str) -> Dict[str, Any]:
        """解析Gemini响应"""
        try:
            # 获取文本响应
            text = response.text

            # 尝试提取JSON（可能在代码块中）
            json_text = text
            if "```json" in text:
                json_text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_text = text.split("```")[1].split("```")[0].strip()

            # 解析JSON
            structured_data = json.loads(json_text)

            return {
                "success": True,
                "extracted_text": text,
                "structured_data": structured_data,
                "content_type": content_type,
                "model": settings.GEMINI_MODEL
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            # 如果JSON解析失败，返回原始文本
            return {
                "success": False,
                "error": f"JSON parse error: {str(e)}",
                "extracted_text": response.text,
                "structured_data": None,
                "raw_response": response.text
            }

    # =========================================================================
    # 图片质量检测
    # =========================================================================

    async def validate_image_quality(self, image_path: str) -> Dict[str, Any]:
        """
        检测图片质量是否适合OCR

        Args:
            image_path: 图片路径

        Returns:
            Dict: 质量评估结果
        """
        try:
            image = Image.open(image_path)

            prompt = """
请评估这张图片的质量，判断是否适合进行OCR文字识别。

**评估标准：**
1. 文字是否清晰可辨
2. 光线是否充足
3. 图片是否正向（未倾斜）
4. 是否有遮挡或污损

**输出格式（JSON）：**
```json
{
    "quality_score": 0-100（分数，100表示质量最好）,
    "is_acceptable": true/false（是否可以用于OCR）,
    "issues": [
        {
            "issue_type": "blur（模糊）/dark（太暗）/tilted（倾斜）/obstruction（遮挡）",
            "severity": "low（轻微）/medium（中等）/high（严重）",
            "description": "具体描述"
        }
    ],
    "recommendations": ["改进建议1", "改进建议2"]
}
```
"""

            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image]
            )

            # 解析响应
            result = self._parse_response(response, "quality_check")

            if result["success"]:
                return result["structured_data"]
            else:
                # 如果解析失败，返回默认评估
                return {
                    "quality_score": 50,
                    "is_acceptable": True,
                    "issues": [],
                    "recommendations": ["无法自动评估，请人工检查"]
                }

        except Exception as e:
            logger.error(f"Failed to validate image quality: {e}")
            return {
                "quality_score": 0,
                "is_acceptable": False,
                "issues": [{"issue_type": "error", "severity": "high", "description": str(e)}],
                "recommendations": ["请重新拍摄图片"]
            }

    # =========================================================================
    # 批量处理
    # =========================================================================

    async def batch_extract(
        self,
        image_paths: List[str],
        content_type: str
    ) -> List[Dict[str, Any]]:
        """
        批量提取多张图片的内容

        Args:
            image_paths: 图片路径列表
            content_type: 内容类型

        Returns:
            List[Dict]: 所有图片的OCR结果
        """
        tasks = [
            self.extract_from_image(path, content_type)
            for path in image_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process image {image_paths[i]}: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "image_path": image_paths[i]
                })
            else:
                result["image_path"] = image_paths[i]
                processed_results.append(result)

        return processed_results

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def extract_latex_formulas(self, text: str) -> List[str]:
        """从文本中提取所有LaTeX公式"""
        import re
        # 匹配 $...$ 或 $$...$$ 格式的公式
        pattern = r'\$\$?(.*?)\$\$?'
        formulas = re.findall(pattern, text)
        return formulas

    async def test_connection(self) -> bool:
        """测试Gemini API连接"""
        try:
            # 发送简单的测试请求
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Hello, this is a test."
            )
            logger.info("Gemini API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            return False


# =========================================================================
# 便捷函数
# =========================================================================

def get_gemini_service() -> GeminiVisionService:
    """获取Gemini服务实例（依赖注入）"""
    return GeminiVisionService()
