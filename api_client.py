"""
TalentOS · API Client
Thin, stateless HTTP wrapper over the FastAPI backend.
Both hr_app.py and candidate_app.py import from here.

Env vars / Streamlit secrets:
  TALENTOS_API_URL — backend base URL (default: http://localhost:8000)
"""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

# ── Secret resolution helper ─────────────────────────────────
def _env(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then OS env, then default."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


_BASE    = _env("TALENTOS_API_URL", "http://localhost:8000").rstrip("/")
_TIMEOUT = 8   # seconds


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _get(path: str) -> Any:
    r = requests.get(f"{_BASE}{path}", timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path: str, payload: dict) -> Any:
    r = requests.post(f"{_BASE}{path}", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _patch(path: str, payload: dict) -> Any:
    r = requests.patch(f"{_BASE}{path}", json=payload, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _delete(path: str) -> None:
    r = requests.delete(f"{_BASE}{path}", timeout=_TIMEOUT)
    r.raise_for_status()


# ─────────────────────────────────────────────────────────────
# JOB ENDPOINTS
# ─────────────────────────────────────────────────────────────

def list_jobs() -> list[dict]:
    """Return all jobs sorted newest-first."""
    try:
        return _get("/jobs")
    except Exception:
        return []


def get_job(job_id: str) -> Optional[dict]:
    """Return a single job dict or None if not found."""
    try:
        return _get(f"/jobs/{job_id}")
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise
    except Exception:
        return None


def create_job(
    title: str,
    company: str,
    location: str,
    job_type: str,
    experience: str,
    description: str,
    required_skills: list[str],
    nice_to_have: list[str] | None = None,
    responsibilities: str = "",
) -> dict:
    """Create a new job listing. Returns the created job dict."""
    return _post("/jobs", {
        "title":            title,
        "company":          company,
        "location":         location,
        "type":             job_type,
        "experience":       experience,
        "description":      description,
        "required_skills":  required_skills,
        "nice_to_have":     nice_to_have or [],
        "responsibilities": responsibilities,
    })


def update_job_status(job_id: str, new_status: str) -> dict:
    """Set job status to live | draft | closed."""
    return _patch(f"/jobs/{job_id}/status", {"status": new_status})


def delete_job(job_id: str) -> None:
    _delete(f"/jobs/{job_id}")


# ─────────────────────────────────────────────────────────────
# REPORT ENDPOINTS
# ─────────────────────────────────────────────────────────────

def submit_report(
    job_id: str,
    candidate_name: str,
    ats_score: int,
    interview_score: int,
    skill_match_score: int,
    final_report: str,
    transcript: list[dict],
) -> dict:
    """Submit a completed candidate report. Returns the saved report dict."""
    return _post(f"/reports/{job_id}", {
        "candidate_name":    candidate_name,
        "ats_score":         ats_score,
        "interview_score":   interview_score,
        "skill_match_score": skill_match_score,
        "final_report":      final_report,
        "transcript":        transcript,
    })


def get_reports_for_job(job_id: str) -> list[dict]:
    """Return list of report dicts for a given job."""
    try:
        return _get(f"/reports/{job_id}")
    except Exception:
        return []


def get_all_reports() -> dict:
    """Return full {job_id: [reports]} map."""
    try:
        return _get("/reports")
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────

def health_check() -> bool:
    """Returns True if API is reachable."""
    try:
        _get("/health")
        return True
    except Exception:
        return False
