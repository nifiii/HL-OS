"""
模块D - 评测引擎端点

生成原创题目并自动批改，支持学情分析
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
from pathlib import Path

from app.models.schemas import (
    AssessmentGenerationRequest,
    AssessmentGenerationResponse,
    AssessmentGradingRequest,
    AssessmentGradingResponse,
    LearningAnalyticsRequest,
    LearningAnalyticsResponse,
    Problem
)
from app.services.claude_service import ClaudeService
from app.services.gemini_service import GeminiVisionService
from app.services.obsidian_service import ObsidianService
from app.core.exceptions import (
    ClaudeServiceError,
    GeminiServiceError,
    ObsidianStorageError,
    HLOSException
)
from app.utils.file_handler import save_uploaded_file

router = APIRouter()
logger = logging.getLogger(__name__)

# 服务实例
claude_service = ClaudeService()
gemini_service = GeminiVisionService()
obsidian_service = ObsidianService()

# 评测缓存（生产环境应使用 Redis）
assessment_cache: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=AssessmentGenerationResponse)
async def generate_assessment(request: AssessmentGenerationRequest):
    """
    生成评测题目（原创题目，防搜索）

    工作流程：
    1. 根据范围和难度分布生成题目
    2. Claude 生成原创题目及详细解答
    3. 返回题目列表和评测 ID

    Args:
        request: 评测生成请求

    Returns:
        AssessmentGenerationResponse: 生成的题目列表
    """
    logger.info(
        f"生成评测 - child: {request.child_name}, subject: {request.subject}, "
        f"topic_range: {request.topic_range}, total_problems: {request.total_problems}"
    )

    try:
        # 调用 Claude 生成题目
        problems = await claude_service.generate_assessment(
            topic_range=request.topic_range,
            difficulty_distribution=request.difficulty_distribution,
            question_types=request.question_types,
            total_problems=request.total_problems,
            prevent_search=request.prevent_search,
            include_detailed_solution=request.include_detailed_solution
        )

        logger.info(f"成功生成 {len(problems)} 道题目")

        # 创建评测 ID 并缓存
        assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.child_name}"

        assessment_data = {
            "assessment_id": assessment_id,
            "child_name": request.child_name,
            "subject": request.subject,
            "topic_range": request.topic_range,
            "difficulty_distribution": request.difficulty_distribution,
            "problems": problems,
            "created_at": datetime.now().isoformat(),
            "graded": False
        }

        assessment_cache[assessment_id] = assessment_data

        return AssessmentGenerationResponse(
            success=True,
            message=f"成功生成 {len(problems)} 道题目",
            assessment_id=assessment_id,
            problems=problems,
            total_problems=len(problems),
            difficulty_distribution=request.difficulty_distribution
        )

    except ClaudeServiceError as e:
        logger.error(f"题目生成失败: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"生成评测失败: {str(e)}", exc_info=True)
        raise HLOSException(
            message=f"生成评测失败: {str(e)}",
            error_code="ASSESSMENT_GENERATION_ERROR",
            status_code=500,
            details={"topic_range": request.topic_range}
        )


@router.post("/grade", response_model=AssessmentGradingResponse)
async def grade_assessment(
    assessment_id: str = Form(...),
    child_name: str = Form(...),
    subject: str = Form(...),
    answer_image: UploadFile = File(...)
):
    """
    自动批改评测

    工作流程：
    1. 学生答题图片上传
    2. Gemini OCR 识别答案
    3. Claude 自动批改每道题
    4. 更新 Obsidian 元数据（Accuracy、Attempts）
    5. 将错题移入 Wrong_Problems 文件夹

    Args:
        assessment_id: 评测 ID
        child_name: 孩子姓名
        subject: 学科
        answer_image: 学生答题图片

    Returns:
        AssessmentGradingResponse: 批改结果
    """
    logger.info(
        f"批改评测 - assessment_id: {assessment_id}, "
        f"child: {child_name}, subject: {subject}"
    )

    try:
        # 1. 检查评测是否存在
        if assessment_id not in assessment_cache:
            raise HTTPException(
                status_code=404,
                detail=f"评测不存在或已过期: {assessment_id}"
            )

        assessment_data = assessment_cache[assessment_id]
        problems = assessment_data["problems"]

        # 2. 保存上传的答题图片
        image_path = await save_uploaded_file(answer_image, "assessments")
        logger.info(f"答题图片已保存: {image_path}")

        # 3. 使用 Gemini OCR 识别答案
        try:
            ocr_result = await gemini_service.extract_from_image(
                image_path=str(image_path),
                content_type="test"
            )

            if not ocr_result.get("success"):
                raise GeminiServiceError(
                    f"OCR 识别失败: {ocr_result.get('error', 'Unknown error')}"
                )

            recognized_problems = ocr_result.get("problems", [])
            logger.info(f"OCR 识别到 {len(recognized_problems)} 道题的答案")

        except Exception as e:
            logger.error(f"OCR 识别失败: {str(e)}", exc_info=True)
            raise GeminiServiceError(
                f"OCR 识别失败: {str(e)}",
                details={"image_path": str(image_path)}
            )

        # 4. 逐题批改
        grading_results = []
        total_score = 0
        total_possible_score = 0

        for i, problem in enumerate(problems):
            # 查找对应的学生答案
            student_answer = ""
            for rec_problem in recognized_problems:
                if rec_problem.get("problem_number") == str(i + 1):
                    student_answer = rec_problem.get("student_answer", "")
                    break

            if not student_answer:
                logger.warning(f"未找到题目 {i+1} 的学生答案")
                grading_results.append({
                    "problem_number": i + 1,
                    "question": problem.get("question", ""),
                    "student_answer": "",
                    "score": 0,
                    "max_score": problem.get("max_score", 10),
                    "feedback": "未作答",
                    "is_correct": False
                })
                total_possible_score += problem.get("max_score", 10)
                continue

            # 使用 Claude 批改
            try:
                grading_result = await claude_service.grade_answer(
                    question=problem,
                    student_answer=student_answer,
                    grading_rubric=problem.get("grading_rubric", "标准答案")
                )

                score = grading_result.get("score", 0)
                max_score = problem.get("max_score", 10)
                total_score += score
                total_possible_score += max_score

                grading_results.append({
                    "problem_number": i + 1,
                    "question": problem.get("question", ""),
                    "student_answer": student_answer,
                    "correct_answer": problem.get("solution", ""),
                    "score": score,
                    "max_score": max_score,
                    "feedback": grading_result.get("feedback", ""),
                    "improvement_suggestions": grading_result.get("improvement_suggestions", []),
                    "is_correct": grading_result.get("is_correct", False)
                })

                logger.info(f"题目 {i+1} 批改完成 - 得分: {score}/{max_score}")

            except Exception as e:
                logger.error(f"批改题目 {i+1} 失败: {str(e)}", exc_info=True)
                grading_results.append({
                    "problem_number": i + 1,
                    "question": problem.get("question", ""),
                    "student_answer": student_answer,
                    "score": 0,
                    "max_score": problem.get("max_score", 10),
                    "feedback": f"批改失败: {str(e)}",
                    "is_correct": False
                })
                total_possible_score += problem.get("max_score", 10)

        # 5. 计算总分和准确率
        accuracy = (total_score / total_possible_score) if total_possible_score > 0 else 0.0

        logger.info(
            f"批改完成 - 总分: {total_score}/{total_possible_score}, "
            f"准确率: {accuracy:.2%}"
        )

        # 6. 保存错题到 Obsidian
        wrong_problems = [r for r in grading_results if not r.get("is_correct", False)]

        if wrong_problems:
            logger.info(f"发现 {len(wrong_problems)} 道错题，保存到 Obsidian")

            for wrong_problem in wrong_problems:
                try:
                    # 构建错题内容
                    content = f"""# 题目

