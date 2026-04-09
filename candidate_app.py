"""
TalentOS · Candidate Assessment Flow
5-Step Pipeline: JD Preview → Resume Upload → Technical Interview → Report → Completion

Changes from standalone version:
  - job_id read from ?job_id=... URL query param
  - fetch_job_data() calls FastAPI GET /jobs/{job_id}
  - Submit Report button calls FastAPI POST /reports/{job_id}
  - All CSS/theme tokens preserved verbatim from talentos_theme.py

Port: 8502 (default)
"""

import streamlit as st
import os, io, json, time, base64, tempfile, requests as _requests
import sys
import importlib.util
import plotly.graph_objects as go
from dotenv import load_dotenv
from gtts import gTTS

# ── Load api_client ────────────────────────────────────────────────────────────
import api_client
get_job       = api_client.get_job
submit_report = api_client.submit_report

# ── Optional imports (graceful fallback) ─────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

try:
    from mindee import ClientV2
    HAS_MINDEE = True
except ImportError:
    HAS_MINDEE = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from firecrawl_service import FirecrawlService
    HAS_FIRECRAWL = True
except ImportError:
    HAS_FIRECRAWL = False

try:
    from pdf_service import extract_hyperlinks
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from config import Config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

try:
    from openrouter_service import chat_with_reasoning_followup
    HAS_OR = True
except ImportError:
    HAS_OR = False

try:
    from transformer_service import calculate_match_score
    HAS_TRANSFORMER = True
except ImportError:
    HAS_TRANSFORMER = False

load_dotenv()

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentOS · Candidate Assessment",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM — FULL CSS (matches talentos_theme.py tokens)
# ─────────────────────────────────────────────────────────────
DESIGN_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════
   ROOT DESIGN TOKENS (identical to talentos_theme.py)
   ═══════════════════════════════════════════ */
:root {
  --bg-base:        #03050D;
  --bg-surface:     #070A17;
  --bg-card:        rgba(255,255,255,0.028);
  --bg-card-hover:  rgba(255,255,255,0.052);
  --border:         rgba(255,255,255,0.07);
  --border-active:  rgba(0,163,255,0.5);
  --border-glow:    rgba(0,229,196,0.3);

  --blue:   #00A3FF;
  --cyan:   #00E5C4;
  --gold:   #F5C842;
  --red:    #FF4D6A;
  --violet: #7B61FF;

  --t1: #EDF0FA;
  --t2: #8B93B0;
  --t3: #4E566E;
  --t4: #2A3050;

  --f-main:  'Sora', sans-serif;
  --f-mono:  'JetBrains Mono', monospace;
  --f-serif: 'Instrument Serif', serif;

  --r-sm: 10px;
  --r-md: 16px;
  --r-lg: 24px;
  --r-xl: 32px;

  --shadow-card: 0 8px 48px rgba(0,0,0,0.6);
  --shadow-glow: 0 0 80px rgba(0,163,255,0.10);
  --shadow-cyan: 0 0 80px rgba(0,229,196,0.10);
  --ease:   cubic-bezier(0.4, 0, 0.2, 1);
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --t: 0.28s;
}

/* ═══════════════════════════════════════════
   GLOBAL RESETS
   ═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background-color: var(--bg-base) !important;
  font-family: var(--f-main) !important;
  color: var(--t1) !important;
}

[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] + div {
  background: transparent !important;
}

/* ═══════════════════════════════════════════
   AMBIENT BACKGROUND MESH
   ═══════════════════════════════════════════ */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 90% 70% at 5%   0%,  rgba(0,163,255,0.075) 0%, transparent 55%),
    radial-gradient(ellipse 60% 55% at 95%  95%, rgba(0,229,196,0.065) 0%, transparent 50%),
    radial-gradient(ellipse 50% 45% at 50%  50%, rgba(123,97,255,0.04)  0%, transparent 65%),
    radial-gradient(ellipse 40% 35% at 80%  10%, rgba(245,200,66,0.03)  0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: ambientShift 18s ease-in-out infinite alternate;
}
@keyframes ambientShift {
  0%   { opacity:1; transform:scale(1) translateY(0px); }
  100% { opacity:0.75; transform:scale(1.04) translateY(-12px); }
}
[data-testid="stAppViewContainer"]::after {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0; opacity: 0.6;
}

/* ═══════════════════════════════════════════
   HIDE STREAMLIT CHROME
   ═══════════════════════════════════════════ */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stSidebar"] { display: none !important; }

/* ═══════════════════════════════════════════
   LAYOUT WRAPPER
   ═══════════════════════════════════════════ */
.main-container {
  max-width: 1060px;
  margin: 0 auto;
  padding: 0 28px 80px;
  position: relative;
  z-index: 1;
}

/* ═══════════════════════════════════════════
   FIXED TOP NAV BAR
   ═══════════════════════════════════════════ */
.topnav-fixed {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(3,5,13,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 14px 28px;
  margin: 0 -28px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  animation: fadeDown 0.5s var(--ease) both;
}
.nav-brand { display: flex; align-items: center; gap: 12px; }
.nav-hex {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, var(--blue), var(--cyan));
  clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff;
  animation: hexPulse 4s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes hexPulse {
  0%,100% { box-shadow: 0 0 20px rgba(0,163,255,0.35); }
  50%      { box-shadow: 0 0 44px rgba(0,229,196,0.5);  }
}
.nav-title {
  font-size: 1.1rem; font-weight: 800; letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--t1) 40%, var(--blue));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.nav-sub {
  font-size: 0.58rem; font-family: var(--f-mono);
  color: var(--t3); letter-spacing: 0.2em;
  text-transform: uppercase; margin-top: 2px;
}

/* ═══════════════════════════════════════════
   STEP PROGRESS BAR (5 steps)
   ═══════════════════════════════════════════ */
.stepper {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 5px 7px;
  gap: 0;
}
.step-item {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 14px; border-radius: 999px;
  font-family: var(--f-mono); font-size: 0.65rem;
  font-weight: 500; letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: all var(--t) var(--ease);
  white-space: nowrap; color: var(--t3);
  position: relative; z-index: 2;
}
.step-item.active {
  background: linear-gradient(135deg, rgba(0,163,255,0.18), rgba(0,229,196,0.1));
  border: 1px solid rgba(0,163,255,0.35);
  color: var(--blue);
  box-shadow: 0 0 24px rgba(0,163,255,0.12);
}
.step-item.done { color: var(--cyan); }
.step-num {
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  flex-shrink: 0; position: relative; z-index: 3;
}
.step-item.active .step-num {
  background: var(--blue); border-color: var(--blue); color: #fff;
  box-shadow: 0 0 10px rgba(0,163,255,0.45);
}
.step-item.done .step-num {
  background: rgba(0,229,196,0.15);
  border-color: rgba(0,229,196,0.4); color: var(--cyan);
}
.step-connector {
  flex-shrink: 0; width: 20px; height: 2px;
  background: var(--border); border-radius: 999px;
  position: relative; z-index: 1; margin: 0 2px;
}
.step-connector.done { background: rgba(0,229,196,0.35); }

