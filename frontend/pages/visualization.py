"""
Visualization Analysis Page (pages/visualization.py)

Simplified version focusing on core grade display features
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List
# import plotly.express as px
# import plotly.graph_objects as go
import os
# import json
from utils import *

# 导入自定义模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the updated data loader that can handle AI grading data
from frontend_utils.data_loader import StudentScore, QuestionAnalysis, AssignmentStats, load_ai_grading_data, load_mock_data
from frontend_utils.chart_components import (
    create_score_distribution_chart, create_grade_pie_chart, create_question_accuracy_chart,
    create_knowledge_heatmap_chart, create_error_analysis_chart, create_difficulty_scatter_chart,
    create_question_heatmap_chart
)

# 页面配置
st.set_page_config(
    page_title="SmarTAI - Grade Visualization",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def init_session_state():
    """Initialize session state"""
    # Initialize basic session state
    initialize_session_state()
    
    # Set default job to MOCK_JOB_001 if not already set
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = "MOCK_JOB_001"
    
    # Always ensure mock data is available
    if 'sample_data' not in st.session_state or not st.session_state.sample_data:
        with st.spinner("Loading data..."):
            st.session_state.sample_data = load_mock_data()
    
    # Check if we have a selected job for AI grading data
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id:
        # Load AI grading data
        with st.spinner("Loading AI grading data..."):
            ai_data = load_ai_grading_data(st.session_state.selected_job_id)
            if "error" not in ai_data:
                st.session_state.ai_grading_data = ai_data
            else:
                st.error(f"Failed to load AI grading data: {ai_data['error']}")
                # Fallback to mock data
                st.session_state.sample_data = load_mock_data()
    
    # Ensure we always have valid sample data
    if 'sample_data' not in st.session_state or not st.session_state.sample_data:
        st.session_state.sample_data = load_mock_data()

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
        st.markdown("<h1 style='text-align: center; color: #000000;'>📈 Student Grade Visualization Analysis</h1>", 
                   unsafe_allow_html=True)

def render_filters(students: List[StudentScore], question_analysis: List[QuestionAnalysis]):
    """Render filters"""
    st.markdown("## 🔍 Data Filters")
    
    # Create tabs for different filter categories
    tab1, tab2 = st.tabs(["Student Filters", "Question Filters"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            # Student ID range filter
            student_ids = [s.student_id for s in students]
            if student_ids:
                min_id = min(student_ids)
                max_id = max(student_ids)
                selected_ids = st.multiselect("Select Student IDs", student_ids, default=student_ids[:5])
        
        with col2:
            # Grade level filter
            grade_levels = list(set([s.grade_level for s in students]))
            selected_grades = st.multiselect("Select Grade Levels", grade_levels, default=grade_levels)
    
    with tab2:
        # Question filters
        if question_analysis:
            question_ids = [q.question_id for q in question_analysis]
            question_types = list(set([q.question_type for q in question_analysis]))
            
            col1, col2 = st.columns(2)
            with col1:
                selected_questions = st.multiselect("Select Questions", question_ids)
            with col2:
                selected_question_types = st.multiselect("Select Question Types", question_types)
    
    # Apply filters button
    if st.button("Apply Filters"):
        st.success("Filters applied!")
    
    return students, question_analysis

def calculate_median_score(students: List[StudentScore]) -> float:
    """Calculate median score"""
    scores = [s.percentage for s in students]
    return np.median(scores) if scores else 0

def render_statistics_overview(students: List[StudentScore], assignment_stats: AssignmentStats):
    """Render statistics overview"""
    st.markdown("## 📊 Score Overview")
    
    # Compute statistics
    if not students:  # Handle empty data
        st.warning("⚠️ No data to display")
        return
    
    scores = [s.percentage for s in students]
    avg_score = np.mean(scores) if scores else 0
    median_score = calculate_median_score(students)
    max_score = np.max(scores) if scores else 0
    min_score = np.min(scores) if scores else 0
    std_score = np.std(scores) if scores else 0
    pass_rate = len([s for s in scores if s >= 60]) / len(scores) * 100 if scores else 0
    excellence_rate = len([s for s in scores if s >= 85]) / len(scores) * 100 if scores else 0
    
    # Display statistic cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{len(students)}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Submissions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{avg_score:.1f}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Average</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{median_score:.1f}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Median</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{max_score:.1f}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Max</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{min_score:.1f}</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Min</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center; border-top: 4px solid #1E3A8A;">
            <div style="font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.25rem;">{pass_rate:.1f}%</div>
            <div style="font-size: 0.875rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Pass Rate</div>
        </div>
        """, unsafe_allow_html=True)

