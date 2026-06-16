"""
github_manager.py — Git / GitHub Operations
=============================================
Handles:
  - Folder scanning (new / modified files, ignore patterns)
  - Git repository initialisation
  - Commit and push to remote
  - Repository status queries
  - GitHub API calls (optional: repo creation, connection test)
"""

import fnmatch
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Ignore Logic ─────────────────────────────────────────────────────────────
def _is_ignored(path: Path, patterns: List[str]) -> bool:
    """Return True if the file matches any ignore pattern."""
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
        if fnmatch.fnmatch(str(path), pattern):
            return True
    return False


# ── Folder Scanner ────────────────────────────────────────────────────────────
def scan_folder(folder: str, ignore_patterns: Optional[List[str]] = None) -> Dict:
    """
    Recursively scan *folder* and return metadata about all files.

    Returns
    -------
    dict:
        files       : list of absolute path strings
        total_size  : total size in bytes
        file_count  : number of files
        extensions  : dict of {extension: count}
        errors      : list of paths that raised permission errors
    """
    if ignore_patterns is None:
        ignore_patterns = [
            "*.tmp", "~$*", "*.swp", "*.bak",
            "Thumbs.db", ".DS_Store", "desktop.ini",
            "__pycache__", "*.pyc",
        ]

    folder_path = Path(folder)
    if not folder_path.exists():
        logger.warning("Watch folder does not exist: %s", folder)
        return {
            "files": [], "total_size": 0,
            "file_count": 0, "extensions": {}, "errors": [],
        }

    files: List[str] = []
    total_size: int = 0
    extensions: Dict[str, int] = {}
    errors: List[str] = []

    for root, dirs, filenames in os.walk(folder_path):
        # Skip hidden directories and common junk dirs
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in {"__pycache__", "node_modules", ".git", "venv", ".venv"}
        ]

        for filename in filenames:
            file_path = Path(root) / filename

            if _is_ignored(file_path, ignore_patterns):
                continue

            try:
                stat = file_path.stat()
                total_size += stat.st_size
                ext = file_path.suffix.lower() or "(no extension)"
                extensions[ext] = extensions.get(ext, 0) + 1
                files.append(str(file_path))
            except PermissionError:
                errors.append(str(file_path))
                logger.warning("Permission denied: %s", file_path)

    logger.info("Scanned %d files in %s", len(files), folder)
    return {
        "files": files,
        "total_size": total_size,
        "file_count": len(files),
        "extensions": extensions,
        "errors": errors,
    }


# ── Git Helpers ───────────────────────────────────────────────────────────────
def _run_git(args: List[str], cwd: str) -> Tuple[int, str, str]:
    """
    Run a git sub-command and return (returncode, stdout, stderr).
    Never raises — caller decides how to handle errors.
    """
    cmd = ["git"] + args
    logger.debug("Running: %s in %s", " ".join(cmd), cwd)
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        msg = "Git is not installed or not in PATH."
        logger.error(msg)
        return 1, "", msg


def is_git_repo(folder: str) -> bool:
    """Return True if *folder* is inside a git repository."""
    code, _, _ = _run_git(["rev-parse", "--git-dir"], folder)
    return code == 0


def init_repo(folder: str, repo_url: str, branch: str = "main", token: str = "") -> Dict:
    """
    Initialise a git repo in *folder* if not already one.
    Adds the remote origin and sets the default branch.

    Returns dict with 'success' bool and 'message' string.
    """
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    if not is_git_repo(folder):
        code, out, err = _run_git(["init", "-b", branch], folder)
        if code != 0:
            # Older git versions may not support -b
            _run_git(["init"], folder)
            _run_git(["checkout", "-b", branch], folder)
        logger.info("Initialised git repo at %s", folder)

    # Configure remote
    if repo_url:
        # Inject token into HTTPS URL for authentication
        auth_url = _inject_token(repo_url, token)

        # Remove existing origin if present
        _run_git(["remote", "remove", "origin"], folder)
        code, out, err = _run_git(["remote", "add", "origin", auth_url], folder)
        if code != 0:
            return {"success": False, "message": f"Failed to add remote: {err}"}
        logger.info("Remote origin set to %s", repo_url)

    return {"success": True, "message": "Repository initialised successfully."}


def _inject_token(url: str, token: str) -> str:
    """Inject a GitHub token into an HTTPS URL for authentication."""
    if not token:
        return url
    if url.startswith("https://"):
        return url.replace("https://", f"https://{token}@")
    return url


