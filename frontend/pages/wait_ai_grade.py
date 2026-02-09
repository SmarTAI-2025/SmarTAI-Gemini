import streamlit as st
import time
import requests
from utils import *
from datetime import datetime
import pandas as pd
import re

# Add natural_sort_key function for mock data display
def natural_sort_key(s):
    """
    Natural sort helper.
    Example: "q2" comes before "q10".
    """
    # 确保输入是字符串
    s = str(s)
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

st.set_page_config(
    page_title="Processing - Intelligent Homework Verification System",
    layout="wide",
    page_icon="⚙️",
    initial_sidebar_state="collapsed" # Initial collapse helps reduce flickering
)

initialize_session_state()

# 在每个页面的顶部调用这个函数
load_custom_css()

# --- 新增：左上角返回主页链接 ---
# 这个链接会固定显示在主内容区域的顶部

# CSS 来彻底隐藏整个侧边-栏容器
#    data-testid="stSidebar" 是整个侧边栏的ID
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def check_for_abandoned_tasks():
    """Check for and abandon tasks that were started but not completed"""
    # Check if there are any pending jobs that should be abandoned
    if 'checking_job_id' in st.session_state:
        job_id = st.session_state.checking_job_id
        # If user has navigated away from the waiting page, abandon the task
        # This is a simple check - in a real implementation you might want more sophisticated logic
        print(f"Potential abandoned task detected: {job_id}")
        # For now, we'll just clear the checking state without abandoning the backend task
        # since the backend task might still be processing
        del st.session_state.checking_job_id

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
        st.markdown("<h1 style='text-align: center; color: #000000;'>🕒 Waiting for AI Grading</h1>", 
                   unsafe_allow_html=True)

render_header()

# Check for abandoned tasks
check_for_abandoned_tasks()

# --- 模拟后端提交和页面跳转 ---

st.title("⚙️ Submitting homework...")
# st.info("请稍候，AI后台正在进行批改分析...")

# Initialize job status in session state
if 'job_status' not in st.session_state:
    st.session_state.job_status = "pending"

# Display mock data while waiting for real results
st.info("Grading task in progress... Below is a mock preview. To check completion status, click 'Grading Results' and refresh the page.")
try:
    from frontend_utils.data_loader import load_mock_data
    mock_data = load_mock_data()
    
    if "student_scores" in mock_data:
        all_mock_students = mock_data["student_scores"]
        all_mock_students.sort(key=lambda s: s.student_id)
        
        st.subheader("Mock Student Grading Preview")
        for student in all_mock_students[:5]:  # Show first 5 students as preview (matching grade_results.py)
            st.markdown(f"### Student: {student.student_name} ({student.student_id})")
            student.questions.sort(key=lambda q: natural_sort_key(q['question_id']))
            data = []
            total_score = 0
            total_max_score = 0
            for question in student.questions:
                data.append({
                    "Question No.": question["question_id"][1:],
                    "Question Type": question["question_type"],
                    "Score": f"{question['score']:.1f}",
                    "Max Score": f"{question['max_score']:.1f}",
                    "Confidence": f"{question['confidence']:.2f}",
                    "Feedback": question["feedback"]
                })
                total_score += question["score"]
                total_max_score += question["max_score"]
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch', hide_index=True)
            st.write(f"**Total Score: {total_score:.1f}/{total_max_score:.1f}**")
            st.divider()
except Exception as e:
    st.warning(f"Failed to load mock data: {e}")

# 2. 【核心逻辑】检查是否存在从其他页面传来的“触发标志”
if st.session_state.get('trigger_ai_grading'):
    
    # 3. 【至关重要】立刻“消费”掉这个标志，防止刷新页面时重复执行！
    del st.session_state.trigger_ai_grading
    
    # 4. 现在，在这里安全地执行你那段只需要运行一次的代码
    st.info("Request received. Submitting to AI backend for grading...")
    try:
        # 使用 with st.spinner 来提供更好的用户反馈
        with st.spinner('Submitting grading task, please wait...'):
            # Use the batch grading endpoint to grade all students
            result = requests.post(
                f"{st.session_state.backend}/ai_grading/grade_all/",
                json={},
                timeout=600
            )
            result.raise_for_status()
            job_response = result.json()
            job_id = job_response.get("job_id")
        
        if not job_id:
            st.error("Backend did not return job_id")
        else:
            # 2. 从 session_state 中获取任务名，如果不存在则提供一个默认名
            task_name = st.session_state.get("task_name", "Untitled Task")
            # Only delete if it exists
            if "task_name" in st.session_state:
                del st.session_state.task_name
            
            # 3. 获取并格式化当前提交时间
            submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 4. 创建一个包含所有任务信息的字典
            task_details = {
                "name": task_name,
                "submitted_at": submission_time
            }

            # 5. 将这个任务的详细信息存入全局的任务字典中，以 job_id 作为唯一的键
            if "jobs" not in st.session_state:
                st.session_state.jobs = {} # Ensure it exists
            
            # Add the new job
            st.session_state.jobs[job_id] = task_details
            # Also store the job_id for immediate access
            st.session_state.current_job_id = job_id
            # Store job_id for status checking
            st.session_state.checking_job_id = job_id
            
            # Debug information
            st.write(f"Stored job ID: {job_id}")
            st.write(f"Jobs in session state: {list(st.session_state.jobs.keys())}")
            
            # 6. 更新成功提示信息，显示用户友好的任务名
            _, img_col, _ = st.columns([1, 1, 1])
            with img_col:
                st.image(
                    "static/checkmark.svg",
                    caption=f"Grading task: {task_name} has been successfully submitted to the AI backend!",
                    width=200
                )
            
            # 使用 st.rerun() 立即刷新页面。
            # 刷新后，因为标志已被删除，所以上面的代码不会再次运行。
            # 同时，下面的轮询器注入代码会检测到新的 job_id 并开始轮询。
            st.rerun()
            
    except Exception as e:
        st.error(f"Submission failed: {e}")

