"""
tests/test_backup.py — Backup & Git Operation Tests
=====================================================
Tests for folder scanning, git helpers, and the backup orchestrator
using mocks to avoid touching real git repos or the network.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestScanFolder(unittest.TestCase):
    """Test the folder scanner with a real temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_file(self, name: str, content: str = "hello"):
        p = Path(self.tmpdir) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def test_empty_folder(self):
        from github_manager import scan_folder
        result = scan_folder(self.tmpdir)
        self.assertEqual(result["file_count"], 0)
        self.assertEqual(result["total_size"], 0)

    def test_single_file(self):
        from github_manager import scan_folder
        self._create_file("notes.txt", "content")
        result = scan_folder(self.tmpdir)
        self.assertEqual(result["file_count"], 1)
        self.assertIn(".txt", result["extensions"])

    def test_multiple_files(self):
        from github_manager import scan_folder
        self._create_file("a.py", "x = 1")
        self._create_file("b.pdf", "pdf")
        self._create_file("c.docx", "doc")
        result = scan_folder(self.tmpdir)
        self.assertEqual(result["file_count"], 3)

    def test_ignores_tmp_files(self):
        from github_manager import scan_folder
        self._create_file("real.txt", "real")
        self._create_file("temp.tmp", "junk")
        self._create_file("~$word.docx", "junk")
        result = scan_folder(self.tmpdir)
        # Only the real file should be counted
        self.assertEqual(result["file_count"], 1)

    def test_recursive_scan(self):
        from github_manager import scan_folder
        self._create_file("folder/sub/deep.txt", "deep")
        self._create_file("folder/notes.py", "code")
        result = scan_folder(self.tmpdir)
        self.assertEqual(result["file_count"], 2)

    def test_nonexistent_folder(self):
        from github_manager import scan_folder
        result = scan_folder(r"C:\DoesNotExist_12345")
        self.assertEqual(result["file_count"], 0)
        self.assertEqual(result["files"], [])

    def test_extension_counts(self):
        from github_manager import scan_folder
        self._create_file("a.py")
        self._create_file("b.py")
        self._create_file("c.txt")
        result = scan_folder(self.tmpdir)
        self.assertEqual(result["extensions"].get(".py"), 2)
        self.assertEqual(result["extensions"].get(".txt"), 1)


class TestIsGitRepo(unittest.TestCase):
    def test_non_repo_folder(self):
        from github_manager import is_git_repo
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertFalse(is_git_repo(tmpdir))

    @patch("github_manager._run_git", return_value=(0, ".git", ""))
    def test_is_git_repo_true(self, mock_git):
        from github_manager import is_git_repo
        result = is_git_repo("/some/path")
        self.assertTrue(result)


class TestRunGit(unittest.TestCase):
    @patch("subprocess.run")
    def test_successful_command(self, mock_run):
        from github_manager import _run_git
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        code, out, err = _run_git(["status"], "/tmp")
        self.assertEqual(code, 0)
        self.assertEqual(out, "ok")

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_git_not_installed(self, mock_run):
        from github_manager import _run_git
        code, out, err = _run_git(["status"], "/tmp")
        self.assertEqual(code, 1)
        self.assertIn("not installed", err)


class TestCommitAndPush(unittest.TestCase):
    @patch("github_manager._run_git")
    def test_no_changes(self, mock_git):
        from github_manager import commit_and_push
        # Simulate: config user ok, add ok, status empty (no changes)
        mock_git.side_effect = [
            (0, "", ""),   # config user.email
            (0, "", ""),   # config user.name
            (0, "", ""),   # add .
            (0, "", ""),   # status --porcelain (empty = no changes)
        ]
        result = commit_and_push("/tmp", "Test commit")
        self.assertEqual(result["message"], "no_changes")
        self.assertTrue(result["success"])
        self.assertEqual(result["files_changed"], 0)

    @patch("github_manager._run_git")
    def test_successful_push(self, mock_git):
        from github_manager import commit_and_push
        mock_git.side_effect = [
            (0, "", ""),            # config email
            (0, "", ""),            # config name
            (0, "", ""),            # add .
            (0, "M  file.txt", ""), # status --porcelain
            (0, "commit done", ""), # commit
            (0, "abc1234", ""),     # rev-parse HEAD
            (0, "pushed", ""),      # push
        ]
        result = commit_and_push("/tmp", "Daily Backup - 2025-08-05")
        self.assertTrue(result["success"])
        self.assertEqual(result["files_changed"], 1)

    @patch("github_manager._run_git")
    def test_push_failure(self, mock_git):
        from github_manager import commit_and_push
        mock_git.side_effect = [
            (0, "", ""),                # config email
            (0, "", ""),                # config name
            (0, "", ""),                # add .
            (0, "M  file.txt", ""),    # status
            (0, "commit done", ""),     # commit
            (0, "abc1234", ""),         # rev-parse
            (1, "", "Authentication failed"),  # push FAILS
        ]
        result = commit_and_push("/tmp", "Test")
        self.assertFalse(result["success"])
        self.assertIn("Authentication failed", result["message"])


class TestBackupOrchestrator(unittest.TestCase):
    @patch("backup.init_db")
    @patch("backup.load_config")
    @patch("backup.scan_folder")
    @patch("backup.init_repo")
    @patch("backup.commit_and_push")
    @patch("backup.log_backup")
    @patch("backup._send_desktop_notification")
    def test_successful_backup(
        self, mock_notify, mock_log, mock_push, mock_init, mock_scan, mock_cfg, mock_db
    ):
        from backup import run_backup

        mock_cfg.return_value.watch_folder = tempfile.gettempdir()
        mock_cfg.return_value.repo_url = "https://github.com/user/repo"
        mock_cfg.return_value.branch = "main"
        mock_cfg.return_value.github_token = "token123"
        mock_cfg.return_value.commit_message_template = "Daily Backup - {date}"
        mock_cfg.return_value.ignore_patterns = []
        mock_cfg.return_value.desktop_notifications = True
        mock_cfg.return_value.email_notifications = False

        mock_scan.return_value = {"file_count": 5, "total_size": 1024, "files": []}
        mock_init.return_value = {"success": True, "message": "OK"}
        mock_push.return_value = {
            "success": True, "files_changed": 5,
            "commit_hash": "abc1234", "message": "Pushed"
        }

        result = run_backup()
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "success")
        mock_log.assert_called_once()

    @patch("backup.init_db")
    @patch("backup.load_config")
    @patch("backup.log_backup")
    @patch("backup._send_desktop_notification")
    def test_missing_folder(self, mock_notify, mock_log, mock_cfg, mock_db):
        from backup import run_backup

        mock_cfg.return_value.watch_folder = r"C:\NonExistentFolder_Test123"
        mock_cfg.return_value.repo_url = "https://github.com/user/repo"
        mock_cfg.return_value.branch = "main"
        mock_cfg.return_value.github_token = ""
        mock_cfg.return_value.commit_message_template = "Daily Backup - {date}"
        mock_cfg.return_value.ignore_patterns = []
        mock_cfg.return_value.desktop_notifications = False
        mock_cfg.return_value.email_notifications = False

        result = run_backup()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")


class TestSchedulerHelpers(unittest.TestCase):
    def test_compute_next_run_valid(self):
        from scheduler import compute_next_run
        result = compute_next_run("23:00")
        self.assertIn("23:00", result)

    def test_compute_next_run_invalid(self):
        from scheduler import compute_next_run
        result = compute_next_run("invalid")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