{wrong_problem['question']}

## 正确答案

{wrong_problem.get('correct_answer', '见详细解答')}

## 错误记录 - {datetime.now().strftime('%Y-%m-%d')}

**学生答案:** {wrong_problem['student_answer']}

**批改反馈:** {wrong_problem['feedback']}

**改进建议:**
{chr(10).join(['- ' + s for s in wrong_problem.get('improvement_suggestions', [])])}
"""

                    # 保存到 Wrong_Problems 文件夹
                    metadata = {
                        "Difficulty": problems[wrong_problem['problem_number'] - 1].get("difficulty", 3),
                        "Accuracy": 0.0,
                        "Last_Modified": datetime.now().isoformat(),
                        "Last_Attempted": datetime.now().isoformat(),
                        "Attempts": 1,
                        "Tags": ["待复习"] + problems[wrong_problem['problem_number'] - 1].get("knowledge_points", []),
                        "Source": f"评测 {assessment_id}"
                    }

                    obsidian_service.save_markdown(
                        child_name=child_name,
                        subject=subject,
                        folder_type="Wrong_Problems",
                        filename=f"assessment_{assessment_id}_problem_{wrong_problem['problem_number']}",
                        content=content,
                        metadata=metadata
                    )

                    logger.info(f"错题 {wrong_problem['problem_number']} 已保存到 Obsidian")

                except Exception as e:
                    logger.error(f"保存错题 {wrong_problem['problem_number']} 失败: {str(e)}")

        # 7. 标记评测为已批改
        assessment_data["graded"] = True
        assessment_data["grading_results"] = grading_results
        assessment_data["total_score"] = total_score
        assessment_data["total_possible_score"] = total_possible_score
        assessment_data["accuracy"] = accuracy

        return AssessmentGradingResponse(
            success=True,
            message="批改完成",
            assessment_id=assessment_id,
            grading_results=grading_results,
            total_score=total_score,
            total_possible_score=total_possible_score,
            accuracy=accuracy,
            wrong_problems_count=len(wrong_problems)
        )

    except (GeminiServiceError, ClaudeServiceError):
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批改失败: {str(e)}", exc_info=True)
        raise HLOSException(
            message=f"批改失败: {str(e)}",
            error_code="ASSESSMENT_GRADING_ERROR",
            status_code=500,
            details={"assessment_id": assessment_id}
        )


@router.post("/analytics", response_model=LearningAnalyticsResponse)
async def get_learning_analytics(request: LearningAnalyticsRequest):
    """
    学情分析

    分析学生在特定学科的学习情况，包括：
    - 知识点掌握情况
    - 薄弱点识别
    - 进步趋势
    - 推荐复习内容

    Args:
        request: 学情分析请求

    Returns:
        LearningAnalyticsResponse: 学情分析结果
    """
    logger.info(
        f"学情分析 - child: {request.child_name}, subject: {request.subject}"
    )

    try:
        # 1. 从 Obsidian 获取错题数据
        wrong_problems = obsidian_service.get_wrong_problems(
            child_name=request.child_name,
            subject=request.subject,
            min_difficulty=request.min_difficulty,
            max_accuracy=request.max_accuracy
        )

        logger.info(f"获取到 {len(wrong_problems)} 道错题")

        # 2. 统计知识点分布
        knowledge_point_stats: Dict[str, Dict[str, Any]] = {}

        for problem in wrong_problems:
            tags = problem.get("metadata", {}).get("Tags", [])
            difficulty = problem.get("metadata", {}).get("Difficulty", 3)
            accuracy = problem.get("metadata", {}).get("Accuracy", 0.0)

            for tag in tags:
                if tag == "待复习":
                    continue

                if tag not in knowledge_point_stats:
                    knowledge_point_stats[tag] = {
                        "knowledge_point": tag,
                        "wrong_count": 0,
                        "avg_difficulty": 0.0,
                        "avg_accuracy": 0.0,
                        "difficulties": [],
                        "accuracies": []
                    }

                knowledge_point_stats[tag]["wrong_count"] += 1
                knowledge_point_stats[tag]["difficulties"].append(difficulty)
                knowledge_point_stats[tag]["accuracies"].append(accuracy)

        # 计算平均值
        for kp, stats in knowledge_point_stats.items():
            stats["avg_difficulty"] = sum(stats["difficulties"]) / len(stats["difficulties"])
            stats["avg_accuracy"] = sum(stats["accuracies"]) / len(stats["accuracies"])
            del stats["difficulties"]
            del stats["accuracies"]

        # 按错题数量排序
        sorted_kps = sorted(
            knowledge_point_stats.values(),
            key=lambda x: x["wrong_count"],
            reverse=True
        )

        # 3. 识别薄弱点（错题数量多且准确率低）
        weak_points = [
            kp for kp in sorted_kps
            if kp["wrong_count"] >= 3 and kp["avg_accuracy"] < 0.6
        ][:5]  # 取前5个薄弱点

        # 4. 生成复习建议
        review_recommendations = []
        for weak_point in weak_points:
            review_recommendations.append({
                "knowledge_point": weak_point["knowledge_point"],
                "priority": "高" if weak_point["avg_accuracy"] < 0.4 else "中",
                "reason": f"错题数量: {weak_point['wrong_count']}, 平均准确率: {weak_point['avg_accuracy']:.1%}",
                "suggested_actions": [
                    "重新学习基础概念",
                    "针对性练习",
                    "查看相关教学课件"
                ]
            })

        logger.info(f"识别到 {len(weak_points)} 个薄弱点")

        return LearningAnalyticsResponse(
            success=True,
            child_name=request.child_name,
            subject=request.subject,
            total_wrong_problems=len(wrong_problems),
            knowledge_point_distribution=sorted_kps,
            weak_points=[wp["knowledge_point"] for wp in weak_points],
            review_recommendations=review_recommendations,
            overall_accuracy=sum(p.get("metadata", {}).get("Accuracy", 0.0) for p in wrong_problems) / len(wrong_problems) if wrong_problems else 1.0
        )

    except Exception as e:
        logger.error(f"学情分析失败: {str(e)}", exc_info=True)
        raise HLOSException(
            message=f"学情分析失败: {str(e)}",
            error_code="ANALYTICS_ERROR",
            status_code=500,
            details={
                "child_name": request.child_name,
                "subject": request.subject
            }
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_assessment_history(
    child_name: str,
    subject: Optional[str] = None,
    limit: int = 20
):
    """
    获取评测历史记录

    Args:
        child_name: 孩子姓名
        subject: 可选的学科过滤
        limit: 返回数量限制

    Returns:
        历史记录列表
    """
    logger.info(f"获取评测历史 - child: {child_name}, subject: {subject}")

    try:
        # TODO: 从缓存或数据库读取历史记录
        # 当前返回内存缓存中的评测

        history = []
        for assessment_id, data in assessment_cache.items():
            if data["child_name"] == child_name:
                if subject and data["subject"] != subject:
                    continue

                history.append({
                    "assessment_id": assessment_id,
                    "subject": data["subject"],
                    "topic_range": data["topic_range"],
                    "total_problems": len(data["problems"]),
                    "graded": data["graded"],
                    "created_at": data["created_at"],
                    "total_score": data.get("total_score"),
                    "accuracy": data.get("accuracy")
                })

        history.sort(key=lambda x: x["created_at"], reverse=True)
        history = history[:limit]

        logger.info(f"找到 {len(history)} 条评测历史")

        return {
            "success": True,
            "child_name": child_name,
            "subject": subject,
            "total_count": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