def render_student_table(students: List[StudentScore]):
    """Render student table"""
    st.markdown("## 📋 Student Score List")
    
    if not students:
        st.warning("⚠️ No student data")
        return
    
    # Prepare table data
    data = []
    for student in students:
        # # Map grade labels to English for display, accept both CN/EN inputs
        # grade_map = {"优秀": "Excellent", "良好": "Good", "中等": "Average", "及格": "Pass", "不及格": "Fail"}
        # grade_label = grade_map.get(student.grade_level, student.grade_level)
        
        # # Determine color based on grade level
        # if grade_label == "Excellent":
        #     grade_color = "#C774F8"
        # elif grade_label == "Good":
        #     grade_color = "#6F99F4"
        # elif grade_label == "Average":
        #     grade_color = "#55DC77"
        # elif grade_label == "Pass":
        #     grade_color = "#E3CC56"
        # else:  # Fail or other
        #     grade_color = "#DA5050"

        # --- 修改开始：统一成绩标签和颜色逻辑 ---
        
        # 获取原始成绩字符串并去空格
        raw_grade = str(student.grade_level).strip()
        
        # 默认值 (Fail / Red)
        grade_label = "Fail"
        grade_color = "#DA5050" # 红色
        
        # 判定逻辑
        if raw_grade in ["优秀", "Excellent", "A"]:
            grade_label = "Excellent"
            grade_color = "#C774F8" # 紫色
        elif raw_grade in ["良好", "Good", "B"]:
            grade_label = "Good"
            grade_color = "#6F99F4" # 蓝色
        elif raw_grade in ["中等", "Average", "C"]:
            grade_label = "Average"
            grade_color = "#55DC77" # 绿色
        elif raw_grade in ["及格", "Pass", "Passing", "D"]:
            # 将 "Passing" 统一映射为 "Pass"，并指定黄色
            grade_label = "Pass"
            grade_color = "#E3CC56" # 黄色
        elif raw_grade in ["不及格", "Fail", "Failing", "F"]:
            # 将 "Failing" 统一映射为 "Fail"
            grade_label = "Fail"
            grade_color = "#DA5050" # 红色
            
        # --- 修改结束 ---
            
        # Apply color to grade level
        colored_grade = f"<span style='color: {grade_color}; font-weight: bold;'>{grade_label}</span>"
        
        data.append({
            "Student ID": student.student_id,
            "Name": student.student_name,
            "Total": f"{student.total_score:.1f}/{student.max_score}",
            "Percentage": f"{student.percentage:.1f}%",
            "Grade": colored_grade,
            "Submitted At": student.submit_time.strftime('%Y-%m-%d %H:%M'),
            "Confidence": f"{student.confidence_score:.1%}",
            "Needs Review": "Yes" if student.need_review else "No"
        })
    
    df = pd.DataFrame(data)
    
    # Display table with colored grade levels
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

