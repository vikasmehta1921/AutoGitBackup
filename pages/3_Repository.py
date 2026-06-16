"""
pages/3_Repository.py — Repository Status
==========================================
Shows:
  - Git repo connection status
  - Current branch + latest commit
  - Pending (untracked / modified) files
  - File extensions breakdown
  - Remote URL & connectivity test
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from github_manager import get_repo_status, scan_folder, verify_connection

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Repository — AutoGitBackup",
    page_icon="📂",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1b2a,#1a2744); border-right:1px solid #243354; }
section[data-testid="stSidebar"] * { color:#c8d6f0 !important; }
.badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.badge-success { background:#1a3a1f; color:#4caf50; border:1px solid #2e6b33; }
.badge-failed  { background:#3a1a1a; color:#f44336; border:1px solid #6b2e2e; }
.badge-info    { background:#1a2a3a; color:#4f8ef7; border:1px solid #2e4a6b; }
.info-box { background:linear-gradient(135deg,#141e30,#1c2d4a); border:1px solid #2a3f63; border-left:4px solid #4f8ef7; border-radius:8px; padding:16px 20px; margin:10px 0; }
h1 { color:#e8f0fe !important; font-weight:700 !important; }
h2 { color:#c8d6f0 !important; font-weight:600 !important; }
h3 { color:#a8c4e8 !important; font-weight:500 !important; }
div[data-testid="metric-container"] { background:linear-gradient(135deg,#141e30,#1c2d4a); border:1px solid #2a3f63; border-radius:12px; padding:18px 22px; }
div[data-testid="metric-container"] label { color:#8aabdd !important; font-size:0.8rem !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color:#e8f0fe !important; font-size:2rem !important; font-weight:700 !important; }
div.stButton > button { background:linear-gradient(135deg,#3b6fd4,#4f8ef7); color:white; border:none; border-radius:8px; padding:0.55rem 1.6rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📂 Repository Status")
st.markdown("*Live status of your local Git repository and GitHub connection.*")
st.divider()

cfg = load_config()

# ── Refresh Button ────────────────────────────────────────────────────────────
col_refresh, _ = st.columns([1, 4])
with col_refresh:
    refresh = st.button("🔄 Refresh Status", use_container_width=True)

if refresh or True:   # Always load on page visit
    if not Path(cfg.watch_folder).exists():
        st.warning(
            f"⚠️ Watch folder **`{cfg.watch_folder}`** does not exist yet.\n\n"
            "Go to ⚙️ **Settings** → *Folder & Repository* and set a valid path, "
            "or run a **Manual Backup** which will create it automatically."
        )
        st.stop()
    with st.spinner("Checking repository status..."):
        repo_status = get_repo_status(cfg.watch_folder)
        scan_result = scan_folder(cfg.watch_folder, cfg.ignore_patterns)

# ── Repo Existence Check ──────────────────────────────────────────────────────
if not repo_status["is_repo"]:
    st.warning(
        "⚠️ No Git repository found in the watch folder.\n\n"
        "Go to **Settings** to configure the watch folder and repository URL, "
        "then run a **Manual Backup** to initialise the repo."
    )
else:
    # ── Git Info Cards ─────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🌿 Branch", repo_status["branch"] or "—")
    with c2:
        st.metric("🔖 Latest Commit", repo_status["latest_commit_hash"] or "—")
    with c3:
        st.metric("📄 Pending Files", len(repo_status["pending_files"]))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Latest Commit Details ──────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"""
        <div class="info-box">
            <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Latest Commit</div>
            <div style="font-size:1rem;font-weight:600;color:#e8f0fe;">{repo_status['latest_commit_msg'] or 'No commits yet'}</div>
            <div style="font-size:0.78rem;color:#6a8ab0;margin-top:6px;">
                Hash: <code style="color:#4f8ef7;">{repo_status['latest_commit_hash'] or '—'}</code>
            </div>
            <div style="font-size:0.78rem;color:#6a8ab0;margin-top:4px;">
                Date: {repo_status['latest_commit_date'] or '—'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Clean up the remote URL for display (strip token)
        display_url = repo_status['remote_url']
        if "@" in display_url:
            display_url = "https://" + display_url.split("@")[-1]

        st.markdown(f"""
        <div class="info-box">
            <div style="font-size:0.75rem;color:#6a8ab0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Remote Origin</div>
            <div style="font-size:0.9rem;color:#4f8ef7;word-break:break-all;">{display_url or 'Not configured'}</div>
            <div style="font-size:0.78rem;color:#6a8ab0;margin-top:6px;">
                Branch: <code style="color:#4f8ef7;">{repo_status['branch'] or '—'}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Pending Files ──────────────────────────────────────────────────────────
    st.markdown("### 📝 Pending Changes")
    pending = repo_status["pending_files"]
    if pending:
        st.markdown(f"*{len(pending)} file(s) will be included in the next backup:*")
        for f in pending[:50]:
            st.markdown(
                f'<div style="font-size:0.85rem;color:#8aabdd;padding:3px 0;">'
                f'📄 <code style="color:#4f8ef7;">{f}</code></div>',
                unsafe_allow_html=True,
            )
        if len(pending) > 50:
            st.markdown(f"*... and {len(pending)-50} more files.*")
    else:
        st.success("✅ No pending changes. Repository is up to date.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Folder Scan Summary ───────────────────────────────────────────────────────
st.markdown("### 📁 Watch Folder Overview")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("📄 Total Files", scan_result["file_count"])
with c2:
    size_mb = scan_result["total_size"] / (1024 * 1024)
    st.metric("💾 Total Size", f"{size_mb:.2f} MB")
with c3:
    st.metric("🏷️ File Types", len(scan_result["extensions"]))

if scan_result["extensions"]:
    st.markdown("**File Type Breakdown:**")
    ext_items = sorted(scan_result["extensions"].items(), key=lambda x: -x[1])
    ext_cols = st.columns(min(len(ext_items), 6))
    for i, (ext, count) in enumerate(ext_items[:6]):
        with ext_cols[i % 6]:
            st.markdown(
                f'<div style="background:#1c2d4a;border:1px solid #2a3f63;border-radius:8px;padding:10px;text-align:center;">'
                f'<div style="font-size:1.1rem;font-weight:700;color:#4f8ef7;">{count}</div>'
                f'<div style="font-size:0.75rem;color:#8aabdd;">{ext}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

if scan_result["errors"]:
    with st.expander(f"⚠️ {len(scan_result['errors'])} inaccessible files"):
        for e in scan_result["errors"]:
            st.markdown(f'`{e}`')

st.markdown("<br>", unsafe_allow_html=True)

# ── Connection Test ───────────────────────────────────────────────────────────
st.markdown("### 🔌 GitHub Connection Test")
if cfg.repo_url:
    if st.button("🧪 Test Connection", use_container_width=False):
        with st.spinner("Testing GitHub connection..."):
            conn = verify_connection(cfg.repo_url, cfg.github_token)
        if conn["connected"]:
            st.success(f"✅ {conn['message']}")
        else:
            st.error(f"❌ {conn['message']}")
else:
    st.info("No repository URL configured. Go to **Settings** to add one.")