/* ═══ SECTION HEADER ════════════════════════════════════════ */
.sec-block { margin-bottom: 28px; animation: fadeUp 0.5s var(--ease) both; }
.sec-tag { font-family: var(--f-mono); font-size: 0.63rem; color: var(--blue); letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 8px; }
.sec-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.04em; color: var(--t1); line-height: 1.1; margin-bottom: 6px; }
.sec-desc { font-size: 0.88rem; color: var(--t2); line-height: 1.6; }

/* ═══ GLASS CARD ════════════════════════════════════════════ */
.g-card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--r-lg); padding: 28px 32px;
  backdrop-filter: blur(20px); box-shadow: var(--shadow-card);
  transition: border-color var(--t) var(--ease), box-shadow var(--t) var(--ease);
  animation: fadeUp 0.55s var(--ease) 0.1s both;
}
.g-card:hover {
  border-color: rgba(0,163,255,0.22);
  box-shadow: var(--shadow-card), var(--shadow-glow);
}

/* ═══ JD HEADER ═════════════════════════════════════════════ */
.jd-header {
  background: linear-gradient(135deg, rgba(0,163,255,0.08) 0%, rgba(123,97,255,0.05) 100%);
  border: 1px solid rgba(0,163,255,0.22);
  border-radius: var(--r-lg); padding: 28px 32px;
  margin-bottom: 20px; animation: fadeUp 0.5s var(--ease) both;
  position: relative; overflow: hidden;
}
.jd-header::before {
  content: ''; position: absolute; top:0; left:0; right:0; height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--cyan), var(--violet));
}
.jd-company-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(0,163,255,0.1); border: 1px solid rgba(0,163,255,0.25);
  border-radius: 999px; padding: 5px 14px;
  font-family: var(--f-mono); font-size: 0.65rem;
  color: var(--blue); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 14px;
}
.jd-title { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.04em; color: var(--t1); margin-bottom: 8px; line-height: 1.15; }
.jd-meta { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 14px; }
.jd-meta-item { display: inline-flex; align-items: center; gap: 7px; font-family: var(--f-mono); font-size: 0.68rem; color: var(--t3); letter-spacing: 0.08em; }
.jd-meta-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--blue); opacity: 0.7; }

/* ═══ JD BODY ═══════════════════════════════════════════════ */
.jd-body { display: grid; grid-template-columns: 1fr 340px; gap: 20px; animation: fadeUp 0.55s var(--ease) 0.15s both; }
.jd-left { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 28px 30px; }
.jd-right { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 28px 24px; }
.jd-col-title { font-family: var(--f-mono); font-size: 0.63rem; color: var(--blue); letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.jd-col-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); }
.jd-body-text { font-size: 0.88rem; color: var(--t2); line-height: 1.85; letter-spacing: 0.01em; }
.skill-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.skill-pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 13px; background: rgba(0,163,255,0.06); border: 1px solid rgba(0,163,255,0.2); border-radius: 999px; font-family: var(--f-mono); font-size: 0.65rem; color: var(--blue); letter-spacing: 0.08em; transition: all 0.2s var(--ease); }
.skill-pill:hover { background: rgba(0,163,255,0.12); border-color: rgba(0,163,255,0.4); transform: translateY(-1px); }
.skill-pill.primary { background: rgba(0,229,196,0.06); border-color: rgba(0,229,196,0.22); color: var(--cyan); }

/* ═══ UPLOAD ZONE ═══════════════════════════════════════════ */
.upload-zone { border: 1.5px dashed rgba(0,163,255,0.28); border-radius: var(--r-md); padding: 44px 32px; text-align: center; background: rgba(0,163,255,0.025); transition: all var(--t) var(--ease); cursor: pointer; }
.upload-zone:hover { border-color: rgba(0,163,255,0.55); background: rgba(0,163,255,0.055); transform: scale(1.005); }
.upload-icon { font-size: 2.6rem; display: block; margin-bottom: 14px; animation: floatIcon 3s ease-in-out infinite; }
@keyframes floatIcon { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
.upload-title { font-size: 1.0rem; font-weight: 600; color: var(--t1); margin-bottom: 6px; }
.upload-hint { font-size: 0.74rem; font-family: var(--f-mono); color: var(--t3); letter-spacing: 0.06em; }

/* ═══ PROCESSING MODAL ══════════════════════════════════════ */
.processing-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(3,5,13,0.82); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); display: flex; align-items: center; justify-content: center; animation: fadeIn 0.35s var(--ease) both; }
.processing-modal { background: rgba(7,10,23,0.95); border: 1px solid rgba(0,163,255,0.28); border-radius: var(--r-xl); padding: 48px 52px; text-align: center; max-width: 440px; width: 100%; box-shadow: 0 32px 80px rgba(0,0,0,0.7), 0 0 80px rgba(0,163,255,0.08); animation: scaleIn 0.4s var(--spring) both; }
.proc-hex-ring { width: 80px; height: 80px; margin: 0 auto 24px; }
.proc-hex { width: 80px; height: 80px; background: linear-gradient(135deg, rgba(0,163,255,0.2), rgba(0,229,196,0.15)); clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%); display: flex; align-items: center; justify-content: center; font-size: 2rem; animation: hexSpin 3s linear infinite; }
@keyframes hexSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.proc-title { font-size: 1.2rem; font-weight: 700; color: var(--t1); margin-bottom: 10px; }
.proc-step { font-family: var(--f-mono); font-size: 0.72rem; color: var(--blue); letter-spacing: 0.1em; margin-bottom: 24px; }
.proc-bar { height: 4px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden; }
.proc-bar-fill { height: 100%; background: linear-gradient(90deg, var(--blue), var(--cyan)); border-radius: 999px; animation: procFill 2.4s ease-in-out infinite; }
@keyframes procFill { 0% { width: 8%; } 60% { width: 82%; } 100% { width: 8%; } }

