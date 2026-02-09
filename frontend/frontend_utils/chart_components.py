"""
Chart Components Utility Module

Contains various visualization chart generation functions, supporting Plotly and Altair charts
"""

# import plotly.express as px
import plotly.graph_objects as go
# from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
# import streamlit as st
from typing import List
# import altair as alt

from .data_loader import StudentScore, QuestionAnalysis

class ChartComponents:
    """Chart Components Class"""
    
    def __init__(self):
        """Initialize chart configuration"""
        # Color scheme
        self.colors = {
            'primary': "#84ABFF",      # Dark blue
            'secondary': "#964BC4",    # Purple
            'success': '#10B981',      # Green
            'warning': '#F59E0B',      # Orange
            'danger': '#EF4444',       # Red
            'info': '#3B82F6',         # Blue
            'teal': '#2E8B57',         # Teal
            'skyblue': '#87CEEB'       # Sky blue
        }
        
        # 图表默认配置
        self.default_layout = {
            'font': {'family': 'Noto Sans SC, sans-serif', 'size': 12},
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 60, 'r': 60, 't': 60, 'b': 60}
        }
    
    def create_score_distribution_histogram(self, student_scores: List[StudentScore]) -> go.Figure:
        """Create score distribution histogram"""
        scores = [score.percentage for score in student_scores]
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=scores,
            nbinsx=10,
            marker_color=self.colors['primary'],
            opacity=0.8,
            name='Student Count'
        ))
        
        # Add average score line
        avg_score = np.mean(scores) if scores else 0
        fig.add_vline(
            x=avg_score,
            line_dash="dash",
            line_color=self.colors['secondary'],
            annotation_text=f"Average: {avg_score:.1f}%"
        )
        
        # Add median line
        median_score = np.median(scores)
        fig.add_vline(
            x=median_score,
            line_dash="dot",
            line_color=self.colors['info'],
            annotation_text=f"Median: {median_score:.1f}%"
        )
        
        fig.update_layout(
            title="Score Distribution Histogram",
            xaxis_title="Score Percentage (%)",
            yaxis_title="Student Count",
            **self.default_layout
        )
        
        return fig
    
    def create_grade_distribution_pie(self, student_scores: List[StudentScore]) -> go.Figure:
        """Create grade distribution pie chart"""
        grade_counts = {}
        for score in student_scores:
            grade = score.grade_level
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        labels = list(grade_counts.keys())
        values = list(grade_counts.values())
        
        # Define colors for each grade level
        grade_colors = {
            'Excellent': "#C774F8",    # Green for excellent
            'Good': "#6F99F4",       # Blue for good
            'Average': "#55DC77",       # Teal for average
            'Passing': "#E3CC56",  # Orange for passing
            'Failing': "#DA5050"    # Red for failing
        }
        
        # Map colors to labels in the same order
        colors = [grade_colors.get(label, self.colors['primary']) for label in labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title="Grade Distribution",
            **self.default_layout
        )
        
        return fig
    
    def create_question_accuracy_bar(self, question_analysis: List[QuestionAnalysis]) -> go.Figure:
        """Create question accuracy bar chart"""
        questions = [f"Q{i+1}" for i in range(len(question_analysis))]
        accuracy_rates = [q.correct_rate * 100 for q in question_analysis]
        question_types = [q.question_type for q in question_analysis]
        
        # Set colors based on question type
        type_colors = {
            'Concept': self.colors['primary'],
            'Calculation': self.colors['success'],
            'Proof': self.colors['warning'],
            'Programming': self.colors['info']
        }
        
        colors = [type_colors.get(qt, self.colors['primary']) for qt in question_types]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=questions,
            y=accuracy_rates,
            marker_color=colors,
            text=[f"{rate:.1f}%" for rate in accuracy_rates],
            textposition='outside',
            name='Accuracy Rate'
        ))
        
        # Add passing line
        fig.add_hline(
            y=60,
            line_dash="dash",
            line_color=self.colors['danger'],
            annotation_text="Passing Line (60%)"
        )
        
        fig.update_layout(
            title="Question Accuracy Analysis",
            xaxis_title="Question Number",
            yaxis_title="Accuracy Rate (%)",
            **self.default_layout
        )
        
        return fig
    
    def create_knowledge_heatmap(self, question_analysis: List[QuestionAnalysis]) -> go.Figure:
        """Create knowledge point mastery heatmap"""
        # Statistics knowledge point mastery
        knowledge_stats = {}
        for qa in question_analysis:
            for kp in qa.knowledge_points:
                if kp not in knowledge_stats:
                    knowledge_stats[kp] = []
                knowledge_stats[kp].append(qa.correct_rate)
        
        # Calculate average mastery
        knowledge_mastery = {kp: np.mean(rates) if rates else 0 for kp, rates in knowledge_stats.items()}
        
        # Create matrix data (for heatmap effect, create a grid)
        knowledge_points = list(knowledge_mastery.keys())
        mastery_values = list(knowledge_mastery.values())
        
        # Reshape data into matrix form
        n_cols = 3
        n_rows = (len(knowledge_points) + n_cols - 1) // n_cols
        
        # Fill data into matrix
        matrix = np.zeros((n_rows, n_cols))
        labels = [['' for _ in range(n_cols)] for _ in range(n_rows)]
        
        for i, (kp, mastery) in enumerate(knowledge_mastery.items()):
            row, col = divmod(i, n_cols)
            if row < n_rows:
                matrix[row][col] = mastery
                labels[row][col] = kp
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            text=labels,
            texttemplate="%{text}<br>%{z:.1%}",
            textfont={"size": 10},
            colorscale='RdYlGn',
            reversescale=False,
            showscale=True,
            colorbar=dict(title="Mastery")
        ))
        
        fig.update_layout(
            title="Knowledge Point Mastery Heatmap",
            xaxis_title="",
            yaxis_title="",
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            **self.default_layout
        )
        
        return fig
    
    def create_student_radar_chart(self, student_score: StudentScore) -> go.Figure:
        """Create student personal ability radar chart"""
        # Statistics abilities by question type
        type_scores = {}
        type_counts = {}
        
        for q in student_score.questions:
            qtype = q['question_type']
            score_rate = q['score'] / q['max_score']
            
            if qtype not in type_scores:
                type_scores[qtype] = 0
                type_counts[qtype] = 0
            
            type_scores[qtype] += score_rate
            type_counts[qtype] += 1
        
        # Calculate average scores for each type
        categories = []
        values = []
        type_names = {
            'Concept': 'Concept Understanding',
            'Calculation': 'Calculation Ability',
            'Proof': 'Proof Reasoning',
            'Programming': 'Programming Implementation'
        }
        
        for qtype, total_score in type_scores.items():
            avg_score = (total_score / type_counts[qtype]) * 100
            categories.append(type_names.get(qtype, qtype))
            values.append(avg_score)
        
        # Close radar chart
        categories.append(categories[0])
        values.append(values[0])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=student_score.student_name,
            line_color=self.colors['primary'],
            fillcolor=self.colors['primary'],
            opacity=0.3
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title=f"{student_score.student_name} - Ability Radar Chart",
            **self.default_layout
        )
        
        return fig
    
    def create_error_analysis_bar(self, question_analysis: List[QuestionAnalysis]) -> go.Figure:
        """Create error analysis bar chart"""
        # Statistics all error types
        error_counts = {}
        for qa in question_analysis:
            for error in qa.common_errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        
        # Sort by frequency, take top 10
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        errors = [item[0] for item in sorted_errors]
        counts = [item[1] for item in sorted_errors]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=counts,
            y=errors,
            orientation='h',
            marker_color=self.colors['danger'],
            text=counts,
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Common Error Analysis (Top 10)",
            xaxis_title="Occurrence Count",
            yaxis_title="Error Type",
            **self.default_layout
        )
        
        return fig
    
    def create_score_trend_line(self, student_scores: List[StudentScore]) -> go.Figure:
        """Create score trend line chart (simulated historical data)"""
        # For demonstration purposes, generate simulated historical trend data
        dates = pd.date_range(start='2024-01-01', end='2024-09-01', freq='ME')
        
        # Simulate class average score trend
        base_score = 75
        trends = []
        for i, date in enumerate(dates):
            # Add some random fluctuations and overall upward trend
            trend_score = base_score + i * 2 + np.random.normal(0, 5)
            trends.append(min(100, max(0, trend_score)))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=trends,
            mode='lines+markers',
            name='Class Average',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=8)
        ))
        
        # Add current score point
        current_avg = np.mean([s.percentage for s in student_scores])
        fig.add_trace(go.Scatter(
            x=[dates[-1] + pd.Timedelta(days=30)],
            y=[current_avg],
            mode='markers',
            name='Current Average',
            marker=dict(size=12, color=self.colors['secondary'])
        ))
        
        fig.update_layout(
            title="Class Score Trend Analysis",
            xaxis_title="Time",
            yaxis_title="Average Score (%)",
            **self.default_layout
        )
        
        return fig
    
    def create_difficulty_vs_accuracy_scatter(self, question_analysis: List[QuestionAnalysis]) -> go.Figure:
        """Create difficulty vs accuracy scatter plot"""
        difficulties = [qa.difficulty for qa in question_analysis]
        accuracies = [qa.correct_rate * 100 for qa in question_analysis]
        question_ids = [qa.question_id for qa in question_analysis]
        question_types = [qa.question_type for qa in question_analysis]
        
        # Set colors based on question type
        type_colors = {
            'Concept': self.colors['primary'],
            'Calculation': self.colors['success'],
            'Proof': self.colors['warning'],
            'Programming': self.colors['info']
        }
        
        fig = go.Figure()
        
        for qtype in set(question_types):
            type_indices = [i for i, qt in enumerate(question_types) if qt == qtype]
            
            fig.add_trace(go.Scatter(
                x=[difficulties[i] for i in type_indices],
                y=[accuracies[i] for i in type_indices],
                mode='markers',
                name=qtype,
                text=[question_ids[i] for i in type_indices],
                marker=dict(
                    size=12,
                    color=type_colors.get(qtype, self.colors['primary']),
                    opacity=0.7
                )
            ))
        
        fig.update_layout(
            title="Question Difficulty vs Accuracy Analysis",
            xaxis_title="Difficulty Coefficient",
            yaxis_title="Accuracy Rate (%)",
            **self.default_layout
        )
        
        return fig
    
    def create_question_heatmap(self, question_analysis: List[QuestionAnalysis]) -> go.Figure:
        """Create question analysis heatmap"""
        if not question_analysis:
            # Create an empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="Question Analysis Heatmap",
                xaxis_title="Question Number",
                yaxis_title="Analysis Dimension",
                **self.default_layout
            )
            return fig
        
        # Prepare data for heatmap
        questions = [q.question_id for q in question_analysis]
        metrics = ["Difficulty", "Accuracy", "Average Score"]
        
        # Create data matrix
        z_data = []
        for metric in metrics:
            row = []
            for q in question_analysis:
                if metric == "Difficulty":
                    row.append(q.difficulty)
                elif metric == "Accuracy":
                    row.append(q.correct_rate)
                elif metric == "Average Score":
                    row.append(q.avg_score / q.max_score if q.max_score > 0 else 0)
            z_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=questions,
            y=metrics,
            colorscale='RdYlGn',
            reversescale=True,  # Reverse scale for better visualization
            showscale=True,
            colorbar=dict(title="Value"),
            text=z_data,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
        ))
        
        fig.update_layout(
            title="Question Analysis Heatmap",
            xaxis_title="Question Number",
            yaxis_title="Analysis Dimension",
            **self.default_layout
        )
        
        return fig


