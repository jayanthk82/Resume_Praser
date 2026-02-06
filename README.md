
# Resume Intelligence AI: Guide

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://atsjbyjayanthkonanki.streamlit.app/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/jayanthk82/ats)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



https://github.com/user-attachments/assets/12c0f120-12ba-441b-a0a4-15985be7091a



This repository contains the Resume Intelligence AI, a sophisticated platform designed to bridge the gap between resume claims and actual technical ability. By integrating automated verification of digital footprints and AI-driven interviewing, we transform static documents into a comprehensive "Recruiter Intelligence" report.

### Core AI Solution
* **Resume Parsing**: Accurately extracting key qualifications using NLP.
* **URL Discovery & Web Crawling**: Identifying relevant online portfolios and gathering real-time data from public sources.
* **Code Insight Extraction**: Leveraging AI to analyze repositories for tech stacks and contribution complexity.
* **AI Interviewing**: Contextual assessments designed to reflect true candidate abilities.

## 🚀 Overview

The application operates in two primary modes:

1. **Resume Analyzer**: Uses Mindee for OCR, PyMuPDF for link extraction, and Firecrawl for web scraping to build a rich user profile via OpenRouter LLMs.
2. **ATS Scorer**: Uses `sentence-transformers` to calculate a semantic match percentage between your profile and a job description.

---

## 🛠️ Setup Instructions

### 1. Prerequisites

Ensure you have Python 3.11+ installed. You will also need API keys for the following services:

* **Mindee**: For resume parsing.
* **Firecrawl**: For scraping external links (GitHub, LinkedIn, Portfolio).
* **OpenRouter**: To access AI models (e.g., `arcee-ai/trinity-large-preview`).

### 2. Installation

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt

```

### 3. Configuration

Create a `.streamlit/secrets.toml` file or set environment variables for the following keys:

```toml
MINDEE_API_KEY = "your_mindee_key"
FIRECRAWL_API_KEY = "your_firecrawl_key"
OPENROUTER_API_KEY = "your_openrouter_key"

```

---

## 🧪 How to Test

### Option A: Local Streamlit UI (Recommended)

Run the interactive dashboard to test the full workflow visually:

```bash
streamlit run app_ui.py

```

1. **Tab 1 (Analyzer)**: Upload a PDF resume. The system will parse text, find links, scrape their content, and generate a recruiter-ready profile.
2. **Tab 2 (Scorer)**: Paste the generated profile and a target Job Description. The system will generate a match score and a gauge chart.

### Option B: Local API (FastAPI)

You can also run the backend as a standalone service:

```bash
uvicorn main:app --reload

```

* **Health Check**: `GET /`
* **Process Resume**: `POST /process_resume` with a JSON body `{"pdf_path": "path/to/resume.pdf"}`.
* **Score Resume**: `POST /score_resume` with `{"user_summary": "...", "jd_summary": "..."}`.

---

## 📂 Project Structure

* `app_ui.py`: Streamlit frontend implementation.
* `main.py`: FastAPI orchestrator for the backend.
* `mindee_service.py`: Logic for extracting structured data from PDFs.
* `pdf_service.py`: Extracts HTTP/HTTPS links from resume files.
* `firecrawl_service.py`: Scrapes content from portfolio or social links.
* `transformer_service.py`: Computes semantic similarity scores.
* `openrouter_service.py`: Manages multi-turn AI reasoning for profile generation.

## 🌐 Live Version

Test the deployed application here: [Resume Intelligence AI](https://atsjbyjayanthkonanki.streamlit.app/)



