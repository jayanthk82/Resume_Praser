"""
TalentOS · HR Recruitment Portal
Job Board → Create Job → Candidate Reports

Data layer: FastAPI backend via shared/api_client.py
Theme:      Full TalentOS design system (tokens identical to talentos_theme.py)
Port:       8501  (default)
"""

import streamlit as st
import os
import sys
import importlib.util

# ── Load api_client ────────────────────────────────────────────────────────────
import api_client

list_jobs          = api_client.list_jobs
get_job            = api_client.get_job
create_job         = api_client.create_job
update_job_status  = api_client.update_job_status
delete_job         = api_client.delete_job
get_reports_for_job = api_client.get_reports_for_job
health_check       = api_client.health_check

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentOS · HR Portal",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM CSS  (identical tokens to talentos_theme.py)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
/* ═══ ROOT TOKENS ═══════════════════════════════════════════ */
:root {
  --bg-base:  #03050D;
  --bg-card:  rgba(255,255,255,0.028);
  --border:   rgba(255,255,255,0.07);
  --blue:     #00A3FF;
  --cyan:     #00E5C4;
  --gold:     #F5C842;
  --red:      #FF4D6A;
  --violet:   #7B61FF;
  --t1: #EDF0FA; --t2: #8B93B0; --t3: #4E566E;
  --f-main: 'Sora', sans-serif;
  --f-mono: 'JetBrains Mono', monospace;
  --r-sm: 10px; --r-md: 16px; --r-lg: 24px; --r-xl: 32px;
  --ease:   cubic-bezier(0.4, 0, 0.2, 1);
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --t: 0.28s;
}

/* ═══ GLOBAL ════════════════════════════════════════════════ */
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
[data-testid="stVerticalBlock"] { background: transparent !important; }

/* ═══ AMBIENT MESH ══════════════════════════════════════════ */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 90% 70% at 5%   0%,  rgba(0,163,255,0.075) 0%, transparent 55%),
    radial-gradient(ellipse 60% 55% at 95%  95%, rgba(0,229,196,0.065) 0%, transparent 50%),
    radial-gradient(ellipse 50% 45% at 50%  50%, rgba(123,97,255,0.04)  0%, transparent 65%);
  pointer-events: none; z-index: 0;
  animation: ambientShift 18s ease-in-out infinite alternate;
}
@keyframes ambientShift {
  0%   { opacity: 1;    transform: scale(1); }
  100% { opacity: 0.75; transform: scale(1.04); }
}

/* ═══ HIDE CHROME ═══════════════════════════════════════════ */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stSidebar"] { display: none !important; }

/* ═══ CENTRE & MAX-WIDTH ════════════════════════════════════ */
[data-testid="stMainBlockContainer"] {
  max-width: 1100px !important;
  margin: 0 auto !important;
  padding: 0 24px 80px !important;
}

/* ═══ TOP NAV ═══════════════════════════════════════════════ */
.topnav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 22px 0 0;
  margin-bottom: 28px;
  animation: fadeDown 0.5s var(--ease) both;
}
.nav-brand { display: flex; align-items: center; gap: 12px; }
.nav-hex {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, var(--blue), var(--cyan));
  clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff;
  animation: hexPulse 4s ease-in-out infinite;
}
@keyframes hexPulse {
  0%,100% { box-shadow: 0 0 20px rgba(0,163,255,0.35); }
  50%      { box-shadow: 0 0 44px rgba(0,229,196,0.5); }
}
.nav-title {
  font-size: 1.15rem; font-weight: 800; letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--t1) 40%, var(--blue));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.nav-sub {
  font-size: 0.58rem; font-family: var(--f-mono); color: var(--t3);
  letter-spacing: 0.2em; text-transform: uppercase; margin-top: 2px;
}
.nav-pills { display: flex; gap: 10px; align-items: center; }
.nav-pill {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(0,163,255,0.08); border: 1px solid rgba(0,163,255,0.22);
  border-radius: 999px; padding: 6px 14px;
  font-family: var(--f-mono); font-size: 0.68rem; color: var(--blue); letter-spacing: 0.1em;
}
.nav-pill.cyan {
  background: rgba(0,229,196,0.07); border-color: rgba(0,229,196,0.22); color: var(--cyan);
}
.pill-dot {
  width: 6px; height: 6px; border-radius: 50%; background: currentColor;
  animation: dotPulse 2s ease infinite;
}
@keyframes dotPulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:0.4;transform:scale(0.7);} }

