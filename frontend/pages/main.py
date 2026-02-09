"""
SmarTAI项目 - 主应用入口文件

智能评估平台的主界面，提供导航和核心功能入口
"""

import streamlit as st
import sys
import os
import json
import requests
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from utils.py (the file, not the folder)
from utils import *
# Import from frontend_utils (the folder we renamed)
from frontend_utils.data_loader import load_ai_grading_data, StudentScore, QuestionAnalysis, AssignmentStats
from frontend_utils.chart_components import create_score_distribution_chart, create_grade_pie_chart

# Get backend URL - from environment variable or hardcoded default
BACKEND_URL = os.environ.get("BACKEND_URL", UTILS_BACKEND_URL)

# 页面配置
st.set_page_config(
    page_title="SmarTAI - Intelligent Assessment Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Quick validation to check if backend is accessible
# This validation will be done later in the init_session_state function
# to ensure the BACKEND_URL is properly set

def load_mock_data():
    """Load mock data for testing when real data is not available"""
    try:
        # Try to load from root directory first (where the file actually is)
        mock_data_path = os.path.join(os.path.dirname(__file__), "..", "mock_data.json")
        if not os.path.exists(mock_data_path):
            # Fallback to frontend directory
            mock_data_path = os.path.join(os.path.dirname(__file__), "mock_data.json")
        
        with open(mock_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Convert string dates back to datetime objects
        for student in data["student_scores"]:
            if isinstance(student["submit_time"], str):
                student["submit_time"] = datetime.fromisoformat(student["submit_time"])
        
        if isinstance(data["assignment_stats"]["create_time"], str):
            data["assignment_stats"]["create_time"] = datetime.fromisoformat(data["assignment_stats"]["create_time"])
        
        # Convert to proper dataclass objects
        student_scores = []
        for student_data in data["student_scores"]:
            student_scores.append(StudentScore(**student_data))
        
        question_analysis = []
        for question_data in data["question_analysis"]:
            question_analysis.append(QuestionAnalysis(**question_data))
        
        assignment_stats = AssignmentStats(**data["assignment_stats"])
        
        return {
            "student_scores": student_scores,
            "question_analysis": question_analysis,
            "assignment_stats": assignment_stats
        }
    except Exception as e:
        st.error(f"Failed to load mock data: {str(e)}")
        # return create_default_data()

def init_session_state():
    """初始化会话状态"""
    # Initialize session state from utils.py
    initialize_session_state()
    
    # Set logged in state
    st.session_state.logged_in = True
    
    # Check backend connectivity - 使用 session_state 中的 backend URL
    try:
        response = requests.get(f"{st.session_state.backend}/docs", timeout=5)
        st.session_state.backend_status = "connected"
    except:
        st.session_state.backend_status = "disconnected"
        st.warning("Connecting to backend. Please wait ~30s then click the refresh button below.")
    
    # Initialize sample data or AI grading data
    if 'sample_data' not in st.session_state:
        with st.spinner("Initializing system data..."):
            # Set default job to MOCK_JOB_001
            st.session_state.selected_job_id = "MOCK_JOB_001"
            
            # Try to load AI grading data if a job is selected
            if 'selected_job_id' in st.session_state:
                ai_data = load_ai_grading_data(st.session_state.selected_job_id)
                if "error" not in ai_data:
                    st.session_state.sample_data = ai_data
                else:
                    # Load mock data if AI data loading fails
                    st.session_state.sample_data = load_mock_data()
            else:
                # Load mock data when no job is selected (before any grading)
                st.session_state.sample_data = load_mock_data()
    
    # Don't load mock jobs from file, use static mock data in history pages instead
    # This prevents the continuous submission of mock grading tasks
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {
            'name': 'Mr. Zhang',
            'role': 'Instructor',
            'department': 'School of Computer Science and Technology'
        }

def render_hero_section():
    """渲染主题部分"""
    st.markdown("""
    <div class="hero-section">
        <h1 style="text-align: center; color: #000000; margin-bottom: 1rem; font-weight: 700;">🎓 SmarTAI</h1>
        <h2 style="text-align: center; color: #000000; margin-bottom: 0.5rem; opacity: 0.9;">Intelligent Assignment Assessment Platform</h2>
        <h4 style='text-align: center; color: #000000;'>Efficient, intelligent, comprehensive — your automated teaching assistant.</h4>
        <p style="font-size: 1.125rem; opacity: 0.8; max-width: 600px; margin: 0 auto;">
            Based on artificial intelligence, providing intelligent grading, deep analysis and visual reports
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def render_user_welcome():
    """渲染用户欢迎信息"""
    user_info = st.session_state.user_info
    col1, col2,col3 = st.columns([35,35,15])
    
    with col1:
        # 显示登录用户信息
        username = st.session_state.get('username', user_info['name'])
        st.markdown(f"""
        ### 👋 Welcome back, {username}!
        **{user_info['role']}** | {user_info['department']}
        """)
    
    with col2:
        current_time = datetime.now()
        st.markdown(f"""
        ### 📅 Today's Information
        **Date:** {current_time.strftime('%Y-%m-%d')}
        **Time:** {current_time.strftime('%H:%M')}
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Refresh Data", width='content'):
            # Refresh data based on selected job or default data without resetting grading state
            if 'selected_job_id' in st.session_state:
                ai_data = load_ai_grading_data(st.session_state.selected_job_id)
                if "error" not in ai_data:
                    st.session_state.sample_data = ai_data
                else:
                    st.session_state.sample_data = load_mock_data()
            else:
                st.session_state.sample_data = load_mock_data()
            st.success("Data has been refreshed!")
            st.rerun()
        
        if st.button("🚪 Log-out", use_container_width=False, type="secondary"):
            # Clear all session state except history records
            clear_session_state_except_history()
            st.success("logged out successfully")
            st.switch_page("pages/login.py")

def render_statistics_overview():
    """Render statistics overview"""
    st.markdown("## 📊 Today's Overview")
    
    # 获取统计数据
    data = st.session_state.sample_data
    
    # Check if data is None or missing required keys
    if data is None:
        st.error("Data loading failed: Unable to retrieve statistics")
        return
        
    if 'student_scores' not in data:
        st.error("Data loading failed: Missing student score information")
        return
        
    students = data['student_scores']
    
    # Handle case where assignment_stats might be missing
    if 'assignment_stats' in data:
        assignment_stats = data['assignment_stats']
        total_students = assignment_stats.total_students
        avg_score = assignment_stats.avg_score
        pass_rate = assignment_stats.pass_rate
        need_review = len([s for s in students if s.need_review])
    else:
        # Calculate stats from student data if assignment_stats is missing
        total_students = len(students)
        avg_score = sum(s.percentage for s in students) / len(students) if students else 0
        pass_rate = len([s for s in students if s.percentage >= 60]) / len(students) * 100 if students else 0
        need_review = len([s for s in students if s.need_review])
    
    # Display statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{total_students}</div>
            <div class="stats-label">Total Students</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{avg_score:.1f}%</div>
            <div class="stats-label">Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{pass_rate:.1f}%</div>
            <div class="stats-label">Pass Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-number">{need_review}</div>
            <div class="stats-label">Pending Review</div>
        </div>
        """, unsafe_allow_html=True)

def render_feature_cards():
    """Render feature cards"""
    st.markdown("## 🚀 Core Features")
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Assignment Grading Report</div>
            <div class="feature-description">
                View detailed grading results, supports manual edits and bulk actions.
                Includes confidence analysis and review suggestions.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("📊 View Grading Report", use_container_width=True, type="primary", key="report_button_1"):
            # Don't clear the selected job ID, keep it so the score report can load the data
            # if 'selected_job_id' in st.session_state:
            #     del st.session_state.selected_job_id
            st.switch_page("pages/score_report.py")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <div class="feature-title">Score Visualization & Analysis</div>
            <div class="feature-description">
                Analyze student performance and question quality with interactive charts.
                Supports multi-dimensional data analysis.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("📈 View Visualization", use_container_width=True, type="primary", key="viz_button_2"):
            # Don't clear the selected job ID, keep it so the visualization can load the data
            # if 'selected_job_id' in st.session_state:
            #     del st.session_state.selected_job_id
            st.switch_page("pages/visualization.py")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🕒</div>
            <div class="feature-title">Grading History</div>
            <div class="feature-description">
                Browse grading history with draft support. Preview and edit drafts,
                view completed assignment details.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("🕒 View History", use_container_width=True, type="primary", key="history_button_3"):
            st.switch_page("pages/history.py")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📚</div>
            <div class="feature-title">Knowledge Database Management</div>
            <div class="feature-description">
                Knowledge base management, supporting viewing, creating, modifying, and deleting knowledge bases and their files,
                viewing details of existing knowledge bases.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("📚 View Knowledge Database", use_container_width=True, type="primary", key="history_button_4"):
            st.switch_page("pages/knowledge_base.py")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add a new row for the backend status feature
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Backend Status Check</div>
            <div class="feature-description">
                Check the connection status between frontend and backend,
                view detailed connection information and error logs.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Check Backend Status", use_container_width=True, type="primary", key="status_button_5"):
            st.switch_page("pages/backend_status.py")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚙️</div>
            <div class="feature-title">System Settings</div>
            <div class="feature-description">
                Configure system parameters and manage user settings.
                Adjust application behavior and preference settings.
            </div>
            <div class="feature-card-buttons">
        """, unsafe_allow_html=True)
        
        if st.button("⚙️ System Settings", use_container_width=True, type="primary", key="settings_button_6"):
            st.info("System settings functionality will be implemented in future versions")

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_upload_section():
    """渲染上传功能区域"""
    st.markdown("## 📤 Assignment Upload")
    
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-top: 8px solid #adc3ff;">
        <h3 style="color: #1E3A8A; margin-top: 0;">Start a new assignment grading workflow</h3>
        <p>Upload problems and student submissions to start AI grading.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Step 1: Upload Problem File")
        st.markdown("Upload a PDF or Word document containing the problems")
        if st.button("📁 Upload Problem File", use_container_width=True, type="primary"):
                st.switch_page("pages/prob_upload.py")

    with col2:
        st.markdown("### 📄 Step 2: Upload Student Assignments")
        st.markdown("Upload student submission files")
        if st.button("📁 Upload Student Assignments", use_container_width=True, type="primary"):
                st.switch_page("pages/hw_upload.py")

def render_quick_preview():
    """渲染快速预览"""
    st.markdown("## 👀 Quick Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Score Distribution")
        try:
            students = st.session_state.sample_data['student_scores']
            fig = create_score_distribution_chart(students)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating chart: {str(e)}")
    
    with col2:
        st.markdown("### 🏆 Grade Levels")
        try:
            students = st.session_state.sample_data['student_scores']
            fig = create_grade_pie_chart(students)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating chart: {str(e)}")

# def render_quick_actions():
#     """渲染快速操作"""
#     st.markdown("""
#     <div class="quick-access">
#         <h3 style="color: #1E3A8A; margin-bottom: 1.5rem;">⚡ 快速操作</h3>
#     """, unsafe_allow_html=True)
    
#     col1, col2, col3, col4, col5, col6 = st.columns(6)
    
#     with col1:
#         if st.button("📋 最新作业", use_container_width=True):
#             st.info("🔄 跳转到最新作业评分...")
    
#     with col2:
#         if st.button("⚠️ 待复核列表", use_container_width=True):
#             st.info("📝 显示需要复核的作业...")
    
#     with col3:
#         if st.button("📈 生成报告", use_container_width=True):
#             with st.spinner("生成综合分析报告中..."):
#                 import time
#                 time.sleep(2)
#             st.success("✅ 综合分析报告已生成！")
    
#     with col4:
#         if st.button("📚 知识库管理", use_container_width=True):
#             st.switch_page("pages/knowledge_base.py")
    
#     with col5:
#         if st.button("📊 批改结果", use_container_width=True):
#             st.switch_page("pages/grade_results.py")
    
#     with col6:
#         if st.button("⚙️ 系统设置", use_container_width=True):
#             st.info("🔧 打开系统设置界面...")
    
#     st.markdown("</div>", unsafe_allow_html=True)

def render_recent_activities():
    """渲染最近活动"""
    st.markdown("## 🕐 Recent Activities")
    
    activities = [
        {
            "time": "2 hours ago",
            "action": "Batch export PDF reports",
            "details": "Exported grading reports for 45 students",
            "status": "Completed"
        },
        {
            "time": "5 hours ago",
            "action": "Review low-confidence answers",
            "details": "Reviewed 8 questions with confidence below 70%",
            "status": "Completed"
        },
        {
            "time": "1 day ago",
            "action": "Generate visual analytics",
            "details": "Generated comprehensive analysis report for Data Structure course",
            "status": "Completed"
        },
        {
            "time": "2 days ago",
            "action": "Upload new assignment",
            "details": "Uploaded midterm exam paper, awaiting AI grading",
            "status": "In progress"
        }
    ]
    
    for activity in activities:
        status_color = "#10B981" if activity["status"] in ("完成", "Completed") else "#F59E0B"
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #1E3A8A;">{activity['action']}</strong><br>
                    <span style="color: #64748B; font-size: 0.875rem;">{activity['details']}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {status_color}; font-weight: 600;">{activity['status']}</span><br>
                    <span style="color: #64748B; font-size: 0.75rem;">{activity['time']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_footer():
    """渲染页脚"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📞 Technical Support
        **Email:** smartai2025@126.com
        """)
    
    with col2: #TODO: 添加帮助链接
        st.markdown("""
        ### 📚 User Help
        - User Guide (Coming soon)
        - FAQs (Coming soon)
        """)
    
    with col3:
        st.markdown("""
        ### ℹ️ System Information
        **Version:** v1.0.0
        **Last Updated:** 2025-09-30
        """)

def render_dashboard():
    """渲染主界面内容（登录后显示）"""
    # 加载CSS和初始化
    load_custom_css()
    init_session_state()
    
    # # Inject pollers for active jobs
    # inject_pollers_for_active_jobs()
    
    # 渲染页面各个部分
    render_hero_section()
    render_user_welcome()
    
    st.markdown("---")
    render_statistics_overview()
    
    st.markdown("---")
    render_upload_section()
    
    st.markdown("---")
    render_feature_cards()
    
    st.markdown("---")
    render_quick_preview()
    
    # st.markdown("---")
    # render_quick_actions()
    
    st.markdown("---")
    render_recent_activities()
    
    render_footer()

    inject_pollers_for_active_jobs()

def main():
    """主函数 - 应用入口点"""
    # 检查登录状态
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # 如果未登录，重定向到登录页面
    if not st.session_state.logged_in:
        st.switch_page("pages/login.py")
    else:
        # 如果已登录，显示主界面内容
        render_dashboard()

def render_st(backend_url):
    """Render the Streamlit app with the given backend URL"""
    # Set the backend URL in environment variable
    os.environ["BACKEND_URL"] = backend_url
    
    # Also update the global BACKEND_URL variable
    global BACKEND_URL
    BACKEND_URL = backend_url
    
    # Run the main application
    main()

def clear_session_state_except_history():
    """Clear session state except for history records"""
    # Store history-related data temporarily
    history_data = {}
    if 'jobs' in st.session_state:
        history_data['jobs'] = st.session_state.jobs
    if 'selected_job_id' in st.session_state:
        history_data['selected_job_id'] = st.session_state.selected_job_id
    if 'selected_job_from_history' in st.session_state:
        history_data['selected_job_from_history'] = st.session_state.selected_job_from_history
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Restore history-related data
    for key, value in history_data.items():
        st.session_state[key] = value
    
    # Reinitialize essential session state
    initialize_session_state()

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

# This is the entry point for Streamlit Cloud
if __name__ == "__main__":
    # When run directly by Streamlit, use the default backend URL
    render_st(BACKEND_URL)
