# utils.py
import streamlit as st
import streamlit.components.v1 as components
import json # Import json library for converting Python lists to JS arrays
import requests
import os
KNOWLEDGE_BASE_DIR = "knowledge_bases"
KNOWLEDGE_BASE_CONFIG = "knowledge_base_config.json"
UTILS_BACKEND_URL = "https://smartai-backend-zefh.onrender.com" # render deployment
# UTILS_BACKEND_URL = "http://localhost:8000" # local testing

def load_knowledge_base_config():
    """Load knowledge base configuration from JSON file to session_state"""
    if os.path.exists(KNOWLEDGE_BASE_CONFIG):
        with open(KNOWLEDGE_BASE_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_custom_css(file_path=None):
    """
    Load CSS file from specified path and apply to Streamlit application.
    Automatically handles relative path issues.
    """
    import os
    
    if file_path is None:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Build the absolute path of the CSS file
        file_path = os.path.join(current_dir, "static", "main.css")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_path}")
    except Exception as e:
        st.error(f"Error loading CSS file: {str(e)}")

def initialize_session_state():
    """
    Helper function that runs at the top of each page, used to initialize session_state.
    If a key does not exist, set its initial value.
    """
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    
    # --- Key change here ---
    # If the 'backend' key does not exist in session_state, set its initial/fixed value
    if "backend" not in st.session_state:
        # Hardcode the backend URL for deployment
        st.session_state.backend = UTILS_BACKEND_URL
        
    if 'prob_changed' not in st.session_state:
        st.session_state.prob_changed = False

    if 'ans_changed' not in st.session_state:
        st.session_state.ans_changed = False

    if 'knowledge_bases' not in st.session_state:
        st.session_state.knowledge_bases = load_knowledge_base_config()

def reset_grading_state():
    """Reset grading state in both frontend and backend (preserves history)"""
    try:
        # Reset backend grading state (preserves history)
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
    
    # Clear frontend grading-related session state (preserve history and job selection)
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

def clear_session_state_except_history():
    """Clear session state except for history records"""
    # Store history-related data temporarily
    history_data = {}
    if 'jobs' in st.session_state:
        history_data['jobs'] = st.session_state.jobs
    if 'selected_job_id' in st.session_state:
        # Always preserve MOCK_JOB_001 selection
        if st.session_state.selected_job_id == "MOCK_JOB_001":
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

def abandon_grading_task(job_id: str):
    """Abandon a grading task and clean up its state"""
    try:
        # Tell backend to discard this specific job
        response = requests.delete(
            f"{st.session_state.backend}/ai_grading/discard_job/{job_id}",
            timeout=5
        )
        if response.status_code == 200:
            print(f"Job {job_id} abandoned successfully")
        else:
            print(f"Failed to abandon job {job_id}: {response.status_code}")
    except Exception as e:
        print(f"Error abandoning job {job_id}: {e}")
    
    # Remove job from session state
    if "jobs" in st.session_state and job_id in st.session_state.jobs:
        del st.session_state.jobs[job_id]
    
    # Clear any checking state for this job
    if "checking_job_id" in st.session_state and st.session_state.checking_job_id == job_id:
        del st.session_state.checking_job_id
    
    # Clear any selection state for this job
    if "selected_job_id" in st.session_state and st.session_state.selected_job_id == job_id:
        del st.session_state.selected_job_id

def update_prob():
    if st.session_state.get('prob_changed', False):
        st.info("Detected that question data has been modified, updating storage to backend...") # Friendly prompt
        try:
            requests.post(
                f"{st.session_state.backend}/human_edit/problems",
                json=st.session_state.prob_data
            )
            
            print("Data has been successfully saved to backend!") # Print log in terminal
            st.toast("Changes have been successfully saved!", icon="✅")

            # After successful save, reset the flag
            st.session_state.prob_changed = False
        except Exception as e:
            st.error(f"Save failed, error message: {e}")
            print(f"Error saving to DB: {e}") # Print error in terminal

def update_ans():
    if st.session_state.get('ans_changed', False):
        st.info("Detected that student answer data has been modified, updating storage to backend...") # Friendly prompt
        try:
            requests.post(
                f"{st.session_state.backend}/human_edit/stu_ans",
                json=st.session_state.processed_data
            )
            
            print("Data has been successfully saved to backend!") # Print log in terminal
            st.toast("Changes have been successfully saved!", icon="✅")

            # After successful save, reset the flag
            st.session_state.prob_changed = False
        except Exception as e:
            st.error(f"Save failed, error message: {e}")
            print(f"Error saving to DB: {e}") # Print error in terminal

