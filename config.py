"""
config.py — Configuration Manager
===================================
Loads settings from config/settings.json and environment variables (.env).
Provides a typed AppConfig dataclass and helper to persist settings.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"
ENV_FILE = BASE_DIR / ".env"
LOG_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "backup_logs.db"

# Load .env file if it exists
load_dotenv(ENV_FILE)


def _get_secret(key: str, default: str = "") -> str:
    """
    Read a secret from Streamlit Cloud secrets (st.secrets) if available,
    otherwise fall back to environment variables loaded from .env.
    This allows the same code to run locally and on Streamlit Community Cloud.
    """
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


# ── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class AppConfig:
    """Typed representation of the application configuration."""

    watch_folder: str = r"C:\Assignments"
    repo_url: str = ""
    branch: str = "main"
    backup_time: str = "23:00"
    task_name: str = "Assignment Auto Backup"
    commit_message_template: str = "Daily Backup - {date}"
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "*.tmp", "~$*", "*.swp", "*.bak",
        "Thumbs.db", ".DS_Store", "desktop.ini", "__pycache__"
    ])
    email_notifications: bool = False
    desktop_notifications: bool = True
    multiple_repos: List[str] = field(default_factory=list)

    # Secrets (from st.secrets on cloud, from .env locally)
    @property
    def github_token(self) -> str:
        return _get_secret("GITHUB_TOKEN")

    @property
    def smtp_host(self) -> str:
        return _get_secret("SMTP_HOST", "smtp.gmail.com")

    @property
    def smtp_port(self) -> int:
        return int(_get_secret("SMTP_PORT", "587"))

    @property
    def smtp_user(self) -> str:
        return _get_secret("SMTP_USER")

    @property
    def smtp_password(self) -> str:
        return _get_secret("SMTP_PASSWORD")

    @property
    def notify_email(self) -> str:
        return _get_secret("NOTIFY_EMAIL")


# ── Loader ───────────────────────────────────────────────────────────────────
def load_config() -> AppConfig:
    """
    Load configuration from settings.json.
    Creates the file with defaults if it does not exist.
    """
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not SETTINGS_FILE.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build config — only pick known keys to avoid errors on schema changes
    cfg = AppConfig()
    for key, value in data.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)

    return cfg


def save_config(cfg: AppConfig) -> None:
    """
    Persist configuration back to settings.json.
    Secrets (tokens, passwords) are intentionally excluded.
    """
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(cfg)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_env_var(key: str, value: str) -> None:
    """
    Write or update a single key in the .env file.
    Used by the Settings page to persist the GitHub token securely.
    """
    env_path = ENV_FILE
    lines = []

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Reload env so the current process picks it up immediately
    os.environ[key] = value
