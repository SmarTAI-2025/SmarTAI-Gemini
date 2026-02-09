# pages/stu_details.py

import streamlit as st
from streamlit_scroll_to_top import scroll_to_here
from utils import *

# --- 页面基础设置 (建议添加) ---
st.set_page_config(
    page_title="Student Homework Details - Intelligent Homework Verification System",
    layout="wide",
    page_icon="📖",
    initial_sidebar_state="expanded"  # 保留Student info侧边栏展开
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

def render_header():
    """Render page header"""
    col1, col2, col3, col4, col5 = st.columns([12,27,30,24,10])
    col = st.columns(1)[0]
    with col1:
        st.page_link("pages/main.py", label="Home", icon="🏠")
    with col2:
        st.page_link("pages/prob_upload.py", label="Re-upload Assignment Questions", icon="📤")
    with col3:
        st.page_link("pages/problems.py", label="Back to Question Recognition Overview", icon="📖")
    with col4:
        st.page_link("pages/hw_upload.py", label="Re-upload Student Answers", icon="📤")
    with col5:
        st.page_link("pages/history.py", label="History", icon="🕒")
    with col:
        st.markdown("<h1 style='text-align: center; color: #000000;'>📝 Student Homework Answer Details</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
render_header()

# --- 安全检查 ---
# 检查必要的数据是否已加载
if 'prob_data' not in st.session_state or not st.session_state.get('prob_data'):
    st.warning("Please upload and process assignment question files on the 'Assignment Questions Upload' page first.")
    st.stop()
if 'processed_data' not in st.session_state or not st.session_state.get('processed_data'):
    st.warning("Please upload and process student answer files on the 'Student Homework Upload' page first.")
    st.stop()
if 'selected_student_id' not in st.session_state or not st.session_state.get('selected_student_id'):
    st.warning("Please select a student from the 'Student Homework Overview' page first.")
    st.stop()


# # --- 滚动逻辑 ---
# # 每次进入详情页时，自动滚动到顶部
# scroll_to_here(50, key='top')
# scroll_to_here(0, key='top_fix')


# --- Sidebar Navigation (consistent with overview page) ---
with st.sidebar:
    st.header("Navigation")
    st.page_link("pages/stu_preview.py", label="Student Answer Overview", icon="📝")
    with st.expander("View by Student", expanded=True):
        student_list = sorted(list(st.session_state.processed_data.keys()))
        current_sid = st.session_state.get('selected_student_id')
        if not student_list:
            st.caption("No student data")
        else:
            def select_student(sid):
                st.session_state['selected_student_id'] = sid
                scroll_to_here(50, key='top')
                scroll_to_here(0, key='top_fix')
            for sid in student_list:
                is_selected = (sid == current_sid)
                st.button(
                    sid,
                    key=f"btn_student_{sid}",
                    on_click=select_student,
                    args=(sid,),
                    disabled=is_selected,
                    use_container_width=True,
                )


# --- 主页面内容：学生详情视图 ---

def render_student_view(student_id):
    """
    Render the view of a single student's homework details and provide editing for each answer.
    """
    problems_data = st.session_state.prob_data
    stu_data = st.session_state.processed_data.get(student_id, {})
    stu_name = stu_data.get("stu_name", "Unknown Name")
    st.header(f"🎓 Student: {student_id} - {stu_name}")
    answers = stu_data.get('stu_ans', [])
    if not answers:
        st.warning("No answer submissions found for this student.")
        return
    for ans in answers:
        q_id = ans.get('q_id')
        question_info = problems_data.get(q_id)
        if not question_info:
            continue
        with st.container(border=True):
            edit_answer_key = f"edit_answer_{student_id}_{q_id}"
            if edit_answer_key not in st.session_state:
                st.session_state[edit_answer_key] = False
            if st.session_state[edit_answer_key]:
                st.markdown(f"**Editing answer for Question {question_info.get('number', '')}:**")
                current_content = ans.get('content', '')
                if isinstance(current_content, dict):
                    first_file = next(iter(current_content.keys()), None)
                    if first_file:
                        new_answer_content = st.text_area(
                            f"Edit code file: {first_file}",
                            value=current_content[first_file],
                            key=f"ans_content_{student_id}_{q_id}",
                            height=250
                        )
                    else:
                        st.info("No file content available to edit.")
                        new_answer_content = ""
                else:
                    new_answer_content = st.text_area(
                        "Edit student answer (supports LaTeX)",
                        value=str(current_content),
                        key=f"ans_content_{student_id}_{q_id}",
                        height=150
                    )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save Answer", key=f"save_ans_btn_{student_id}_{q_id}", type="primary", use_container_width=True):
                        if isinstance(current_content, dict) and first_file:
                             st.session_state.processed_data[student_id]['stu_ans'][answers.index(ans)]['content'][first_file] = new_answer_content
                        else:
                            st.session_state.processed_data[student_id]['stu_ans'][answers.index(ans)]['content'] = new_answer_content
                        st.session_state.ans_changed = True
                        st.session_state[edit_answer_key] = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_ans_btn_{student_id}_{q_id}", use_container_width=True):
                        st.session_state[edit_answer_key] = False
                        st.rerun()
            else:
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    st.markdown(f"**Question {question_info.get('number', '')}:**")
                    stem_text = question_info.get('stem', 'Stem content is empty').strip()
                    if stem_text.startswith('$') and stem_text.endswith('$'):
                        st.latex(stem_text.strip('$'))
                    else:
                        st.markdown(stem_text)
                    if ans.get('flag'):
                        for flag in ans['flag']:
                            st.error(f"🚩 **Needs manual review**: {flag}")
                    st.markdown("**Student Answer:**")
                    q_type = question_info.get('type')
                    content = ans.get('content')
                    if q_type == "编程题" and isinstance(content, dict):
                        if content.keys():
                            file_to_show = st.selectbox("Select code file", options=list(content.keys()), key=f"file_{student_id}_{q_id}", label_visibility="collapsed")
                            if file_to_show:
                                st.code(content[file_to_show], language="python")
                        else:
                            st.info("This student did not submit files for this programming question.")
                    else:
                        try:
                            content_str = str(content).strip()
                            if content_str.startswith('$') and content_str.endswith('$'):
                                st.latex(content_str.strip('$'))
                            else:
                                st.markdown(content_str, unsafe_allow_html=True)
                        except Exception:
                            st.text(str(content))
                with col2:
                    if st.button("✏️ Edit Answer", key=f"edit_ans_btn_{student_id}_{q_id}"):
                        st.session_state[edit_answer_key] = True
                        st.rerun()





# 获取当前选定的学生ID并渲染其视图
selected_student_id = st.session_state.get('selected_student_id')
render_student_view(selected_student_id)

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

def return_top():
    scroll_to_here(50, key='top')
    scroll_to_here(0, key='top_fix')
# Use column layout to push the button to the right (same as your code)
col1, _, col2 = st.columns([8, 40, 8])

with col1:
    st.button(
        "Return to Top", 
        on_click=return_top,
        use_container_width=False
    )

with col2:
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