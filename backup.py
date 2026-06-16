"""
backup.py — Core Backup Orchestrator
======================================
This is the main entry point for the backup process. It:
  1. Loads configuration
  2. Scans the watch folder
  3. Initialises the git repo if needed
  4. Commits and pushes changes
  5. Logs the result to SQLite
  6. Sends desktop (and optionally email) notifications
  7. Writes to logs/app.log

Usage:
    python backup.py --now       # Run immediately
    python backup.py --daemon    # Run on a schedule (uses 'schedule' library)
    python backup.py --dry-run   # Scan files but don't commit/push
"""

import argparse
import logging
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

import schedule

from config import LOG_DIR, load_config
from database import init_db, log_backup
from github_manager import (
    commit_and_push,
    init_repo,
    scan_folder,
)

# ── Logging Setup ─────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("backup")


# ── Notification Helpers ──────────────────────────────────────────────────────
def _send_desktop_notification(title: str, message: str) -> None:
    """Send a Windows desktop (toast) notification via plyer."""
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="AutoGitBackup",
            timeout=8,
        )
    except Exception as exc:
        logger.debug("Desktop notification failed: %s", exc)


def _send_email_notification(subject: str, body: str, cfg) -> None:
    """Send an email notification via SMTP if configured."""
    if not cfg.email_notifications:
        return
    if not (cfg.smtp_user and cfg.smtp_password and cfg.notify_email):
        logger.debug("Email notification skipped — SMTP not configured.")
        return

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = cfg.smtp_user
        msg["To"] = cfg.notify_email

        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.starttls()
            server.login(cfg.smtp_user, cfg.smtp_password)
            server.sendmail(cfg.smtp_user, [cfg.notify_email], msg.as_string())
        logger.info("Email notification sent to %s", cfg.notify_email)
    except Exception as exc:
        logger.warning("Email notification failed: %s", exc)


