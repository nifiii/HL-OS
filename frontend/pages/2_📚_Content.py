"""
模块C: 教学内容生成界面
"""

import streamlit as st
import requests
import os
from typing import List, Dict, Any

# 配置
st.set_page_config(
    page_title="内容生成",
    page_icon="📚",
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
    .preview-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1.5rem;
        margin-top: 1rem;
        max-height: 600px;
        overflow-y: auto;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
            padding: 0 1rem;
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

        .stSlider {
            padding: 1rem 0;
        }

        .stNumberInput input {
            font-size: 1rem !important;
            padding: 0.75rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }

        .preview-box {
            padding: 1rem;
            max-height: 400px;
        }

        .stExpander {
            margin-bottom: 0.5rem;
        }
    }

    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem;
        }

        .section-header {
            font-size: 1.1rem;
        }

        .stButton button {
            font-size: 1.2rem !important;
            padding: 1rem !important;
            min-height: 56px !important;
        }

        h1, h2, h3 {
            font-size: 1.2rem !important;
        }

        .preview-box {
            padding: 0.75rem;
            font-size: 0.9rem;
        }
    }

    .stButton button:active {
        transform: scale(0.98);
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown('<div class="main-header">📚 教学内容生成系统</div>', unsafe_allow_html=True)

# 初始化 session state
if "preview_data" not in st.session_state:
    st.session_state.preview_data = None
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False

# ========== 第一步：基本信息 ==========
st.markdown('<div class="section-header">📝 第一步：基本信息</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    child_name = st.text_input(
        "孩子姓名 *",
        value="小明",
        help="输入孩子的姓名"
    )

with col2:
    subject = st.selectbox(
        "学科 *",
        options=["数学", "语文", "英语", "物理", "化学", "生物", "历史", "地理"],
        help="选择教学学科"
    )

# ========== 第二步：知识点选择 ==========
st.markdown('<div class="section-header">🎯 第二步：知识点选择</div>', unsafe_allow_html=True)

knowledge_source = st.radio(
    "知识点来源",
    options=["从错题本选择", "自定义输入"],
    horizontal=True
)

knowledge_points: List[str] = []

if knowledge_source == "从错题本选择":
    st.info("💡 系统会从错题本中提取常见知识点供您选择")

    # TODO: 从后端 API 获取错题本知识点
    # 当前为模拟数据
    available_knowledge_points = [
        "二次函数顶点式",
        "一元二次方程求根公式",
        "完全平方公式",
        "因式分解",
        "勾股定理"
    ]

    selected_points = st.multiselect(
        "选择知识点（可多选）",
        options=available_knowledge_points,
        default=[],
        help="从错题本中选择需要重点讲解的知识点"
    )

    knowledge_points = selected_points

else:  # 自定义输入
    custom_input = st.text_area(
        "输入知识点（每行一个）",
        value="",
        height=150,
        help="每行输入一个知识点，例如：\n- 二次函数顶点式\n- 配方法"
    )

    if custom_input.strip():
        knowledge_points = [kp.strip() for kp in custom_input.strip().split("\n") if kp.strip()]

# 显示当前选择的知识点
if knowledge_points:
    st.success(f"✅ 已选择 {len(knowledge_points)} 个知识点: {', '.join(knowledge_points)}")
else:
    st.warning("⚠️ 请至少选择一个知识点")

# ========== 第三步：参数配置 ==========
st.markdown('<div class="section-header">⚙️ 第三步：参数配置</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    difficulty = st.slider(
        "难度等级",
        min_value=1,
        max_value=5,
        value=3,
        help="1=基础，3=中等，5=困难"
    )
    st.caption(f"{'⭐' * difficulty} ({['基础', '较易', '中等', '较难', '困难'][difficulty-1]})")

with col2:
    style = st.selectbox(
        "教学风格",
        options=["启发式", "费曼式", "详解式", "实例驱动"],
        help="选择教学方法风格"
    )

with col3:
    duration_minutes = st.number_input(
        "目标时长（分钟）",
        min_value=5,
        max_value=120,
        value=30,
        step=5,
        help="课件预计讲解时长"
    )

# 高级选项
with st.expander("🔧 高级选项"):
    use_rag = st.checkbox(
        "使用 RAG 检索教材内容",
        value=True,
        help="启用后会从教材库中检索相关内容作为参考"
    )

    rag_top_k = st.slider(
        "RAG 检索数量",
        min_value=1,
        max_value=10,
        value=5,
        help="从教材库检索的相关段落数量"
    )

    additional_requirements = st.text_area(
        "额外要求（可选）",
        value="",
        height=100,
        help="例如：需要包含具体例题、强调易错点等"
    )

# ========== 第四步：生成与预览 ==========
st.markdown('<div class="section-header">🚀 第四步：生成与预览</div>', unsafe_allow_html=True)

# 生成按钮
generate_button_disabled = (
    not knowledge_points or
    not child_name.strip() or
    st.session_state.generation_in_progress
)

if st.button(
    "🎨 生成教学内容",
    type="primary",
    disabled=generate_button_disabled,
    use_container_width=True
):
    st.session_state.generation_in_progress = True

    with st.spinner("🤖 Claude 正在生成教学内容，请稍候..."):
        try:
            # 调用后端 API
            response = requests.post(
                f"{BACKEND_URL}/api/v1/teaching/generate",
                json={
                    "child_name": child_name,
                    "subject": subject,
                    "knowledge_points": knowledge_points,
                    "difficulty": difficulty,
                    "style": style,
                    "duration_minutes": duration_minutes,
                    "use_rag": use_rag,
                    "rag_top_k": rag_top_k,
                    "additional_requirements": additional_requirements or None
                },
                timeout=120  # 2分钟超时
            )

            if response.status_code == 200:
                result = response.json()
                preview_id = result.get("preview_id")

                # 获取预览内容
                preview_response = requests.get(
                    f"{BACKEND_URL}/api/v1/teaching/preview/{preview_id}",
                    timeout=10
                )

                if preview_response.status_code == 200:
                    st.session_state.preview_data = preview_response.json()
                    st.success("✅ 教学内容生成成功！")
                else:
                    st.error(f"❌ 获取预览失败: {preview_response.text}")
            else:
                st.error(f"❌ 生成失败: {response.text}")

        except requests.exceptions.Timeout:
            st.error("❌ 请求超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 网络错误: {str(e)}")
        except Exception as e:
            st.error(f"❌ 发生错误: {str(e)}")

    st.session_state.generation_in_progress = False

# 显示预览内容
if st.session_state.preview_data:
    st.markdown("---")
    st.markdown("### 📄 内容预览")

    preview = st.session_state.preview_data

    # 显示元信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("知识点数量", len(preview.get("knowledge_points", [])))
    with col2:
        st.metric("难度等级", f"{'⭐' * preview.get('difficulty', 3)}")
    with col3:
        st.metric("教学风格", preview.get("style", ""))
    with col4:
        st.metric("目标时长", f"{preview.get('duration_minutes', 0)} 分钟")

    # Marp 内容预览
    st.markdown("#### Marp 课件内容")
    with st.expander("📝 点击查看完整 Marp 源码", expanded=True):
        marp_content = preview.get("marp_content", "")
        st.code(marp_content, language="markdown", line_numbers=True)

    # ========== 第五步：审批 ==========
    st.markdown('<div class="section-header">✅ 第五步：审批与保存</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        modifications = st.text_area(
            "修改建议（可选）",
            value="",
            height=100,
            help="如需修改，请输入具体建议"
        )

    with col2:
        st.markdown("#### 操作")

        if st.button("✅ 通过并保存", type="primary", use_container_width=True):
            with st.spinner("保存中..."):
                try:
                    approval_response = requests.post(
                        f"{BACKEND_URL}/api/v1/teaching/approve",
                        json={
                            "preview_id": preview.get("preview_id"),
                            "approved": True,
                            "modifications": modifications or None
                        },
                        timeout=30
                    )

                    if approval_response.status_code == 200:
                        result = approval_response.json()
                        st.success(f"✅ 已保存到 Obsidian: {result.get('obsidian_file_path', '')}")
                        st.session_state.preview_data = None  # 清除预览
                        st.balloons()
                    else:
                        st.error(f"❌ 保存失败: {approval_response.text}")

                except Exception as e:
                    st.error(f"❌ 保存时发生错误: {str(e)}")

        if st.button("❌ 拒绝", use_container_width=True):
            rejection_reason = st.text_input("拒绝原因（可选）", value="")

            try:
                approval_response = requests.post(
                    f"{BACKEND_URL}/api/v1/teaching/approve",
                    json={
                        "preview_id": preview.get("preview_id"),
                        "approved": False,
                        "rejection_reason": rejection_reason or None
                    },
                    timeout=10
                )

                if approval_response.status_code == 200:
                    st.info("已拒绝该内容")
                    st.session_state.preview_data = None  # 清除预览
                else:
                    st.error(f"❌ 操作失败: {approval_response.text}")

            except Exception as e:
                st.error(f"❌ 发生错误: {str(e)}")

# ========== 底部导航 ==========
st.markdown("---")
if st.button("← 返回首页"):
    st.switch_page("app.py")
