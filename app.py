"""
app.py — AutoGitBackup Streamlit Dashboard Entry Point
========================================================
Multi-page Streamlit application. This file configures the global
page settings, injects custom CSS, and renders the sidebar navigation.

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Make sure sibling modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_stats
from config import load_config
from scheduler import get_task_status, compute_next_run

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoGitBackup",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "Report a bug": None,
        "About": "# AutoGitBackup\nAutomatic Assignment Backup to GitHub",
    },
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hide default Streamlit elements ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #1a2744 100%);
    border-right: 1px solid #243354;
}
section[data-testid="stSidebar"] * {
    color: #c8d6f0 !important;
}

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #141e30 0%, #1c2d4a 100%);
    border: 1px solid #2a3f63;
    border-radius: 12px;
    padding: 18px 22px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(79, 142, 247, 0.15);
}
div[data-testid="metric-container"] label {
    color: #8aabdd !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #e8f0fe !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* ── Primary button ── */
div.stButton > button[kind="primary"],
div.stButton > button {
    background: linear-gradient(135deg, #3b6fd4 0%, #4f8ef7 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(79, 142, 247, 0.3);
}
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(79, 142, 247, 0.45);
    background: linear-gradient(135deg, #4478e8 0%, #5fa0ff 100%);
}

/* ── Section headers ── */
h1 { color: #e8f0fe !important; font-weight: 700 !important; }
h2 { color: #c8d6f0 !important; font-weight: 600 !important; }
h3 { color: #a8c4e8 !important; font-weight: 500 !important; }

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-success { background: #1a3a1f; color: #4caf50; border: 1px solid #2e6b33; }
.badge-failed  { background: #3a1a1a; color: #f44336; border: 1px solid #6b2e2e; }
.badge-warn    { background: #3a2e1a; color: #ff9800; border: 1px solid #6b521a; }
.badge-info    { background: #1a2a3a; color: #4f8ef7; border: 1px solid #2e4a6b; }

/* ── Info box ── */
.info-box {
    background: linear-gradient(135deg, #141e30, #1c2d4a);
    border: 1px solid #2a3f63;
    border-left: 4px solid #4f8ef7;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 10px 0;
}

/* ── Table ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* ── Input fields ── */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] > div {
    background: #141e30 !important;
    border: 1px solid #2a3f63 !important;
    border-radius: 8px !important;
    color: #e8f0fe !important;
}
</style>
""", unsafe_allow_html=True)


