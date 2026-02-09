"""
Historical Grading Records (pages/history.py)

Provides complete management of grading history, including:
1. Draft storage: after uploading assignments, you can save as draft, preview recognition results, and manually adjust
2. Record viewing: view completed grading records and visual analysis
3. Record management: delete, edit draft records
"""

import streamlit as st
import requests
# import json
# import os
# from datetime import datetime, timedelta
# from typing import Dict, List, Any, Optional
# import pandas as pd
from utils import *

# Import data loader for AI grading data
from frontend_utils.data_loader import load_ai_grading_data

# Page configuration
st.set_page_config(
    page_title="SmarTAI - Historical Grading Records",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
initialize_session_state()
load_custom_css()

def init_storage_state():
    """Initialize storage state"""
    if 'completed_records' not in st.session_state:
        st.session_state.completed_records = {}  # Completed records
    
    # Initialize mock data for consistency with other pages
    if 'sample_data' not in st.session_state:
        from frontend_utils.data_loader import load_mock_data
        with st.spinner("Loading mock data..."):
            st.session_state.sample_data = load_mock_data()

def render_header():
    """Render page header"""
    col1, col3, col2 = st.columns([4, 16, 4])

    # col3 = st.columns(1)[0]

    with col1:
        if st.button("🏠 Return to Home", type="secondary"):
            st.switch_page("pages/main.py")
    
    with col2:
        if st.button("🔄 Refresh Interface", type="secondary"):
            try:
                # Try to reconnect to backend first
                test_response = requests.get(f"{st.session_state.backend}/ai_grading/all_jobs", timeout=5)
                if test_response.status_code == 200:
                    sync_completed_records()
                    st.success("Records have been refreshed!")
                else:
                    st.warning(f"Backend connection abnormal (status code: {test_response.status_code}), records may not be fully refreshed.")
                    sync_completed_records()
                    st.success("Records have been refreshed!")
            except Exception as e:
                st.warning(f"Unable to connect to backend: {str(e)}, will use cached data to refresh interface.")
                sync_completed_records()
                st.success("Records have been refreshed!")
            st.rerun()

    with col3:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🕒 Historical Grading Records</h1>", 
                   unsafe_allow_html=True)
        
def sync_completed_records():
    """Sync completed grading records"""
    if "jobs" in st.session_state and st.session_state.jobs:
        # Create a copy of the keys to avoid "dictionary changed size during iteration" error
        job_ids = list(st.session_state.jobs.keys())
        for job_id in job_ids:
            # Check if job_id still exists (in case it was deleted during iteration)
            if job_id not in st.session_state.jobs:
                continue
                
            task_info = st.session_state.jobs[job_id]
            
            # Handle mock jobs - don't remove them, but don't poll them either
            if job_id.startswith("MOCK_JOB_"):
                # Keep mock jobs in session state but don't poll them
                continue
                
            # Check if this is a mock job
            is_mock = task_info.get("is_mock", False)
            
            if is_mock:
                # Keep mock jobs in session state but don't poll them
                continue



def render_tabs():
    """Render main tabs"""
    tab1, tab2 = st.tabs(["✅ Completed Grading", "📊 Overview"])
    
    with tab1:
        render_completed_records()
    
    with tab2:
        render_statistics_overview()

def render_mock_data_preview():
    """Render mock data preview"""
    st.markdown("## 🔍 Mock Data Preview")
    st.markdown("This shows mock data consistent with the score report and visualization pages.")
    
    # Load mock data
    from frontend_utils.data_loader import load_mock_data
    mock_data = st.session_state.get('sample_data', load_mock_data())
    
    students = mock_data.get('student_scores', [])
    assignment_stats = mock_data.get('assignment_stats', None)
    question_analysis = mock_data.get('question_analysis', [])
    
    if not students:
        st.warning("No mock data available.")
        return
    
    # Display assignment stats
    if assignment_stats:
        st.markdown(f"### Assignment Statistics")
        st.markdown(f"**Assignment Name:** {assignment_stats.assignment_name}")
        st.markdown(f"**Total Students:** {assignment_stats.total_students}")
        st.markdown(f"**Submitted:** {assignment_stats.submitted_count}")
        st.markdown(f"**Average Score:** {assignment_stats.avg_score:.1f}")
        st.markdown(f"**Highest Score:** {assignment_stats.max_score:.1f}")
        st.markdown(f"**Lowest Score:** {assignment_stats.min_score:.1f}")
        st.markdown(f"**Pass Rate:** {assignment_stats.pass_rate:.1f}%")
    
    st.markdown("---")
    
    # Display top students
    st.markdown("### Top Student Scores (Top 10)")
    sorted_students = sorted(students, key=lambda x: x.percentage, reverse=True)
    
    # Prepare data for display
    data = []
    for i, student in enumerate(sorted_students[:10], 1):
        data.append({
            "Rank": i,
            "Student ID": student.student_id,
            "Name": student.student_name,
            "Total Score": f"{student.total_score:.1f}/{student.max_score}",
            "Percentage": f"{student.percentage:.1f}%",
            "Grade Level": student.grade_level
        })
    
    import pandas as pd
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch')
    
    st.markdown("---")
    
    # Display question analysis if available
    if question_analysis:
        st.markdown("### Question Analysis Overview")
        # Prepare data for display
        question_data = []
        for question in question_analysis[:10]:  # Show first 10 questions
            question_data.append({
                "Question ID": question.question_id,
                "Question Type": question.question_type,
                "Difficulty": f"{question.difficulty:.2f}",
                "Correct Rate": f"{question.correct_rate:.1%}",
                "Average Score": f"{question.avg_score:.1f}/{question.max_score}"
            })
        
        df_questions = pd.DataFrame(question_data)
        st.dataframe(df_questions, width='stretch')





