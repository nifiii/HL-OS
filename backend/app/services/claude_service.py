"""
Claude服务
使用Anthropic Claude Sonnet 4.5 API进行教学内容生成、试题生成和自动批改
"""

from anthropic import AsyncAnthropic
from typing import List, Dict, Any, Optional
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """Claude AI服务"""

    def __init__(self):
        """初始化Claude服务"""
        # 支持代理接入方式
        if settings.ANTHROPIC_BASE_URL and settings.ANTHROPIC_AUTH_TOKEN:
            # 使用代理方式
            self.client = AsyncAnthropic(
                base_url=settings.ANTHROPIC_BASE_URL,
                api_key=settings.ANTHROPIC_AUTH_TOKEN  # 代理使用auth_token作为api_key
            )
            logger.info(f"ClaudeService initialized with proxy: base_url={settings.ANTHROPIC_BASE_URL}")
        elif settings.ANTHROPIC_API_KEY:
            # 使用标准方式
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("ClaudeService initialized with standard API")
        else:
            raise ValueError("Either ANTHROPIC_API_KEY or (ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN) must be set")

        self.model_teaching = settings.CLAUDE_MODEL_TEACHING
        self.model_grading = settings.CLAUDE_MODEL_GRADING
        logger.info(f"Using models: teaching={self.model_teaching}, grading={self.model_grading}")

    # =========================================================================
    # 模块C: 教学内容生成
    # =========================================================================

    async def generate_teaching_content(
        self,
        knowledge_points: List[str],
        context_from_rag: str,
        difficulty: int,
        style: str,
        duration_minutes: int,
        child_name: Optional[str] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        生成教学内容（Marp PPT格式）

        Args:
            knowledge_points: 要讲解的知识点列表
            context_from_rag: 从AnythingLLM检索的教材背景内容
            difficulty: 难度等级 (1-5星)
            style: 教学风格 (启发式/费曼式/详解式)
            duration_minutes: 目标时长（分钟）
            child_name: 孩子姓名（可选，用于个性化）
            additional_instructions: 额外指示（可选）

        Returns:
            str: Marp Markdown格式的PPT内容
        """
        system_prompt = f"""你是一位经验丰富的特级教师，擅长{style}教学法。
你的任务是为中小学生创建高质量的教学课件（Marp PPT格式）。

**教学原则：**
1. 因材施教：根据难度等级调整讲解深度
2. 循序渐进：从简单到复杂，从已知到未知
3. 理论结合实践：每个概念都配合例题
4. 启发思考：多用提问引导，而非直接告知答案
5. 视觉化：使用图表、公式、颜色等增强理解

**Marp格式要求：**
- 使用YAML frontmatter设置主题和样式
- 用`---`分隔每一页幻灯片
- 使用Markdown语法（标题、列表、代码块、LaTeX数学公式）
- 每页内容不要过多（保持简洁）
- 使用`<!-- presenter notes -->`添加讲解备注

**难度等级说明：**
- 1星：基础概念，小学低年级水平
- 2星：基础应用，小学高年级水平
- 3星：标准难度，初中水平
- 4星：提高难度，中考/高中水平
- 5星：竞赛难度，需要深入思考"""

        user_prompt = f"""请为以下内容创建一份教学课件：

**知识点：**
{', '.join(knowledge_points)}

**参考教材内容：**
{context_from_rag}

**教学参数：**
- 难度等级：{difficulty}/5星
- 教学风格：{style}
- 目标时长：{duration_minutes}分钟
- 学生姓名：{child_name or '同学'}

**额外要求：**
{additional_instructions or '无'}

**输出结构：**
1. 第1页：标题页（知识点名称+难度标识）
2. 第2页：引入（为什么要学这个？实际应用场景）
3. 第3-N页：核心概念讲解（拆解难点，配合例题）
4. 倒数第2页：变式练习（巩固理解）
5. 最后1页：总结与思考题

请生成完整的Marp Markdown课件：
"""

        try:
            response = await self.client.messages.create(
                model=self.model_teaching,
                max_tokens=8192,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            marp_content = response.content[0].text

            logger.info(f"Generated teaching content for: {', '.join(knowledge_points)}")
            return marp_content

        except Exception as e:
            logger.error(f"Failed to generate teaching content: {e}")
            raise

    # =========================================================================
    # 模块D: 试题生成
    # =========================================================================

    async def generate_assessment(
        self,
        topic_range: List[str],
        difficulty_distribution: Dict[int, int],
        question_types: List[str],
        context_from_rag: str,
        total_points: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        生成测评题目（原创题目，防止搜索到答案）

        Args:
            topic_range: 考察范围（知识点列表）
            difficulty_distribution: 难度分布 {难度: 题数}，如 {1: 2, 2: 3, 3: 3, 4: 2}
            question_types: 题型列表 ["multiple_choice", "short_answer", "calculation", "proof"]
            context_from_rag: 教材参考内容
            total_points: 总分（默认100分）

        Returns:
            List[Dict]: 题目列表，每题包含question_id, question_text, type, difficulty等
        """
        # 计算总题数和每题分值
        total_questions = sum(difficulty_distribution.values())
        points_per_question = total_points // total_questions

        system_prompt = """你是一位资深的命题专家，擅长设计原创的、高质量的考题。

**命题原则：**
1. 原创性：题目必须原创，不能直接使用教材或习题集的题目
2. 科学性：题目表述清晰、答案唯一、无歧义
3. 梯度性：不同难度的题目区分度明显
4. 防搜性：题目表述略作变化，避免学生直接搜索到答案
5. 实用性：贴近生活或实际应用场景

**题型说明：**
- multiple_choice：选择题（4个选项）
- short_answer：简答题/填空题
- calculation：计算题（需要详细步骤）
- proof：证明题（需要逻辑推理）

**难度标准：**
- 1星：基础概念，直接套用公式
- 2星：基础应用，一步推理
- 3星：标准难度，多步推理
- 4星：提高难度，需要综合分析
- 5星：竞赛难度，创新思维"""

        user_prompt = f"""请生成一套原创测评题目：

**考察范围：**
{', '.join(topic_range)}

**难度分布：**
{json.dumps(difficulty_distribution, ensure_ascii=False)}

**题型要求：**
{', '.join(question_types)}

**参考教材（仅作背景参考，不要直接照搬题目）：**
{context_from_rag[:1000]}...

**总分：** {total_points}分
**总题数：** {total_questions}题

**输出格式（JSON数组）：**
```json
[
    {{
        "question_id": "唯一ID（如q1, q2）",
        "question_text": "题目内容（数学公式用LaTeX，如$x^2+3x+2=0$）",
        "question_type": "题型",
        "difficulty": 1-5,
        "points": 分值,
        "options": ["A选项", "B选项", "C选项", "D选项"]（仅选择题）,
        "correct_answer": "标准答案",
        "solution": "详细解答步骤",
        "grading_rubric": "评分标准（如：正确列式2分，计算正确3分）",
        "knowledge_points": ["考察的知识点1", "知识点2"],
        "hint": "提示（如果难度较大）"
    }}
]
```

请生成题目：
"""

        try:
            response = await self.client.messages.create(
                model=self.model_teaching,
                max_tokens=8192,
                temperature=0.8,  # 提高温度增加原创性
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # 提取JSON
            content = response.content[0].text
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            questions = json.loads(json_str)

            logger.info(f"Generated {len(questions)} assessment questions")
            return questions

        except Exception as e:
            logger.error(f"Failed to generate assessment: {e}")
            raise

    # =========================================================================
    # 模块D: 自动批改
    # =========================================================================

    async def grade_answer(
        self,
        question: Dict[str, Any],
        student_answer: str,
        show_detailed_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        自动批改学生答案

        Args:
            question: 题目信息（包含question_text, correct_answer, grading_rubric等）
            student_answer: 学生的答案
            show_detailed_feedback: 是否显示详细反馈

        Returns:
            Dict: 批改结果（score, is_correct, feedback等）
        """
        system_prompt = """你是一位公正、细心的阅卷老师。

**批改原则：**
1. 公正性：按评分标准严格打分，不偏不倚
2. 细致性：检查每一个步骤，关注思路和方法
3. 鼓励性：指出错误的同时，肯定正确的部分
4. 建设性：提供具体的改进建议，而非泛泛而谈

**评分要点：**
- 答案正确：满分
- 方法正确但计算错误：扣少量分（如总分的10-20%）
- 思路部分正确：根据进度给部分分
- 完全错误：0分，但要指出错在哪里"""

        user_prompt = f"""请批改以下学生答案：

**题目：**
{question['question_text']}

**标准答案：**
{question['correct_answer']}

**评分标准：**
{question.get('grading_rubric', '按正确性评分')}

**题目分值：**
{question['points']}分

**学生答案：**
{student_answer}

**输出格式（JSON）：**
```json
{{
    "score": 实际得分,
    "max_score": {question['points']},
    "is_correct": true/false,
    "correctness_rate": 正确率（0-1之间的小数）,
    "feedback": "总体评价（简短）",
    "detailed_feedback": {{
        "strengths": ["正确的地方1", "正确的地方2"],
        "errors": ["错误1", "错误2"],
        "suggestions": ["改进建议1", "建议2"]
    }},
    "partial_credit_breakdown": {{
        "步骤1": 得分,
        "步骤2": 得分
    }},
    "knowledge_gaps": ["需要加强的知识点1", "知识点2"]
}}
```

请开始批改：
"""

        try:
            response = await self.client.messages.create(
                model=self.model_grading,
                max_tokens=2048,
                temperature=0.3,  # 降低温度保证一致性
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # 提取JSON
            content = response.content[0].text
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            grading_result = json.loads(json_str)

            # 如果不需要详细反馈，删除详细部分
            if not show_detailed_feedback:
                grading_result.pop("detailed_feedback", None)
                grading_result.pop("partial_credit_breakdown", None)

            logger.info(f"Graded answer: {grading_result['is_correct']}, score: {grading_result['score']}/{grading_result['max_score']}")
            return grading_result

        except Exception as e:
            logger.error(f"Failed to grade answer: {e}")
            raise

    # =========================================================================
    # 批量批改
    # =========================================================================

    async def batch_grade(
        self,
        questions_and_answers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量批改多道题目

        Args:
            questions_and_answers: 包含question和student_answer的字典列表

        Returns:
            List[Dict]: 每道题的批改结果
        """
        import asyncio

        tasks = [
            self.grade_answer(
                question=item['question'],
                student_answer=item['student_answer'],
                show_detailed_feedback=item.get('show_detailed_feedback', True)
            )
            for item in questions_and_answers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to grade question {i}: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "question_id": questions_and_answers[i]['question'].get('question_id')
                })
            else:
                result["question_id"] = questions_and_answers[i]['question'].get('question_id')
                processed_results.append(result)

        return processed_results

    # =========================================================================
    # 学情分析
    # =========================================================================

    async def analyze_learning_progress(
        self,
        grading_history: List[Dict[str, Any]],
        knowledge_point: str
    ) -> Dict[str, Any]:
        """
        分析学习进度和薄弱环节

        Args:
            grading_history: 历史批改记录
            knowledge_point: 当前知识点

        Returns:
            Dict: 分析结果和建议
        """
        system_prompt = """你是一位经验丰富的教学顾问，擅长分析学生的学习情况。

请根据学生的答题历史，提供专业的学情分析和学习建议。"""

        user_prompt = f"""请分析以下学习数据：

**知识点：** {knowledge_point}

**历史答题记录：**
{json.dumps(grading_history, ensure_ascii=False, indent=2)}

**请提供：**
1. 整体掌握情况评估（百分比）
2. 薄弱环节识别
3. 进步趋势分析
4. 个性化学习建议
5. 推荐的练习重点

**输出格式（JSON）：**
```json
{{
    "mastery_level": 0-100（掌握程度百分比）,
    "weak_points": ["薄弱点1", "薄弱点2"],
    "progress_trend": "improving（进步中）/stable（稳定）/declining（退步）",
    "recommendations": ["建议1", "建议2"],
    "focus_areas": ["需要重点练习的领域1", "领域2"]
}}
```
"""

        try:
            response = await self.client.messages.create(
                model=self.model_grading,
                max_tokens=2048,
                temperature=0.5,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            content = response.content[0].text
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content

            analysis = json.loads(json_str)
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze learning progress: {e}")
            raise

    # =========================================================================
    # 辅助方法
    # =========================================================================

    async def test_connection(self) -> bool:
        """测试Claude API连接"""
        try:
            response = await self.client.messages.create(
                model=self.model_teaching,
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello, this is a test."}]
            )
            logger.info("Claude API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Claude API connection test failed: {e}")
            return False


# =========================================================================
# 便捷函数
# =========================================================================

def get_claude_service() -> ClaudeService:
    """获取Claude服务实例（依赖注入）"""
    return ClaudeService()
