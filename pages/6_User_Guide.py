"""
6_User_Guide.py — Step-by-Step Setup Guide
============================================
A comprehensive guide for new users to set up and use AutoGitBackup.
"""

import streamlit as st

st.set_page_config(
    page_title="User Guide — AutoGitBackup",
    page_icon="📖",
    layout="wide",
)

# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1b2a,#1a2744); border-right:1px solid #243354; }
section[data-testid="stSidebar"] * { color:#c8d6f0 !important; }
.step-box {
    background: linear-gradient(135deg, #141e30, #1c2d4a);
    border: 1px solid #2a3f63;
    border-left: 4px solid #4f8ef7;
    border-radius: 10px;
    padding: 20px 24px;
    margin: 12px 0;
}
.step-number {
    display: inline-block;
    background: linear-gradient(135deg, #3b6fd4, #4f8ef7);
    color: white;
    width: 32px; height: 32px;
    border-radius: 50%;
    text-align: center;
    line-height: 32px;
    font-weight: 700;
    font-size: 0.9rem;
    margin-right: 10px;
}
.highlight {
    background: #1a2744;
    border: 1px solid #2a3f63;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("# 📖 User Guide")
st.markdown("*Complete step-by-step guide to set up AutoGitBackup on your computer*")
st.divider()

# ── Prerequisites ─────────────────────────────────────────────────────────────
st.markdown("## 📋 Prerequisites")
st.markdown("""
Before you begin, make sure you have the following installed on your **Windows** computer:
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="step-box">
        <h4>🐍 Python 3.10+</h4>
        <p>Download from <a href="https://python.org/downloads" target="_blank">python.org</a></p>
        <p style="font-size:0.8rem; color:#8aabdd;">✅ Check "Add to PATH" during installation</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="step-box">
        <h4>📦 Git</h4>
        <p>Download from <a href="https://git-scm.com/downloads" target="_blank">git-scm.com</a></p>
        <p style="font-size:0.8rem; color:#8aabdd;">✅ Use default settings during installation</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="step-box">
        <h4>🐙 GitHub Account</h4>
        <p>Sign up at <a href="https://github.com/join" target="_blank">github.com</a></p>
        <p style="font-size:0.8rem; color:#8aabdd;">✅ Free account is enough</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Step-by-Step Guide ────────────────────────────────────────────────────────
st.markdown("## 🚀 Setup Steps")

# Step 1
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">1</span> Clone the Repository</h3>
    <p>Open <b>Command Prompt</b> or <b>PowerShell</b> and run:</p>
</div>
""", unsafe_allow_html=True)

st.code("""git clone https://github.com/vikasmehta1921/AutoGitBackup.git
cd AutoGitBackup""", language="powershell")

# Step 2
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">2</span> Install Dependencies</h3>
    <p>Install all required Python packages with one command:</p>
</div>
""", unsafe_allow_html=True)

st.code("pip install -r requirements.txt", language="powershell")

# Step 3
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">3</span> Create a GitHub Personal Access Token</h3>
    <p>You need a token so the app can push files to your GitHub repo automatically.</p>
</div>
""", unsafe_allow_html=True)

with st.expander("📝 How to create a GitHub Token (click to expand)", expanded=False):
    st.markdown("""
    1. Go to **[github.com/settings/tokens](https://github.com/settings/tokens)**
    2. Click **"Generate new token"** → **"Generate new token (classic)"**
    3. Fill in:
       - **Note:** `AutoGitBackup`
       - **Expiration:** `No expiration` (or 90 days if you prefer)
       - **Scopes:** ✅ Check **`repo`** (full control of repositories)
    4. Click **"Generate token"** at the bottom
    5. **Copy the token immediately!** (starts with `ghp_...`)

    > ⚠️ **You can only see the token ONCE!** Save it somewhere safe before closing the page.
    """)

# Step 4
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">4</span> Configure Your Token</h3>
    <p>Create a <code>.env</code> file in the project folder with your token:</p>
</div>
""", unsafe_allow_html=True)

st.code("""# Copy .env.example to .env
copy .env.example .env

# Then open .env in any text editor and add your token:
# GITHUB_TOKEN=ghp_your_token_here""", language="powershell")

st.warning("⚠️ **Never share your token publicly or commit the `.env` file to GitHub!** The `.gitignore` already protects it.")

# Step 5
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">5</span> Create Your GitHub Repository</h3>
    <p>Create a <b>new repository</b> on GitHub where your assignments will be backed up.</p>
</div>
""", unsafe_allow_html=True)

with st.expander("📝 How to create the repository (click to expand)", expanded=False):
    st.markdown("""
    1. Go to **[github.com/new](https://github.com/new)**
    2. Fill in:
       - **Repository name:** `my-assignments` (or any name you like)
       - **Visibility:** `Private` (keeps your files private)
       - ✅ Check **"Add a README file"**
    3. Click **"Create repository"**
    4. Copy the URL — e.g., `https://github.com/yourusername/my-assignments.git`
    """)

# Step 6
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">6</span> Launch the Dashboard</h3>
    <p>Start the Streamlit dashboard to configure everything visually:</p>
</div>
""", unsafe_allow_html=True)

st.code("streamlit run app.py", language="powershell")

st.info("The dashboard will open at **http://localhost:8501** in your browser.")

# Step 7
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">7</span> Configure Settings in Dashboard</h3>
    <p>Go to the <b>⚙️ Settings</b> page in the sidebar and configure:</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="highlight">
        <h4>📁 Folder & Repository</h4>
        <ul>
            <li><b>Watch Folder:</b> Path to your assignments folder<br>
                <code>C:\\Users\\YourName\\Assignments</code></li>
            <li><b>Repository URL:</b> Your GitHub repo URL<br>
                <code>https://github.com/you/my-assignments.git</code></li>
            <li><b>Branch:</b> <code>main</code></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="highlight">
        <h4>🔐 Security & Schedule</h4>
        <ul>
            <li><b>GitHub Token:</b> Paste your token → click <b>Save Token</b></li>
            <li><b>Backup Time:</b> <code>23:00</code> (11 PM daily)</li>
            <li>Click <b>"Register Scheduled Task"</b> to enable auto-backup</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Step 8
st.markdown("""
<div class="step-box">
    <h3><span class="step-number">8</span> Run Your First Backup</h3>
    <p>Go to <b>🚀 Manual Backup</b> in the sidebar and click <b>"Backup Now"</b></p>
</div>
""", unsafe_allow_html=True)

st.success("🎉 **That's it!** Your assignments will now be automatically backed up to GitHub every day at your scheduled time.")

st.divider()

# ── CLI Usage ─────────────────────────────────────────────────────────────────
st.markdown("## 💻 Command Line Usage")
st.markdown("You can also use AutoGitBackup from the terminal without the dashboard:")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Backup Commands")
    st.code("""# Run backup immediately
python backup.py --now

# Dry run (preview without pushing)
python backup.py --dry-run

# Run as a background daemon
python backup.py --daemon""", language="powershell")

with col2:
    st.markdown("### Scheduler Commands")
    st.code("""# Create daily scheduled task
python scheduler.py --create

# Check scheduler status
python scheduler.py --status

# Remove scheduled task
python scheduler.py --delete""", language="powershell")

st.divider()

# ── FAQ ───────────────────────────────────────────────────────────────────────
st.markdown("## ❓ Frequently Asked Questions")

with st.expander("What file types are backed up?"):
    st.markdown("""
    **All files** in your watch folder are backed up, including:
    - 📄 PDFs, Word documents (`.pdf`, `.docx`, `.doc`)
    - 💻 Code files (`.py`, `.java`, `.cpp`, `.js`, `.html`)
    - 📊 Spreadsheets (`.xlsx`, `.csv`)
    - 📝 Notes and text files (`.txt`, `.md`)
    - 🖼️ Images (`.png`, `.jpg`, `.gif`)

    **Ignored files** (configurable): `*.tmp`, `~$*`, `*.swp`, `Thumbs.db`, `__pycache__`
    """)

with st.expander("What happens if I have no internet?"):
    st.markdown("""
    The backup will **still commit locally**. When you're back online, the next backup
    will push all pending commits to GitHub automatically.
    """)

with st.expander("Can I back up multiple folders?"):
    st.markdown("""
    Yes! Go to **⚙️ Settings** → **Multiple Repositories** and add additional
    repository URLs. Each folder gets its own backup schedule.
    """)

with st.expander("Is my data safe?"):
    st.markdown("""
    - ✅ Your GitHub token is stored in a local `.env` file, **never uploaded**
    - ✅ Your assignment files go to **your own GitHub repo** (can be private)
    - ✅ The `.gitignore` prevents sensitive files from being shared
    - ✅ Every backup is logged in a local SQLite database
    """)

with st.expander("How do I stop auto-backups?"):
    st.markdown("""
    **Option 1 — Dashboard:** Go to ⚙️ Settings → click **"Remove Scheduled Task"**

    **Option 2 — Terminal:**
    ```
    python scheduler.py --delete
    ```
    """)

with st.expander("Can I use this on Mac or Linux?"):
    st.markdown("""
    The core backup system works on all platforms. However, the **Windows Task Scheduler**
    integration is Windows-only. On Mac/Linux, you can use `cron` instead:
    ```
    # Add to crontab (runs daily at 11 PM)
    0 23 * * * cd /path/to/AutoGitBackup && python backup.py --now
    ```
    """)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0 5px 0; font-size:0.75rem; color:#3a5a8a;">
    Built with ❤️ by <b>Vikas</b> &nbsp;·&nbsp; AutoGitBackup v1.0 &nbsp;·&nbsp; Python · SQLite · Streamlit
</div>
""", unsafe_allow_html=True)