def render_completed_records():
    """Render completed grading records"""
    st.markdown("## ✅ Completed Grading")
    st.markdown("This shows completed AI grading records where you can view results and visual analysis.")

    # --- Change 1: Simplify logic ---
    # Remove calls to sync_completed_records() and complex merging logic.
    # Create a fresh dictionary to safely build the display list instead of modifying session_state.
    all_completed_display = {}

    # --- Change 2: Permanently display mock data task ---
    # Directly read mock data from session_state and add it as the first item to the display list.
    # This ensures the mock task is always visible and not accidentally removed.
    if 'sample_data' in st.session_state and st.session_state.sample_data:
        assignment_stats = st.session_state.sample_data.get('assignment_stats')
        if assignment_stats:
            mock_job_id = "MOCK_JOB_001"
            submit_time = assignment_stats.create_time.strftime("%Y-%m-%d %H:%M:%S")
            all_completed_display[mock_job_id] = {
                "task_name": f"Mock Data - {assignment_stats.assignment_name}",
                "submitted_at": submit_time,
                "completed_at": submit_time, # For mock, completed time is the same
                "status": "completed"
            }

    # --- Change 3: Safely iterate and check real tasks ---
    # Read all real tasks from st.session_state.jobs.
    # Key point: This loop only reads data to check status and never deletes or modifies st.session_state.jobs itself.
    # This fixes the core bug of history record loss.
    if "jobs" in st.session_state and st.session_state.jobs:
        # Sort by submission time in reverse order so the latest tasks appear first
        sorted_job_ids = sorted(
            st.session_state.jobs.keys(),
            key=lambda jid: st.session_state.jobs[jid].get("submitted_at", "0"),
            reverse=True
        )
        
        for job_id in sorted_job_ids:
            if job_id.startswith("MOCK_JOB_"):
                continue  # Mock tasks handled above

            task_info = st.session_state.jobs[job_id]
            status = "pending"  # Default status
            try:
                # Query backend for the latest task status
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=3)
                if result.ok:
                    status = result.json().get("status", "pending")
            except requests.RequestException:
                status = "error" # Network request failed

            # Only add tasks with status "completed" to display list
            if status == "completed":
                all_completed_display[job_id] = {
                    "task_name": task_info.get("name", "Unknown Task"),
                    "submitted_at": task_info.get("submitted_at", "Unknown Time"),
                    "completed_at": "Just now", # Could fetch accurate completion time from backend
                    "status": "completed"
                }

    if not all_completed_display:
        st.info("No completed grading records.")
        return

    sorted_records_list = sorted(
        all_completed_display.items(), 
        key=lambda item: item[1]['submitted_at'], 
        reverse=True
    )
    # --- Change 4: Adjust display and navigation logic ---
    # Iterate through the safely constructed all_completed_display dictionary to show records.
    for job_id, record in sorted_records_list:
        with st.container():
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #10B981;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="color: #1E3A8A; margin: 0 0 0.5rem 0;">✅ {record['task_name']}</h3>
                        <p style="color: #64748B; margin: 0; font-size: 0.9rem;">
                            <strong>Submitted At:</strong> {record['submitted_at']} | 
                            <strong>Completed At:</strong> {record['completed_at']}
                        </p>
                    </div>
                    <div>
                        <span style="background: #D1FAE5; color: #065F46; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                            Completed
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col0, col1, col2, col3, col4 = st.columns(5)

            with col0:
                if st.button("📊 Grading Result", key=f"result_{job_id}", width='stretch', type="secondary"):
                    st.session_state.selected_job_from_history = job_id
                    st.switch_page("pages/grade_results.py")

            with col1:
                if st.button("💯 Score Report", key=f"view_{job_id}", width='stretch', type="secondary"):
                    # Use a dedicated temporary variable to pass the selection
                    st.session_state.selected_job_from_history = job_id
                    st.switch_page("pages/score_report.py")

            with col2:
                if st.button("📈 Performance Analysis", key=f"viz_{job_id}", width='stretch'):
                    # Same temporary variable
                    st.session_state.selected_job_from_history = job_id
                    st.switch_page("pages/visualization.py")

            with col3:
                if st.button("📄 Export PDF Report", key=f"report_{job_id}", width='stretch'):
                    try:
                        # Import PDF generator
                        from frontend_utils.pdf_generator import generate_assignment_report
                        
                        # Get data for the report
                        if job_id.startswith("MOCK_JOB"):
                            # Use mock data
                            data = st.session_state.sample_data
                        else:
                            # Fetch data from backend
                            with st.spinner("Fetching data..."):
                                ai_data = load_ai_grading_data(job_id)
                                if "error" not in ai_data:
                                    data = ai_data
                                else:
                                    st.error(f"Failed to fetch data: {ai_data['error']}")
                                    st.stop()
                        
                        students = data.get('student_scores', [])
                        assignment_stats = data.get('assignment_stats', None)
                        question_analysis = data.get('question_analysis', [])
                        
                        if assignment_stats and students:
                            with st.spinner("Generating report..."):
                                # Generate PDF report
                                pdf_path = generate_assignment_report(assignment_stats, students, question_analysis)
                                
                                # Provide download link
                                with open(pdf_path, "rb") as file:
                                    st.download_button(
                                        label="📥 Download PDF Report",
                                        data=file,
                                        file_name=f"{assignment_stats.assignment_name}_report.pdf",
                                        mime="application/pdf",
                                        key=f"download_{job_id}"
                                    )
                                st.success("Report generated! Click the button above to download.")
                        else:
                            st.warning("Unable to generate report: missing required data.")
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
            
            with col4:
                # --- Change 6: Fix deletion logic ---
                # Ensure the delete button only works for real tasks and only removes from st.session_state.jobs.
                if not job_id.startswith("MOCK_JOB") and st.button("🗑️ Delete Record", key=f"remove_{job_id}", width='stretch', type="secondary"):
                    if job_id in st.session_state.jobs:
                        del st.session_state.jobs[job_id]
                        st.success("Record removed!")
                        st.rerun()
                elif job_id.startswith("MOCK_JOB"):
                     st.button("Example Mock Task", disabled=True, key=f"remove_{job_id}", width='stretch')


