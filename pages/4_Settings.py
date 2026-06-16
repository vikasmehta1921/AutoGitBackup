"""
pages/4_Settings.py — Application Settings
============================================
Allows users to configure:
  - Watch folder path
  - GitHub repository URL
  - Branch name
  - Backup time
  - GitHub token (stored in .env)
  - Desktop / email notification toggles
  - Windows Task Scheduler registration
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, save_config, save_env_var
from scheduler import create_task, delete_task, get_task_status

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Settings — AutoGitBackup",
    page_icon="⚙️",
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
h1 { color:#e8f0fe !important; font-weight:700 !important; }
h2 { color:#c8d6f0 !important; font-weight:600 !important; }
h3 { color:#a8c4e8 !important; font-weight:500 !important; }
div.stButton > button { background:linear-gradient(135deg,#3b6fd4,#4f8ef7); color:white; border:none; border-radius:8px; padding:0.55rem 1.6rem; font-weight:600; transition:all 0.2s; }
div.stButton > button:hover { transform:translateY(-1px); }
div[data-testid="stTextInput"] input { background:#141e30 !important; border:1px solid #2a3f63 !important; border-radius:8px !important; color:#e8f0fe !important; }
div[data-testid="stSelectbox"] > div { background:#141e30 !important; border:1px solid #2a3f63 !important; border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ⚙️ Settings")
st.markdown("*Configure AutoGitBackup behaviour and connections.*")
st.divider()

cfg = load_config()

# ── Section 1: Folder & Repository ───────────────────────────────────────────
st.markdown("### 📁 Folder & Repository")
with st.form("repo_settings_form"):
    col1, col2 = st.columns(2)
    with col1:
        watch_folder = st.text_input(
            "Watch Folder Path",
            value=cfg.watch_folder,
            help="Local folder to monitor and backup",
            placeholder=r"C:\Assignments",
        )
        branch = st.text_input(
            "Git Branch",
            value=cfg.branch,
            help="Target branch for pushes (usually 'main')",
        )
    with col2:
        repo_url = st.text_input(
            "GitHub Repository URL",
            value=cfg.repo_url,
            help="HTTPS URL — e.g. https://github.com/username/assignments",
            placeholder="https://github.com/username/repo",
        )
        backup_time = st.text_input(
            "Backup Time (24-hour HH:MM)",
            value=cfg.backup_time,
            help="Time to run the daily backup",
        )

    submitted_repo = st.form_submit_button("💾 Save Folder & Repository Settings", use_container_width=True)

if submitted_repo:
    # Validate folder path
    folder_path = Path(watch_folder)
    if not folder_path.exists():
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            st.info(f"📁 Folder created: {watch_folder}")
        except Exception as e:
            st.error(f"Could not create folder: {e}")

    # Validate time format
    try:
        h, m = map(int, backup_time.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except (ValueError, AssertionError):
        st.error("Invalid time format. Use HH:MM (e.g. 23:00)")
        st.stop()

    cfg.watch_folder = watch_folder
    cfg.repo_url = repo_url
    cfg.branch = branch
    cfg.backup_time = backup_time
    save_config(cfg)
    st.success("✅ Settings saved successfully!")

st.markdown("<br>", unsafe_allow_html=True)

# ── Section 2: GitHub Token ───────────────────────────────────────────────────
st.markdown("### 🔑 GitHub Authentication")
st.markdown("""
<div class="info-box">
    <div style="font-size:0.85rem;color:#8aabdd;line-height:1.8;">
        Your GitHub token is stored in the <code>.env</code> file and never committed to Git.<br>
        Generate a token at <a href="https://github.com/settings/tokens" target="_blank" style="color:#4f8ef7;">
        github.com/settings/tokens</a> with <b>repo</b> scope.
    </div>
