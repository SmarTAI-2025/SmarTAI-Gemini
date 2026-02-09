import streamlit as st
import requests
# import os
# from PIL import Image
import time
from utils import *

# --- Page basic settings ---
# Use "wide" layout to get more space, and set page title and icon
st.set_page_config(
    page_title="Upload Homework - Intelligent Homework Verification System", 
    layout="wide",
    page_icon="📂"
)

def main():
    """Main function"""
    # Initialization
    initialize_session_state()
    load_custom_css()
    
    # Only reset grading state if we're starting a completely new grading process
    # Check if we have existing grading data that should be preserved
    if 'processed_data' not in st.session_state or not st.session_state.get('processed_data'):
        reset_grading_state()
    
    # Render page
    render_header()
    render_upload_section()

def render_header():
    """Render page header"""
    col1, col2, col3, _, col4 = st.columns([8,26,40,15,8])
    col = st.columns(1)[0]

    with col1:
        st.page_link("pages/main.py", label="Home", icon="🏠")

    with col2:
        st.page_link("pages/prob_upload.py", label="Re-upload Assignment Questions", icon="📤")

    with col3:
        st.page_link("pages/problems.py", label="Return to Question Recognition Overview", icon="📖")

    with col4:
        st.page_link("pages/history.py", label="History", icon="🕒")
    
    with col:
        st.markdown("""
    <div class="hero-section">
        <h1 style="text-align: center; color: #000000; margin-bottom: 1rem; font-weight: 700;">🎓 SmarTAI Intelligent Homework Assessment Platform</h1>
        <h4 style='text-align: center; color: #000000;'>Efficient, Intelligent, Comprehensive - Your Automated Teaching Assistant.</h4>
    </div>
    """, unsafe_allow_html=True)
        st.markdown("---")
        
def render_upload_section():
    """渲染作业上传核心功能区"""
    if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
        st.warning("Please upload the assignment problem file in the 'Upload Assignment Questions' page first.")
        st.stop()

    # --- 后端服务地址 ---
    # BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/hw_upload")

    # --- 初始化会话状态 ---
    # if 'processed_data' not in st.session_state:
    #     st.session_state.processed_data = None
    st.session_state.processed_data = None

    # 如果数据已处理，直接跳转，避免重复上传
    # if st.session_state.processed_data:
    #     st.switch_page("pages/problems.py")

    # # --- 页面标题和简介 ---
    # st.title("🚀 智能作业核查系统")
    # st.markdown("高效、智能、全面——您的自动化教学助理。")
    # st.markdown("---")


    # --- 1. 作业上传核心功能区 ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📂 Upload Student Homework")
    st.caption("Please compress all student homework files (e.g., PDF, Word, code files, images) into a single archive before uploading.")

    uploaded_hw_file = st.file_uploader(
        "Drag and drop or click to select homework archive",
        type=['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
        help="Supports common compression formats like .zip, .rar, .7z, .tar.gz."
    )
    if uploaded_hw_file is not None:
        st.success(f"File '{uploaded_hw_file.name}' selected.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. 确认与提交区 ---
    st.markdown("---")
    st.header("✅ Confirm and Start Verification")
    st.info("Please review the information above. Click the button below to start processing your files.")

    # 当用户上传了作业文件后，才激活确认按钮
    if uploaded_hw_file is not None:
        if st.button("Confirm and Start Intelligent Verification", type="primary", width='stretch'):
            # Check if there's already an active grading task
            if is_grading_in_progress():
                st.error("A grading task is currently in progress. Submitting a new task is not allowed. Please wait.")
                return
                
            with st.spinner("Uploading and requesting AI analysis, please wait a few minutes..."):
                # 准备要发送的文件
                files_to_send = {
                    "file": (uploaded_hw_file.name, uploaded_hw_file.getvalue(), uploaded_hw_file.type)
                }
                # (这里可以添加逻辑来处理其他上传的文件，例如答案、测试用例等)
                # st.session_state.task_name=uploaded_hw_file.name
                try:
                    # 实际使用时，你需要根据后端API来组织和发送所有数据
                    response = requests.post(f"{st.session_state.backend}/hw_preview/", files=files_to_send, timeout=600)
                    response.raise_for_status()

                    # st.session_state.processed_data = response.json()      
                    students = response.json()                            
                    st.session_state.processed_data = students   #以stu_id为key索引

                    # print(st.session_state.processed_data)
          
                    st.success("✅ File uploaded successfully, backend processing started! Redirecting to preview page...")
                    time.sleep(1) # 短暂显示成功信息
                    st.switch_page("pages/stu_preview.py")

                except requests.exceptions.RequestException as e:
                    st.error(f"Network or server error: {e}")
                except Exception as e:
                    st.error(f"Unknown error occurred: {e}")
    else:
        # 如果用户还未上传文件，则按钮禁用
        st.button("Confirm and Start Intelligent Verification", type="primary", width='stretch', disabled=True)
        st.warning("Please upload the student homework archive above first.")

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
    keys_to_clear = [
        'ai_grading_data',
        'sample_data',
        'selected_job_id',
        'report_job_selector',
        'selected_job_from_history'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()