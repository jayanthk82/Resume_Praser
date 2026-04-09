# TalentOS Deployment Guide (Streamlit Cloud + External API)

This repository has been adapted for deployment where the **FastAPI backend** and **Streamlit frontends** are separated (Option B).

Here is how to deploy it:

## 1. Deploy the Backend (FastAPI)
Streamlit Cloud does not allow raw FastAPI apps to expose port 8000. You need to deploy `main.py` to a specialized API host like **Render**, **Railway**, or **Heroku**.
1. Set the root command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
2. Once deployed, you will get an API URL (e.g., `https://talentos-api.onrender.com`).

## 2. Deploy Streamlit Cloud Frontend(s)
You have two Streamlit apps: `hr_app.py` and `candidate_app.py`.
Deploy them as two separate Streamlit Cloud projects, pointing to this exact same GitHub branch.

### HR App Deployment
- **Main file path**: `hr_app.py`
- In Streamlit Cloud, go to **Settings > Secrets** and add:
  ```toml
  TALENTOS_API_URL = "https://your-deployed-api-url.com"
  CANDIDATE_APP_URL = "https://your-candidate-app-url.streamlit.app"
  ```
  *(Note: You will generate the candidate app URL in the next step. Update this secret afterwards!)*

### Candidate App Deployment
- **Main file path**: `candidate_app.py`
- In Streamlit Cloud, go to **Settings > Secrets** and add your AI keys and the API URL:
  ```toml
  TALENTOS_API_URL = "https://your-deployed-api-url.com"
  
  MINDEE_API_KEY = "md_..."
  FIRECRAWL_API_KEY = "fc-..."
  OPENROUTER_API_KEY = "sk-or-..."
  HUGGINGFACE_API_KEY = "hf_..."
  ```

## 3. Data Note
Since you elected **no external database**, the backend writes data locally (to `/data/jobs.json` and `/data/reports.json`). Be aware that services like Render/Railway scale horizontally or restage periodically, meaning local files will eventually be wiped. This is completely okay for an ephemeral hackathon run!