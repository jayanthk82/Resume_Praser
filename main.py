"""
TalentOS · FastAPI Backend
Decoupled data layer between HR portal and Candidate assessment.

Storage: Local JSON files under ./data/
  jobs.json    — job listings keyed by job_id
  reports.json — candidate reports keyed by job_id → list[Report]
"""

from __future__ import annotations

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# APP BOOTSTRAP
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="TalentOS API",
    description="Decoupled data layer for TalentOS HR & Candidate flows.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# LOCAL FILE STORE
# ─────────────────────────────────────────────────────────────
_BASE_DIR     = Path(__file__).parent / "data"
_JOBS_FILE    = _BASE_DIR / "jobs.json"
_REPORTS_FILE = _BASE_DIR / "reports.json"


def _ensure_data_dir() -> None:
    _BASE_DIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path) -> dict:
    _ensure_data_dir()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save(path: Path, data: dict) -> None:
    _ensure_data_dir()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title:       str
    company:     str
    location:    str = "Remote"
    type:        str = "Full-time"
    experience:  str = "3-5 Years"
    description: str = ""
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have:    List[str] = Field(default_factory=list)
    responsibilities: str = ""


class JobOut(JobCreate):
    id:          str
    status:      str
    created_at:  str
    candidates:  int = 0


class ReportCreate(BaseModel):
    candidate_name:    str
    ats_score:         int = Field(ge=0, le=100)
    interview_score:   int = Field(ge=0, le=100)
    skill_match_score: int = Field(ge=0, le=100)
    final_report:      str = ""
    transcript:        List[dict] = Field(default_factory=list)


class ReportOut(ReportCreate):
    id:             str
    job_id:         str
    recommendation: str
    submitted_at:   str


class JobStatusUpdate(BaseModel):
    status: str


# ─────────────────────────────────────────────────────────────
# RECOMMENDATION HELPER
# ─────────────────────────────────────────────────────────────

def _derive_recommendation(ats: int, interview: int, skill: int) -> str:
    avg = (ats + interview + skill) / 3
    if avg >= 78:
        return "Proceed"
    if avg >= 58:
        return "Hold"
    return "Reject"


# ─────────────────────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────────────────────

_SEED_JOBS: dict = {
    "DEMO-001": {
        "id": "DEMO-001",
        "title": "Senior Full-Stack Engineer",
        "company": "Anthropic",
        "location": "Remote · Global",
        "type": "Full-time",
        "experience": "5+ Years",
        "description": (
            "We are looking for a Senior Full-Stack Engineer to join our "
            "AI Products team. You will design and build production-grade "
            "web applications that serve researchers, enterprises, and millions "
            "of end-users interacting with Claude.\n\n"
            "You will work across the entire stack — from crafting pixel-perfect "
            "React interfaces to architecting resilient Python/FastAPI backends "
            "and managing cloud infrastructure on AWS."
        ),
        "required_skills": [
            "React / Next.js", "TypeScript", "Python", "FastAPI",
            "PostgreSQL", "Redis", "AWS (EC2, S3, Lambda)",
            "Docker / Kubernetes", "REST & GraphQL APIs", "CI/CD Pipelines",
            "System Design",
        ],
        "nice_to_have": ["LLM integrations", "Streamlit", "Vector DBs", "Terraform"],
        "responsibilities": (
            "• Architect and ship full-stack features end-to-end\n"
            "• Define and enforce frontend/backend coding standards\n"
            "• Optimise application performance and scalability\n"
            "• Collaborate with design on UI/UX implementation\n"
            "• Own production monitoring, alerting, and incident response\n"
            "• Mentor junior engineers and conduct technical interviews"
        ),
        "status": "live",
        "created_at": "2025-03-01",
        "candidates": 3,
    },
    "DEMO-002": {
        "id": "DEMO-002",
        "title": "ML Engineer — Alignment",
        "company": "Anthropic",
        "location": "San Francisco · Hybrid",
        "type": "Full-time",
        "experience": "3+ Years",
        "description": "Work on frontier model alignment and RLHF pipelines.",
        "required_skills": ["Python", "PyTorch", "RLHF", "LLMs", "JAX"],
        "nice_to_have": ["Transformers", "CUDA", "Distributed Training"],
        "responsibilities": (
            "• Research and implement RLHF pipelines\n"
            "• Evaluate model behaviour across safety benchmarks\n"
            "• Collaborate closely with the safety and policy teams"
        ),
        "status": "live",
        "created_at": "2025-03-05",
        "candidates": 1,
    },
}