# If we have a job to check status for
if 'checking_job_id' in st.session_state:
    job_id = st.session_state.checking_job_id
    
    # Display current status
    st.subheader("Task Status")
    status_container = st.empty()
    
    # Add refresh button with backend reconnection capability
    if st.button("🔄 Refresh Status"):
        try:
            response = requests.get(
                f"{st.session_state.backend}/ai_grading/grade_result/{job_id}",
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                st.session_state.job_status = result.get("status", "unknown")
            else:
                st.error(f"Failed to fetch status: {response.status_code}")
                st.warning("Attempting to reconnect to backend...")
                try:
                    test_response = requests.get(f"{st.session_state.backend}/ai_grading/all_jobs", timeout=5)
                    if test_response.status_code == 200:
                        st.success("Backend connection restored!")
                    else:
                        st.error(f"Backend connection failed (status code: {test_response.status_code})")
                except Exception as reconnect_error:
                    st.error(f"Backend connection failed: {str(reconnect_error)}")
        except Exception as e:
            st.error(f"Error while fetching status: {e}")
            # Try to reconnect to backend
            st.warning("Attempting to reconnect to backend...")
            try:
                test_response = requests.get(f"{st.session_state.backend}/ai_grading/all_jobs", timeout=5)
                if test_response.status_code == 200:
                    st.success("Backend connection restored!")
                else:
                    st.error(f"Backend connection failed (status code: {test_response.status_code})")
            except Exception as reconnect_error:
                st.error(f"Backend connection failed: {str(reconnect_error)}")
    
    # Auto-check status with backend reconnection capability
    try:
        response = requests.get(
            f"{st.session_state.backend}/ai_grading/grade_result/{job_id}",
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            st.session_state.job_status = status
            
            # Update display based on status
            if status == "pending":
                status_container.info("🕒 Task is processing, please wait...")
            elif status == "completed":
                success_message = "✅ Task completed! Please go to Grading Results page to view"
                status_container.success(success_message)
                st.info(success_message)  # Display the message on the web page as well
                # Remove the job from checking
                if 'checking_job_id' in st.session_state:
                    del st.session_state.checking_job_id
                # Set the current job as selected
                st.session_state.selected_job_id = job_id
                # Set newly submitted job ID for grade_results.py to auto-select this job
                st.session_state.newly_submitted_job_id = job_id
                # Wait a moment and then redirect
                time.sleep(2)
                st.switch_page("pages/grade_results.py")
            elif status == "error":
                status_container.error(f"❌ Task processing error: {result.get('message', 'Unknown error')}")
                # Remove the job from checking
                if 'checking_job_id' in st.session_state:
                    del st.session_state.checking_job_id
            else:
                status_container.warning(f"⚠️ Current status: {status}")
        else:
            status_container.error(f"Failed to fetch status: {response.status_code}")
            # Try to reconnect to backend
            try:
                test_response = requests.get(f"{st.session_state.backend}/ai_grading/all_jobs", timeout=5)
                if test_response.status_code != 200:
                    st.warning("Backend connection may be disconnected, please click the Refresh Status button to try reconnecting")
            except Exception:
                st.warning("Backend connection may be disconnected, please click the Refresh Status button to try reconnecting")
    except Exception as e:
        status_container.error(f"Error while fetching status: {e}")
        # Try to reconnect to backend
        try:
            test_response = requests.get(f"{st.session_state.backend}/ai_grading/all_jobs", timeout=5)
            if test_response.status_code != 200:
                st.warning("Backend connection may be disconnected, please click the Refresh Status button to try reconnecting")
        except Exception:
            st.warning("Backend connection may be disconnected, please click the Refresh Status button to try reconnecting")

    # Show job details
    if job_id in st.session_state.jobs:
        task_details = st.session_state.jobs[job_id]
        st.write(f"Task Name: {task_details.get('name', 'Untitled Task')}")
        st.write(f"Submitted At: {task_details.get('submitted_at', 'Unknown time')}")

# Auto-refresh every 5 seconds if we're still checking
if 'checking_job_id' in st.session_state:
    st.markdown(
        """
        <script>
        setTimeout(function(){
            window.parent.location.reload();
        }, 5000);
        </script>
        """,
        unsafe_allow_html=True
    )
    st.info("The page will auto-refresh in 5 seconds to check task status...")

inject_pollers_for_active_jobs()

def reset_grading_state_on_navigation():
    """Reset grading state when navigating away from grading pages"""
    try:
        # Reset backend grading state (preserves history)
        response = requests.delete(
            f"{st.session_state.backend}/ai_grading/reset_all_grading",
            timeout=5
        )
        if response.status_code == 200:
            print("Backend grading state reset successfully on navigation")
        else:
            print(f"Failed to reset backend grading state on navigation: {response.status_code}")
    except Exception as e:
        print(f"Error resetting backend grading state on navigation: {e}")
    
    # Clear frontend grading-related session state (preserve history and job selection)
    # Only clear intermediate grading variables, preserve completed results
    keys_to_clear = [
        'ai_grading_data',
        'report_job_selector',
        'checking_job_id',
        'job_status'
    ]
    
    # Only clear sample_data if it's not MOCK_JOB_001
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id != "MOCK_JOB_001":
        keys_to_clear.append('sample_data')
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