def render_charts(students: List[StudentScore], question_analysis: List[QuestionAnalysis]):
    """Render charts"""
    st.markdown("## 📈 Score Distribution Charts")
    
    if not students:
        st.warning("⚠️ No data to display")
        return
    
    try:
        # Create tabs for different chart categories
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Score Distribution", "Question Analysis", "Error Analysis", "Question Heatmap", "Knowledge Mastery", "Teaching Suggestions"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Score Distribution Histogram")
                fig1 = create_score_distribution_chart(students)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.markdown("### Grade Level Distribution")
                fig2 = create_grade_pie_chart(students)
                st.plotly_chart(fig2, use_container_width=True)
        
        with tab2:
            if question_analysis:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Question Accuracy Analysis")
                    fig3 = create_question_accuracy_chart(question_analysis)
                    st.plotly_chart(fig3, use_container_width=True)
                
                with col2:
                    st.markdown("### Question Difficulty vs Accuracy")
                    fig4 = create_difficulty_scatter_chart(question_analysis)
                    st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No question analysis data")
        
        with tab3:
            if question_analysis:
                st.markdown("### Frequent Errors (Top 10)")
                fig6 = create_error_analysis_chart(question_analysis)
                st.plotly_chart(fig6, use_container_width=True)
            else:
                st.info("No error analysis data")
                
        with tab4:
            if question_analysis:
                st.markdown("### Question Analysis Heatmap")
                fig7 = create_question_heatmap_chart(question_analysis)
                st.plotly_chart(fig7, use_container_width=True)
            else:
                st.info("No question analysis data")
                
        with tab5:
            # Knowledge mastery section under development
            st.info("Knowledge mastery is under development. Stay tuned...")
            
        with tab6:
            st.info("Teaching suggestions are under development...")
                
    except Exception as e:
        st.error(f"Error generating charts: {str(e)}")

