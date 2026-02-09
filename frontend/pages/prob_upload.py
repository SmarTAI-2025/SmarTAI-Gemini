import streamlit as st
import requests
import os
# from PIL import Image
import time
from utils import *
import hashlib
from datetime import datetime
import json

# --- Page basic settings ---
# Use "wide" layout to get more space, and set page title and icon
st.set_page_config(
    page_title="Upload Assignment Questions - Intelligent Homework Verification System", 
    layout="wide",
    page_icon="📂"
)

KNOWLEDGE_BASE_DIR = "knowledge_bases"
KNOWLEDGE_BASE_CONFIG = "knowledge_base_config.json"

def save_knowledge_base_config():
    """Save knowledge base configuration"""
    try:
        with open(KNOWLEDGE_BASE_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.knowledge_bases, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        st.error(f"Failed to save knowledge base configuration: {e}")

def create_knowledge_base(name: str, description: str, category: str = "General"):
    """Create new knowledge base"""
    kb_id = f"kb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
    kb_path = os.path.join(KNOWLEDGE_BASE_DIR, kb_id)
    
    if not os.path.exists(kb_path):
        os.makedirs(kb_path)
    
    kb_info = {
        "id": kb_id,
        "name": name,
        "description": description,
        "category": category,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "file_count": 0,
        "total_size": 0,
        "files": {}
    }
    
    st.session_state.knowledge_bases[kb_id] = kb_info
    save_knowledge_base_config()
    return kb_id

def add_file_to_kb(kb_id: str, file_name: str, file_content: bytes, file_type: str = "unknown"):
    """向知识库添加文件"""
    if kb_id not in st.session_state.knowledge_bases:
        return False
    
    kb_path = os.path.join(KNOWLEDGE_BASE_DIR, kb_id)
    file_path = os.path.join(kb_path, file_name)
    
    try:
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 更新配置
        file_id = hashlib.md5((file_name + datetime.now().isoformat()).encode()).hexdigest()[:12]
        file_info = {
            "id": file_id,
            "name": file_name,
            "type": file_type,
            "size": len(file_content),
            "uploaded_at": datetime.now().isoformat(),
            "path": file_path
        }
        
        st.session_state.knowledge_bases[kb_id]["files"][file_id] = file_info
        st.session_state.knowledge_bases[kb_id]["file_count"] += 1
        st.session_state.knowledge_bases[kb_id]["total_size"] += len(file_content)
        st.session_state.knowledge_bases[kb_id]["updated_at"] = datetime.now().isoformat()
        
        save_knowledge_base_config()
        return True
    except Exception as e:
        st.error(f"Failed to add file: {e}")
        return False
    
def main():
    """主函数"""
    # 初始化
    initialize_session_state()
    load_custom_css()
    
    # ------------------ ✅ 新增修复代码开始 ------------------
    # 检查内存中是否已有数据，如果没有，尝试从 JSON 文件加载
    if 'knowledge_bases' not in st.session_state or not st.session_state.knowledge_bases:
        st.session_state.knowledge_bases = {} # 先初始化为空字典
        
        # 如果配置文件存在，读取文件内容
        if os.path.exists(KNOWLEDGE_BASE_CONFIG):
            try:
                with open(KNOWLEDGE_BASE_CONFIG, 'r', encoding='utf-8') as f:
                    st.session_state.knowledge_bases = json.load(f)
                # print(f"成功加载知识库配置: {len(st.session_state.knowledge_bases)} 个知识库")
            except Exception as e:
                st.error(f"Failed to read knowledge base configuration file: {e}")
                # 如果读取失败，保持为空字典，避免程序崩溃
                st.session_state.knowledge_bases = {}
    # ------------------ ✅ 新增修复代码结束 ------------------
    
    # Only reset grading state if we're starting a completely new grading process
    # Check if we have existing problem data that should be preserved
    if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
        reset_grading_state()
    
    # 渲染页面
    render_header()
    render_upload_section()

def render_header():
    """渲染页面头部"""
    col1, _, col2 = st.columns([8,50,8])
    col = st.columns(1)[0]

    with col1:
        st.page_link("pages/main.py", label="Back to Home", icon="🏠")
    
    with col2:
        st.page_link("pages/history.py", label="History", icon="🕒")
    
    with col:
        st.markdown("""
    <div class="hero-section">
        <h1 style="text-align: center; color: #000000; margin-bottom: 1rem; font-weight: 700;">🎓 SmarTAI Intelligent Assignment Assessment Platform</h1>
        <h4 style='text-align: center; color: #000000;'>Efficient, intelligent, comprehensive — your automated teaching assistant.</h4>
    </div>
    """, unsafe_allow_html=True)
        st.markdown("---")
        
def render_upload_section():
    """渲染作业上传部分"""
    # --- 后端服务地址 ---
    # BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/hw_upload")

    # --- 初始化会话状态 ---
    # if 'prob_data' not in st.session_state:
    #     st.session_state.prob_data = None
    st.session_state.prob_data = None

    # 如果数据已处理，直接跳转，避免重复上传
    # if st.session_state.prob_data:
    #     st.switch_page("pages/problems.py")

    # --- 页面标题和简介 ---
    # st.title("🚀 智能作业核查系统")
    # st.markdown("高效、智能、全面——您的自动化教学助理。")
    # st.markdown("---")


    # --- 作业上传核心功能区 ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📂 Upload Assignment Problems")
    st.caption("Please upload the problem file for this assignment.")

    uploaded_prob_file = st.file_uploader(
        "Upload Problem File",
        type=["txt", "pdf", "docx"],
        help="Provide standard problems; AI will automatically identify question types."
    )
    if uploaded_prob_file is not None:
        st.success(f"File '{uploaded_prob_file.name}' selected.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

    # --- 高级选项配置区 (默认展开) ---
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("⚙️ Advanced Options")

        # # --- 新增：多模型协同批改设置 ---
        # st.subheader("🤖 Multi-model Collaborative Grading")
        # st.caption("Introduce multiple expert models for collaborative grading across disciplines.")

        # # 预设可选的AI模型列表
        # available_models = ["Gemini", "ChatGPT", "DeepSeek", "ZhiPuAI (GLM)", "Claude"]
        
        # selected_models = st.multiselect(
        #     "Select AI models for collaborative grading (multi-select)",
        #     options=available_models,
        #     default=["Gemini", "ChatGPT"],
        #     help="SmarTAI will match relevant expert models and aggregate scores based on confidence."
        # )

        # # 初始化或更新模型权重
        # if 'ai_weights' not in st.session_state:
        #     st.session_state.ai_weights = {}

        # # 仅当用户选择了模型后，才显示权重设置
        # if selected_models:
        #     st.markdown("##### Model Weight Configuration")
            
        #     # 使用字典来存储权重，以便于后续处理
        #     current_weights = {}
            
        #     # 为了更好的布局，每行最多显示两个滑块
        #     cols = st.columns(2)
        #     col_idx = 0
            
        #     for model in selected_models:
        #         with cols[col_idx]:
        #             # 固定权重为50，不可滑动
        #             st.slider(
        #                 f"'{model}' Weight",
        #                 min_value=0,
        #                 max_value=100,
        #                 value=50,
        #                 key=f"weight_{model}",
        #                 disabled=True  # 禁用滑块
        #             )
        #             current_weights[model] = 50  # 固定设置为50
        #         # 切换到下一列
        #         col_idx = (col_idx + 1) % 2
            
        #     # 更新session_state中的权重记录
        #     st.session_state.ai_weights = current_weights
            
        #     st.info("Tip: All model weights are fixed at 50; the system will adjust final scores automatically based on confidence.")
        # else:
        #     st.warning("Please select at least one AI model to proceed.")
        
        # st.markdown("---")


        # --- 评分与批改设置 (原代码，可稍作标题调整以更好地区分) ---
        st.subheader("📝 Scoring Criteria")

        # 上传参考答案
        uploaded_answer_file = st.file_uploader(
            "Upload Reference Answer (optional)",
            help="Provide a standard answer file. AI will use it as a key reference."
        )

        # 评分细则
        scoring_method = st.radio(
            "Scoring mode",
            options=("Preset Strictness", "Custom Rubric"),
            help="Select a preset scoring standard or provide a detailed rubric."
        )

        if scoring_method == "Preset Strictness":
            strictness = st.selectbox(
                "Select strictness level",
                options=["Lenient", "Moderate", "Strict"],
                index=1
            )
        else:
            st.info("You can describe scoring points below or upload a rubric file.")
            scoring_desc = st.text_area(
                "Describe your scoring requirements in natural language",
                placeholder="e.g., Q1 worth 30 points: steps 10, computation 10, final result 10..."
            )
            rubric_file = st.file_uploader("Or upload a rubric file (optional)", type=["pdf", "docx"])

        st.markdown("---")

        # --- 编程题专项设置 ---
        st.subheader("💻 Programming-specific Settings")
        uploaded_test_cases = st.file_uploader(
            "Upload Test Cases (optional)",
            help="Upload test input and expected output files for code questions."
        )
        st.caption("ℹ️ If not provided, the system will try to auto-generate generic test data.")

        st.markdown("---")

        # --- 专业知识库配置 ---
        st.subheader("📚 Configure Knowledge Base")
        st.caption("Upload relevant textbooks, handouts, or references. AI will consult them during analysis and grading for more professional feedback.")

        kb_choice = st.radio(
            "Knowledge Base Options",
            options=("Do not use", "Use Existing Knowledge Base", "Create New Knowledge Base")
        )

        if kb_choice == "Use Existing Knowledge Base":
            kb_list = st.session_state.get("knowledge_bases", {})
            if not kb_list:
                st.warning("No available knowledge base. Please create one first.")
            else:
                kb_options = {kb_id: kb_info["name"] for kb_id, kb_info in kb_list.items()}
                selected_kb_id = st.selectbox("Select an existing knowledge base", options=list(kb_options.keys()), format_func=lambda k: kb_options[k])
                st.success(f"Selected knowledge base: **{kb_options[selected_kb_id]}**")
        elif kb_choice == "Create New Knowledge Base":
            st.markdown("##### 1. Choose Category")
            categories = ["General", "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Other"]
            if "category_selection" not in st.session_state:
                st.session_state.category_selection = "General"
            st.selectbox("Category", categories, key="category_selection")
            st.markdown("#### 2. Fill in details")
            with st.form("create_kb_form"):
                new_kb_name = st.text_input("New Knowledge Base Name*", placeholder="e.g., Advanced Calculus - Chapter 5 - Key Points")
                new_kb_desc = st.text_area("Knowledge Base Description (optional)", placeholder="Briefly describe included content, course, or chapters.")
                new_kb_category = None
                if st.session_state.category_selection == "Other":
                    new_kb_category = st.text_input("Custom Category", placeholder="Enter a custom category...")
                kb_files = st.file_uploader("Upload Knowledge Base Files (multi-select)", accept_multiple_files=True)
                submitted = st.form_submit_button("✅ Create Knowledge Base", type="primary", use_container_width=True)
            if submitted:
                if not new_kb_name:
                    st.error("Knowledge base name cannot be empty.")
                elif not kb_files:
                    st.error("Please upload at least one knowledge base file.")
                else:
                    final_category = new_kb_category or "General"
                    with st.spinner(f"Creating knowledge base '{new_kb_name}'..."):
                        # 调用您已有的函数来创建知识库
                        kb_id = create_knowledge_base(new_kb_name, new_kb_desc, final_category)
                        
                        # 如果有上传文件，则添加到知识库中
                        if kb_files:
                            success_count = 0
                            for uploaded_file in kb_files:
                                file_content = uploaded_file.read()
                                file_type = uploaded_file.type or "unknown"
                                if add_file_to_kb(kb_id, uploaded_file.name, file_content, file_type):
                                    success_count += 1
                            st.success(f"✅ Knowledge base '{new_kb_name}' created successfully and uploaded {len(kb_files)} files!")
                            st.caption("Tip: Created knowledge bases are saved to your account for future reuse.")

    st.markdown('</div>', unsafe_allow_html=True)


    # --- 确认与提交区 ---
    st.markdown("---")
    st.header("✅ Confirm and Start Problem Recognition")
    st.info("Please review the above information. Click the button below to start processing your files.")

    # 当用户上传了作业文件后，才激活确认按钮
    if uploaded_prob_file:
        if st.button("Confirm information and start intelligent recognition", type="primary", use_container_width=True):
            # Check if there's already an active grading task
            if is_grading_in_progress():
                st.error("A grading task is currently in progress. New submissions are not allowed at this time. Please wait.")
                return
                
            with st.spinner("Uploading and requesting AI analysis, please wait a few minutes..."):
                # 准备要发送的文件
                files_to_send = {
                    "file": (uploaded_prob_file.name, uploaded_prob_file.getvalue(), uploaded_prob_file.type)
                }
                # (这里可以添加逻辑来处理其他上传的文件，例如答案、测试用例等)
                st.session_state.task_name=uploaded_prob_file.name
                try:
                    # TODO: 实际使用时，你需要根据后端API来组织和发送所有数据
                    response = requests.post(f"{st.session_state.backend}/prob_preview/", files=files_to_send, timeout=600)
                    response.raise_for_status()
                    
                    problems = response.json()
                    # Store the data in the correct format for problems.py
                    # The backend returns a dictionary with q_id as keys, which is what we need
                    st.session_state.prob_data = problems
                            
                    st.success("✅ File uploaded successfully, backend processing started! Redirecting to preview page...")
                    time.sleep(1) # 短暂显示成功信息
                    st.switch_page("pages/problems.py")

                except requests.exceptions.RequestException as e:
                    st.error(f"Network or server error: {e}")
                except Exception as e:
                    st.error(f"Unknown error occurred: {e}")
    else:
        # 如果用户还未上传文件，则按钮禁用
        st.button("Confirm information and start intelligent checking", type="primary", use_container_width=True, disabled=True)
        st.warning("Please upload the assignment problems above first.")

def is_grading_in_progress():
    """Check if there's an active grading task in progress"""
    # Check if there's a checking_job_id in session state
    return 'checking_job_id' in st.session_state

def reset_grading_state():
    """Reset grading state to allow fresh grading"""
    try:
        # Reset backend grading state
        response = requests.delete(
            f"{st.session_state.backend}/ai_grading/reset_all_grading",
            timeout=5
        )
        if response.status_code == 200:
            print("Backend grading state reset successfully")
        else:
            print(f"Failed to reset backend grading state: {response.status_code}")
    except Exception as e:
        print(f"Error resetting backend grading state: {e}")
    
    # Clear frontend grading-related session state
    # Preserve completed results and analysis data
    keys_to_clear = [
        'ai_grading_data',
        'report_job_selector',
        'selected_job_from_history'
    ]
    
    # Only clear sample_data if it's not MOCK_JOB_001
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id != "MOCK_JOB_001":
        keys_to_clear.append('sample_data')
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()