# Global chart components instance
chart_components = ChartComponents()

# Convenience functions
def create_score_distribution_chart(student_scores: List[StudentScore]) -> go.Figure:
    """Convenience function to create score distribution chart"""
    return chart_components.create_score_distribution_histogram(student_scores)

def create_grade_pie_chart(student_scores: List[StudentScore]) -> go.Figure:
    """Convenience function to create grade pie chart"""
    return chart_components.create_grade_distribution_pie(student_scores)

def create_question_accuracy_chart(question_analysis: List[QuestionAnalysis]) -> go.Figure:
    """Convenience function to create question accuracy chart"""
    return chart_components.create_question_accuracy_bar(question_analysis)

def create_knowledge_heatmap_chart(question_analysis: List[QuestionAnalysis]) -> go.Figure:
    """Convenience function to create knowledge heatmap"""
    return chart_components.create_knowledge_heatmap(question_analysis)

def create_student_radar_chart(student_score: StudentScore) -> go.Figure:
    """Convenience function to create student radar chart"""
    return chart_components.create_student_radar_chart(student_score)

def create_error_analysis_chart(question_analysis: List[QuestionAnalysis]) -> go.Figure:
    """Convenience function to create error analysis chart"""
    return chart_components.create_error_analysis_bar(question_analysis)

def create_trend_chart(student_scores: List[StudentScore]) -> go.Figure:
    """Convenience function to create trend chart"""
    return chart_components.create_score_trend_line(student_scores)

def create_difficulty_scatter_chart(question_analysis: List[QuestionAnalysis]) -> go.Figure:
    """Convenience function to create difficulty scatter chart"""
    return chart_components.create_difficulty_vs_accuracy_scatter(question_analysis)

def create_question_heatmap_chart(question_analysis: List[QuestionAnalysis]) -> go.Figure:
    """Convenience function to create question heatmap"""
    return chart_components.create_question_heatmap(question_analysis)