def render_weakness_analysis(question_analysis: List[QuestionAnalysis]):
    """Render teaching weakness analysis"""
    st.markdown("## ⚠️ Teaching Weakness Identification")
    
    if not question_analysis:
        st.info("No question analysis data")
        return
    
    # Find questions with low correct rates (high error rates)
    low_correct_questions = [q for q in question_analysis if q.correct_rate < 0.6]
    
    if low_correct_questions:
        # Sort by correct rate (ascending)
        low_correct_questions.sort(key=lambda x: x.correct_rate)
        
        st.markdown("### Error-Prone Questions Ranking")
        for i, question in enumerate(low_correct_questions[:5], 1):  # Top 5
            error_color = "#EF4444" if question.correct_rate < 0.4 else "#F59E0B"
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0.5rem 0; border-left: 4px solid {error_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="color: #1E3A8A; margin: 0;">{i}. Question {question.question_id} ({question.question_type})</h4>
                    <span style="font-size: 1.2rem; font-weight: bold; color: {error_color};">{question.correct_rate:.1%}</span>
                </div>
                <p style="margin: 0.5rem 0 0 0; color: #64748B;">Knowledge Points: {', '.join(question.knowledge_points[:3])}</p>
                <p style="margin: 0.5rem 0 0 0; color: #64748B;">Common Errors: {', '.join(question.common_errors[:3])}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No significant teaching weaknesses detected")

def render_export_section():
    """Render export and sharing section"""
    st.markdown("## 📤 Data Export & Sharing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Export to Feishu Bitable")
        st.info("This feature will be implemented in a future version")
        
    with col2:
        st.markdown("### Generate Dashboard Snapshot")
        st.info("This feature will be implemented in a future version")
    
    with col3:
        st.markdown("### Generate PDF Report")
        if st.button("📄 Generate PDF Report"):
            try:
                from frontend_utils.pdf_generator import generate_assignment_report
                if 'ai_grading_data' in st.session_state and st.session_state.ai_grading_data:
                    data = st.session_state.ai_grading_data
                elif 'sample_data' in st.session_state and st.session_state.sample_data:
                    data = st.session_state.sample_data
                else:
                    from frontend_utils.data_loader import load_mock_data
                    data = load_mock_data()
                students = data.get('student_scores', [])
                assignment_stats = data.get('assignment_stats', None)
                question_analysis = data.get('question_analysis', [])
                if assignment_stats and students:
                    with st.spinner("Generating PDF report..."):
                        pdf_path = generate_assignment_report(assignment_stats, students, question_analysis)
                        with open(pdf_path, "rb") as file:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=file,
                                file_name=f"{assignment_stats.assignment_name}_Visualization_Report.pdf",
                                mime="application/pdf",
                                key="download_pdf_viz"
                            )
                        st.success("PDF generated. Click above to download.")
                else:
                    st.warning("Cannot generate report: missing required data.")
            except Exception as e:
                st.error(f"Error generating PDF report: {str(e)}")

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
    keys_to_clear = [
        'ai_grading_data',
        'report_job_selector'
    ]
    
    # Only clear sample_data if it's not MOCK_JOB_001
    if 'selected_job_id' in st.session_state and st.session_state.selected_job_id != "MOCK_JOB_001":
        keys_to_clear.append('sample_data')
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def main():
    """Main function"""
    # 初始化
    init_session_state()
    
    # 渲染页面
    render_header()
    
    selectable_jobs = get_all_jobs_for_selection()
    if not selectable_jobs:
        st.info("No grading jobs found; showing mock data.")
        selectable_jobs = {"MOCK_JOB_001": "Mock Data: Example Assignment"}
    job_ids = list(selectable_jobs.keys())
    default_index = 0
    if "selected_job_from_history" in st.session_state:
        job_id_from_history = st.session_state.selected_job_from_history
        if job_id_from_history in job_ids:
            default_index = job_ids.index(job_id_from_history)
        del st.session_state.selected_job_from_history
    elif "selected_job_id" in st.session_state and st.session_state.selected_job_id in job_ids:
        default_index = job_ids.index(st.session_state.selected_job_id)
    elif "MOCK_JOB_001" in job_ids:
        default_index = job_ids.index("MOCK_JOB_001")
    def on_selection_change():
        """Callback: update global job ID when selection changes"""
        st.session_state.selected_job_id = st.session_state.viz_job_selector
    selected_job = st.selectbox(
        "Select a grading job for visualization",
        options=job_ids,
        format_func=lambda jid: selectable_jobs.get(jid, jid),
        index=default_index,
        key="viz_job_selector",
        on_change=on_selection_change
    )
    
    # 实时更新全局选择ID，确保页面内状态一致
    st.session_state.selected_job_id = selected_job
    st.markdown("---")

    # --- 改动 4: 根据下拉框的选择，加载对应的数据 ---
    data_to_display = None
    if selected_job.startswith("MOCK_JOB"):
        # 如果是模拟任务，直接从 session_state 加载模拟数据
        data_to_display = st.session_state.get('sample_data', load_mock_data())
    else:
        # 如果是真实任务，从后端API加载数据
        with st.spinner("Loading AI grading data..."):
            ai_data = load_ai_grading_data(selected_job)
            if "error" not in ai_data:
                data_to_display = ai_data
            else:
                st.error(f"Failed to load AI grading data: {ai_data['error']}")
                st.info("Displaying sample data as fallback.")
                data_to_display = st.session_state.get('sample_data', load_mock_data())
    
    if not data_to_display:
        st.warning("Unable to load data for the selected task.")
        st.stop()
        
    # --- 改动 5: 使用新加载的数据驱动页面渲染 ---
    # 旧代码是直接从 st.session_state.ai_grading_data 或 sample_data 中获取数据,
    # 现在我们统一从 data_to_display 变量中获取。
    # 后续的渲染函数完全不需要修改。
    students = data_to_display.get('student_scores', [])
    assignment_stats = data_to_display.get('assignment_stats', None)
    question_analysis = data_to_display.get('question_analysis', [])
    
    # 如果 assignment_stats 不存在，创建一个默认的（此逻辑与您原代码一致）
    if not assignment_stats and students:
         assignment_stats = AssignmentStats(
            assignment_id="DEFAULT",
            assignment_name="Example Homework",
            total_students=len(students),
            submitted_count=len(students),
            avg_score=np.mean([s.percentage for s in students]) if students and len(students) > 0 else 0,
            max_score=max([s.percentage for s in students]) if students and len(students) > 0 else 0,
            min_score=min([s.percentage for s in students]) if students and len(students) > 0 else 0,
            std_score=np.std([s.percentage for s in students]) if students and len(students) > 0 else 0,
            pass_rate=(len([s for s in students if s.percentage >= 60]) / len(students) * 100) if students and len(students) > 0 else 0,
            question_count=len(question_analysis),
            create_time=datetime.now()
        )

    # 渲染统计概览
    if assignment_stats:
        render_statistics_overview(students, assignment_stats)
    
    st.markdown("---")
    
    # 渲染学生表格
    render_student_table(students)
    
    st.markdown("---")
    
    # 渲染图表
    render_charts(students, question_analysis)
    
    st.markdown("---")
    
    # 渲染教学薄弱环节分析
    render_weakness_analysis(question_analysis)
    
    st.markdown("---")
    
    # 渲染导出和分享功能
    render_export_section()

    inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()