_SEED_REPORTS: dict = {
    "DEMO-001": [
        {
            "id": str(uuid.uuid4()),
            "job_id": "DEMO-001",
            "candidate_name": "Alice Zhang",
            "ats_score": 91,
            "interview_score": 88,
            "skill_match_score": 93,
            "recommendation": "Proceed",
            "final_report": "## Executive Summary\nAlice is an exceptional candidate…",
            "transcript": [],
            "submitted_at": "2025-03-10 14:22",
        },
        {
            "id": str(uuid.uuid4()),
            "job_id": "DEMO-001",
            "candidate_name": "Bob Müller",
            "ats_score": 74,
            "interview_score": 69,
            "skill_match_score": 72,
            "recommendation": "Hold",
            "final_report": "## Executive Summary\nBob shows solid fundamentals…",
            "transcript": [],
            "submitted_at": "2025-03-11 09:47",
        },
    ],
    "DEMO-002": [
        {
            "id": str(uuid.uuid4()),
            "job_id": "DEMO-002",
            "candidate_name": "Carlos Santos",
            "ats_score": 85,
            "interview_score": 80,
            "skill_match_score": 87,
            "recommendation": "Proceed",
            "final_report": "## Executive Summary\nCarlos has strong RLHF expertise…",
            "transcript": [],
            "submitted_at": "2025-03-08 11:30",
        },
    ],
}


def _seed_if_empty() -> None:
    jobs = _load(_JOBS_FILE)
    if not jobs:
        _save(_JOBS_FILE, _SEED_JOBS)
    reports = _load(_REPORTS_FILE)
    if not reports:
        _save(_REPORTS_FILE, _SEED_REPORTS)


# ─────────────────────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    _seed_if_empty()


# ─────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "TalentOS API", "version": "1.0.0"}


# ─────────────────────────────────────────────────────────────
# JOBS — CRUD
# ─────────────────────────────────────────────────────────────

@app.get("/jobs", response_model=List[JobOut], tags=["jobs"])
def list_jobs():
    jobs = _load(_JOBS_FILE)
    return sorted(jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)


@app.get("/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
def get_job(job_id: str):
    jobs = _load(_JOBS_FILE)
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return jobs[job_id]


@app.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED, tags=["jobs"])
def create_job(payload: JobCreate):
    jobs   = _load(_JOBS_FILE)
    job_id = f"JOB-{uuid.uuid4().hex[:6].upper()}"
    now    = datetime.now().strftime("%Y-%m-%d")
    job_record = {
        **payload.model_dump(),
        "id":         job_id,
        "status":     "live",
        "created_at": now,
        "candidates": 0,
    }
    jobs[job_id] = job_record
    _save(_JOBS_FILE, jobs)
    return job_record


@app.patch("/jobs/{job_id}/status", response_model=JobOut, tags=["jobs"])
def update_job_status(job_id: str, payload: JobStatusUpdate):
    jobs = _load(_JOBS_FILE)
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if payload.status not in ("live", "draft", "closed"):
        raise HTTPException(status_code=422, detail="status must be live | draft | closed")
    jobs[job_id]["status"] = payload.status
    _save(_JOBS_FILE, jobs)
    return jobs[job_id]


@app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["jobs"])
def delete_job(job_id: str):
    jobs = _load(_JOBS_FILE)
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    del jobs[job_id]
    _save(_JOBS_FILE, jobs)


# ─────────────────────────────────────────────────────────────
# REPORTS — SUBMIT & FETCH
# ─────────────────────────────────────────────────────────────

@app.post(
    "/reports/{job_id}",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
    tags=["reports"],
)
def submit_report(job_id: str, payload: ReportCreate):
    jobs = _load(_JOBS_FILE)
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    reports   = _load(_REPORTS_FILE)
    report_id = str(uuid.uuid4())
    now       = datetime.now().strftime("%Y-%m-%d %H:%M")

    rec = ReportOut(
        **payload.model_dump(),
        id=report_id,
        job_id=job_id,
        recommendation=_derive_recommendation(
            payload.ats_score, payload.interview_score, payload.skill_match_score
        ),
        submitted_at=now,
    )

    if job_id not in reports:
        reports[job_id] = []
    reports[job_id].append(rec.model_dump())
    _save(_REPORTS_FILE, reports)

    jobs[job_id]["candidates"] = jobs[job_id].get("candidates", 0) + 1
    _save(_JOBS_FILE, jobs)

    return rec


@app.get("/reports", response_model=dict, tags=["reports"])
def list_all_reports():
    return _load(_REPORTS_FILE)


@app.get("/reports/{job_id}", response_model=List[ReportOut], tags=["reports"])
def get_reports_for_job(job_id: str):
    jobs = _load(_JOBS_FILE)
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    reports = _load(_REPORTS_FILE)
    return reports.get(job_id, [])
