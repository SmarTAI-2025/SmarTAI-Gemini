# SmarTAI

**SmarTAI** is an intelligent assignment assessment platform tailored for higher education science and engineering courses. Powered by Gemini-3-flash, it automates the grading of complex question types—including computational problems, mathematical proofs, and programming tasks. The system integrates RAG-based knowledge retrieval and interactive data visualization  to provide precise feedback and deep insights into student performance.

## Environment Setup

```bash
pip install -r requirements.txt
```

## Running Tests

`cd /path/to/project-root`

**1. Start the Backend Service**

Run the following command first:

`python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`

> **Note:**
> * The `--reload` flag enables hot reloading for easier development and debugging.
> * `python -m` can optionally be omitted.
> 
> 

> **(Optional) Test the backend in a new terminal:**
> ```bash
> curl -X POST "http://localhost:8000/file_preview" \
>      -F "file=@hw.zip"
> ```
> 

**2. Start the Frontend Application**

Run the following command in a new terminal:

`streamlit run frontend/app.py --client.showSidebarNavigation=False`

> **Note:**
> * `--client.showSidebarNavigation=False`: Hides the default Streamlit file directory sidebar.
> * Ports are assigned randomly; the access URL will be displayed in the console after startup.
> * `--server.headless true`: Prevents the browser from opening automatically (useful for headless environments like containers or remote servers). You can omit this parameter during local development to automatically open the browser.
> 

## Integrated Startup (Recommended for Development)

`streamlit run app.py`

This script automatically launches both the backend and frontend services, handling port allocation and environment variable configuration for you.

## AI Auto-Grading Feature

This project now includes an AI-powered auto-grading feature that supports the following question types:

* Calculation Problems
* Conceptual Questions
* Proofs
* Programming/Coding Problems

### Feature Workflow

1. **Upload:** After students upload their assignments, the system automatically identifies the questions and answers.
2. **Execution:** Click the "Start AI Grading" button to generate grading tasks for each student.
3. **Review:** Grading results will be displayed on the "Grading Results" page.

### API Endpoints

* `POST /ai_grading_new/grade_student/` - Initiate a grading task for a student.
* `GET /ai_grading_new/grade_result/{job_id}` - Retrieve grading results.

## Deployment Guide

For detailed deployment instructions, please refer to [DEPLOYMENT.md](https://www.google.com/search?q=DEPLOYMENT.md). The guide includes:

1. **Managed Platform Deployment** (Recommended):
* **Frontend:** Deploy to Streamlit Community Cloud.
* **Backend:** Deploy to Render (Configuration file located at `backend/render.yaml`).


2. **Containerized Deployment**:
* Uses Docker and Docker Compose.
* Suitable for production environments requiring granular control.


3. **Environment Configuration**:
* `BACKEND_URL`: The URL used by the frontend to connect to the backend.
* `FRONTEND_URLS`: The frontend origins allowed by the backend (CORS configuration).
