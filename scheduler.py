"""
scheduler.py — Windows Task Scheduler Integration
===================================================
Creates, queries, and removes a Windows Task Scheduler task
that runs backup.py daily at the configured time (default 23:00).

Usage (from command line):
    python scheduler.py --create
    python scheduler.py --status
    python scheduler.py --delete
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from config import load_config

logger = logging.getLogger(__name__)

# Path to this project's backup.py
BASE_DIR = Path(__file__).parent.resolve()
BACKUP_SCRIPT = BASE_DIR / "backup.py"


# ── Internal Helpers ──────────────────────────────────────────────────────────
def _run_schtasks(args: list) -> subprocess.CompletedProcess:
    """Run schtasks.exe and return the CompletedProcess result."""
    cmd = ["schtasks"] + args
    logger.debug("schtasks command: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _python_exe() -> str:
    """Return the absolute path to the current Python executable."""
    return sys.executable


# ── Public API ────────────────────────────────────────────────────────────────
def create_task(task_name: str = None, backup_time: str = None) -> Dict:
    """
    Register a daily Task Scheduler task that runs backup.py.

    Parameters
    ----------
    task_name   : Override the task name from config
    backup_time : Override time from config (format HH:MM, 24-hour)

    Returns
    -------
    dict with 'success' bool and 'message' str
    """
    cfg = load_config()
    task_name = task_name or cfg.task_name
    backup_time = backup_time or cfg.backup_time

    python_exe = _python_exe()
    script_path = str(BACKUP_SCRIPT)

    # Build the action: pythonw.exe backup.py --now  (windowless)
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if not Path(pythonw).exists():
        pythonw = python_exe  # fallback to python.exe

    action = f'"{pythonw}" "{script_path}" --now'

    result = _run_schtasks([
        "/Create",
        "/F",                            # overwrite if exists
        "/TN", task_name,
        "/TR", action,
        "/SC", "DAILY",
        "/ST", backup_time,
        "/RL", "HIGHEST",               # run with highest privileges available
    ])

    if result.returncode == 0:
        logger.info("Task '%s' created successfully.", task_name)
        return {
            "success": True,
            "message": f"Task '{task_name}' scheduled daily at {backup_time}.",
        }
    else:
        logger.error("Failed to create task: %s", result.stderr)
        return {
            "success": False,
            "message": result.stderr.strip() or result.stdout.strip(),
        }


def delete_task(task_name: str = None) -> Dict:
    """
    Remove the Task Scheduler task.

    Returns dict with 'success' bool and 'message' str.
    """
    cfg = load_config()
    task_name = task_name or cfg.task_name

    result = _run_schtasks(["/Delete", "/TN", task_name, "/F"])

    if result.returncode == 0:
        logger.info("Task '%s' deleted.", task_name)
        return {"success": True, "message": f"Task '{task_name}' removed."}
    else:
        return {
            "success": False,
            "message": result.stderr.strip() or result.stdout.strip(),
        }


def get_task_status(task_name: str = None) -> Dict:
    """
    Query Task Scheduler for the task status.

    Returns
    -------
    dict:
        exists          : bool
        status          : str  (Ready | Running | Disabled | not found)
        next_run_time   : str
        last_run_time   : str
        last_result     : str
        raw             : str  (full schtasks output)
    """
    cfg = load_config()
    task_name = task_name or cfg.task_name

    result = _run_schtasks(["/Query", "/TN", task_name, "/FO", "LIST", "/V"])

    if result.returncode != 0:
        return {
            "exists": False,
            "status": "not found",
            "next_run_time": "—",
            "last_run_time": "—",
            "last_result": "—",
            "raw": result.stderr,
        }

    # Parse the verbose LIST output
    data = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()

    return {
        "exists": True,
        "status": data.get("Status", "Unknown"),
        "next_run_time": data.get("Next Run Time", "—"),
        "last_run_time": data.get("Last Run Time", "—"),
        "last_result": data.get("Last Result", "—"),
        "raw": result.stdout,
    }


def compute_next_run(backup_time: str = "23:00") -> str:
    """
    Compute the next scheduled run datetime string (local time).
    Used by the dashboard when the scheduler task isn't found.
    """
    try:
        h, m = map(int, backup_time.split(":"))
        now = datetime.now()
        candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "23:00 (today or tomorrow)"


# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Manage the AutoGitBackup Windows Task Scheduler task."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Create / register the task")
    group.add_argument("--delete", action="store_true", help="Remove the task")
    group.add_argument("--status", action="store_true", help="Show task status")

    args = parser.parse_args()

    if args.create:
        res = create_task()
        print(res["message"])
        sys.exit(0 if res["success"] else 1)

    elif args.delete:
        res = delete_task()
        print(res["message"])
        sys.exit(0 if res["success"] else 1)

    elif args.status:
        res = get_task_status()
        print(f"Exists      : {res['exists']}")
        print(f"Status      : {res['status']}")
        print(f"Next Run    : {res['next_run_time']}")
        print(f"Last Run    : {res['last_run_time']}")
        print(f"Last Result : {res['last_result']}")
