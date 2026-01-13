"""
HL-OS Streamlit前端 - 家长控制面板（移动端优化版）
"""

import streamlit as st
import os

# 页面配置
st.set_page_config(
    page_title="HL-OS 家长控制面板",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"  # 移动端自动折叠
)

# 移动端优化CSS
st.markdown("""
<style>
    /* 基础样式 */
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
        color: #2ca02c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        /* 标题字体缩小 */
        .main-header {
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding: 0 1rem;
        }

        .section-header {
            font-size: 1.3rem;
            margin-top: 1.5rem;
            padding: 0 0.5rem;
        }

        /* 调整内容区域内边距 */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }

        /* 优化按钮样式 */
        .stButton button {
            font-size: 1.1rem !important;
            padding: 0.75rem 1rem !important;
            min-height: 48px !important;
            width: 100% !important;
        }

        /* 优化统计卡片 */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
        }

        /* 侧边栏优化 */
        [data-testid="stSidebar"] {
            width: 250px !important;
        }

        /* 列间距调整 */
        [data-testid="column"] {
            padding: 0.5rem !important;
        }
    }

    /* 小屏幕适配（手机竖屏）*/
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .section-header {
            font-size: 1.1rem;
            margin-top: 1rem;
        }

        /* 进一步增大按钮 */
        .stButton button {
            font-size: 1.2rem !important;
            padding: 1rem !important;
            min-height: 56px !important;
        }

        /* 优化文本大小 */
        p, li {
            font-size: 0.95rem !important;
        }

        /* 统计卡片更紧凑 */
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }
    }

    /* 触摸友好的按钮样式 */
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s;
    }

    .stButton button:active {
        transform: scale(0.98);
    }

    /* 页脚样式 */
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding: 1rem;
    }

    @media (max-width: 480px) {
        .footer {
            font-size: 0.8rem;
            padding: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 检测设备类型
def is_mobile():
    """简单的移动端检测（通过屏幕宽度）"""
    return st.session_state.get('is_mobile', False)

# 主页面
st.markdown('<div class="main-header">🎓 HL-OS 家庭智能学习系统</div>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.title("📱 导航")
    st.markdown("---")

    # 系统状态
    st.subheader("系统状态")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    st.info(f"🔗 后端API: {backend_url}")

    st.markdown("---")

    # 功能模块
    st.subheader("功能模块")
    st.page_link("pages/1_📸_Validation.py", label="📸 作业校验", use_container_width=True)
    st.page_link("pages/2_📚_Content.py", label="📚 内容生成", use_container_width=True)
    st.page_link("pages/3_📝_Assessment.py", label="📝 评测管理", use_container_width=True)

    st.markdown("---")

    # 移动端提示
    st.caption("💡 提示：在移动设备上点击左上角菜单图标可展开导航")

# 主内容区 - 响应式布局
# 使用 st.container 和条件渲染实现移动端单列布局
st.markdown("### 🚀 快速开始")

# 功能卡片 1: 感知与校验
with st.container():
    st.markdown('<div class="section-header">📸 感知与校验</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        - 📷 拍照上传作业/试卷
        - 🤖 AI自动OCR识别
        - ✅ 家长校验确认
        - 📁 自动分类存储
        """)
    with col2:
        if st.button("开始", key="btn_validation", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📸_Validation.py")

st.markdown("---")

# 功能卡片 2: 教学内容
with st.container():
    st.markdown('<div class="section-header">📚 教学内容</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        - 🎯 选择知识点
        - ⚙️ 设定难度和风格
        - 🎨 AI生成个性化课件
        - 👀 预览和确认推送
        """)
    with col2:
        if st.button("生成", key="btn_content", use_container_width=True, type="primary"):
            st.switch_page("pages/2_📚_Content.py")

st.markdown("---")

# 功能卡片 3: 评测引擎
with st.container():
    st.markdown('<div class="section-header">📝 评测引擎</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        - 📋 配置考察范围
        - 📊 设定难度分布
        - 💡 AI生成原创题目
        - ✏️ 自动批改分析
        """)
    with col2:
        if st.button("创建", key="btn_assessment", use_container_width=True, type="primary"):
            st.switch_page("pages/3_📝_Assessment.py")

# 快速统计
st.markdown("---")
st.markdown("### 📊 数据统计")

# 使用两行两列布局，更适合移动端
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    st.metric("今日校验", "0", delta="作业", delta_color="off")

with row1_col2:
    st.metric("错题本", "0", delta="题目", delta_color="off")

with row2_col1:
    st.metric("知识卡片", "0", delta="张", delta_color="off")

with row2_col2:
    st.metric("完成课件", "0", delta="份", delta_color="off")

# 页脚
st.markdown("---")
st.markdown("""
<div class="footer">
    HL-OS v1.0.0 | 家庭智能学习系统<br>
    Powered by Claude & Gemini
</div>
""", unsafe_allow_html=True)