def commit_and_push(
    folder: str,
    commit_message: str,
    branch: str = "main",
    token: str = "",
    repo_url: str = "",
) -> Dict:
    """
    Stage all changes, commit, and push to the remote.

    Returns
    -------
    dict:
        success         : bool
        files_changed   : int
        commit_hash     : str | None
        message         : str
        stdout          : str
        stderr          : str
    """
    # 1. Configure git user if not already set (needed in fresh environments)
    _run_git(["config", "user.email", "autogitbackup@local"], folder)
    _run_git(["config", "user.name", "AutoGitBackup"], folder)

    # 2. Inject token into remote URL
    if repo_url and token:
        auth_url = _inject_token(repo_url, token)
        _run_git(["remote", "set-url", "origin", auth_url], folder)

    # 3. Stage everything
    code, out, err = _run_git(["add", "."], folder)
    if code != 0:
        return {
            "success": False, "files_changed": 0,
            "commit_hash": None,
            "message": f"git add failed: {err}",
            "stdout": out, "stderr": err,
        }

    # 4. Check if there's anything to commit
    code, status_out, _ = _run_git(["status", "--porcelain"], folder)
    if not status_out:
        logger.info("No changes to commit.")
        return {
            "success": True, "files_changed": 0,
            "commit_hash": None,
            "message": "no_changes",
            "stdout": "", "stderr": "",
        }

    files_changed = len([l for l in status_out.splitlines() if l.strip()])

    # 5. Commit
    code, out, err = _run_git(["commit", "-m", commit_message], folder)
    if code != 0:
        return {
            "success": False, "files_changed": 0,
            "commit_hash": None,
            "message": f"git commit failed: {err}",
            "stdout": out, "stderr": err,
        }

    # 6. Get commit hash
    _, commit_hash, _ = _run_git(["rev-parse", "--short", "HEAD"], folder)

    # 7. Push
    code, out, err = _run_git(["push", "-u", "origin", branch], folder)
    if code != 0:
        return {
            "success": False, "files_changed": files_changed,
            "commit_hash": commit_hash,
            "message": f"git push failed: {err}",
            "stdout": out, "stderr": err,
        }

    logger.info("Pushed commit %s (%d files)", commit_hash, files_changed)
    return {
        "success": True, "files_changed": files_changed,
        "commit_hash": commit_hash,
        "message": f"Successfully pushed {files_changed} file(s) — {commit_hash}",
        "stdout": out, "stderr": err,
    }


# ── Repository Status ─────────────────────────────────────────────────────────
def get_repo_status(folder: str) -> Dict:
    """
    Return current status of the git repository in *folder*.

    Returns
    -------
    dict:
        is_repo             : bool
        branch              : str
        latest_commit_hash  : str
        latest_commit_msg   : str
        latest_commit_date  : str
        pending_files       : list of str
        remote_url          : str
        ahead_behind        : str
    """
    if not is_git_repo(folder):
        return {
            "is_repo": False,
            "branch": "", "latest_commit_hash": "",
            "latest_commit_msg": "No repository found",
            "latest_commit_date": "",
            "pending_files": [], "remote_url": "", "ahead_behind": "",
        }

    _, branch, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], folder)
    _, commit_hash, _ = _run_git(["rev-parse", "--short", "HEAD"], folder)
    _, commit_msg, _ = _run_git(
        ["log", "-1", "--pretty=%s"], folder)
    _, commit_date, _ = _run_git(
        ["log", "-1", "--pretty=%ci"], folder)
    _, remote_url, _ = _run_git(["remote", "get-url", "origin"], folder)
    _, status_raw, _ = _run_git(["status", "--porcelain"], folder)
    _, ahead_behind, _ = _run_git(
        ["status", "--porcelain=v2", "--branch"], folder)

    pending = [l[3:] for l in status_raw.splitlines() if l.strip()]

    return {
        "is_repo": True,
        "branch": branch,
        "latest_commit_hash": commit_hash,
        "latest_commit_msg": commit_msg,
        "latest_commit_date": commit_date,
        "pending_files": pending,
        "remote_url": remote_url,
        "ahead_behind": ahead_behind,
    }


def verify_connection(repo_url: str, token: str = "") -> Dict:
    """
    Test whether the GitHub remote is reachable and we have push access.
    Uses 'git ls-remote' which is lightweight and doesn't modify anything.
    """
    auth_url = _inject_token(repo_url, token)
    code, out, err = _run_git(["ls-remote", "--heads", auth_url], [])

    # _run_git needs a cwd — use a temp approach
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", auth_url],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            return {"connected": True, "message": "Connection successful."}
        else:
            return {"connected": False, "message": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"connected": False, "message": "Connection timed out."}
    except Exception as e:
        return {"connected": False, "message": str(e)}