def get_master_poller_html(jobs_json: str, backend_url: str) -> str:
    """
    Generate a "master" polling script.
    This script receives a JSON object containing all task details,
    and internally starts polling for each job_id.
    """
    be = backend_url.rstrip("/")
    # jobs_json is now a JSON string of a dictionary, for example:
    # '{"job1":{"name":"file1.pdf", "submitted_at":"..."}, "job2":{...}}'
    return f"""
    <script>
    (function() {{
        const backend = '{be}';
        let jobsData; // <-- Variable name modified to reflect it as a data object

        try {{
            jobsData = JSON.parse('{jobs_json}');
        }} catch (e) {{
            console.error("Unable to parse task data object:", e);
            jobsData = {{}};
        }}

        // Get all task IDs to be polled (i.e., the keys of the object)
        const jobIds = Object.keys(jobsData);

        if (jobIds.length === 0) {{
            return;
        }}

        // Define a function to start polling for a single task
        // <-- Receives job_id and the corresponding task details object
        const startPollingForJob = (jobId, taskDetails) => {{
            const completedKey = `job-completed-${{jobId}}`;

            if (sessionStorage.getItem(completedKey)) {{
                return;
            }}

            const intervalId = setInterval(async () => {{
                try {{
                    // The polling URL still only uses job_id
                    const resp = await fetch(backend + '/ai_grading/grade_result/' + jobId);
                    if (!resp.ok) return;

                    const data = await resp.json();
                    if (data && data.status === 'completed') {{
                        clearInterval(intervalId);
                        if (!sessionStorage.getItem(completedKey)) {{
                            // --- Core modification: Generate user-friendly popup message ---
                            const taskName = taskDetails.name || "Unnamed task";
                            const submittedAt = taskDetails.submitted_at || "Unknown time";
                            alert("The task you submitted at [" + submittedAt + "]: " + taskName + " has been successfully completed! Please jump to the grading results page to view");
                            // Mark as completed to prevent duplicate popups
                            sessionStorage.setItem(completedKey, 'true');
                            // --- New feature: Refresh current page ---
                            window.parent.location.href = '/pages/grade_results.py';
                            // -----------------------------
                        }}
                    }}
                }} catch (err) {{
                    // Silently handle errors
                }}
            }}, 3000);
        }};

        // Iterate through all task IDs, start polling for each one, and pass in their detailed information
        jobIds.forEach(jobId => {{
            startPollingForJob(jobId, jobsData[jobId]);
        }});

    }})();
    </script>
    """

def inject_pollers_for_active_jobs():
    """
    【核心函数优化版】将所有活动任务的ID打包，一次性注入一个主轮询器。
    """
    # Only poll for real jobs, not mock jobs
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    if "backend" not in st.session_state:
        # Hardcode the backend URL for deployment
        st.session_state.backend = UTILS_BACKEND_URL

    # Filter out mock jobs - only poll for real jobs
    real_jobs = {}
    if st.session_state.jobs:
        for job_id, job_info in st.session_state.jobs.items():
            # Skip mock jobs entirely
            if job_id.startswith("MOCK_JOB_"):
                continue
            # Skip mock jobs with is_mock flag
            is_mock = job_info.get("is_mock", False)
            if not is_mock:
                real_jobs[job_id] = job_info

    if not real_jobs:
        return

    # 将 Python 的 job_id 列表转换为 JSON 格式的字符串
    jobs_json_string = json.dumps(real_jobs)

    # 获取包含所有轮询逻辑的单个主脚本
    master_js_code = get_master_poller_html(jobs_json_string, st.session_state.backend)

    # 全局只调用这一次 components.html！
    components.html(master_js_code, height=0)

# import sys
# # --- START: 动态路径修改 ---
# # 这段代码会确保无论你从哪里运行脚本，都能正确找到 frontent 模块

# # 1. 获取当前文件 (utils.py) 所在的目录 (frontent/)
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # 2. 获取 'frontent/' 的父目录 (也就是 'project/')
# project_root = os.path.dirname(current_dir)

# # 3. 如果 'project/' 目录不在Python的搜索路径中，就把它加进去
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# # --- END: 动态路径修改 ---


# # 现在，因为 'project/' 目录已经在搜索路径里了，
# # 下面这个绝对导入就一定能成功
# from frontend.poller_component import poll_and_rerun

# def inject_pollers_for_active_jobs():
#     """
#     【最终版】使用自定义组件注入轮询器，并在完成后触发 st.rerun()。
#     此函数现在是对 poll_and_rerun 组件的一个封装。
#     """
#     if "jobs" not in st.session_state:
#         st.session_state.jobs = {}
#     if "backend" not in st.session_state:
#         # 确保有一个默认的后端URL
#         st.session_state.backend = "http://localhost:8000"

#     # 筛选出需要轮询的真实任务
#     real_jobs = {
#         job_id: job_info
#         for job_id, job_info in st.session_state.jobs.items()
#         if not job_id.startswith("MOCK_JOB_") and not job_info.get("is_mock", False)
#     }

#     if not real_jobs:
#         return

#     # 将任务字典转换为 JSON 字符串
#     jobs_json_string = json.dumps(real_jobs)

#     # 调用组件函数，它会处理所有前端逻辑和 rerun 触发
#     # 我们为 key 提供一个固定的字符串，以确保组件在不同页面间保持一致性
#     poll_and_rerun(jobs_json_string, st.session_state.backend, key="global_job_poller")


# utils.py

# ... (keep all your existing functions like initialize_session_state, etc.) ...

def get_all_jobs_for_selection():
    """
    Gets all jobs for selection in a dropdown, including mock and real tasks.
    Returns a dictionary mapping job_id to a user-friendly name.
    """
    all_jobs_for_selection = {}

    # 1. Add the mock task first as a baseline option
    if 'sample_data' in st.session_state and st.session_state.sample_data:
        assignment_stats = st.session_state.sample_data.get('assignment_stats')
        mock_job_id = "MOCK_JOB_001"
        if assignment_stats:
            all_jobs_for_selection[mock_job_id] = f"{assignment_stats.assignment_name}"
        else:
            # Fallback name if assignment_stats is None
            all_jobs_for_selection[mock_job_id] = "Example Homework"

    # 2. Add all real jobs from the session state
    if "jobs" in st.session_state and st.session_state.jobs:
        # Sort jobs by submission time, newest first
        sorted_job_ids = sorted(
            st.session_state.jobs.keys(),
            key=lambda jid: st.session_state.jobs[jid].get("submitted_at", "0"),
            reverse=True
        )

        for job_id in sorted_job_ids:
            if job_id.startswith("MOCK_JOB_"):
                continue

            task_info = st.session_state.jobs[job_id]
            job_name = task_info.get("name", f"Task-{job_id[:8]}")
            all_jobs_for_selection[job_id] = job_name

    return all_jobs_for_selection