/* ═══ INTERVIEW LAYOUT ══════════════════════════════════════ */
.interview-grid { display: grid; grid-template-columns: minmax(0, 4fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.q-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); overflow: hidden; }
.q-panel-header { padding: 20px 28px; background: linear-gradient(135deg, rgba(0,163,255,0.06), rgba(0,229,196,0.03)); border-bottom: 1px solid var(--border); position: relative; }
.q-panel-header::before { content: ''; position: absolute; top:0; left:0; right:0; height: 3px; background: linear-gradient(90deg, var(--blue), var(--cyan), var(--violet)); }
.q-panel-body { padding: 28px; }
.q-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 26px 28px; margin-bottom: 18px; animation: fadeUp 0.45s var(--ease) both; }
.q-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(0,163,255,0.1); border: 1px solid rgba(0,163,255,0.3); border-radius: 999px; padding: 5px 14px; font-family: var(--f-mono); font-size: 0.66rem; color: var(--blue); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 14px; }
.q-text { font-size: 1.15rem; font-weight: 600; color: var(--t1); line-height: 1.7; letter-spacing: -0.01em; }
.play-btn-wrap { margin-top: 20px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.play-note { font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); letter-spacing: 0.08em; }
.mic-label { font-family: var(--f-mono); font-size: 0.64rem; color: var(--t3); letter-spacing: 0.16em; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
.answer-label { font-family: var(--f-mono); font-size: 0.62rem; color: var(--cyan); letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 8px; }
.mic-label::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); min-width: 80px; }
.cam-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); overflow: hidden; position: sticky; top: 80px; }
.cam-header { padding: 13px 16px; border-bottom: 1px solid var(--border); font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); letter-spacing: 0.14em; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
.cam-dot-live { width: 6px; height: 6px; border-radius: 50%; background: var(--red); animation: dotPulse 1.4s ease infinite; }

/* ═══ REPORT PAGE ════════════════════════════════════════════ */
.candidate-summary-card { background: linear-gradient(160deg, rgba(0,163,255,0.07), rgba(0,229,196,0.04)); border: 1px solid rgba(0,163,255,0.2); border-radius: var(--r-lg); padding: 28px 24px; position: sticky; top: 80px; }
.avatar-ring { width: 72px; height: 72px; margin: 0 auto 18px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: linear-gradient(135deg, rgba(0,163,255,0.15), rgba(0,229,196,0.1)); border: 2px solid rgba(0,163,255,0.3); font-size: 2.2rem; }
.cand-name { font-size: 1.1rem; font-weight: 700; color: var(--t1); text-align: center; margin-bottom: 4px; }
.cand-role { font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); text-align: center; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 16px; }
.score-divider { height: 1px; background: var(--border); margin: 16px 0; }
.score-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.score-lbl { font-family: var(--f-mono); font-size: 0.63rem; color: var(--t3); letter-spacing: 0.1em; }
.score-val { font-family: var(--f-mono); font-size: 0.8rem; font-weight: 700; }
.score-bar-track { height: 5px; background: rgba(255,255,255,0.05); border-radius: 999px; overflow: hidden; margin-bottom: 14px; }
.score-bar-fill { height: 100%; border-radius: 999px; }
.report-body-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 30px 34px; animation: fadeUp 0.5s var(--ease) both; }
.report-text { font-size: 0.88rem; color: var(--t2); line-height: 1.85; }
.report-text h2 { font-size: 0.75rem; font-family: var(--f-mono); color: var(--blue); letter-spacing: 0.18em; text-transform: uppercase; margin: 20px 0 8px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }

/* ═══ COMPLETION OVERLAY ════════════════════════════════════ */
.completion-overlay { display: flex; align-items: center; justify-content: center; padding: 40px 20px; }
.completion-card { background: rgba(7,10,23,0.96); border: 1px solid rgba(0,229,196,0.28); border-radius: var(--r-xl); padding: 52px 60px; max-width: 560px; width: 100%; text-align: center; box-shadow: 0 32px 80px rgba(0,0,0,0.7), 0 0 80px rgba(0,229,196,0.08); animation: scaleIn 0.5s var(--spring) both; position: relative; overflow: hidden; }
.completion-card::before { content: ''; position: absolute; top:0; left:0; right:0; height: 3px; background: linear-gradient(90deg, var(--cyan), var(--blue), var(--violet)); }
.completion-icon { font-size: 3.5rem; display: block; margin-bottom: 20px; animation: floatIcon 3s ease-in-out infinite; }
.completion-title { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.04em; color: var(--t1); margin-bottom: 14px; }
.completion-sub { font-size: 0.88rem; color: var(--t2); line-height: 1.75; margin-bottom: 28px; }
.completion-badge { display: inline-flex; align-items: center; gap: 10px; background: rgba(0,229,196,0.08); border: 1px solid rgba(0,229,196,0.28); border-radius: 999px; padding: 8px 20px; font-family: var(--f-mono); font-size: 0.7rem; color: var(--cyan); letter-spacing: 0.12em; }
.comp-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); animation: dotPulse 2s ease infinite; }

/* ═══ INPUTS ════════════════════════════════════════════════ */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.028) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important; color: var(--t1) !important;
  font-family: var(--f-main) !important; font-size: 0.88rem !important;
  padding: 11px 15px !important; transition: all var(--t) var(--ease) !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus { border-color: rgba(0,163,255,0.5) !important; box-shadow: 0 0 0 4px rgba(0,163,255,0.09) !important; }
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder { color: var(--t3) !important; }

/* ═══ BUTTONS ═══════════════════════════════════════════════ */
[data-testid="stButton"] > button {
  font-family: var(--f-main) !important; font-weight: 700 !important;
  font-size: 0.82rem !important; letter-spacing: 0.06em !important;
  text-transform: uppercase !important; border-radius: var(--r-sm) !important;
  transition: all 0.24s var(--spring) !important;
}
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #0070D8, var(--blue), #00C8FF) !important;
  background-size: 200% 200% !important; border: none !important; color: #fff !important;
  box-shadow: 0 4px 24px rgba(0,163,255,0.4) !important; padding: 12px 24px !important;
  animation: btnShimmer 4s ease infinite !important;
}
@keyframes btnShimmer { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
[data-testid="stButton"] > button[kind="primary"]:hover { box-shadow: 0 6px 36px rgba(0,163,255,0.6) !important; transform: translateY(-2px) scale(1.01) !important; }
[data-testid="stButton"] > button:not([kind="primary"]) { background: rgba(255,255,255,0.04) !important; border: 1px solid var(--border) !important; color: var(--t2) !important; }
[data-testid="stButton"] > button:not([kind="primary"]):hover { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.16) !important; color: var(--t1) !important; transform: translateY(-1px) !important; }