/* ═══ API STATUS BANNER ════════════════════════════════════ */
.api-banner {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 18px;
  border-radius: var(--r-sm);
  font-family: var(--f-mono); font-size: 0.66rem; letter-spacing: 0.1em;
  margin-bottom: 20px; animation: fadeUp 0.4s var(--ease) both;
}
.api-banner.ok  { background: rgba(0,229,196,0.05); border: 1px solid rgba(0,229,196,0.2); color: var(--cyan); }
.api-banner.err { background: rgba(255,77,106,0.05); border: 1px solid rgba(255,77,106,0.2); color: var(--red); }

/* ═══ NATIVE STREAMLIT TABS ════════════════════════════════ */
[data-testid="stTabs"] [data-testid="stTabBar"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 4px !important;
  padding-bottom: 0 !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"] {
  font-family: var(--f-mono) !important;
  font-size: 0.7rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  color: var(--t3) !important;
  background: transparent !important;
  border: none !important;
  border-radius: var(--r-sm) var(--r-sm) 0 0 !important;
  padding: 10px 22px !important;
  transition: all var(--t) var(--ease) !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
  color: var(--t2) !important;
  background: rgba(255,255,255,0.03) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--blue) !important;
  background: rgba(0,163,255,0.1) !important;
  border-bottom: 2px solid var(--blue) !important;
}
[data-testid="stTabPanel"] {
  padding: 28px 0 0 !important;
  background: transparent !important;
}

/* ═══ SECTION HEADER ════════════════════════════════════════ */
.sec-tag {
  font-family: var(--f-mono); font-size: 0.62rem; color: var(--blue);
  letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 8px;
}
.sec-title {
  font-size: 1.8rem; font-weight: 800; letter-spacing: -0.04em;
  color: var(--t1); line-height: 1.1; margin-bottom: 6px;
}
.sec-desc { font-size: 0.87rem; color: var(--t2); line-height: 1.6; margin-bottom: 24px; }

/* ═══ JOB CARDS ═════════════════════════════════════════════ */
.job-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 22px 24px;
  transition: all var(--t) var(--ease);
  animation: fadeUp 0.5s var(--ease) both;
  position: relative; overflow: hidden;
}
.job-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--blue), var(--cyan), var(--violet));
}
.job-card:hover {
  border-color: rgba(0,163,255,0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 48px rgba(0,0,0,0.6), 0 0 60px rgba(0,163,255,0.08);
}
.jc-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.jc-company { font-family: var(--f-mono); font-size: 0.63rem; color: var(--blue); letter-spacing: 0.12em; text-transform: uppercase; }
.jc-title   { font-size: 1.02rem; font-weight: 700; color: var(--t1); margin-bottom: 5px; }
.jc-meta    { font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); letter-spacing: 0.06em; margin-bottom: 14px; }
.skill-pill {
  display: inline-block; margin: 2px; padding: 3px 9px;
  background: rgba(0,163,255,0.07); border: 1px solid rgba(0,163,255,0.2);
  border-radius: 999px; font-family: var(--f-mono); font-size: 0.6rem; color: var(--blue);
}
.jc-stats  { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.jc-stat   { display: inline-flex; align-items: center; gap: 5px; background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 999px; padding: 4px 10px; font-family: var(--f-mono); font-size: 0.61rem; color: var(--t3); }
.jc-stat-val { font-weight: 700; color: var(--t1); }
.link-box {
  margin-top: 12px; background: rgba(0,163,255,0.04); border: 1px solid rgba(0,163,255,0.18);
  border-radius: var(--r-sm); padding: 9px 12px;
  font-family: var(--f-mono); font-size: 0.59rem; color: var(--blue);
  letter-spacing: 0.04em; word-break: break-all; display: flex; gap: 8px;
}

/* ═══ STATUS PILLS ══════════════════════════════════════════ */
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-family: var(--f-mono); font-size: 0.63rem; font-weight: 500; white-space: nowrap; }
.pill-live   { background: rgba(0,229,196,0.08);  border: 1px solid rgba(0,229,196,0.28); color: var(--cyan); }
.pill-draft  { background: rgba(78,86,110,0.15);  border: 1px solid rgba(78,86,110,0.35); color: var(--t3); }
.pill-closed { background: rgba(255,77,106,0.07); border: 1px solid rgba(255,77,106,0.25); color: var(--red); }

/* ═══ FORM LABELS ═══════════════════════════════════════════ */
.field-label { font-family: var(--f-mono); font-size: 0.63rem; color: var(--t3); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 6px; display: flex; align-items: center; gap: 7px; }
.field-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--blue); }

