"""
模块A: 作业校验界面（移动端优化版）
"""

import streamlit as st
import requests
import os
from io import BytesIO

st.set_page_config(
    page_title="作业校验",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="auto"
)

# 移动端优化CSS
st.markdown("""
<style>
    /* 移动端适配 */
    @media (max-width: 768px) {
        /* 标题字体 */
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }

        /* 内容区域间距 */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 0.5rem !important;
        }

        /* 按钮优化 */
        .stButton button {
            font-size: 1.1rem !important;
            padding: 0.75rem 1rem !important;
            min-height: 48px !important;
            border-radius: 8px !important;
        }

        /* 文件上传器优化 */
        [data-testid="stFileUploader"] {
            font-size: 1rem !important;
        }

        /* 输入框优化 */
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            font-size: 1rem !important;
            padding: 0.75rem !important;
        }

        /* Tab 优化 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem !important;
            padding: 0.5rem 0.75rem !important;
        }

        /* 图片容器优化 */
        [data-testid="stImage"] {
            margin-bottom: 1rem;
        }

        /* Slider 优化 */
        .stSlider {
            padding: 1rem 0;
        }

        /* Multiselect 优化 */
        .stMultiSelect {
            font-size: 0.9rem !important;
        }

        /* Checkbox 增大点击区域 */
        .stCheckbox {
            padding: 0.5rem 0;
        }

        .stCheckbox label {
            font-size: 1rem !important;
        }
    }

    /* 小屏幕适配 */
    @media (max-width: 480px) {
        h1 {
            font-size: 1.3rem !important;
        }

        .stButton button {
            font-size: 1.2rem !important;
            padding: 1rem !important;
            min-height: 56px !important;
        }

        .stTextArea textarea {
            font-size: 1rem !important;
            min-height: 200px !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem !important;
            padding: 0.4rem 0.6rem !important;
        }
    }

    /* 触摸友好 */
    .stButton button:active {
        transform: scale(0.98);
    }

    /* 图片预览优化 */
    .validation-image {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("📸 作业校验系统")
st.markdown("拍照上传作业，AI识别后进行人工校验")

# 后端API地址
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 侧边栏配置
with st.sidebar:
    st.subheader("⚙️ 配置")
    child_name = st.text_input("孩子姓名", value="张三")
    subject = st.selectbox("学科", ["数学", "语文", "英语", "物理", "化学"])
    content_type = st.selectbox(
        "内容类型",
        ["homework", "test", "textbook", "worksheet"],
        format_func=lambda x: {
            "homework": "📝 作业",
            "test": "📋 试卷",
            "textbook": "📚 教材",
            "worksheet": "📄 练习"
        }[x]
    )

    st.markdown("---")
    st.caption("💡 提示：先上传图片，识别后再校验")

# 主内容区
tab1, tab2, tab3 = st.tabs(["📤 上传", "✏️ 校验", "📁 历史"])

# ========== Tab 1: 上传图片 ==========
with tab1:
    st.subheader("📷 拍照或上传作业图片")

    uploaded_file = st.file_uploader(
        "选择图片文件",
        type=["jpg", "jpeg", "png"],
        help="支持JPG、PNG格式，最大10MB"
    )

    if uploaded_file:
        # 图片预览（移动端全宽显示）
        st.image(uploaded_file, caption="📸 上传的图片", use_container_width=True)

        # 图片信息（使用 expander 节省空间）
        with st.expander("📊 查看图片信息"):
            st.write(f"**文件名:** {uploaded_file.name}")
            st.write(f"**文件大小:** {uploaded_file.size / 1024:.2f} KB")
            st.write(f"**文件类型:** {uploaded_file.type}")

        st.markdown("---")

        # 识别按钮（移动端友好）
        if st.button("🚀 开始AI识别", type="primary", use_container_width=True):
            with st.spinner("🤖 AI正在识别中，请稍候..."):
                try:
                    # 调用后端API
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {
                        "child_name": child_name,
                        "subject": subject,
                        "content_type": content_type
                    }

                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/perception/upload",
                        files=files,
                        data=data,
                        timeout=60
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ 识别完成！任务ID: {result['task_id']}")

                        # 保存到session state
                        st.session_state['last_task_id'] = result['task_id']
                        st.session_state['last_image'] = uploaded_file.getvalue()
                        st.session_state['ocr_result'] = result.get('result', {})

                        # 引导用户切换Tab
                        st.info("👉 请切换到 **✏️ 校验** 标签进行人工确认")
                    else:
                        st.error(f"❌ 识别失败: {response.text}")

                except Exception as e:
                    st.error(f"❌ 请求失败: {str(e)}")
                    st.info("💡 确保后端服务已启动并配置正确的BACKEND_URL")

# ========== Tab 2: 校验内容 ==========
with tab2:
    st.subheader("✏️ 校验AI识别结果")

    if 'last_task_id' in st.session_state:
        task_id = st.session_state['last_task_id']

        # 移动端：垂直布局，桌面端：三栏布局
        # 使用 expander 来节省移动端空间

        # 1. 原始图片（可折叠）
        with st.expander("📸 查看原始图片", expanded=False):
            if 'last_image' in st.session_state:
                st.image(st.session_state['last_image'], use_container_width=True)

        # 2. AI识别结果
        st.markdown("**🤖 AI识别结果**")
        ocr_result = st.session_state.get('ocr_result', {})
        ai_text = ocr_result.get('text', '示例：\n1. 已知函数 f(x) = 2x + 3，求 f(5) 的值。\n学生答案：13 ✓')

        st.text_area(
            "识别文本",
            value=ai_text,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )

        st.markdown("---")

        # 3. 人工校验输入
        st.markdown("**✍️ 修正文本（如有错误）**")
        corrected_text = st.text_area(
            "修正文本",
            value="",
            height=200,
            placeholder="如果AI识别有误，请在此修正...\n没有错误可留空直接提交",
            label_visibility="collapsed"
        )

        # 元数据配置（使用 expander）
        st.markdown("---")
        with st.expander("⚙️ 元数据设置", expanded=True):
            difficulty = st.slider("难度等级", 1, 5, 3, help="1=基础，5=困难")

            tags = st.multiselect(
                "标签",
                ["待复习", "已掌握", "重难点", "基础概念", "拔高题"],
                default=[]
            )

            knowledge_points = st.text_input(
                "知识点",
                placeholder="例如：一次函数, 函数值"
            )

        # 保存选项
        st.markdown("---")
        st.markdown("**💾 保存设置**")

        save_col1, save_col2 = st.columns(2)
        with save_col1:
            save_to_obsidian = st.checkbox("✅ 保存到Obsidian", value=True)
        with save_col2:
            embed_in_anythingllm = st.checkbox("🔍 嵌入AnythingLLM", value=True)

        folder_type = st.selectbox(
            "保存位置",
            ["No_Problems", "Wrong_Problems", "Cards"],
            format_func=lambda x: {
                "No_Problems": "📝 已完成作业",
                "Wrong_Problems": "❌ 错题本",
                "Cards": "💡 知识卡片"
            }[x]
        )

        # 提交按钮（移动端友好）
        st.markdown("---")
        if st.button("✅ 确认并保存", type="primary", use_container_width=True):
            with st.spinner("💾 保存中..."):
                try:
                    # 调用 validation API
                    final_text = corrected_text if corrected_text.strip() else ai_text

                    payload = {
                        "task_id": task_id,
                        "child_name": child_name,
                        "subject": subject,
                        "folder_type": folder_type,
                        "corrected_content": final_text,
                        "metadata": {
                            "Difficulty": difficulty,
                            "Tags": tags,
                            "Knowledge_Points": knowledge_points.split(",") if knowledge_points else []
                        },
                        "save_to_obsidian": save_to_obsidian,
                        "embed_in_anythingllm": embed_in_anythingllm
                    }

                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/validation/submit",
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ 保存成功！")
                        st.balloons()

                        if result.get('obsidian_file_path'):
                            st.info(f"📁 Obsidian: {result['obsidian_file_path']}")
                        if result.get('embedding_status') == 'queued':
                            st.info("🔄 AnythingLLM 嵌入任务已加入队列")

                        # 清除 session state
                        if st.button("🔄 继续校验新作业"):
                            del st.session_state['last_task_id']
                            del st.session_state['last_image']
                            st.rerun()
                    else:
                        st.error(f"❌ 保存失败: {response.text}")

                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
    else:
        st.info("👆 请先在 **📤 上传** 标签中上传并识别图片")

# ========== Tab 3: 历史记录 ==========
with tab3:
    st.subheader("📁 历史校验记录")
    st.info("🚧 功能开发中...")
    st.markdown("""
    **即将支持：**
    - 查看最近校验的作业
    - 按学科筛选
    - 按日期筛选
    - 快速跳转到 Obsidian 文件
    """)

# 页脚
st.markdown("---")
if st.button("🏠 返回首页", use_container_width=True):
    st.switch_page("app.py")
