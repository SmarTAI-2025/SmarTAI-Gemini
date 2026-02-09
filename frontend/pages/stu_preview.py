# pages/stu_preview.py

import streamlit as st
import pandas as pd
from utils import *
import re

# --- 页面基础设置 (建议添加) ---
st.set_page_config(
    page_title="Student Homework Overview - Intelligent Homework Verification System",
    layout="wide",
    page_icon="📖",
    initial_sidebar_state="expanded"  # 保留Student info侧边栏展开
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

def render_header():
    """Render page header"""
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col = st.columns(1)[0]

    with col1:
        st.page_link("pages/main.py", label="Home", icon="🏠")
    
    with col2:
        st.page_link("pages/history.py", label="History", icon="🕒")

    with col3:
        st.page_link("pages/problems.py", label="Assignment", icon="📖")

    with col4:
        st.page_link("pages/stu_preview.py", label="Student Homework", icon="📝")
    
    with col5:
        st.page_link("pages/grade_results.py", label="Grading Results", icon="📊")

    with col6:
        st.page_link("pages/score_report.py", label="Score Report", icon="💯")

    with col7:
        st.page_link("pages/visualization.py", label="Grade Analysis", icon="📈")
    
    with col:
        st.markdown("<h1 style='text-align: center; color: #000000;'>📝 Student Homework Preview</h1>", 
                   unsafe_allow_html=True)

render_header()

# --- Safety check ---
# Check if necessary data has been loaded
if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
    st.warning("Please upload and process assignment question files on the 'Assignment Questions Upload' page first.")
    # st.page_link("pages/prob_upload.py", label="Return to Question Upload Page", icon="📤")
    st.stop()
if 'processed_data' not in st.session_state or not st.session_state.get('processed_data'):
    st.warning("Please upload and process student answer files on the 'Student Homework Upload' page first.")
    # st.page_link("pages/hw_upload.py", label="Return to Answer Upload Page", icon="📤")
    st.stop()


# --- Sidebar Navigation ---
with st.sidebar:
    st.header("Navigation")
    st.page_link("pages/stu_preview.py", label="Student Answer Overview", icon="📝")
    with st.expander("View by Student", expanded=True):
        student_list = sorted(list(st.session_state.processed_data.keys()))
        if not student_list:
            st.caption("No student data yet")
        else:
            def select_student(sid):
                st.session_state['selected_student_id'] = sid
            for sid in student_list:
                if st.button(
                    sid,
                    key=f"btn_student_{sid}",
                    on_click=select_student,
                    args=(sid,),
                    use_container_width=True
                ):
                    st.session_state['selected_student_id'] = sid
                    st.switch_page("pages/stu_details.py")


# --- 主页面内容：学生总览仪表盘 ---

def render_students_dashboard():
    """
    Display an overview table of all students' homework status
    """
    students_data = st.session_state.processed_data
    problems_data = st.session_state.prob_data
    if not students_data or not problems_data:
        st.info("Not enough student or question data to generate the overview.")
        return
    dashboard_data = []
    sorted_stu_ids = sorted(students_data.keys())
    for stu_id in sorted_stu_ids:
        student_data = students_data[stu_id]
        name = student_data.get("stu_name", "Unknown Name")
        row = {
            'Student ID': stu_id,
            'Name': name,
        }
        answers = student_data.get('stu_ans', [])
        ans_qid_list = []
        for ans in answers:
            q_id = ans.get('q_id')
            ans_qid_list.append(q_id)
            num = ans.get('number', 'Unknown question number')
            q_num = "Question "+str(num)
            if ans.get('flag'):
                row[q_num] = "🚩 Needs manual review"
            elif not ans.get('content'):
                row[q_num] = "❌ Not submitted"
            else:
                row[q_num] = "✅ Submitted and recognized"
        for q_id in problems_data.keys():
            if q_id not in ans_qid_list:
                q_num = problems_data[q_id].get('number', 'Unknown question number')
                row[q_num] = "❌ Not submitted"
        dashboard_data.append(row)
    if dashboard_data:
        df = pd.DataFrame(dashboard_data)
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(s))]
        problem_columns = [col for col in df.columns if col not in ['Student ID', 'Name']]
        sorted_problem_columns = sorted(problem_columns, key=natural_sort_key)
        final_column_order = ['Student ID', 'Name'] + sorted_problem_columns
        df = df[final_column_order]
        df = df.set_index(['Student ID', 'Name'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Unable to generate student homework overview.")

# 渲染总览视图
render_students_dashboard()

# --- 新增：右下角跳转链接 ---
def start_ai_grading_and_navigate():
    """
    这个函数做了两件事：
    1. 在 session_state 中设置一个“一次性触发”的标志。
    2. 命令 Streamlit 跳转到任务轮询页面。
    """
    st.session_state.trigger_ai_grading = True  # 使用与目标页面匹配的标志
    # st.switch_page("pages/wait_ai_grade.py")   # 跳转到你的目标页面

# ----------------------------------------------------
# 添加一个分隔符，使其与主内容分开
st.divider()

# Use column layout to push the button to the right (same as your code)
col_spacer, col_button = st.columns([48, 8])

with col_button:
    # 2. Create a button and tell it to call the above function when clicked
    if st.button(
        "🚀 Start AI Grading", 
        on_click=start_ai_grading_and_navigate, 
        use_container_width=False
    ):
        update_prob()
        update_ans()
        st.switch_page("pages/wait_ai_grade.py")   # Jump to your target page

inject_pollers_for_active_jobs()


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
        'report_job_selector',
        'selected_job_from_history'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