</div>
""", unsafe_allow_html=True)

with st.form("token_form"):
    token_display = "•" * 20 if cfg.github_token else ""
    new_token = st.text_input(
        "GitHub Personal Access Token",
        value=token_display,
        type="password",
        help="Leave unchanged to keep the existing token",
    )
    save_token = st.form_submit_button("🔒 Save Token Securely", use_container_width=True)

if save_token:
    token_to_save = new_token.strip()
    if token_to_save and token_to_save != "•" * 20:
        save_env_var("GITHUB_TOKEN", token_to_save)
        st.success("✅ Token saved to .env file!")
    else:
        st.info("Token unchanged.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Section 3: Notifications ──────────────────────────────────────────────────
st.markdown("### 🔔 Notifications")
with st.form("notification_form"):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        desktop_notif = st.toggle(
            "Desktop Notifications",
            value=cfg.desktop_notifications,
            help="Show Windows toast notifications on backup success/failure",
        )
    with col_n2:
        email_notif = st.toggle(
            "Email Notifications",
            value=cfg.email_notifications,
            help="Send email after each backup (requires SMTP config in .env)",
        )

    if email_notif:
        st.markdown("*Configure SMTP credentials in your `.env` file:*")
        st.code(
            "SMTP_HOST=smtp.gmail.com\n"
            "SMTP_PORT=587\n"
            "SMTP_USER=your_email@gmail.com\n"
            "SMTP_PASSWORD=your_app_password\n"
            "NOTIFY_EMAIL=recipient@example.com",
            language="ini",
        )

    save_notif = st.form_submit_button("🔔 Save Notification Settings", use_container_width=True)

if save_notif:
    cfg.desktop_notifications = desktop_notif
    cfg.email_notifications = email_notif
    save_config(cfg)
    st.success("✅ Notification settings saved!")

st.markdown("<br>", unsafe_allow_html=True)

# ── Section 4: Windows Task Scheduler ────────────────────────────────────────
st.markdown("### 📅 Windows Task Scheduler")

task_info = get_task_status()
if task_info["exists"]:
    st.markdown(f"""
    <div class="info-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:1rem;font-weight:600;color:#4caf50;">✅ Task is scheduled</div>
                <div style="font-size:0.82rem;color:#8aabdd;margin-top:4px;">
                    Status: {task_info['status']} &nbsp;·&nbsp; Next run: {task_info['next_run_time']}
                </div>
                <div style="font-size:0.78rem;color:#6a8ab0;margin-top:2px;">
                    Last run: {task_info['last_run_time']} &nbsp;·&nbsp; Result: {task_info['last_result']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 Re-register Task", use_container_width=True):
            result = create_task(backup_time=cfg.backup_time)
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
    with col_s2:
        if st.button("🗑️ Remove Task", use_container_width=True):
            result = delete_task()
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])
else:
    st.markdown("""
    <div class="info-box" style="border-left-color:#ff9800;">
        <div style="font-size:1rem;font-weight:600;color:#ff9800;">⚠️ Task not scheduled</div>
        <div style="font-size:0.82rem;color:#8aabdd;margin-top:4px;">
            Click the button below to register a daily backup at {time}.
        </div>
    </div>
    """.replace("{time}", cfg.backup_time), unsafe_allow_html=True)

    if st.button("📅 Register Scheduled Task", use_container_width=False):
        result = create_task(backup_time=cfg.backup_time)
        if result["success"]:
            st.success(result["message"])
            st.rerun()
        else:
            st.error(result["message"])
            st.markdown("**Note:** Task Scheduler registration may require Administrator privileges.")
            st.code(
                f'schtasks /Create /TN "{cfg.task_name}" /TR "pythonw.exe backup.py --now" '
                f'/SC DAILY /ST {cfg.backup_time} /F',
                language="powershell",
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── Section 5: Danger Zone ────────────────────────────────────────────────────
st.markdown("### ⚠️ Danger Zone")
with st.expander("🗑️ Clear All Backup Records"):
    st.warning("This will permanently delete all backup history from the database.")
    confirm = st.text_input("Type **DELETE** to confirm", key="danger_confirm")
    if st.button("🗑️ Clear All Records", type="secondary"):
        if confirm.strip().upper() == "DELETE":
            from database import clear_all_backups
            count = clear_all_backups()
            st.success(f"Deleted {count} backup record(s).")
        else:
            st.error("Type DELETE to confirm.")