[data-testid="stDownloadButton"] > button {
  background: linear-gradient(135deg, rgba(245,200,66,0.12), rgba(245,200,66,0.06)) !important;
  border: 1px solid rgba(245,200,66,0.32) !important; color: var(--gold) !important;
  font-family: var(--f-main) !important; font-weight: 700 !important;
  font-size: 0.78rem !important; letter-spacing: 0.06em !important;
  text-transform: uppercase !important; border-radius: var(--r-sm) !important;
  padding: 11px 18px !important; transition: all 0.22s var(--ease) !important;
}
[data-testid="stDownloadButton"] > button:hover { background: linear-gradient(135deg, rgba(245,200,66,0.22), rgba(245,200,66,0.12)) !important; box-shadow: 0 4px 24px rgba(245,200,66,0.2) !important; transform: translateY(-1px) !important; }

[data-testid="stExpander"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; }
[data-testid="stExpander"] summary { font-family: var(--f-main) !important; font-size: 0.8rem !important; font-weight: 500 !important; color: var(--t2) !important; }
[data-testid="stExpander"] summary:hover { color: var(--t1) !important; }

[data-testid="stWidgetLabel"] p, label { font-family: var(--f-main) !important; font-size: 0.76rem !important; font-weight: 500 !important; color: var(--t2) !important; letter-spacing: 0.04em !important; text-transform: uppercase !important; }
[data-testid="stAlert"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; font-family: var(--f-main) !important; }
div[data-testid="stAlert"][kind="info"]    { border-left: 3px solid var(--blue) !important; }
div[data-testid="stAlert"][kind="success"] { border-left: 3px solid var(--cyan) !important; }
div[data-testid="stAlert"][kind="warning"] { border-left: 3px solid var(--gold) !important; }

/* ═══ MISC ═══════════════════════════════════════════════════ */
.field-label { font-family: var(--f-mono); font-size: 0.65rem; color: var(--t3); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 7px; }
.field-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--blue); }
.divider-label { display: flex; align-items: center; gap: 14px; margin: 28px 0 20px; font-family: var(--f-mono); font-size: 0.63rem; color: var(--t3); letter-spacing: 0.16em; text-transform: uppercase; }
.divider-label::before { content:''; flex:1; height:1px; background: linear-gradient(90deg,transparent,var(--border)); }
.divider-label::after  { content:''; flex:1; height:1px; background: linear-gradient(270deg,transparent,var(--border)); }
.spacer-xs { height: 8px; }
.spacer-sm { height: 14px; }
.spacer-md { height: 24px; }
.spacer-lg { height: 40px; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

@keyframes fadeUp   { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeDown { from { opacity:0; transform:translateY(-16px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeIn   { from { opacity:0; } to { opacity:1; } }
@keyframes scaleIn  { from { opacity:0; transform:scale(0.92); } to { opacity:1; transform:scale(1); } }
@keyframes dotPulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(0.7); } }
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# CONSTANTS & CONFIG
# ─────────────────────────────────────────────────────────────
HF_API_KEY   = os.getenv("HUGGINGFACE_API_KEY", "")
WHISPER_URL  = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3"
MODEL        = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
NUM_QUESTIONS = 4
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
FIRECRAWL_API_KEY  = os.getenv("FIRECRAWL_API_KEY", "")


# ─────────────────────────────────────────────────────────────
# RESOURCE CACHING
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_ats_model():
    if HAS_ST:
        return SentenceTransformer("all-MiniLM-L6-v2")
    return None


@st.cache_resource
def get_llm():
    if HAS_OPENAI and OPENROUTER_API_KEY:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    return None


ats_model = load_ats_model()
llm       = get_llm()


# ─────────────────────────────────────────────────────────────
# URL QUERY PARAMS — read job_id from ?job_id=...
# ─────────────────────────────────────────────────────────────
_params    = st.query_params
_url_job_id = _params.get("job_id", "DEMO-001")


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
DEFAULTS: dict = {
    "page":                 "jd",
    "job_id":               _url_job_id,
    "job_data":             None,
    "resume_file":          None,
    "resume_links":         [],
    "crawled_data":         "",
    "profile_text":         "",
    "ats_score":            0,
    "interview_questions":  [],
    "current_q_index":      0,
    "audio_played":         False,
    "interview_answers":    [],
    "interview_score":      0,
    "skill_match_score":    0,
    "final_report":         "",
    "candidate_name":       "Candidate",
    "report_submitted":     False,
    "submit_error":         "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Update job_id if URL param changed (e.g. new tab session)
if st.session_state.job_id != _url_job_id:
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.job_id = _url_job_id


# ─────────────────────────────────────────────────────────────
# JOB DATA FETCHER  — calls FastAPI backend
# ─────────────────────────────────────────────────────────────
def fetch_job_data(job_id: str) -> dict:
    """
    Fetch job from TalentOS API.
    Falls back to a demo payload if the API is unreachable or job not found.
    """
    job = get_job(job_id)
    if job:
        return job
    # Graceful fallback for offline / DEMO runs
    return {
        "id":          job_id,
        "title":       "Senior Full-Stack Engineer",
        "company":     "TalentOS Demo",
        "location":    "Remote · Global",
        "type":        "Full-time",
        "experience":  "5+ Years",
        "description": (
            "This is a demo assessment. The real job description will load "
            "once the TalentOS API is running. Start it with:\n\n"
            "  uvicorn api.main:app --reload --port 8000"
        ),
        "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "AWS"],
        "nice_to_have":    ["Docker", "Redis", "LLM integrations"],
        "responsibilities": "• Build production-grade applications end-to-end.",
    }


# ─────────────────────────────────────────────────────────────
# REPORT SUBMISSION  — calls FastAPI POST /reports/{job_id}
# ─────────────────────────────────────────────────────────────
def _submit_report_to_api() -> bool:
    """
    POST the completed assessment report to the TalentOS backend.
    Returns True on success.
    """
    try:
        submit_report(
            job_id            = st.session_state.job_id,
            candidate_name    = str(st.session_state.candidate_name or "Candidate"),
            ats_score         = max(0, min(100, int(round(st.session_state.ats_score)))),
            interview_score   = max(0, min(100, int(round(st.session_state.interview_score)))),
            skill_match_score = max(0, min(100, int(round(st.session_state.skill_match_score)))),
            final_report      = str(st.session_state.final_report or ""),
            transcript        = list(st.session_state.interview_answers or []),
        )
        return True
    except Exception as exc:
        st.session_state.submit_error = str(exc)
        return False


# ─────────────────────────────────────────────────────────────
# FIRECRAWL INTEGRATION
# ─────────────────────────────────────────────────────────────
def crawl_candidate_links(links: list[str]) -> str:
    if not links or not FIRECRAWL_API_KEY:
        return ""
    results = []
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type":  "application/json",
    }
    for url in links[:6]:
        try:
            resp = _requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True, "waitFor": 1500},
                headers=headers, timeout=20,
            )
            if resp.status_code == 200:
                data    = resp.json()
                content = data.get("data", {}).get("markdown", "") or data.get("data", {}).get("content", "")
                if content:
                    results.append(f"--- Source: {url} ---\n{content[:3000]}\n")
        except Exception as exc:
            results.append(f"--- Source: {url} (fetch failed: {exc}) ---\n")
    return "\n".join(results)


def extract_pdf_links(file_bytes: bytes) -> list[str]:
    if not HAS_PDF:
        return []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        links = extract_hyperlinks(tmp_path)
        os.unlink(tmp_path)
        return links
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
# AUDIO HELPERS
# ─────────────────────────────────────────────────────────────
def _tts_bytes(text: str) -> bytes:
    tts_obj = gTTS(text=text, lang="en", slow=False)
    fp = io.BytesIO()
    tts_obj.write_to_fp(fp)
    fp.seek(0)
    return fp.read()


def transcribe_audio(audio_bytes: bytes) -> str:
    if not HF_API_KEY:
        return "[STT unavailable — set HUGGINGFACE_API_KEY]"
    headers  = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "audio/wav"}
    response = _requests.post(WHISPER_URL, headers=headers, data=audio_bytes, timeout=30)
    if response.status_code == 200:
        return response.json().get("text", "").strip()
    return f"[Transcription error: {response.status_code}]"