# ── Initialise DB on startup ──────────────────────────────────────────────────
init_db()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.5rem;">🔄</div>
        <div style="font-size:1.2rem; font-weight:700; color:#e8f0fe; margin-top:6px;">
            AutoGitBackup
        </div>
        <div style="font-size:0.75rem; color:#6a8ab0; margin-top:2px;">
            Automatic Assignment Backup
        </div>
    </div>
    <hr style="border-color:#243354; margin: 10px 0 20px 0;">
    """, unsafe_allow_html=True)

    cfg = load_config()
    task_info = get_task_status()

    if task_info["exists"]:
        next_run = task_info["next_run_time"]
        sched_badge = '<span class="badge badge-success">● Scheduled</span>'
    else:
        next_run = compute_next_run(cfg.backup_time)
        sched_badge = '<span class="badge badge-warn">● Not Scheduled</span>'

    st.markdown(f"""
    <div style="padding:0 8px;">
        <div style="font-size:0.72rem; color:#6a8ab0; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">
            Scheduler
        </div>
        {sched_badge}
        <div style="font-size:0.8rem; color:#8aabdd; margin-top:8px;">
            Next: {next_run}
        </div>
    </div>
    <hr style="border-color:#243354; margin: 16px 0;">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:0 8px; font-size:0.72rem; color:#6a8ab0; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">
        Navigation
    </div>
    """, unsafe_allow_html=True)


# ── Home Page Content ─────────────────────────────────────────────────────────
st.markdown("# 🔄 AutoGitBackup Dashboard")
st.markdown("*Automatic Assignment Backup to GitHub — Built by **Vikas***")
st.divider()

stats = get_stats()
cfg = load_config()

# ── KPI Metrics Row ───────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

last_backup = stats["last_backup"]
last_backup_str = (
    last_backup["backup_datetime"].strftime("%b %d, %H:%M")
    if last_backup and last_backup["backup_datetime"]
    else "Never"
)

with col1:
    st.metric("📁 Total Backups", stats["total_backups"])
with col2:
    st.metric("✅ Successful", stats["successful"])
with col3:
    st.metric("❌ Failed", stats["failed"])
with col4:
    st.metric("📄 Files Backed Up", stats["total_files_uploaded"])
with col5:
    st.metric("🎯 Success Rate", f"{stats['success_rate']}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Status Cards Row ──────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    if last_backup:
        status = last_backup["status"]
        badge_class = {
            "success": "badge-success",
            "failed": "badge-failed",
            "no_changes": "badge-info",
        }.get(status, "badge-info")
        status_icon = {"success": "✅", "failed": "❌", "no_changes": "ℹ️"}.get(status, "•")
        st.markdown(f"""
        <div class="info-box">
            <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
                Last Backup
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:1.4rem;font-weight:700;color:#e8f0fe;">{last_backup_str}</div>
                    <div style="font-size:0.82rem;color:#8aabdd;margin-top:4px;">
                        {last_backup['commit_message']}
                    </div>
                    <div style="font-size:0.78rem;color:#6a8ab0;margin-top:4px;">
                        {last_backup['files_uploaded']} file(s) &nbsp;·&nbsp; {last_backup.get('duration_seconds',0) or 0:.1f}s
                    </div>
                </div>
                <div style="font-size:2rem;">{status_icon}</div>
            </div>
            <div style="margin-top:10px;">
                <span class="badge {badge_class}">{status.upper().replace('_',' ')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
            <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
                Last Backup
            </div>
            <div style="color:#8aabdd;">No backups yet. Run your first backup!</div>
        </div>
        """, unsafe_allow_html=True)

with col_b:
    task_info = get_task_status()
    if task_info["exists"]:
        sched_color = "#4caf50"
        sched_text = "Active"
        sched_icon = "📅"
    else:
        sched_color = "#ff9800"
        sched_text = "Not Configured"
        sched_icon = "⚠️"

    st.markdown(f"""
    <div class="info-box">
        <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
            Scheduler Status
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:1.4rem;font-weight:700;color:{sched_color};">{sched_text}</div>
                <div style="font-size:0.82rem;color:#8aabdd;margin-top:4px;">
                    Daily at {cfg.backup_time}
                </div>
                <div style="font-size:0.78rem;color:#6a8ab0;margin-top:4px;">
                    Next run: {task_info.get('next_run_time', compute_next_run(cfg.backup_time))}
                </div>
            </div>
            <div style="font-size:2rem;">{sched_icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Repository & Folder Info ──────────────────────────────────────────────────
col_c, col_d = st.columns(2)
with col_c:
    st.markdown(f"""
    <div class="info-box">
        <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
            Current Configuration
        </div>
        <div style="font-size:0.85rem;color:#e8f0fe;line-height:2;">
            📁 <b>Watch Folder:</b> <code style="color:#4f8ef7;">{cfg.watch_folder}</code><br>
            🔗 <b>Repository:</b> <code style="color:#4f8ef7;">{cfg.repo_url or 'Not configured'}</code><br>
            🌿 <b>Branch:</b> <code style="color:#4f8ef7;">{cfg.branch}</code><br>
            🔑 <b>Token:</b> {'<span style="color:#4caf50;">Configured ✓</span>' if cfg.github_token else '<span style="color:#f44336;">Not set ✗</span>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_d:
    st.markdown(f"""
    <div class="info-box">
        <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
            Quick Stats
        </div>
        <div style="font-size:0.85rem;color:#e8f0fe;line-height:2.2;">
            📊 <b>Total Backups:</b> {stats['total_backups']}<br>
            ✅ <b>Success Rate:</b> {stats['success_rate']}%<br>
            📄 <b>Total Files Uploaded:</b> {stats['total_files_uploaded']}<br>
            ⏭ <b>No-Change Runs:</b> {stats['no_changes']}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the sidebar to navigate to **Backup History**, **Repository Status**, **Settings**, or **Manual Backup**.")

st.markdown("""
<div style="text-align:center; padding: 20px 0 5px 0; font-size:0.75rem; color:#3a5a8a;">
    Built with ❤️ by <b>Vikas</b> &nbsp;·&nbsp; AutoGitBackup v1.0 &nbsp;·&nbsp; Python · SQLite · Streamlit
</div>
""", unsafe_allow_html=True)