# ── Core Backup Logic ─────────────────────────────────────────────────────────
def run_backup(dry_run: bool = False) -> dict:
    """
    Execute a complete backup cycle.

    Parameters
    ----------
    dry_run : If True, scan files but do not commit or push.

    Returns
    -------
    dict with keys: success, status, files_changed, message, duration
    """
    start_time = datetime.now(timezone.utc).astimezone()  # local time
    logger.info("=" * 60)
    logger.info("AutoGitBackup started at %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))

    cfg = load_config()
    init_db()

    watch_folder = cfg.watch_folder
    repo_url = cfg.repo_url
    branch = cfg.branch
    token = cfg.github_token

    # ── 1. Validate folder ────────────────────────────────────────────────────
    if not Path(watch_folder).exists():
        msg = f"Watch folder does not exist: {watch_folder}"
        logger.error(msg)
        _record_and_notify(
            cfg=cfg,
            start_time=start_time,
            status="failed",
            files=0,
            message="Daily Backup Attempt",
            error=msg,
            repo_url=repo_url,
        )
        return {"success": False, "status": "failed", "files_changed": 0,
                "message": msg, "duration": 0}

    # ── 2. Scan folder ────────────────────────────────────────────────────────
    logger.info("Scanning folder: %s", watch_folder)
    scan_result = scan_folder(watch_folder, cfg.ignore_patterns)
    logger.info("Files detected: %d (%.1f KB total)",
                scan_result["file_count"],
                scan_result["total_size"] / 1024)

    if dry_run:
        logger.info("[DRY RUN] Would commit %d files. Exiting without changes.",
                    scan_result["file_count"])
        return {
            "success": True, "status": "dry_run",
            "files_changed": scan_result["file_count"],
            "message": "Dry run — no changes made.",
            "duration": 0,
        }

    # ── 3. Initialise repo if needed ──────────────────────────────────────────
    init_result = init_repo(watch_folder, repo_url, branch, token)
    if not init_result["success"]:
        logger.error("Repo init failed: %s", init_result["message"])
        _record_and_notify(
            cfg=cfg, start_time=start_time, status="failed", files=0,
            message="Repo initialisation failed",
            error=init_result["message"], repo_url=repo_url,
        )
        return {"success": False, "status": "failed", "files_changed": 0,
                "message": init_result["message"],
                "duration": _elapsed(start_time)}

    # ── 4. Commit & push ──────────────────────────────────────────────────────
    commit_msg = cfg.commit_message_template.format(
        date=start_time.strftime("%Y-%m-%d")
    )
    logger.info("Committing with message: '%s'", commit_msg)

    push_result = commit_and_push(
        folder=watch_folder,
        commit_message=commit_msg,
        branch=branch,
        token=token,
        repo_url=repo_url,
    )

    duration = _elapsed(start_time)

    # ── 5. Determine status ───────────────────────────────────────────────────
    if push_result["message"] == "no_changes":
        status = "no_changes"
        files_changed = 0
        logger.info("No changes to commit.")
    elif push_result["success"]:
        status = "success"
        files_changed = push_result["files_changed"]
        logger.info("Backup successful! %d file(s) pushed. Hash: %s",
                    files_changed, push_result.get("commit_hash", ""))
    else:
        status = "failed"
        files_changed = 0
        logger.error("Backup failed: %s", push_result["message"])

    # ── 6. Log to DB + notify ─────────────────────────────────────────────────
    _record_and_notify(
        cfg=cfg,
        start_time=start_time,
        status=status,
        files=files_changed,
        message=commit_msg,
        error=push_result.get("message") if not push_result["success"] else None,
        repo_url=repo_url,
        duration=duration,
    )

    logger.info("Backup completed in %.2f seconds", duration)
    logger.info("=" * 60)

    return {
        "success": push_result["success"],
        "status": status,
        "files_changed": files_changed,
        "message": push_result["message"],
        "duration": duration,
    }


# ── Private Helpers ───────────────────────────────────────────────────────────
def _elapsed(start: datetime) -> float:
    return (datetime.now(timezone.utc).astimezone() - start).total_seconds()


def _record_and_notify(
    cfg, start_time: datetime, status: str, files: int,
    message: str, error: str = None, repo_url: str = "",
    duration: float = None,
) -> None:
    """Log to DB and send notifications."""
    # Extract repo name from URL
    repo_name = ""
    if repo_url:
        repo_name = repo_url.rstrip("/").split("/")[-1]
        owner = repo_url.rstrip("/").split("/")[-2] if "/" in repo_url else ""
        if owner:
            repo_name = f"{owner}/{repo_name}"

    # Database
    log_backup(
        backup_datetime=start_time,
        files_uploaded=files,
        commit_message=message,
        status=status,
        error_message=error,
        repository_name=repo_name,
        duration_seconds=duration,
    )

    # Desktop notification
    if cfg.desktop_notifications:
        if status == "success":
            _send_desktop_notification(
                "✅ AutoGitBackup — Success",
                f"Backed up {files} file(s) to {repo_name or 'GitHub'}",
            )
        elif status == "failed":
            _send_desktop_notification(
                "❌ AutoGitBackup — Failed",
                f"Backup failed: {error or 'Unknown error'}",
            )
        elif status == "no_changes":
            _send_desktop_notification(
                "ℹ️ AutoGitBackup",
                "No changes detected. Backup skipped.",
            )

    # Email
    subject_map = {
        "success": f"✅ AutoGitBackup: {files} file(s) pushed",
        "failed": f"❌ AutoGitBackup: Backup failed",
        "no_changes": "ℹ️ AutoGitBackup: No changes",
    }
    body = (
        f"Backup Report — {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Status      : {status}\n"
        f"Files       : {files}\n"
        f"Repository  : {repo_name}\n"
        f"Duration    : {f'{duration:.1f}s' if duration is not None else '—'}\n"
    )
    if error:
        body += f"Error       : {error}\n"
    _send_email_notification(subject_map.get(status, "AutoGitBackup"), body, cfg)


# ── Daemon Mode ───────────────────────────────────────────────────────────────
def run_daemon() -> None:
    """
    Keep process alive and run backup daily at the configured time.
    Use this only if you prefer not to use Windows Task Scheduler.
    """
    cfg = load_config()
    backup_time = cfg.backup_time  # e.g. "23:00"
    logger.info("Daemon mode: backup scheduled daily at %s", backup_time)
    schedule.every().day.at(backup_time).do(run_backup)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AutoGitBackup — automatic assignment backup to GitHub."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--now", action="store_true",
        help="Run a backup immediately and exit."
    )
    group.add_argument(
        "--daemon", action="store_true",
        help="Keep running and backup daily at the configured time."
    )
    group.add_argument(
        "--dry-run", action="store_true",
        help="Scan files without committing or pushing."
    )

    args = parser.parse_args()

    if args.now or not any([args.now, args.daemon, args.dry_run]):
        result = run_backup()
        sys.exit(0 if result["success"] else 1)

    elif args.daemon:
        run_daemon()

    elif args.dry_run:
        result = run_backup(dry_run=True)
        print(result["message"])
        sys.exit(0)