# ─────────────────────────────────────────────────────────────
# LLM HELPERS
# ─────────────────────────────────────────────────────────────
def llm_chat(prompt: str, system: str = "", followup: str = "") -> str:
    if not llm:
        return "⚠ LLM not configured. Set OPENROUTER_API_KEY."
    if HAS_OR:
        res = chat_with_reasoning_followup(
            client=llm, initial_prompt=prompt,
            follow_up_prompt=followup or "Provide the final output. No reasoning tags.",
            model=MODEL,
        )
        return res.content
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = llm.chat.completions.create(model=MODEL, messages=messages, max_tokens=2000)
    return resp.choices[0].message.content.strip()


def build_profile(resume_text: str, crawled: str, role: str) -> str:
    return llm_chat(
        prompt=(
            f"Create a detailed candidate intelligence profile.\n"
            f"Target Role: {role}\nResume Data: {resume_text}\n"
            f"Online Presence / Links: {crawled or '(none scraped)'}"
        ),
        followup="Output ONLY the final clean profile. Remove all reasoning.",
    )


def generate_questions(profile: str, role: str) -> list[str]:
    raw = llm_chat(
        prompt=(
            f"You are a senior technical interviewer.\n"
            f"Generate exactly {NUM_QUESTIONS} sharp, role-specific questions "
            f"to evaluate the candidate below.\n"
            f"Target Role: {role}\nProfile: {profile}\n"
            f"Rules: tie each question to the profile; mix behavioural, "
            f"situational, and technical; avoid generic openers."
        ),
        followup=(
            f"Return ONLY a numbered list of {NUM_QUESTIONS} questions, "
            "one per line. No headers, no explanations."
        ),
    )
    lines = [q.strip() for q in raw.split("\n") if q.strip()]
    return lines[:NUM_QUESTIONS] if len(lines) >= NUM_QUESTIONS else (
        lines + [f"Tell us about a challenging project in your {role} career."] * (NUM_QUESTIONS - len(lines))
    )


def score_interview(qa_pairs: list[dict], role: str) -> tuple[int, int]:
    if not qa_pairs:
        return 55, 60
    qa_text = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs])
    raw = llm_chat(
        prompt=(
            f"Evaluate this interview transcript for the role: {role}\n{qa_text}\n"
            'Return a JSON object: {"interview_score": <int 0-100>, "skill_match_score": <int 0-100>}'
        ),
        followup="Return ONLY the JSON object. No explanation.",
    )
    try:
        raw_clean = raw.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_clean)
        return int(data.get("interview_score", 65)), int(data.get("skill_match_score", 65))
    except Exception:
        return 65, 68


def generate_report(profile: str, role: str, qa_pairs: list, ats: int, iv: int, skill: int) -> str:
    qa_text = "\n".join(
        [f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}" for i, qa in enumerate(qa_pairs)]
    )
    return llm_chat(
        prompt=(
            f"Write a comprehensive candidate evaluation report.\n"
            f"Role: {role} | ATS: {ats}% | Interview: {iv}% | Skill Match: {skill}%\n"
            f"Profile: {profile}\nTranscript:\n{qa_text}\n"
            "Sections: ## Executive Summary / ## Technical Competency / "
            "## Interview Analysis / ## Strengths / ## Development Areas / "
            "## Cultural Fit / ## Hiring Recommendation / ## Final Verdict"
        ),
        followup="Write the final polished report. Use markdown headers. Remove reasoning.",
    )


# ─────────────────────────────────────────────────────────────
# SHARED COMPONENTS
# ─────────────────────────────────────────────────────────────
STEP_LABELS = ["Job Details", "Resume", "Interview", "Report", "Complete"]


def render_topnav():
    current    = st.session_state.page
    page_order = ["jd", "upload", "interview", "report", "complete"]
    try:
        current_idx = page_order.index(current)
    except ValueError:
        current_idx = 0

    steps_html = ""
    for i, label in enumerate(STEP_LABELS):
        if i < current_idx:
            cls, num = "done", "✓"
        elif i == current_idx:
            cls, num = "active", str(i + 1)
        else:
            cls, num = "", str(i + 1)

        steps_html += f"""
        <div class="step-item {cls}">
          <div class="step-num">{num}</div>
          {label}
        </div>"""
        if i < len(STEP_LABELS) - 1:
            conn_cls = "done" if i < current_idx else ""
            steps_html += f'<div class="step-connector {conn_cls}"></div>'

    st.markdown(f"""
    <div class="main-container">
      <div class="topnav-fixed">
        <div class="nav-brand">
          <div class="nav-hex">⬡</div>
          <div>
            <div class="nav-title">TalentOS</div>
            <div class="nav-sub">AI Recruitment Platform</div>
          </div>
        </div>
        <div class="stepper">{steps_html}</div>
      </div>
    """, unsafe_allow_html=True)


