import streamlit as st
# 假设 utils.py 和你的主 app 在同一级目录
from utils import * 

# --- Page basic settings (recommended to add) ---
st.set_page_config(
    page_title="Question Recognition Overview - Intelligent Homework Verification System",
    layout="wide",
    page_icon="📝"
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
        st.markdown("<h1 style='text-align: center; color: #000000;'>📖 Assignment Questions</h1>", 
                   unsafe_allow_html=True)

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

render_header()
# --- 安全检查 ---
# 检查必要的数据是否已加载st.session_state.prob_data
if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
    st.warning("Please upload assignment question files on the 'Assignment Questions Upload' page first.")
    # st.page_link("pages/prob_upload.py", label="Back to Upload Page", icon="📤")
    st.stop()


# --- 渲染函数 (从原代码复制过来，无需修改) ---
def render_question_overview():
    # st.header("📝 题目识别概览")
    st.caption("You can change the question type using the left dropdown, or click Edit to modify the stem and scoring criteria.")
    
    # Handle the data format returned by the backend
    # The backend returns a dictionary with q_id as keys
    problems = st.session_state.prob_data

    if not problems:
        st.info("No question information found in the data.")
        return

    # Ensure problems is a dictionary with q_id as keys
    # Handle different possible data formats
    if isinstance(problems, dict):
        # Check if it's the format with 'problems' key
        if 'problems' in problems:
            # This is the old format, need to convert
            problems_data = problems['problems']
            if isinstance(problems_data, list):
                # Convert list to dictionary with q_id as keys
                problems = {q['q_id']: q for q in problems_data}
            else:
                # Already in correct format
                problems = problems_data
        # If no 'problems' key, assume it's already in the correct format (dict with q_id as keys)
    elif isinstance(problems, list):
        # Convert list to dictionary with q_id as keys
        problems = {q['q_id']: q for q in problems}
    
    # Now we should have a dictionary with q_id as keys
    # Make sure st.session_state.prob_data is also in the correct format for editing
    if isinstance(st.session_state.prob_data, dict) and 'problems' in st.session_state.prob_data:
        # Convert to the correct format for editing
        problems_data = st.session_state.prob_data['problems']
        if isinstance(problems_data, list):
            st.session_state.prob_data = {q['q_id']: q for q in problems_data}
        else:
            st.session_state.prob_data = problems_data
    
    for q_id, q in problems.items():
        with st.container(border=True):
            # 为题干编辑和评分标准编辑分别创建独立的session state
            edit_stem_key = f"edit_stem_{q_id}"
            edit_criterion_key = f"edit_criterion_{q_id}"
            if edit_stem_key not in st.session_state:
                st.session_state[edit_stem_key] = False
            if edit_criterion_key not in st.session_state:
                st.session_state[edit_criterion_key] = False

            # --- 模式1: 编辑题干 ---
            if st.session_state[edit_stem_key]:
                st.markdown(f"**Editing Question: {q.get('number', '')}**")
                new_stem = st.text_area("Edit stem (supports LaTeX)", value=q.get('stem', ''), key=f"q_stem_{q_id}", height=150)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save Stem", key=f"save_stem_btn_{q_id}", type="primary", use_container_width=True):
                        # Ensure st.session_state.prob_data is in the correct format for editing
                        if isinstance(st.session_state.prob_data, dict):
                            if q_id in st.session_state.prob_data:
                                st.session_state.prob_data[q_id]['stem'] = new_stem
                            elif 'problems' in st.session_state.prob_data:
                                # Handle old format
                                if isinstance(st.session_state.prob_data['problems'], dict) and q_id in st.session_state.prob_data['problems']:
                                    st.session_state.prob_data['problems'][q_id]['stem'] = new_stem
                        st.session_state.prob_changed = True
                        st.session_state[edit_stem_key] = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_stem_btn_{q_id}", use_container_width=True):
                        st.session_state[edit_stem_key] = False
                        st.rerun()

            # --- 模式2: 编辑评分标准 ---
            elif st.session_state[edit_criterion_key]:
                st.markdown(f"**Editing Scoring Criteria: {q.get('number', '')}**")
                new_criterion = st.text_area("Edit scoring criteria", value=q.get('criterion', ''), key=f"q_criterion_{q_id}", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save Criteria", key=f"save_criterion_btn_{q_id}", type="primary", use_container_width=True):
                        # Ensure st.session_state.prob_data is in the correct format for editing
                        if isinstance(st.session_state.prob_data, dict):
                            if q_id in st.session_state.prob_data:
                                st.session_state.prob_data[q_id]['criterion'] = new_criterion
                            elif 'problems' in st.session_state.prob_data:
                                # Handle old format
                                if isinstance(st.session_state.prob_data['problems'], dict) and q_id in st.session_state.prob_data['problems']:
                                    st.session_state.prob_data['problems'][q_id]['criterion'] = new_criterion
                        st.session_state.prob_changed = True
                        st.session_state[edit_criterion_key] = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_criterion_btn_{q_id}", use_container_width=True):
                        st.session_state[edit_criterion_key] = False
                        st.rerun()
            
            # --- 模式3: 正常显示 ---
            else:
                col1, col2, col3 = st.columns([0.2, 0.65, 0.15])
                with col1:
                    # Display English labels while storing Chinese values
                    q_types_cn = ["概念题", "计算题", "证明题", "推理题", "编程题", "其他"]
                    q_types_en = ["Concept", "Calculation", "Proof", "Reasoning", "Programming", "Other"]
                    cn_to_en = dict(zip(q_types_cn, q_types_en))
                    en_to_cn = dict(zip(q_types_en, q_types_cn))

                    current_type_cn = q.get('type')
                    current_type_en = cn_to_en.get(current_type_cn, "Concept")
                    current_type_index = q_types_en.index(current_type_en) if current_type_en in q_types_en else 0

                    new_type_en = st.selectbox(
                        "Question Type", options=q_types_en, index=current_type_index,
                        key=f"q_type_{q_id}", label_visibility="collapsed"
                    )
                    new_type_cn = en_to_cn.get(new_type_en, current_type_cn)
                    # 如果类型发生变化，直接更新（存储为中文以兼容其他页面逻辑）
                    if new_type_cn != q.get('type'):
                        # Update the session state with the new type
                        if isinstance(st.session_state.prob_data, dict):
                            if q_id in st.session_state.prob_data:
                                st.session_state.prob_data[q_id]['type'] = new_type_cn
                            elif 'problems' in st.session_state.prob_data:
                                # Handle old format
                                if isinstance(st.session_state.prob_data['problems'], dict) and q_id in st.session_state.prob_data['problems']:
                                    st.session_state.prob_data['problems'][q_id]['type'] = new_type_cn
                        st.session_state.prob_changed = True
                        st.rerun()

                with col2:
                    st.markdown(f"**{q.get('number', 'N/A')}:** {q.get('stem', 'Stem content is empty')}")
                    # 新增：显示评分标准
                    st.markdown(f"**Scoring Criteria:** *{q.get('criterion', 'Empty')}*")

                with col3:
                    if st.button("✏️ Edit Stem", key=f"edit_stem_btn_{q_id}"):
                        st.session_state[edit_stem_key] = True
                        st.rerun()
                    # New: Edit scoring criteria button
                    if st.button("✏️ Edit Criteria", key=f"edit_criterion_btn_{q_id}"):
                        st.session_state[edit_criterion_key] = True
                        st.rerun()



# --- 页面主逻辑 ---
render_question_overview()

# --- 新增：右下角跳转链接 ---
def start_ai_grading_and_navigate():
    """
    This function does two things:
    1. Sets a "one-time trigger" flag in session_state.
    2. Commands Streamlit to jump to the task polling page.
    """
    st.session_state.trigger_ai_grading = True  # Use the flag that matches the target page
    # st.switch_page("pages/wait_ai_grade.py")   # Jump to your target page

# ----------------------------------------------------
# Add a divider to separate it from the main content
st.divider()

# Use column layout to push the button to the right (same as your code)
col_spacer, col_button = st.columns([60, 6])

with col_button:
    # 2. Create a button and tell it to call the above function when clicked
    if st.button(
        "✅ Confirm Questions", 
        on_click=start_ai_grading_and_navigate, 
        use_container_width=True # Make the button fill the column width for better visual effect
    ):
        update_prob()
        update_ans()
        st.switch_page("pages/hw_upload.py")   # Jump to your target page

inject_pollers_for_active_jobs()