/* ═══ CREATED LINK BANNER ═══════════════════════════════════ */
.link-banner { background: rgba(0,229,196,0.05); border: 1px solid rgba(0,229,196,0.22); border-radius: var(--r-md); padding: 18px 22px; margin-top: 16px; }
.link-banner-label { font-family: var(--f-mono); font-size: 0.62rem; color: var(--cyan); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 8px; }
.link-banner-url   { font-family: var(--f-mono); font-size: 0.82rem; color: var(--t1); word-break: break-all; }

/* ═══ REPORTS TABLE ═════════════════════════════════════════ */
.rt-wrap { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-lg); overflow: hidden; animation: fadeUp 0.5s var(--ease) both; }
.rt-wrap table { width: 100%; border-collapse: collapse; }
.rt-wrap thead th { font-family: var(--f-mono); font-size: 0.6rem; color: var(--t3); letter-spacing: 0.14em; text-transform: uppercase; padding: 12px 16px; border-bottom: 1px solid var(--border); text-align: left; }
.rt-wrap tbody td { font-size: 0.84rem; color: var(--t2); padding: 13px 16px; border-bottom: 1px solid rgba(255,255,255,0.03); vertical-align: middle; }
.rt-wrap tbody tr:last-child td { border-bottom: none; }
.rt-wrap tbody tr:hover td { background: rgba(0,163,255,0.03); color: var(--t1); }
.score-badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-family: var(--f-mono); font-size: 0.63rem; font-weight: 700; }
.badge-green { background: rgba(0,229,196,0.1);   color: var(--cyan);  border: 1px solid rgba(0,229,196,0.25); }
.badge-blue  { background: rgba(0,163,255,0.1);   color: var(--blue);  border: 1px solid rgba(0,163,255,0.25); }
.badge-gold  { background: rgba(245,200,66,0.1);  color: var(--gold);  border: 1px solid rgba(245,200,66,0.25); }
.badge-red   { background: rgba(255,77,106,0.08); color: var(--red);   border: 1px solid rgba(255,77,106,0.22); }

/* ═══ STAT CHIPS ════════════════════════════════════════════ */
.stat-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 20px 0 4px; }
.stat-chip { flex: 1; min-width: 130px; padding: 18px 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); animation: fadeUp 0.5s var(--ease) both; }
.stat-chip.hi { background: linear-gradient(135deg,rgba(0,229,196,0.07),rgba(0,163,255,0.04)); border-color: rgba(0,229,196,0.2); }
.stat-val { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1; }
.stat-lbl { font-family: var(--f-mono); font-size: 0.6rem; color: var(--t3); letter-spacing: 0.14em; text-transform: uppercase; margin-top: 6px; }

/* ═══ FOLDER HEADER ═════════════════════════════════════════ */
.folder-header { display: flex; align-items: center; gap: 14px; padding: 14px 20px; margin-bottom: 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); animation: fadeUp 0.45s var(--ease) both; }
.folder-title { font-size: 0.92rem; font-weight: 700; color: var(--t1); }
.folder-meta  { font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); letter-spacing: 0.07em; }

/* ═══ REPORT FULL TEXT ══════════════════════════════════════ */
.report-full {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 22px 26px;
  font-size: 0.86rem; color: var(--t2); line-height: 1.85;
  max-height: 420px; overflow-y: auto;
}
.report-full h2 {
  font-size: 0.78rem; font-family: var(--f-mono); color: var(--blue);
  letter-spacing: 0.18em; text-transform: uppercase; margin: 18px 0 8px;
  border-bottom: 1px solid var(--border); padding-bottom: 6px;
}

/* ═══ INPUTS ════════════════════════════════════════════════ */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.028) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--t1) !important;
  font-family: var(--f-main) !important;
  font-size: 0.88rem !important;
  padding: 11px 15px !important;
  transition: all var(--t) var(--ease) !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
  border-color: rgba(0,163,255,0.5) !important;
  box-shadow: 0 0 0 4px rgba(0,163,255,0.09) !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder { color: var(--t3) !important; }

[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,0.028) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--t1) !important;
  font-family: var(--f-main) !important;
}

/* ═══ BUTTONS ═══════════════════════════════════════════════ */
[data-testid="stButton"] > button {
  font-family: var(--f-main) !important;
  font-weight: 700 !important; font-size: 0.82rem !important;
  letter-spacing: 0.06em !important; text-transform: uppercase !important;
  border-radius: var(--r-sm) !important;
  transition: all 0.24s var(--spring) !important;
}
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #0070D8, var(--blue), #00C8FF) !important;
  background-size: 200% 200% !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 24px rgba(0,163,255,0.4) !important;
  padding: 12px 24px !important;
  animation: btnShimmer 4s ease infinite !important;
}
@keyframes btnShimmer { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
[data-testid="stButton"] > button[kind="primary"]:hover {
  box-shadow: 0 6px 36px rgba(0,163,255,0.6) !important;
  transform: translateY(-2px) scale(1.01) !important;
}
[data-testid="stButton"] > button:not([kind="primary"]) {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--border) !important; color: var(--t2) !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.16) !important; color: var(--t1) !important;
  transform: translateY(-1px) !important;
}