def close_container():
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# TAB 1 · JOB DESCRIPTION
# ─────────────────────────────────────────────────────────────
def page_jd():
    render_topnav()

    if st.session_state.job_data is None:
        with st.spinner("⬡ Loading job details…"):
            st.session_state.job_data = fetch_job_data(st.session_state.job_id)

    jd = st.session_state.job_data
    # Guard: if job_data was accidentally stored as a list, re-fetch or extract
    if isinstance(jd, list):
        matched = next((j for j in jd if j.get("id") == st.session_state.job_id), None)
        if matched:
            jd = matched
        else:
            jd = fetch_job_data(st.session_state.job_id)
        st.session_state.job_data = jd

    st.markdown(f"""
    <div class="sec-block" style="margin-top:4px;">
      <div class="sec-tag">Step 01 · Assessment</div>
      <div class="sec-title">Job Details</div>
      <div class="sec-desc">Review the role carefully before proceeding to your assessment.</div>
    </div>
    """, unsafe_allow_html=True)

    skills_preview = " · ".join(jd.get("required_skills", [])[:5])
    resp_lines = [
        f"<li>{l[2:].strip()}</li>" for l in jd.get("responsibilities", "").split("\n")
        if l.strip().startswith("•")
    ]
    resp_html = f"<ul style='padding-left:18px;margin:0;'>{''.join(resp_lines)}</ul>" if resp_lines else (
        f"<p class='jd-body-text'>{jd.get('responsibilities','')}</p>"
    )

    st.markdown(f"""
    <div class="jd-header">
      <div class="jd-company-badge">⬡ &nbsp; {jd["company"]}</div>
      <div class="jd-title">{jd["title"]}</div>
      <div style="font-size:0.88rem; color:var(--t2); line-height:1.5; margin-bottom:4px;">
        {jd.get("description","").split(chr(10))[0]}
      </div>
      <div class="jd-meta">
        <div class="jd-meta-item"><div class="jd-meta-dot"></div>{jd.get("location","Remote")}</div>
        <div class="jd-meta-item"><div class="jd-meta-dot"></div>{jd.get("type","Full-time")}</div>
        <div class="jd-meta-item"><div class="jd-meta-dot"></div>{jd.get("experience","")}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    req_skills_html = "".join(
        f'<span class="skill-pill primary">◈ {s}</span>'
        for s in jd.get("required_skills", [])
    )
    nth_skills_html = "".join(
        f'<span class="skill-pill">◇ {s}</span>'
        for s in jd.get("nice_to_have", [])
    )

    st.markdown(f"""
    <div class="jd-body">
      <div class="jd-left">
        <div class="jd-col-title">Role Overview</div>
        <div class="jd-body-text" style="white-space:pre-line;">{jd.get("description","")}</div>
        <div class="jd-col-title" style="margin-top:24px;">Key Responsibilities</div>
        <div class="jd-body-text">{resp_html}</div>
      </div>
      <div class="jd-right">
        <div class="jd-col-title">Required Skills</div>
        <div class="skill-grid">{req_skills_html}</div>
        <div class="jd-col-title" style="margin-top:20px;">Nice to Have</div>
        <div class="skill-grid">{nth_skills_html}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
    col_cta, _ = st.columns([2, 3])
    with col_cta:
        if st.button(
            "⬡ Begin Assessment →",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.page = "upload"
            st.rerun()

    close_container()


# ─────────────────────────────────────────────────────────────
# TAB 2 · RESUME UPLOAD
# ─────────────────────────────────────────────────────────────
def page_upload():
    render_topnav()

    jd = st.session_state.job_data or {}

    st.markdown("""
    <div class="sec-block" style="margin-top:4px;">
      <div class="sec-tag">Step 02 · Resume</div>
      <div class="sec-title">Upload Your Resume</div>
      <div class="sec-desc">
        Upload your CV and optionally add profile links for deeper analysis.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_upload, col_links = st.columns([1.4, 1], gap="large")

    with col_upload:
        st.markdown('<div class="field-label"><div class="field-dot"></div>Resume / CV Document</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            label="resume_upload", label_visibility="collapsed",
            type=["pdf", "docx"], help="Accepted formats: PDF, DOCX · Max 10 MB",
        )
        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            st.markdown(f"""
            <div style="margin-top:12px;display:flex;align-items:center;gap:10px;
                        background:rgba(0,229,196,0.05);border:1px solid rgba(0,229,196,0.2);
                        border-radius:var(--r-sm);padding:10px 16px;">
              <span style="font-size:1.2rem;">📄</span>
              <div>
                <div style="font-size:0.85rem;font-weight:600;color:var(--t1);">{uploaded_file.name}</div>
                <div style="font-family:var(--f-mono);font-size:0.63rem;color:var(--cyan);letter-spacing:0.08em;">
                  {size_kb:.1f} KB · Ready to process
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_links:
        st.markdown('<div class="field-label" style="margin-top:0;"><div class="field-dot"></div>Portfolio &amp; Profile Links <span style="color:var(--t4);font-size:0.6rem;">(optional)</span></div>', unsafe_allow_html=True)
        gh_link   = st.text_input("GitHub Profile", placeholder="https://github.com/yourname", label_visibility="collapsed", key="inp_gh")
        portfolio = st.text_input("Portfolio / Website", placeholder="https://yourportfolio.com", label_visibility="collapsed", key="inp_port")
        linkedin  = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/yourname", label_visibility="collapsed", key="inp_li")
        st.markdown('<div style="font-family:var(--f-mono);font-size:0.6rem;color:var(--t3);letter-spacing:0.08em;margin-top:10px;">◈ Links are scraped to enrich your profile analysis</div>', unsafe_allow_html=True)

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    st.markdown('<div class="field-label"><div class="field-dot"></div>Your Full Name</div>', unsafe_allow_html=True)
    cand_name = st.text_input(
        "Full name", placeholder="e.g. Alex Johnson",
        label_visibility="collapsed", key="inp_name",
    )

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
    col_cta, _ = st.columns([2, 3])
    with col_cta:
        if st.button(
            "⬡ Process Resume & Begin Interview →",
            type="primary",
            use_container_width=True,
            disabled=(uploaded_file is None),
        ):
            if not cand_name.strip():
                st.warning("⚠ Please enter your full name before continuing.")
                st.stop()

            st.session_state.candidate_name = cand_name.strip()
            manual_links = [l.strip() for l in [gh_link, portfolio, linkedin] if l.strip()]

            with st.status("⬡ Building your candidate profile…", expanded=True) as status:
                try:
                    status.write("⬡ Stage 1 · Extracting resume content…")
                    resume_bytes = uploaded_file.getvalue()
                    st.session_state.resume_file = resume_bytes

                    pdf_links = []
                    if uploaded_file.type == "application/pdf":
                        pdf_links = extract_pdf_links(resume_bytes)
                    all_links = list(set(pdf_links + manual_links))
                    st.session_state.resume_links = all_links

                    if all_links:
                        status.write(f"◈ Stage 2 · Crawling {len(all_links)} candidate links…")
                        crawled = crawl_candidate_links(all_links)
                        st.session_state.crawled_data = crawled
                    else:
                        status.write("◈ Stage 2 · No external links to crawl — skipping.")
                        crawled = ""

                    status.write("◎ Stage 3 · Synthesising intelligence profile…")
                    resume_text = resume_bytes[:8000].decode("utf-8", errors="replace")
                    st.session_state.profile_text = build_profile(
                        resume_text, crawled, jd.get("title", "the target role")
                    )

                    status.write("◈ Stage 4 · Computing ATS semantic match…")
                    if HAS_TRANSFORMER and ats_model:
                        st.session_state.ats_score = int(round(calculate_match_score(
                            st.session_state.profile_text, jd.get("title", ""), ats_model,
                        )))
                    else:
                        st.session_state.ats_score = 72

                    status.write("▶ Stage 5 · Generating personalised interview questions…")
                    st.session_state.interview_questions = generate_questions(
                        st.session_state.profile_text, jd.get("title", "the target role"),
                    )
                    st.session_state.current_q_index   = 0
                    st.session_state.audio_played      = False
                    st.session_state.interview_answers = []
                    st.session_state.page              = "interview"
                    status.update(label="✓ Profile built — starting technical interview", state="complete", expanded=False)
                except Exception as exc:
                    status.update(label=f"⚠ Pipeline error: {exc}", state="error")

            st.rerun()

    close_container()


# ─────────────────────────────────────────────────────────────
# TAB 3 · TECHNICAL INTERVIEW
# ─────────────────────────────────────────────────────────────
def page_interview():
    render_topnav()

    idx   = st.session_state.current_q_index
    total = len(st.session_state.interview_questions)

    if idx >= total:
        st.session_state.page = "report"
        st.rerun()

    q_text = st.session_state.interview_questions[idx]

    st.markdown(f"""
    <div class="sec-block" style="margin-top:4px;">
      <div class="sec-tag">Step 03 · Live Interview</div>
      <div class="sec-title">Technical Assessment</div>
      <div class="sec-desc">Answer each question out loud — your response is transcribed automatically.</div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_cam = st.columns([4, 1], gap="medium")

    with col_main:
        st.markdown(f"""
        <div class="q-card">
          <div class="q-badge">▶ &nbsp; Question {idx + 1} of {total}</div>
          <div class="q-text">{q_text}</div>
        </div>
        """, unsafe_allow_html=True)

        audio_key = f"_tts_bytes_{idx}"
        if audio_key not in st.session_state:
            with st.spinner("⬡ Generating audio…"):
                st.session_state[audio_key] = _tts_bytes(q_text)

        st.markdown('<div class="play-btn-wrap"><span class="play-note">▶ &nbsp; Question audio — plays automatically below</span></div>', unsafe_allow_html=True)
        st.audio(st.session_state[audio_key], format="audio/mp3", autoplay=True)

        st.markdown('<div class="mic-label" style="margin-top:18px;">◉ &nbsp; Record your answer</div>', unsafe_allow_html=True)
        recorded = st.audio_input("ans", key=f"aq_{idx}", label_visibility="collapsed")

        if recorded:
            with st.spinner("⬡ Transcribing…"):
                transcript_text = transcribe_audio(recorded.getvalue())

            st.markdown('<div class="answer-label">◈ &nbsp; Review &amp; edit transcription</div>', unsafe_allow_html=True)
            edited = st.text_area(
                "tr", label_visibility="collapsed",
                value=transcript_text, height=120, key=f"edit_q_{idx}",
                placeholder="Transcription appears here — edit if needed…",
            )

            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            is_last   = (idx + 1 >= total)
            btn_label = "Submit & Generate Report →" if is_last else "Submit · Next Question ▶"

            c1, c2 = st.columns([3, 1])
            with c1:
                if st.button(btn_label, type="primary", use_container_width=True, key=f"next_btn_{idx}"):
                    st.session_state.interview_answers.append({
                        "question": q_text,
                        "answer":   edited or "(no answer)",
                    })
                    st.session_state.current_q_index += 1
                    if is_last:
                        _build_report()
                    st.rerun()
            with c2:
                if st.button("Skip", use_container_width=True, key=f"skip_btn_{idx}"):
                    st.session_state.interview_answers.append({
                        "question": q_text, "answer": "(skipped)",
                    })
                    st.session_state.current_q_index += 1
                    if st.session_state.current_q_index >= total:
                        _build_report()
                    st.rerun()
        else:
            st.markdown('<div style="font-family:var(--f-mono);font-size:0.63rem;color:var(--t3);letter-spacing:0.08em;margin-top:8px;">◎ Record your answer above to continue</div>', unsafe_allow_html=True)

    with col_cam:
        st.markdown('<div class="cam-panel"><div class="cam-header"><div class="cam-dot-live"></div>Camera Preview</div></div>', unsafe_allow_html=True)
        st.camera_input("cam", key=f"cam_{idx}", label_visibility="collapsed")
        st.markdown('<div style="font-family:var(--f-mono);font-size:.6rem;color:var(--t3);letter-spacing:.08em;text-align:center;margin-top:6px;">◎ Live · Allow camera access if prompted</div>', unsafe_allow_html=True)

    close_container()


def _build_report():
    """Generate scores and final report after all questions are answered."""
    jd = st.session_state.job_data or {}
    with st.spinner("⬡ Compiling evaluation report…"):
        iv_score, skill_score = score_interview(
            st.session_state.interview_answers, jd.get("title", "the role"),
        )
        st.session_state.interview_score   = iv_score
        st.session_state.skill_match_score = skill_score
        st.session_state.final_report = generate_report(
            profile   = st.session_state.profile_text,
            role      = jd.get("title", "the role"),
            qa_pairs  = st.session_state.interview_answers,
            ats       = st.session_state.ats_score,
            iv        = iv_score,
            skill     = skill_score,
        )
        st.session_state.page = "report"


# ─────────────────────────────────────────────────────────────
# TAB 4 · REPORT
# ─────────────────────────────────────────────────────────────
def page_report():
    render_topnav()

    ats   = st.session_state.ats_score
    iv    = st.session_state.interview_score
    skill = st.session_state.skill_match_score
    name  = st.session_state.candidate_name or "Candidate"
    jd    = st.session_state.job_data or {}

    ats_color   = "#00E5C4" if ats   >= 80 else ("#00A3FF" if ats   >= 60 else "#F5C842")
    iv_color    = "#00E5C4" if iv    >= 80 else ("#00A3FF" if iv    >= 60 else "#F5C842")
    skill_color = "#00E5C4" if skill >= 80 else ("#00A3FF" if skill >= 60 else "#F5C842")

    st.markdown("""
    <div class="sec-block" style="margin-top:4px;">
      <div class="sec-tag">Step 04 · Evaluation</div>
      <div class="sec-title">Assessment Report</div>
      <div class="sec-desc">AI-generated evaluation based on resume analysis and live interview.</div>
    </div>
    """, unsafe_allow_html=True)

    col_summary, col_report = st.columns([0.85, 1.7], gap="large")

    with col_summary:
        bar_color = ats_color
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=ats,
            number={"font": {"size": 44, "color": "#EDF0FA", "family": "Sora"}, "suffix": "%"},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4E566E", "tickfont": {"color": "#4E566E", "size": 9, "family": "JetBrains Mono"}},
                "bar": {"color": bar_color, "thickness": 0.24},
                "bgcolor": "rgba(255,255,255,0.02)", "borderwidth": 0,
                "steps": [
                    {"range": [0,  40], "color": "rgba(255,77,106,0.07)"},
                    {"range": [40, 70], "color": "rgba(245,200,66,0.07)"},
                    {"range": [70,100], "color": "rgba(0,229,196,0.07)"},
                ],
                "threshold": {"line": {"color": bar_color, "width": 3}, "thickness": 0.8, "value": ats},
            },
        ))
        fig.update_layout(
            height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=16, r=16, t=16, b=6), font={"family": "Sora"},
        )
        st.plotly_chart(fig, use_container_width=True, key="gauge_chart")

        st.markdown(f"""
        <div class="candidate-summary-card">
          <div class="avatar-ring">🧑</div>
          <div class="cand-name">{name}</div>
          <div class="cand-role">{jd.get("title","Role")}</div>
          <div class="score-divider"></div>
          <div class="score-row"><div class="score-lbl">ATS Score</div><div class="score-val" style="color:{ats_color};">{ats}%</div></div>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:{ats}%;background:linear-gradient(90deg,{ats_color},var(--cyan));"></div></div>
          <div class="score-row"><div class="score-lbl">Interview Score</div><div class="score-val" style="color:{iv_color};">{iv}%</div></div>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:{iv}%;background:linear-gradient(90deg,{iv_color},var(--blue));"></div></div>
          <div class="score-row"><div class="score-lbl">Skill Match</div><div class="score-val" style="color:{skill_color};">{skill}%</div></div>
          <div class="score-bar-track"><div class="score-bar-fill" style="width:{skill}%;background:linear-gradient(90deg,{skill_color},var(--violet));"></div></div>
        </div>
        """, unsafe_allow_html=True)

    with col_report:
        st.markdown(f"""
        <div class="report-body-card">
          <div class="report-text">{st.session_state.final_report}</div>
        </div>
        """, unsafe_allow_html=True)

    # Transcript expander
    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    with st.expander("◎ View Full Interview Transcript"):
        for i, qa in enumerate(st.session_state.interview_answers):
            st.markdown(f"""
            <div style="margin-bottom:18px;padding:16px 20px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-md);">
              <div style="font-family:var(--f-mono);font-size:0.65rem;color:var(--blue);letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;">Question {i+1}</div>
              <div style="font-size:0.9rem;font-weight:600;color:var(--t1);margin-bottom:8px;line-height:1.5;">{qa["question"]}</div>
              <div style="font-size:0.85rem;color:var(--t2);line-height:1.7;padding-top:8px;border-top:1px solid var(--border);">{qa["answer"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # Submit & Download
    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
    col_submit, col_dl = st.columns([1.6, 1], gap="medium")

    with col_submit:
        # Show error if a previous submit failed
        if st.session_state.submit_error:
            st.error(f"⚠ Submission failed: {st.session_state.submit_error}")

        btn_label = (
            "✓ Report Submitted to HR →"
            if st.session_state.report_submitted
            else "⬡ · Submit Report to HR Dashboard →"
        )
        if st.button(
            btn_label,
            type="primary",
            use_container_width=True,
            disabled=st.session_state.report_submitted,
        ):
            with st.spinner("⬡ Transmitting report to HR…"):
                ok = _submit_report_to_api()
            if ok:
                st.session_state.report_submitted = True
                st.session_state.submit_error     = ""
                st.session_state.page             = "complete"
                st.rerun()
            else:
                st.rerun()   # show error banner on next render

    with col_dl:
        jd_t       = jd.get("title", "Role")
        report_txt = (
            f"TalentOS · Candidate Assessment Report\n{'='*55}\n"
            f"Candidate : {name}\nRole      : {jd_t}\n"
            f"Job ID    : {st.session_state.job_id}\n"
            f"ATS Score : {ats}% | Interview: {iv}% | Skill Match: {skill}%\n"
            f"{'='*55}\n\n{st.session_state.final_report}\n\n"
            f"{'─'*55}\nInterview Transcript\n{'─'*55}\n"
        ) + "\n".join(
            [f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}\n"
             for i, qa in enumerate(st.session_state.interview_answers)]
        )
        st.download_button(
            "◈ · Download Report (.txt)",
            data=report_txt,
            file_name=f"TalentOS_{name.replace(' ','_')}_Report.txt",
            use_container_width=True,
        )

    close_container()


# ─────────────────────────────────────────────────────────────
# TAB 5 · COMPLETION
# ─────────────────────────────────────────────────────────────
def page_complete():
    render_topnav()

    name = st.session_state.candidate_name or "Candidate"
    jd   = st.session_state.job_data or {}

    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="completion-overlay">
      <div class="completion-card">
        <span class="completion-icon">🎉</span>
        <div class="completion-title">You're All Done, {name.split()[0]}!</div>
        <div class="completion-sub">
          Thank you for attending and applying for the
          <strong style="color:var(--t1);">{jd.get("title","role")}</strong>
          position at <strong style="color:var(--t1);">{jd.get("company","")}</strong>.
          <br><br>
          Your assessment has been submitted and is now under review by our
          recruitment team. We'll be in touch within 3–5 business days.
        </div>
        <div class="completion-badge">
          <div class="comp-dot"></div>
          Assessment Submitted · Under Review
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:420px;"></div>', unsafe_allow_html=True)
    col_c, _ = st.columns([2, 3])
    with col_c:
        if st.button("⬡ Close & Return to Home", use_container_width=True):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    close_container()


# ─────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────
PAGE = st.session_state.page

if   PAGE == "jd":        page_jd()
elif PAGE == "upload":    page_upload()
elif PAGE == "interview": page_interview()
elif PAGE == "report":    page_report()
elif PAGE == "complete":  page_complete()