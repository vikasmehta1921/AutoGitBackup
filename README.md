# 🔄 AutoGitBackup

> **Automatic Assignment Backup to GitHub** — Python · SQLite · Streamlit · Windows Task Scheduler

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green?logo=sqlite)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

---

## 📖 Overview

AutoGitBackup is a complete automation system that:

- 📁 **Monitors** a local folder (`C:\Assignments` by default) for new and modified files
- 🔄 **Backs up automatically** every day at 11:00 PM via Windows Task Scheduler
- 📊 **Logs everything** to an SQLite database (backup time, files, status, errors)
- 🌐 **Provides a dashboard** via Streamlit with history, charts, and manual trigger
- 🔔 **Notifies you** via desktop toast and optional email

---

## ✨ Features

| Feature | Details |
|---|---|
| 📁 Folder Monitoring | Recursive scan, ignore patterns, file metadata |
| 🔄 Auto Git Backup | `git add`, `commit`, `push` with token auth |
| 🗄️ SQLite Logging | Every run logged with timestamp, status, duration |
| 📅 Task Scheduler | Registers Windows Task Scheduler entry automatically |
| 🌐 Streamlit Dashboard | 5-page professional dark-theme UI |
| 🔔 Desktop Notifications | Windows toast via `plyer` |
| 📧 Email Alerts | Optional SMTP notifications |
| 📊 Charts | Daily activity + status distribution (Plotly) |
| ⬇️ CSV Export | Download full backup history |
| 🧪 Dry Run Mode | Preview without committing |

---

## 📁 Project Structure

```
AutoGitBackup/
├── app.py                    # Streamlit dashboard entry point (Home)
├── backup.py                 # Core backup orchestrator (CLI)
├── database.py               # SQLAlchemy ORM + CRUD helpers
├── scheduler.py              # Windows Task Scheduler integration
├── github_manager.py         # Git operations + folder scanner
├── config.py                 # Settings loader (.env + settings.json)
├── requirements.txt          # Python dependencies
├── README.md
├── backup_logs.db            # SQLite database (auto-created)
├── .env.example              # Template for secrets
├── .gitignore
│
├── config/
│   └── settings.json         # App configuration
│
├── logs/
│   └── app.log               # Application log file
│
├── pages/                    # Streamlit multi-page app
│   ├── 1_Home.py
│   ├── 2_History.py          # Backup history + charts + CSV export
│   ├── 3_Repository.py       # Git repo status + connection test
│   ├── 4_Settings.py         # Configure folder, repo, token, scheduler
│   └── 5_Manual_Backup.py    # Trigger immediate backup
│
└── tests/
    ├── test_database.py      # Database unit tests
    └── test_backup.py        # Backup + git operation tests
```

---

## 🚀 Installation

### Prerequisites

| Requirement | Version | Download |
|---|---|---|
| Python | 3.9+ | [python.org](https://python.org) |
| Git | Any recent | [git-scm.com](https://git-scm.com) |
| GitHub Account | — | [github.com](https://github.com) |

### Step 1 — Clone or download this project

```powershell
# Navigate to the project folder
cd "C:\Users\vinay\OneDrive\Desktop\short project\AutoGitBackup"
```

### Step 2 — Create a virtual environment (recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

```powershell
# Copy the template
copy .env.example .env

# Open .env and add your GitHub token
notepad .env
```

Your `.env` file should look like:

```ini
GITHUB_TOKEN=ghp_your_token_here
```

### Step 5 — Configure settings

Open the Streamlit dashboard (see below) and go to ⚙️ **Settings**, or directly edit `config/settings.json`:

```json
{
  "watch_folder": "C:\\Assignments",
  "repo_url": "https://github.com/yourusername/assignments",
  "branch": "main",
  "backup_time": "23:00"
}
```

### Step 6 — Launch the dashboard

```powershell
streamlit run app.py
```

Visit **http://localhost:8501** in your browser.

---

## 🔑 GitHub Setup

### Generating a Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name: `AutoGitBackup`
4. Set expiration: `No expiration` (or your preference)
5. Check the **`repo`** scope (full control of private repositories)
6. Click **Generate token**
7. Copy the token and paste it in `.env` or the Settings page

### Creating a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create a new **private** or public repository (e.g., `assignments`)
3. Copy the HTTPS URL: `https://github.com/yourusername/assignments`
4. Paste it in Settings → Repository URL

---

## 📅 Windows Task Scheduler Setup

### Option A — Via Dashboard (Recommended)

1. Open the dashboard → ⚙️ **Settings**
2. Scroll to "Windows Task Scheduler"
3. Click **"Register Scheduled Task"**
4. The task will run `backup.py --now` daily at your configured time

### Option B — Manual (PowerShell as Administrator)

```powershell
schtasks /Create /TN "Assignment Auto Backup" `
  /TR "pythonw.exe C:\path\to\AutoGitBackup\backup.py --now" `
  /SC DAILY /ST 23:00 /F /RL HIGHEST
```

### Verify the task

```powershell
schtasks /Query /TN "Assignment Auto Backup" /FO LIST /V
```

---

## 💻 CLI Usage

```powershell
# Run backup immediately
python backup.py --now

# Dry run (scan only, no commits)
python backup.py --dry-run

# Run as daemon (no Task Scheduler needed)
python backup.py --daemon

# Manage Task Scheduler
python scheduler.py --create
python scheduler.py --status
python scheduler.py --delete
```

---

## 🗄️ Database Schema

**Table: `backups`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `backup_datetime` | DATETIME | When the backup started (UTC) |
| `files_uploaded` | INTEGER | Files committed in this run |
| `commit_message` | TEXT | Git commit message |
| `status` | TEXT | `success` \| `failed` \| `no_changes` |
| `error_message` | TEXT | Exception text (if failed) |
| `repository_name` | TEXT | `owner/repo` format |
| `duration_seconds` | REAL | Elapsed seconds |

Query examples:

```sql
-- Last 10 backups
SELECT * FROM backups ORDER BY backup_datetime DESC LIMIT 10;

-- Failed backups with errors
SELECT backup_datetime, error_message FROM backups WHERE status = 'failed';

-- Total files backed up
SELECT SUM(files_uploaded) FROM backups WHERE status = 'success';
```

---

## 🧪 Running Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run database tests only
python -m unittest tests/test_database.py -v

# Run backup tests only
python -m unittest tests/test_backup.py -v
```

---

## 🔔 Notification Setup

### Desktop Notifications
Enabled by default. Uses `plyer` — works on Windows 10/11.

### Email Notifications
Add to `.env`:

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
NOTIFY_EMAIL=recipient@example.com
```

> **Gmail users**: Use an [App Password](https://myaccount.google.com/apppasswords), not your regular password.

---

## 🔒 Security

- GitHub token stored in `.env` (excluded from git via `.gitignore`)
- Token injected into HTTPS URLs at runtime — never written to `settings.json`
- Input validation on all Settings page forms
- Repository URL validation before pushing

---

## 🛣️ Future Scope

- ☁️ Google Drive / OneDrive / Dropbox integration
- 🤖 AI-based file categorization
- 📱 Mobile push notifications
- 🐧 Linux cron job support
- 👥 Team collaboration & multi-user support
- 🔄 Restore previous file versions from GitHub

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

*Built with Python, SQLAlchemy, Streamlit, and Git.*