/* ═══ DOWNLOAD BUTTON ═══════════════════════════════════════ */
[data-testid="stDownloadButton"] > button {
  background: linear-gradient(135deg, rgba(245,200,66,0.12), rgba(245,200,66,0.06)) !important;
  border: 1px solid rgba(245,200,66,0.32) !important; color: var(--gold) !important;
  font-family: var(--f-main) !important; font-weight: 700 !important;
  font-size: 0.78rem !important; letter-spacing: 0.06em !important;
  text-transform: uppercase !important; border-radius: var(--r-sm) !important;
  padding: 11px 18px !important; transition: all 0.22s var(--ease) !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background: linear-gradient(135deg, rgba(245,200,66,0.22), rgba(245,200,66,0.12)) !important;
  box-shadow: 0 4px 24px rgba(245,200,66,0.2) !important;
  transform: translateY(-1px) !important;
}

/* ═══ EXPANDER ══════════════════════════════════════════════ */
[data-testid="stExpander"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; }
[data-testid="stExpander"] summary { font-family: var(--f-main) !important; font-size: 0.8rem !important; font-weight: 500 !important; color: var(--t2) !important; }
[data-testid="stExpander"] summary:hover { color: var(--t1) !important; }

[data-testid="stWidgetLabel"] p, label { font-family: var(--f-main) !important; font-size: 0.76rem !important; font-weight: 500 !important; color: var(--t2) !important; letter-spacing: 0.04em !important; text-transform: uppercase !important; }

[data-testid="stAlert"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; font-family: var(--f-main) !important; }
div[data-testid="stAlert"][kind="success"] { border-left: 3px solid var(--cyan) !important; }
div[data-testid="stAlert"][kind="warning"] { border-left: 3px solid var(--gold) !important; }
div[data-testid="stAlert"][kind="info"]    { border-left: 3px solid var(--blue) !important; }

.divider-label { display: flex; align-items: center; gap: 14px; margin: 24px 0 18px; font-family: var(--f-mono); font-size: 0.62rem; color: var(--t3); letter-spacing: 0.16em; text-transform: uppercase; }
.divider-label::before { content:''; flex:1; height:1px; background:linear-gradient(90deg,transparent,var(--border)); }
.divider-label::after  { content:''; flex:1; height:1px; background:linear-gradient(270deg,transparent,var(--border)); }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.16); }

@keyframes fadeUp   { from{opacity:0;transform:translateY(18px);} to{opacity:1;transform:translateY(0);} }
@keyframes fadeDown { from{opacity:0;transform:translateY(-14px);} to{opacity:1;transform:translateY(0);} }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SESSION STATE  (UI-only state — no business data stored here)
# ─────────────────────────────────────────────────────────────
if "view_job_id" not in st.session_state:
    st.session_state.view_job_id = None
if "last_created_job_id" not in st.session_state:
    st.session_state.last_created_job_id = None
if "api_ok" not in st.session_state:
    import time as _time
    for _attempt in range(5):
        if health_check():
            st.session_state.api_ok = True
            break
        _time.sleep(1)
    else:
        st.session_state.api_ok = False


# ─────────────────────────────────────────────────────────────
# DATA LOADER (cached with short TTL for near-realtime updates)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=15, show_spinner=False)
def _cached_jobs() -> list[dict]:
    return list_jobs()


@st.cache_data(ttl=15, show_spinner=False)
def _cached_reports(job_id: str) -> list[dict]:
    return get_reports_for_job(job_id)


def _invalidate_cache() -> None:
    """Clear all cached data after a write operation."""
    st.cache_data.clear()


# ─────────────────────────────────────────────────────────────
# HELPER RENDERERS  — return HTML strings, never call st.*
# ─────────────────────────────────────────────────────────────
CANDIDATE_APP_URL = os.getenv("CANDIDATE_APP_URL", "http://localhost:8502")


def make_link(job_id: str) -> str:
    return f"{CANDIDATE_APP_URL}?job_id={job_id}"


def status_pill(status: str) -> str:
    cls = {"live": "pill-live", "draft": "pill-draft", "closed": "pill-closed"}.get(
        status, "pill-draft"
    )
    return f'<span class="pill {cls}"><span class="pill-dot"></span>{status.upper()}</span>'


