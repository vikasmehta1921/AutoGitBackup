"""
pages/5_Manual_Backup.py — Manual Backup Trigger
==================================================
Allows users to trigger an immediate backup from the dashboard.
Streams live log output and shows a summary result card.
"""

import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, BASE_DIR
from database import get_all_backups

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Manual Backup — AutoGitBackup",
    page_icon="🚀",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1b2a,#1a2744); border-right:1px solid #243354; }
section[data-testid="stSidebar"] * { color:#c8d6f0 !important; }
.info-box { background:linear-gradient(135deg,#141e30,#1c2d4a); border:1px solid #2a3f63; border-left:4px solid #4f8ef7; border-radius:8px; padding:16px 20px; margin:10px 0; }
.result-success { background:linear-gradient(135deg,#0d2211,#1a3a1f); border:1px solid #2e6b33; border-left:4px solid #4caf50; border-radius:8px; padding:20px 24px; }
.result-failed  { background:linear-gradient(135deg,#220d0d,#3a1a1a); border:1px solid #6b2e2e; border-left:4px solid #f44336; border-radius:8px; padding:20px 24px; }
.result-nochange{ background:linear-gradient(135deg,#0d1522,#1a2a3a); border:1px solid #2e4a6b; border-left:4px solid #4f8ef7; border-radius:8px; padding:20px 24px; }
h1 { color:#e8f0fe !important; font-weight:700 !important; }
h2 { color:#c8d6f0 !important; font-weight:600 !important; }
h3 { color:#a8c4e8 !important; font-weight:500 !important; }
div.stButton > button { background:linear-gradient(135deg,#3b6fd4,#4f8ef7); color:white; border:none; border-radius:8px; padding:0.65rem 2rem; font-weight:700; font-size:1.05rem; letter-spacing:0.03em; transition:all 0.2s; box-shadow:0 4px 16px rgba(79,142,247,0.3); }
div.stButton > button:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(79,142,247,0.45); }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🚀 Manual Backup")
st.markdown("*Trigger an immediate backup without waiting for the scheduled run.*")
st.divider()

cfg = load_config()

# ── Pre-flight Checklist ──────────────────────────────────────────────────────
st.markdown("### ✅ Pre-flight Checklist")

checks_ok = True
col1, col2, col3 = st.columns(3)

with col1:
    folder_exists = Path(cfg.watch_folder).exists()
    if folder_exists:
        st.markdown(f"""
        <div class="info-box" style="border-left-color:#4caf50;">
            <div style="font-size:0.85rem;font-weight:600;color:#4caf50;">✅ Watch Folder</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">{cfg.watch_folder}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        checks_ok = False
        st.markdown(f"""
        <div class="info-box" style="border-left-color:#f44336;">
            <div style="font-size:0.85rem;font-weight:600;color:#f44336;">❌ Watch Folder Missing</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">{cfg.watch_folder} — not found</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    has_token = bool(cfg.github_token)
    if has_token:
        st.markdown("""
        <div class="info-box" style="border-left-color:#4caf50;">
            <div style="font-size:0.85rem;font-weight:600;color:#4caf50;">✅ GitHub Token</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">Token configured</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box" style="border-left-color:#ff9800;">
            <div style="font-size:0.85rem;font-weight:600;color:#ff9800;">⚠️ No GitHub Token</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">Set in Settings → Authentication</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    has_repo = bool(cfg.repo_url)
    if has_repo:
        st.markdown(f"""
        <div class="info-box" style="border-left-color:#4caf50;">
            <div style="font-size:0.85rem;font-weight:600;color:#4caf50;">✅ Repository URL</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">{cfg.repo_url.split('/')[-1] if cfg.repo_url else '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        checks_ok = False
        st.markdown("""
        <div class="info-box" style="border-left-color:#f44336;">
            <div style="font-size:0.85rem;font-weight:600;color:#f44336;">❌ No Repository URL</div>
            <div style="font-size:0.75rem;color:#6a8ab0;margin-top:4px;">Configure in Settings</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Backup Options ────────────────────────────────────────────────────────────
st.markdown("### ⚙️ Backup Options")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    dry_run = st.checkbox(
        "🧪 Dry Run (scan files but don't commit/push)",
        value=False,
        help="Use this to preview what would be backed up without making any changes.",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Trigger Button ────────────────────────────────────────────────────────────
col_btn, _ = st.columns([1, 2])
with col_btn:
    trigger = st.button(
        "🚀  Backup Now",
        disabled=not checks_ok,
        use_container_width=True,
    )

if not checks_ok:
    st.warning("⚠️ Please fix the issues above in **Settings** before running a backup.")

# ── Run Backup ────────────────────────────────────────────────────────────────
if trigger:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📡 Live Output")

    backup_script = BASE_DIR / "backup.py"
    cmd = [sys.executable, str(backup_script), "--now"]
    if dry_run:
        cmd = [sys.executable, str(backup_script), "--dry-run"]

    log_area = st.empty()
    log_lines = []

    start_ts = time.time()
    success = False
    last_line = ""

    try:
        with st.spinner("Running backup..."):
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(BASE_DIR),
            )

            for line in process.stdout:
                line = line.rstrip()
                log_lines.append(line)
                last_line = line
                log_area.code("\n".join(log_lines[-30:]), language=None)

            process.wait()
            success = process.returncode == 0

    except Exception as exc:
        st.error(f"Failed to launch backup process: {exc}")
        st.stop()

    duration = time.time() - start_ts

    # ── Result Summary ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Result")

    if dry_run:
        st.markdown(f"""
        <div class="result-nochange">
            <div style="font-size:1.3rem;font-weight:700;color:#4f8ef7;">🧪 Dry Run Complete</div>
            <div style="font-size:0.9rem;color:#8aabdd;margin-top:8px;">
                Folder scanned in {duration:.1f}s. No changes were committed.
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif success:
        # Fetch the latest DB record to get file count
        latest = get_all_backups(limit=1)
        files = latest[0]["files_uploaded"] if latest else "?"
        status_label = latest[0]["status"] if latest else "success"

        if status_label == "no_changes":
            st.markdown(f"""
            <div class="result-nochange">
                <div style="font-size:1.3rem;font-weight:700;color:#4f8ef7;">ℹ️ No Changes Detected</div>
                <div style="font-size:0.9rem;color:#8aabdd;margin-top:8px;">
                    All files are already up-to-date on GitHub. Duration: {duration:.1f}s
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-success">
                <div style="font-size:1.3rem;font-weight:700;color:#4caf50;">✅ Backup Successful!</div>
                <div style="font-size:0.9rem;color:#8aabdd;margin-top:8px;">
                    {files} file(s) pushed to GitHub in {duration:.1f}s.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
    else:
        st.markdown(f"""
        <div class="result-failed">
            <div style="font-size:1.3rem;font-weight:700;color:#f44336;">❌ Backup Failed</div>
            <div style="font-size:0.9rem;color:#8aabdd;margin-top:8px;">
                Duration: {duration:.1f}s. Check the log output above for details.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📄 Full Log Output"):
        st.code("\n".join(log_lines), language=None)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent Backups Mini Table ─────────────────────────────────────────────────
st.markdown("### 🕐 Recent Backups")
recent = get_all_backups(limit=5)
if recent:
    for r in recent:
        status = r["status"]
        icon = {"success": "✅", "failed": "❌", "no_changes": "ℹ️"}.get(status, "•")
        dt_str = r["backup_datetime"].strftime("%Y-%m-%d %H:%M") if r["backup_datetime"] else "—"
        st.markdown(
            f'<div style="font-size:0.83rem;color:#8aabdd;padding:5px 0;border-bottom:1px solid #1c2d4a;">'
            f'{icon} &nbsp; <b style="color:#e8f0fe;">{dt_str}</b> &nbsp;·&nbsp; {r["files_uploaded"]} file(s) &nbsp;·&nbsp; '
            f'<code style="color:#4f8ef7;">{status}</code>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("No backups yet.")