def render_statistics_overview():
    """Render statistics overview"""
    st.markdown("## 📊 Overview")
    
    # Calculate statistics
    completed_count = len(st.session_state.get('completed_records', {}))
    
    # Calculate completed tasks from jobs
    if "jobs" in st.session_state and st.session_state.jobs:
        # Create a copy of the keys to avoid "dictionary changed size during iteration" error
        job_ids = list(st.session_state.jobs.keys())
        for job_id in job_ids:
            # Check if job_id still exists (in case it was deleted during iteration)
            if job_id not in st.session_state.jobs:
                continue
                
            # Skip mock jobs entirely
            if job_id.startswith("MOCK_JOB_"):
                continue
                
            task_info = st.session_state.jobs[job_id]
            
            # Check if this is a mock job
            is_mock = task_info.get("is_mock", False)
            
            if is_mock:
                continue
            
            try:
                result = requests.get(f"{st.session_state.backend}/ai_grading/grade_result/{job_id}", timeout=5)
                result.raise_for_status()
                status = result.json().get("status", "Unknown")
                if status == "completed":
                    completed_count += 1
            except:
                continue
    
    # Add mock data to statistics
    if 'sample_data' in st.session_state and st.session_state.sample_data:
        assignment_stats = st.session_state.sample_data.get('assignment_stats')
        if assignment_stats:
            completed_count += 1
    
    total_records = completed_count
    
    # Display statistics cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #1E3A8A;">
            <h1 style="color: #1E3A8A; margin: 0; font-size: 3rem;">{total_records}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Total Records</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #10B981;">
            <h1 style="color: #10B981; margin: 0; font-size: 3rem;">{completed_count}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        completion_rate = 100.0 if total_records > 0 else 0
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 4px solid #8B5CF6;">
            <h1 style="color: #8B5CF6; margin: 0; font-size: 3rem;">{completion_rate:.1f}%</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Completion Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 📅 Recent Activity")
    st.info("No recent activity records.")

def main():
    """Main function"""
    init_storage_state()
    
    render_header()
    st.markdown("---")
    
    render_tabs()
    
    # Call this function on every page
    inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()