def score_badge(score: int) -> str:
    cls = (
        "badge-green" if score >= 80
        else "badge-blue" if score >= 65
        else "badge-gold" if score >= 50
        else "badge-red"
    )
    return f'<span class="score-badge {cls}">{score}%</span>'


def rec_badge(rec: str) -> str:
    cls = {
        "Proceed": "badge-green",
        "Hold":    "badge-gold",
        "Reject":  "badge-red",
    }.get(rec, "badge-blue")
    return f'<span class="score-badge {cls}">{rec}</span>'


# ─────────────────────────────────────────────────────────────
# API STATUS BANNER
# ─────────────────────────────────────────────────────────────
if st.session_state.api_ok:
    st.markdown(
        '<div class="api-banner ok">⬡ &nbsp; TalentOS API · Connected</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="api-banner err">⚠ &nbsp; TalentOS API · Unreachable — '
        'start the backend with: <code>uvicorn main:app --reload --port 8000</code></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# LOAD LIVE DATA
# ─────────────────────────────────────────────────────────────
jobs_list        = _cached_jobs()
jobs_dict        = {j["id"]: j for j in jobs_list}
total_jobs       = len(jobs_list)
total_candidates = sum(j.get("candidates", 0) for j in jobs_list)

# ─────────────────────────────────────────────────────────────
# TOP NAV
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topnav">
  <div class="nav-brand">
    <div class="nav-hex">⬡</div>
    <div>
      <div class="nav-title">TalentOS</div>
      <div class="nav-sub">HR Recruitment Portal</div>
    </div>
  </div>
  <div class="nav-pills">
    <div class="nav-pill"><div class="pill-dot"></div>{total_jobs} Active Jobs</div>
    <div class="nav-pill cyan"><div class="pill-dot"></div>{total_candidates} Candidates</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab_board, tab_create, tab_reports = st.tabs(
    ["⬡  Job Board", "＋  Create Job", "◈  Reports"]
)


# ═════════════════════════════════════════════════════════════
# TAB 1 · JOB BOARD
# ═════════════════════════════════════════════════════════════
with tab_board:
    hdr_col, refresh_col = st.columns([5, 1])
    with hdr_col:
        st.markdown("""
        <div class="sec-tag">HR Portal · Jobs</div>
        <div class="sec-title">Active Job Listings</div>
        <div class="sec-desc">Live positions with their unique candidate assessment links.</div>
        """, unsafe_allow_html=True)
    with refresh_col:
        st.markdown('<div style="padding-top:28px;"></div>', unsafe_allow_html=True)
        if st.button("↺ Refresh", key="refresh_board"):
            _invalidate_cache()
            st.session_state.api_ok = health_check()
            st.rerun()

    if not jobs_list:
        st.info("⬡ No jobs yet — switch to Create Job to add your first listing.")
    else:
        for i in range(0, len(jobs_list), 2):
            pair = jobs_list[i : i + 2]
            cols = st.columns(len(pair), gap="medium")

            for col, job in zip(cols, pair):
                with col:
                    link        = make_link(job["id"])
                    skills      = job.get("required_skills", job.get("skills", []))
                    skills_html = "".join(
                        f'<span class="skill-pill">{s}</span>' for s in skills[:6]
                    )
                    st.markdown(f"""
                    <div class="job-card">
                      <div class="jc-top">
                        <div class="jc-company">{job["company"]}</div>
                        {status_pill(job["status"])}
                      </div>
                      <div class="jc-title">{job["title"]}</div>
                      <div class="jc-meta">
                        {job["location"]} &nbsp;·&nbsp; {job["type"]} &nbsp;·&nbsp; {job["experience"]}
                      </div>
                      <div style="margin-bottom:4px;">{skills_html}</div>
                      <div class="jc-stats">
                        <div class="jc-stat">ID <span class="jc-stat-val">{job["id"]}</span></div>
                        <div class="jc-stat">Candidates <span class="jc-stat-val">{job.get("candidates",0)}</span></div>
                        <div class="jc-stat">Posted <span class="jc-stat-val">{job["created_at"]}</span></div>
                      </div>
                      <div class="link-box">🔗 &nbsp;{link}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    b1, b2 = st.columns(2, gap="small")
                    with b1:
                        if st.button("⬡ Copy Link", key=f"copy_{job['id']}", use_container_width=True):
                            st.toast(f"Link for {job['id']}: {link}", icon="🔗")
                    with b2:
                        if st.button("◈ Reports", key=f"rpt_{job['id']}", use_container_width=True):
                            st.session_state.view_job_id = job["id"]
                            st.toast(f"Open the Reports tab to view {job['title']}.", icon="📋")


# ═════════════════════════════════════════════════════════════
# TAB 2 · CREATE JOB
# ═════════════════════════════════════════════════════════════
with tab_create:
    st.markdown("""
    <div class="sec-tag">HR Portal · New Listing</div>
    <div class="sec-title">Create a New Job</div>
    <div class="sec-desc">
      Fill in the role details. A unique assessment link is generated and
      persisted to the TalentOS backend instantly.
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown('<div class="field-label"><div class="field-dot"></div>Job Title &nbsp;<span style="color:var(--red);">*</span></div>', unsafe_allow_html=True)
        cj_title = st.text_input("Job Title", placeholder="e.g. Senior Backend Engineer",
                                  label_visibility="collapsed", key="cj_title")

        st.markdown('<div class="field-label"><div class="field-dot"></div>Company Name &nbsp;<span style="color:var(--red);">*</span></div>', unsafe_allow_html=True)
        cj_company = st.text_input("Company Name", placeholder="e.g. Acme Corp",
                                    label_visibility="collapsed", key="cj_company")

        st.markdown('<div class="field-label"><div class="field-dot"></div>Location</div>', unsafe_allow_html=True)
        cj_location = st.text_input("Location", placeholder="e.g. Remote · Global",
                                     label_visibility="collapsed", key="cj_location")

        cx, ce = st.columns(2, gap="small")
        with cx:
            st.markdown('<div class="field-label"><div class="field-dot"></div>Job Type</div>', unsafe_allow_html=True)
            cj_type = st.selectbox("Job Type",
                                   ["Full-time", "Part-time", "Contract", "Internship"],
                                   label_visibility="collapsed", key="cj_type")
        with ce:
            st.markdown('<div class="field-label"><div class="field-dot"></div>Experience</div>', unsafe_allow_html=True)
            cj_exp = st.selectbox("Experience",
                                  ["0-1 Years", "1-3 Years", "3-5 Years", "5+ Years", "10+ Years"],
                                  label_visibility="collapsed", key="cj_exp")

    with col_r:
        st.markdown('<div class="field-label"><div class="field-dot"></div>Job Description</div>', unsafe_allow_html=True)
        cj_desc = st.text_area("Job Description", height=180,
                                placeholder="Describe the role, responsibilities, and team context…",
                                label_visibility="collapsed", key="cj_desc")

        st.markdown('<div class="field-label"><div class="field-dot"></div>Required Skills — comma separated</div>', unsafe_allow_html=True)
        cj_skills = st.text_input("Skills", placeholder="e.g. Python, React, AWS, PostgreSQL",
                                   label_visibility="collapsed", key="cj_skills")

        st.markdown('<div class="field-label"><div class="field-dot"></div>Nice-to-Have Skills — comma separated</div>', unsafe_allow_html=True)
        cj_nth = st.text_input("Nice-to-Have", placeholder="e.g. Terraform, Vector DBs",
                                label_visibility="collapsed", key="cj_nth")

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    cta_col, _ = st.columns([2, 3])
    with cta_col:
        do_create = st.button(
            "⬡ Create Job & Generate Link →",
            type="primary",
            use_container_width=True,
        )

    if do_create:
        if not cj_title.strip():
            st.warning("⚠ Job Title is required.")
        elif not cj_company.strip():
            st.warning("⚠ Company Name is required.")
        elif not st.session_state.api_ok:
            st.error("⚠ Cannot reach TalentOS API — ensure the backend is running.")
        else:
            skills_lst = [s.strip() for s in cj_skills.split(",") if s.strip()]
            nth_lst    = [s.strip() for s in cj_nth.split(",")    if s.strip()]

            with st.spinner("⬡ Creating job listing…"):
                try:
                    job_record = create_job(
                        title            = cj_title.strip(),
                        company          = cj_company.strip(),
                        location         = cj_location.strip() or "Remote",
                        job_type         = cj_type,
                        experience       = cj_exp,
                        description      = cj_desc.strip(),
                        required_skills  = skills_lst,
                        nice_to_have     = nth_lst,
                    )
                    jid      = job_record["id"]
                    gen_link = make_link(jid)

                    st.session_state.view_job_id         = jid
                    st.session_state.last_created_job_id = jid
                    _invalidate_cache()
                    st.success(f"✓ Job created! ID: **{jid}**")

                    st.markdown(f"""
                    <div class="link-banner">
                      <div class="link-banner-label">✓ &nbsp; Share this link with your candidate</div>
                      <div class="link-banner-url">{gen_link}</div>
                    </div>
                    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:14px;">
                      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-md);padding:14px 18px;">
                        <div style="font-family:var(--f-mono);font-size:.6rem;color:var(--t3);letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px;">Job ID</div>
                        <div style="font-family:var(--f-mono);font-size:.9rem;font-weight:700;color:var(--blue);">{jid}</div>
                      </div>
                      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-md);padding:14px 18px;">
                        <div style="font-family:var(--f-mono);font-size:.6rem;color:var(--t3);letter-spacing:.12em;text-transform:uppercase;margin-bottom:5px;">Status</div>
                        {status_pill("live")}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as exc:
                    st.error(f"⚠ Failed to create job: {exc}")


# ═════════════════════════════════════════════════════════════
# TAB 3 · REPORTS
# ═════════════════════════════════════════════════════════════
with tab_reports:
    rpt_hdr, rpt_refresh = st.columns([5, 1])
    with rpt_hdr:
        st.markdown("""
        <div class="sec-tag">HR Portal · Evaluations</div>
        <div class="sec-title">Candidate Reports</div>
        <div class="sec-desc">All submitted assessments organised by Job ID.</div>
        """, unsafe_allow_html=True)
    with rpt_refresh:
        st.markdown('<div style="padding-top:28px;"></div>', unsafe_allow_html=True)
        if st.button("↺ Refresh", key="refresh_reports"):
            _invalidate_cache()
            st.rerun()

    # Re-fetch jobs list after possible refresh
    jobs_list_rpt = _cached_jobs()
    if not jobs_list_rpt:
        st.info("⬡ No jobs found — create one first.")
        st.stop()

    job_ids    = [j["id"] for j in jobs_list_rpt]
    job_labels = {j["id"]: f"{j['title']}  ·  {j['id']}" for j in jobs_list_rpt}

    # Default selection: last created job or first in list
    default_sel = st.session_state.view_job_id
    if default_sel not in job_ids:
        default_sel = job_ids[0]
    default_idx = job_ids.index(default_sel)

    sel_col, _ = st.columns([2, 3])
    with sel_col:
        selected_id = st.selectbox(
            "Select Job",
            options=job_ids,
            format_func=lambda x: job_labels[x],
            index=default_idx,
            key="rpt_job_select",
            label_visibility="collapsed",
        )
    st.session_state.view_job_id = selected_id

    job_info  = {j["id"]: j for j in jobs_list_rpt}[selected_id]
    reports   = _cached_reports(selected_id)
    count_lbl = f"{len(reports)} candidate report{'s' if len(reports) != 1 else ''}"

    # Folder header
    st.markdown(f"""
    <div class="folder-header">
      <div style="font-size:1.5rem;">📁</div>
      <div style="flex:1;">
        <div class="folder-title">{job_info["title"]}</div>
        <div class="folder-meta">
          {selected_id} &nbsp;·&nbsp; {job_info["company"]} &nbsp;·&nbsp; {count_lbl}
        </div>
      </div>
      <div>{status_pill(job_info["status"])}</div>
    </div>
    """, unsafe_allow_html=True)

    if not reports:
        st.info("⬡ No candidate reports submitted for this job yet. "
                "Share the assessment link from the Job Board tab.")
    else:
        # Summary table (full in ONE markdown call)
        rows = "".join(f"""
        <tr>
          <td><strong style="color:var(--t1);">{r["candidate_name"]}</strong></td>
          <td>{score_badge(r["ats_score"])}</td>
          <td>{score_badge(r["interview_score"])}</td>
          <td>{score_badge(r["skill_match_score"])}</td>
          <td>{rec_badge(r["recommendation"])}</td>
          <td style="font-family:var(--f-mono);font-size:.7rem;color:var(--t3);">{r["submitted_at"]}</td>
        </tr>""" for r in reports)

        st.markdown(f"""
        <div class="rt-wrap">
          <table>
            <thead><tr>
              <th>Candidate</th><th>ATS Score</th><th>Interview</th>
              <th>Skill Match</th><th>Recommendation</th><th>Submitted</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

        # Cohort stats
        avg_ats   = round(sum(r["ats_score"]         for r in reports) / len(reports))
        avg_iv    = round(sum(r["interview_score"]    for r in reports) / len(reports))
        avg_skill = round(sum(r["skill_match_score"]  for r in reports) / len(reports))
        proceed   = sum(1 for r in reports if r["recommendation"] == "Proceed")

        st.markdown(f"""
        <div class="divider-label">Cohort Summary</div>
        <div class="stat-row">
          <div class="stat-chip">
            <div class="stat-val" style="color:var(--blue);">{avg_ats}%</div>
            <div class="stat-lbl">Avg ATS</div>
          </div>
          <div class="stat-chip">
            <div class="stat-val" style="color:var(--cyan);">{avg_iv}%</div>
            <div class="stat-lbl">Avg Interview</div>
          </div>
          <div class="stat-chip">
            <div class="stat-val" style="color:var(--violet);">{avg_skill}%</div>
            <div class="stat-lbl">Avg Skill Match</div>
          </div>
          <div class="stat-chip hi">
            <div class="stat-val" style="color:var(--cyan);">{proceed}/{len(reports)}</div>
            <div class="stat-lbl">Shortlisted</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Individual report expanders
        st.markdown(
            '<div class="divider-label" style="margin-top:28px;">Individual Reports</div>',
            unsafe_allow_html=True,
        )

        for r in reports:
            with st.expander(
                f"  {r['candidate_name']}  ·  {r['recommendation']}  ·  ATS {r['ats_score']}%"
            ):
                info_col, dl_col = st.columns([2, 1], gap="medium")

                with info_col:
                    st.markdown(f"""
                    <div style="font-size:.86rem;color:var(--t2);line-height:2.0;">
                      <strong style="color:var(--t1);">Submitted:</strong>&nbsp;{r["submitted_at"]}<br>
                      <strong style="color:var(--t1);">Job ID:</strong>&nbsp;
                        <span style="font-family:var(--f-mono);color:var(--blue);">{r["job_id"]}</span><br>
                      <strong style="color:var(--t1);">Scores:</strong>&nbsp;
                        ATS {score_badge(r["ats_score"])} &nbsp;
                        Interview {score_badge(r["interview_score"])} &nbsp;
                        Skill {score_badge(r["skill_match_score"])}<br>
                      <strong style="color:var(--t1);">Verdict:</strong>&nbsp;{rec_badge(r["recommendation"])}
                    </div>
                    """, unsafe_allow_html=True)

                    # Full report text
                    if r.get("final_report"):
                        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="report-full">{r["final_report"]}</div>',
                            unsafe_allow_html=True,
                        )

                    # Interview transcript
                    if r.get("transcript"):
                        with st.expander("◎ Interview Transcript"):
                            for idx, qa in enumerate(r["transcript"]):
                                st.markdown(f"""
                                <div style="margin-bottom:14px;padding:14px 18px;
                                            background:var(--bg-card);border:1px solid var(--border);
                                            border-radius:var(--r-md);">
                                  <div style="font-family:var(--f-mono);font-size:.63rem;
                                              color:var(--blue);letter-spacing:.12em;
                                              text-transform:uppercase;margin-bottom:6px;">
                                    Question {idx+1}
                                  </div>
                                  <div style="font-size:.88rem;font-weight:600;color:var(--t1);
                                              margin-bottom:7px;line-height:1.5;">
                                    {qa.get("question","")}
                                  </div>
                                  <div style="font-size:.84rem;color:var(--t2);line-height:1.7;
                                              padding-top:7px;border-top:1px solid var(--border);">
                                    {qa.get("answer","")}
                                  </div>
                                </div>
                                """, unsafe_allow_html=True)

                with dl_col:
                    skills_str  = ", ".join(job_info.get("required_skills", []))
                    report_txt  = (
                        f"TalentOS · Candidate Report\n{'='*52}\n"
                        f"Candidate      : {r['candidate_name']}\n"
                        f"Role           : {job_info['title']}\n"
                        f"Job ID         : {r['job_id']}\n"
                        f"ATS Score      : {r['ats_score']}%\n"
                        f"Interview Score: {r['interview_score']}%\n"
                        f"Skill Match    : {r['skill_match_score']}%\n"
                        f"Recommendation : {r['recommendation']}\n"
                        f"Submitted      : {r['submitted_at']}\n"
                        f"{'='*52}\n\n"
                        f"{r.get('final_report','')}\n\n"
                        f"{'─'*52}\nInterview Transcript\n{'─'*52}\n"
                    )
                    if r.get("transcript"):
                        report_txt += "\n".join(
                            f"Q{i+1}: {qa.get('question','')}\n"
                            f"A{i+1}: {qa.get('answer','')}\n"
                            for i, qa in enumerate(r["transcript"])
                        )
                    safe_name = r["candidate_name"].replace(" ", "_")
                    st.download_button(
                        label="◈ Download Report",
                        data=report_txt,
                        file_name=f"TalentOS_{safe_name}_{r['job_id']}.txt",
                        use_container_width=True,
                        key=f"dl_{r['id']}",
                    )