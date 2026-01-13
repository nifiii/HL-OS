"""
模块D: 评测引擎界面
"""

import streamlit as st
import requests
import os
from typing import List, Dict, Any

# 配置
st.set_page_config(
    page_title="评测管理",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="auto"
)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 移动端优化CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .problem-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .grading-result-correct {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .grading-result-wrong {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
            padding: 0 1rem;
            margin-bottom: 1.5rem;
        }

        .section-header {
            font-size: 1.2rem;
            margin-top: 1rem;
            padding: 0.5rem 0.5rem 0.3rem;
        }

        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 0.5rem !important;
        }

        .stButton button {
            font-size: 1.1rem !important;
            padding: 0.75rem 1rem !important;
            min-height: 48px !important;
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox select, .stMultiSelect {
            font-size: 1rem !important;
        }

        .stNumberInput input {
            font-size: 1rem !important;
            padding: 0.75rem !important;
        }

        .stSlider {
            padding: 1rem 0;
        }

        .stFileUploader {
            font-size: 1rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }

        .stExpander {
            margin-bottom: 0.5rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem !important;
            padding: 0.5rem 0.75rem !important;
        }

        .problem-card {
            padding: 0.75rem;
            font-size: 0.95rem;
        }

        .grading-result-correct, .grading-result-wrong {
            padding: 0.75rem;
            font-size: 0.95rem;
        }

        h3 {
            font-size: 1.1rem !important;
        }
    }

    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .section-header {
            font-size: 1.1rem;
        }

        .stButton button {
            font-size: 1.2rem !important;
            padding: 1rem !important;
            min-height: 56px !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem !important;
            padding: 0.4rem 0.6rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }

        .problem-card {
            padding: 0.5rem;
            font-size: 0.9rem;
        }

        .grading-result-correct, .grading-result-wrong {
            padding: 0.5rem;
            font-size: 0.9rem;
        }
    }

    .stButton button:active {
        transform: scale(0.98);
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-header">📝 评测引擎系统</div>', unsafe_allow_html=True)

# 初始化 session state
if "assessment_data" not in st.session_state:
    st.session_state.assessment_data = None
if "grading_data" not in st.session_state:
    st.session_state.grading_data = None
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "生成题目"

# Tab 导航
tabs = st.tabs(["生成题目", "批改答案", "学情分析"])

# ========== Tab 1: 生成题目 ==========
with tabs[0]:
    st.markdown('<div class="section-header">📚 生成原创题目</div>', unsafe_allow_html=True)

    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        child_name = st.text_input("孩子姓名 *", value="小明")
    with col2:
        subject = st.selectbox(
            "学科 *",
            options=["数学", "语文", "英语", "物理", "化学", "生物", "历史", "地理"]
        )

    # 范围配置
    st.markdown("### 考察范围")
    range_source = st.radio(
        "范围来源",
        options=["按章节", "按错题本", "自定义"],
        horizontal=True
    )

    topic_range = []
    if range_source == "按章节":
        # TODO: 从后端获取章节列表
        available_chapters = [
            "第一章：二次函数",
            "第二章：一元二次方程",
            "第三章：旋转",
            "第四章：圆"
        ]
        selected_chapters = st.multiselect("选择章节", options=available_chapters)
        topic_range = selected_chapters

    elif range_source == "按错题本":
        st.info("将从错题本中提取高频知识点")
        # TODO: 从后端 API 获取错题本知识点
        topic_range = ["错题本高频知识点"]

    else:  # 自定义
        custom_range = st.text_area(
            "输入考察范围（每行一个）",
            height=100,
            help="例如：\n- 二次函数顶点式\n- 配方法"
        )
        if custom_range.strip():
            topic_range = [r.strip() for r in custom_range.strip().split("\n") if r.strip()]

    # 难度分布
    st.markdown("### 难度分布")
    col1, col2, col3 = st.columns(3)
    with col1:
        basic_count = st.number_input("基础题", min_value=0, max_value=20, value=5)
    with col2:
        medium_count = st.number_input("中档题", min_value=0, max_value=20, value=3)
    with col3:
        hard_count = st.number_input("提高题", min_value=0, max_value=20, value=2)

    total_problems = basic_count + medium_count + hard_count
    st.info(f"📊 总题数: {total_problems} 题")

    # 题型选择
    st.markdown("### 题型选择")
    question_types = st.multiselect(
        "选择题型",
        options=["选择题", "填空题", "计算题", "证明题", "应用题"],
        default=["选择题", "填空题", "计算题"]
    )

    # 高级选项
    with st.expander("🔧 高级选项"):
        prevent_search = st.checkbox(
            "防搜索设计",
            value=True,
            help="生成原创题目，避免学生直接搜索到答案"
        )
        include_detailed_solution = st.checkbox(
            "包含详细解答",
            value=True,
            help="为每道题生成详细的解题步骤"
        )

    # 生成按钮
    if st.button(
        "🚀 生成题目",
        type="primary",
        disabled=(total_problems == 0 or not topic_range),
        use_container_width=True
    ):
        with st.spinner("🤖 Claude 正在生成原创题目，请稍候..."):
            try:
                # 构建难度分布字典
                difficulty_distribution = {}
                if basic_count > 0:
                    difficulty_distribution[1] = basic_count
                    difficulty_distribution[2] = basic_count
                if medium_count > 0:
                    difficulty_distribution[3] = medium_count
                if hard_count > 0:
                    difficulty_distribution[4] = hard_count
                    difficulty_distribution[5] = hard_count

                response = requests.post(
                    f"{BACKEND_URL}/api/v1/assessment/generate",
                    json={
                        "child_name": child_name,
                        "subject": subject,
                        "topic_range": topic_range,
                        "difficulty_distribution": difficulty_distribution,
                        "question_types": question_types,
                        "total_problems": total_problems,
                        "prevent_search": prevent_search,
                        "include_detailed_solution": include_detailed_solution
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    st.session_state.assessment_data = response.json()
                    st.success(f"✅ 成功生成 {total_problems} 道题目！")
                else:
                    st.error(f"❌ 生成失败: {response.text}")

            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，请稍后重试")
            except Exception as e:
                st.error(f"❌ 发生错误: {str(e)}")

    # 显示生成的题目
    if st.session_state.assessment_data:
        st.markdown("---")
        st.markdown("### 📄 生成的题目")

        assessment = st.session_state.assessment_data
        problems = assessment.get("problems", [])

        for i, problem in enumerate(problems):
            with st.expander(f"题目 {i+1} - {problem.get('type', '未知类型')} - {'⭐' * problem.get('difficulty', 3)}"):
                st.markdown(f"**题目:** {problem.get('question', '')}")
                st.markdown(f"**分值:** {problem.get('max_score', 10)} 分")
                st.markdown(f"**知识点:** {', '.join(problem.get('knowledge_points', []))}")

                if include_detailed_solution:
                    st.markdown("**详细解答:**")
                    st.code(problem.get("solution", ""), language="markdown")

        # 下载按钮（导出为 Markdown）
        markdown_content = f"# {subject} - 评测试卷\n\n"
        markdown_content += f"**学生:** {child_name}\n"
        markdown_content += f"**范围:** {', '.join(topic_range)}\n"
        markdown_content += f"**总分:** {sum(p.get('max_score', 10) for p in problems)} 分\n\n"
        markdown_content += "---\n\n"

        for i, problem in enumerate(problems):
            markdown_content += f"## 题目 {i+1} ({problem.get('max_score', 10)}分)\n\n"
            markdown_content += f"{problem.get('question', '')}\n\n"
            markdown_content += "---\n\n"

        st.download_button(
            label="📥 下载试卷（Markdown）",
            data=markdown_content,
            file_name=f"{child_name}_{subject}_assessment.md",
            mime="text/markdown"
        )

# ========== Tab 2: 批改答案 ==========
with tabs[1]:
    st.markdown('<div class="section-header">✅ 自动批改答案</div>', unsafe_allow_html=True)

    if not st.session_state.assessment_data:
        st.warning("⚠️ 请先在「生成题目」tab 中生成评测")
    else:
        assessment = st.session_state.assessment_data
        assessment_id = assessment.get("assessment_id")

        st.info(f"📝 当前评测 ID: {assessment_id}")
        st.info(f"📊 题目数量: {assessment.get('total_problems', 0)} 题")

        # 上传答题图片
        st.markdown("### 上传学生答题图片")
        answer_image = st.file_uploader(
            "选择答题图片",
            type=["jpg", "jpeg", "png"],
            help="上传学生手写答题的图片，系统将自动识别并批改"
        )

        if answer_image and st.button("🎯 开始批改", type="primary", use_container_width=True):
            with st.spinner("🤖 正在识别答案并批改，请稍候..."):
                try:
                    # 构建表单数据
                    files = {"answer_image": answer_image}
                    data = {
                        "assessment_id": assessment_id,
                        "child_name": child_name,
                        "subject": subject
                    }

                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/assessment/grade",
                        files=files,
                        data=data,
                        timeout=180  # 3分钟超时
                    )

                    if response.status_code == 200:
                        st.session_state.grading_data = response.json()
                        st.success("✅ 批改完成！")
                    else:
                        st.error(f"❌ 批改失败: {response.text}")

                except requests.exceptions.Timeout:
                    st.error("❌ 请求超时，请稍后重试")
                except Exception as e:
                    st.error(f"❌ 发生错误: {str(e)}")

        # 显示批改结果
        if st.session_state.grading_data:
            st.markdown("---")
            st.markdown("### 📊 批改结果")

            grading = st.session_state.grading_data

            # 总分显示
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总分", f"{grading.get('total_score', 0)}/{grading.get('total_possible_score', 0)}")
            with col2:
                st.metric("准确率", f"{grading.get('accuracy', 0):.1%}")
            with col3:
                st.metric("错题数", grading.get('wrong_problems_count', 0))
            with col4:
                st.metric("正确数", grading.get('total_problems', 0) - grading.get('wrong_problems_count', 0))

            # 逐题显示
            st.markdown("### 逐题分析")
            grading_results = grading.get("grading_results", [])

            for result in grading_results:
                is_correct = result.get("is_correct", False)
                css_class = "grading-result-correct" if is_correct else "grading-result-wrong"

                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**题目 {result.get('problem_number')}:** {result.get('question', '')[:100]}...")
                with col2:
                    score = result.get('score', 0)
                    max_score = result.get('max_score', 10)
                    st.markdown(f"**得分:** {score}/{max_score} 分")

                st.markdown(f"**学生答案:** {result.get('student_answer', '')}")

                if not is_correct:
                    st.markdown(f"**正确答案:** {result.get('correct_answer', '')}")
                    st.markdown(f"**批改反馈:** {result.get('feedback', '')}")

                    suggestions = result.get('improvement_suggestions', [])
                    if suggestions:
                        st.markdown("**改进建议:**")
                        for suggestion in suggestions:
                            st.markdown(f"- {suggestion}")

                st.markdown('</div>', unsafe_allow_html=True)

            # 下载批改报告
            report_content = f"# 批改报告\n\n"
            report_content += f"**学生:** {child_name}\n"
            report_content += f"**学科:** {subject}\n"
            report_content += f"**总分:** {grading.get('total_score', 0)}/{grading.get('total_possible_score', 0)}\n"
            report_content += f"**准确率:** {grading.get('accuracy', 0):.1%}\n\n"
            report_content += "---\n\n"

            for result in grading_results:
                report_content += f"## 题目 {result.get('problem_number')}\n\n"
                report_content += f"**得分:** {result.get('score', 0)}/{result.get('max_score', 10)}\n\n"
                report_content += f"**学生答案:** {result.get('student_answer', '')}\n\n"
                if not result.get("is_correct", False):
                    report_content += f"**批改反馈:** {result.get('feedback', '')}\n\n"
                report_content += "---\n\n"

            st.download_button(
                label="📥 下载批改报告",
                data=report_content,
                file_name=f"{child_name}_{subject}_grading_report.md",
                mime="text/markdown"
            )

# ========== Tab 3: 学情分析 ==========
with tabs[2]:
    st.markdown('<div class="section-header">📈 学情分析</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        analytics_child = st.text_input("孩子姓名", value="小明", key="analytics_child")
    with col2:
        analytics_subject = st.selectbox(
            "学科",
            options=["数学", "语文", "英语", "物理", "化学", "生物", "历史", "地理"],
            key="analytics_subject"
        )

    # 筛选条件
    with st.expander("🔍 筛选条件"):
        min_difficulty = st.slider("最低难度", 1, 5, 1)
        max_accuracy = st.slider("最大准确率", 0.0, 1.0, 0.8, 0.1)

    if st.button("📊 生成学情分析", type="primary", use_container_width=True):
        with st.spinner("分析中..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/assessment/analytics",
                    json={
                        "child_name": analytics_child,
                        "subject": analytics_subject,
                        "min_difficulty": min_difficulty,
                        "max_accuracy": max_accuracy
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    analytics = response.json()

                    # 总览
                    st.markdown("### 总览")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("错题总数", analytics.get("total_wrong_problems", 0))
                    with col2:
                        st.metric("整体准确率", f"{analytics.get('overall_accuracy', 0):.1%}")

                    # 知识点分布
                    st.markdown("### 知识点掌握情况")
                    kp_distribution = analytics.get("knowledge_point_distribution", [])

                    if kp_distribution:
                        import pandas as pd
                        df = pd.DataFrame(kp_distribution)
                        st.dataframe(
                            df[["knowledge_point", "wrong_count", "avg_difficulty", "avg_accuracy"]],
                            use_container_width=True
                        )
                    else:
                        st.info("暂无数据")

                    # 薄弱点
                    st.markdown("### 薄弱知识点")
                    weak_points = analytics.get("weak_points", [])

                    if weak_points:
                        for wp in weak_points:
                            st.warning(f"⚠️ {wp}")
                    else:
                        st.success("✅ 暂无明显薄弱点")

                    # 复习建议
                    st.markdown("### 复习建议")
                    recommendations = analytics.get("review_recommendations", [])

                    for rec in recommendations:
                        with st.expander(f"{rec.get('knowledge_point')} - 优先级: {rec.get('priority')}"):
                            st.markdown(f"**原因:** {rec.get('reason')}")
                            st.markdown("**建议:**")
                            for action in rec.get('suggested_actions', []):
                                st.markdown(f"- {action}")

                else:
                    st.error(f"❌ 分析失败: {response.text}")

            except Exception as e:
                st.error(f"❌ 发生错误: {str(e)}")

# ========== 底部导航 ==========
st.markdown("---")
if st.button("← 返回首页"):
    st.switch_page("app.py")
