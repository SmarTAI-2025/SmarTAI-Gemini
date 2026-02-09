"""
Data Models and Data Loader Module

Contains student score, assignment statistics, question analysis data classes and AI grading data loading functions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
# import pandas as pd
import numpy as np
import requests
import streamlit as st
import json
import os

@dataclass
class StudentScore:
    """Student Score Data Class"""
    student_id: str
    student_name: str
    total_score: float
    max_score: float
    submit_time: datetime
    questions: List[Dict[str, Any]] = field(default_factory=list)
    need_review: bool = False
    confidence_score: float = 0.85
    
    @property
    def percentage(self) -> float:
        """Calculate percentage score"""
        return (self.total_score / self.max_score) * 100 if self.max_score > 0 else 0
    
    @property
    def grade_level(self) -> str:
        """Get grade level"""
        percentage = self.percentage
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Good"
        elif percentage >= 70:
            return "Average"
        elif percentage >= 60:
            return "Passing"
        else:
            return "Failing"

@dataclass
class QuestionAnalysis:
    """Question Analysis Data Class"""
    question_id: str
    question_type: str  # concept, calculation, proof, programming
    topic: str
    difficulty: float  # 0-1
    correct_rate: float
    avg_score: float
    max_score: float
    common_errors: List[str] = field(default_factory=list)
    knowledge_points: List[str] = field(default_factory=list)
    
    @property
    def difficulty_level(self) -> str:
        """Get difficulty level"""
        if self.difficulty <= 0.3:
            return "Easy"
        elif self.difficulty <= 0.6:
            return "Medium"
        else:
            return "Difficult"

@dataclass
class AssignmentStats:
    """Assignment Statistics Data Class"""
    assignment_id: str
    assignment_name: str
    total_students: int
    submitted_count: int
    avg_score: float
    max_score: float
    min_score: float
    std_score: float
    pass_rate: float
    question_count: int
    create_time: datetime
    
    @property
    def submission_rate(self) -> float:
        """Calculate submission rate"""
        return (self.submitted_count / self.total_students) * 100 if self.total_students > 0 else 0

def check_all_jobs() -> Dict[str, Any]:
    """
    Check all jobs for debugging purposes
    """
    try:
        response = requests.get(
            f"{st.session_state.backend}/ai_grading/all_jobs",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to check jobs: {str(e)}"}

def load_mock_data() -> Dict[str, Any]:
    """
    Load mock data for testing when real data is not available
    """
    try:
        # Try to load from root directory first (where the file actually is)
        mock_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "mock_data.json")
        if not os.path.exists(mock_data_path):
            # Fallback to frontend directory
            mock_data_path = os.path.join(os.path.dirname(__file__), "..", "mock_data.json")
        
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
        # Return empty data structure instead of error
        return {
            "student_scores": [],
            "question_analysis": [],
            "assignment_stats": None
        }

def load_ai_grading_data(job_id: str) -> Dict[str, Any]:
    """
    Load actual data from AI grading system
    """
    try:
        # Debug information
        print(f"Requesting AI grading data for job {job_id}")
        
        # If it's a mock job, return mock data directly
        if job_id == "MOCK_JOB_001":
            return load_mock_data()
        
        # Get grading results
        response = requests.get(
            f"{st.session_state.backend}/ai_grading/grade_result/{job_id}",
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        # Debug information
        print(f"Loading AI grading data for job {job_id}")
        print(f"Result status: {result.get('status', 'no status')}")
        print(f"Full result: {result}")
        
        # Check if the job is completed - this is the key fix
        if result.get("status") != "completed":
            # Also check if the result contains data even if status is not explicitly "completed"
            if "results" not in result and "corrections" not in result:
                # If we can't get real data, return mock data
                # st.info("This shows 【Sample Mock Task】!")
                return load_mock_data()
        
        # Map question types: from internal types to English display names
        # type_display_mapping = {
        #     "concept": "Concept",
        #     "calculation": "Calculation", 
        #     "proof": "Proof",
        #     "programming": "Programming"
        # }

        type_display_mapping1 = {
            "concept": "Concept",
            "calculation": "Calculation", 
            "proof": "Proof",
            "programming": "Programming",
            "other": "Other"
        }

        type_display_mapping2 = {
            "概念题": "Concept",
            "计算题": "Calculation", 
            "证明题": "Proof",
            "编程题": "Programming",
            "其他" : "Other",
            "其它" : "Other"
        }
        
        # Convert AI grading data to the format required by visualization pages
        if "results" in result:  # Batch grading results
            # Process batch grading results
            students_data = []
            all_corrections = []
            
            for student_result in result["results"]:
                student_id = student_result["student_id"]
                # student_name = student_result["student_name"]
                # 优先取 student_name，取不到取 name，再取不到就用 ID 拼凑
                student_name = student_result.get("student_name", f"Student {student_id}")
                corrections = student_result["corrections"]
                all_corrections.extend(corrections)
                
                # Calculate student total score
                total_score = sum(c["score"] for c in corrections)
                max_score = sum(c["max_score"] for c in corrections)
                
                # Convert question data
                questions = []
                for correction in corrections:
                    # Directly use the returned type, if it's already Chinese use directly, otherwise map
                    question_type = correction["type"]
                    if question_type in type_display_mapping1:
                        display_type = type_display_mapping1[question_type]
                    elif question_type in type_display_mapping2:
                        display_type = type_display_mapping2[question_type]
                    elif question_type in type_display_mapping1.values():
                        display_type = question_type
                    else:
                        # display_type = "Concept"  # Default type
                        display_type = "Other"
                    
                    question = {
                        "question_id": correction["q_id"],
                        "question_type": display_type,  # Use English display type
                        "score": correction["score"],
                        "max_score": correction["max_score"],
                        "confidence": correction["confidence"],
                        "feedback": correction["comment"],
                        "knowledge_points": correction.get("hits", []),
                        "step_analysis": [
                            {
                                "step_number": step["step_no"],
                                "step_title": f"Step {step['step_no']}",
                                "is_correct": step.get("is_correct", True),
                                "points_earned": step["score"],
                                "max_points": correction["max_score"] / len(correction.get("steps", [1])),
                                "feedback": step.get("desc", ""),
                                "error_type": None if step.get("is_correct", True) else "Logic Error"
                            }
                            for step in correction.get("steps", [])
                        ]
                    }
                    questions.append(question)
                
                # Create StudentScore object
                student_score = StudentScore(
                    student_id=student_id,
                    # student_name=f"Student{student_id}",  # In real application, get real name from student data
                    student_name=student_name,
                    total_score=total_score,
                    max_score=max_score,
                    submit_time=datetime.now(),
                    questions=questions,
                    confidence_score=np.mean([q["confidence"] for q in questions]) if questions else 0.85
                )
                students_data.append(student_score)
            
            # Generate question analysis data
            question_analysis = []
            question_stats = {}
            
            # Statistics for each question's accuracy rate, etc.
            for correction in all_corrections:
                q_id = correction["q_id"]
                if q_id not in question_stats:
                    question_stats[q_id] = {
                        "total_score": 0,
                        "max_score": 0,
                        "count": 0,
                        "correct_count": 0
                    }
                
                question_stats[q_id]["total_score"] += correction["score"]
                question_stats[q_id]["max_score"] += correction["max_score"]
                question_stats[q_id]["count"] += 1
                if correction["score"] >= correction["max_score"] * 0.6:  # Simple correct definition
                    question_stats[q_id]["correct_count"] += 1
            
            # Create QuestionAnalysis objects
            for q_id, stats in question_stats.items():
                avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
                max_score = stats["max_score"] / stats["count"] if stats["count"] > 0 else 10
                correct_rate = stats["correct_count"] / stats["count"] if stats["count"] > 0 else 0
                difficulty = 1 - correct_rate  # Simple reverse mapping
                
                # Get question type
                # Find the question type (get the first match from statistics)
                question_type = "Other"  # Default type
                for correction in all_corrections:
                    if correction["q_id"] == q_id:
                        question_type = correction["type"]
                        if question_type in type_display_mapping1:
                            question_type = type_display_mapping1[question_type]
                        elif question_type in type_display_mapping2:
                            question_type = type_display_mapping2[question_type]
                        elif question_type not in type_display_mapping1.values():
                            # question_type = "Concept"  # Default type
                            question_type = "Other"
                        break
                
                analysis = QuestionAnalysis(
                    question_id=q_id,
                    question_type=question_type,  # Use English display type
                    topic=f"Question{q_id}",
                    difficulty=difficulty,
                    correct_rate=correct_rate,
                    avg_score=avg_score,
                    max_score=max_score,
                    common_errors=["Calculation Error", "Concept Understanding Inaccurate"][:2],
                    knowledge_points=[f"Knowledge Point{np.random.randint(1, 5)}" for _ in range(np.random.randint(1, 3))]
                )
                question_analysis.append(analysis)
            
            # Generate assignment statistics data
            total_students = len(students_data)
            submitted_count = total_students
            scores = [s.total_score for s in students_data]
            
            assignment_stats = AssignmentStats(
                assignment_id="AI_GRADING_JOB",
                assignment_name="AI Automated Grading Assignment",
                total_students=total_students,
                submitted_count=submitted_count,
                avg_score=np.mean(scores) if scores else 0,
                max_score=max(scores) if scores else 0,
                min_score=min(scores) if scores else 0,
                std_score=np.std(scores) if scores else 0,
                pass_rate=(len([s for s in students_data if s.percentage >= 60]) / total_students * 100) if total_students > 0 else 0,
                question_count=len(question_analysis),
                create_time=datetime.now()
            )
            
            return {
                "student_scores": students_data,
                "question_analysis": question_analysis,
                "assignment_stats": assignment_stats
            }
            
        elif "corrections" in result:  # Single student grading results
            # Process single student grading results
            corrections = result["corrections"]
            
            # Calculate student total score
            total_score = sum(c["score"] for c in corrections)
            max_score = sum(c["max_score"] for c in corrections)
            
            # Convert question data
            questions = []
            for correction in corrections:
                # Directly use the returned type, if it's already Chinese use directly, otherwise map
                question_type = correction["type"]
                if question_type in type_display_mapping1:
                    display_type = type_display_mapping1[question_type]
                elif question_type in type_display_mapping2:
                    display_type = type_display_mapping2[question_type]
                elif question_type in type_display_mapping1.values():
                    display_type = question_type
                else:
                    # display_type = "Concept"  # Default type
                    display_type = "Other"
                    
                
                question = {
                    "question_id": correction["q_id"],
                    "question_type": display_type,  # Use English display type
                    "score": correction["score"],
                    "max_score": correction["max_score"],
                    "confidence": correction["confidence"],
                    "feedback": correction["comment"],
                    "knowledge_points": correction.get("hits", []),
                    "step_analysis": [
                        {
                            "step_number": step["step_no"],
                            "step_title": f"Step {step['step_no']}",
                            "is_correct": step.get("is_correct", True),
                            "points_earned": step["score"],
                            "max_points": correction["max_score"] / len(correction.get("steps", [1])),
                            "feedback": step.get("desc", ""),
                            "error_type": None if step.get("is_correct", True) else "Logic Error"
                        }
                        for step in correction.get("steps", [])
                    ]
                }
                questions.append(question)
            
            # Create StudentScore object
            student_score = StudentScore(
                student_id=result.get("student_id", "unknown"),
                # student_name=f"Student{result.get('student_id', 'unknown')}",
                student_name=student_name,
                total_score=total_score,
                max_score=max_score,
                submit_time=datetime.now(),
                questions=questions,
                confidence_score=np.mean([q["confidence"] for q in questions]) if questions else 0.85
            )
            
            # Generate question analysis data (based on single student data, limited statistical significance)
            question_analysis = []
            for correction in corrections:
                # Get question type
                question_type = correction["type"]
                if question_type in type_display_mapping1:
                    display_type = type_display_mapping1[question_type]
                elif question_type in type_display_mapping2:
                    display_type = type_display_mapping2[question_type]
                elif question_type in type_display_mapping1.values():
                    display_type = question_type
                else:
                    # display_type = "Concept"  # Default type
                    display_type = "Other"
                    
                
                analysis = QuestionAnalysis(
                    question_id=correction["q_id"],
                    question_type=display_type,  # Use English display type
                    topic=f"Question{correction['q_id']}",
                    difficulty=1 - (correction["score"] / correction["max_score"]),
                    correct_rate=correction["score"] / correction["max_score"],
                    avg_score=correction["score"],
                    max_score=correction["max_score"],
                    common_errors=["Calculation Error", "Concept Understanding Inaccurate"][:2],
                    knowledge_points=correction.get("hits", [f"Knowledge Point{np.random.randint(1, 5)}"])
                )
                question_analysis.append(analysis)
            
            # Generate assignment statistics data
            assignment_stats = AssignmentStats(
                assignment_id="AI_GRADING_JOB",
                assignment_name="AI Automated Grading Assignment",
                total_students=1,
                submitted_count=1,
                avg_score=total_score,
                max_score=max_score,
                min_score=total_score,
                std_score=0,
                pass_rate=100 if (total_score / max_score) >= 0.6 else 0,
                question_count=len(corrections),
                create_time=datetime.now()
            )
            
            return {
                "student_scores": [student_score],
                "question_analysis": question_analysis,
                "assignment_stats": assignment_stats
            }
        
        # If we can't get real data, return mock data
        # st.info("This shows 【Sample Mock Task】!")
        return load_mock_data()
        
    except Exception as e:
        # If there's an error, return mock data
        st.warning(f"Failed to load AI grading data: {str(e)}, showing mock data")
        return load_mock_data()