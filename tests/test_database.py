"""
tests/test_database.py — Database Unit Tests
=============================================
Tests for all database CRUD operations, stats aggregation,
and DataFrame helpers using an in-memory SQLite database.
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Override DB path to use in-memory DB for tests ───────────────────────────
import config as cfg_module
cfg_module.DB_PATH = Path(":memory:")

# Patch engine to use in-memory SQLite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database as db_module

_test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
db_module.engine = _test_engine
db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


class TestDatabaseInit(unittest.TestCase):
    def setUp(self):
        db_module.init_db()

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_init_creates_table(self):
        """init_db() should create the backups table."""
        db_module.init_db()  # Calling again should be idempotent
        records = db_module.get_all_backups()
        self.assertIsInstance(records, list)

    def test_table_is_empty_initially(self):
        records = db_module.get_all_backups()
        self.assertEqual(len(records), 0)


class TestLogBackup(unittest.TestCase):
    def setUp(self):
        db_module.init_db()

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_log_success(self):
        """Should insert a success record and return it."""
        record = db_module.log_backup(
            files_uploaded=5,
            commit_message="Daily Backup - 2025-08-05",
            status="success",
            repository_name="user/assignments",
            duration_seconds=3.14,
        )
        self.assertIsNotNone(record.id)
        self.assertEqual(record.status, "success")
        self.assertEqual(record.files_uploaded, 5)

    def test_log_failed(self):
        """Should insert a failure record with error message."""
        record = db_module.log_backup(
            files_uploaded=0,
            commit_message="Daily Backup - 2025-08-05",
            status="failed",
            error_message="Authentication failed",
        )
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.error_message, "Authentication failed")

    def test_log_no_changes(self):
        """Should insert a no_changes record."""
        record = db_module.log_backup(
            files_uploaded=0,
            commit_message="Daily Backup",
            status="no_changes",
        )
        self.assertEqual(record.status, "no_changes")
        self.assertEqual(record.files_uploaded, 0)

    def test_multiple_records(self):
        """Should store multiple records independently."""
        for i in range(3):
            db_module.log_backup(
                files_uploaded=i,
                commit_message=f"Backup #{i}",
                status="success",
            )
        records = db_module.get_all_backups()
        self.assertEqual(len(records), 3)


class TestGetAllBackups(unittest.TestCase):
    def setUp(self):
        db_module.init_db()
        # Insert test data
        db_module.log_backup(files_uploaded=2, commit_message="A", status="success",
                              backup_datetime=datetime(2025, 8, 1, 23, 0))
        db_module.log_backup(files_uploaded=0, commit_message="B", status="failed",
                              backup_datetime=datetime(2025, 8, 2, 23, 0))
        db_module.log_backup(files_uploaded=0, commit_message="C", status="no_changes",
                              backup_datetime=datetime(2025, 8, 3, 23, 0))

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_returns_newest_first(self):
        records = db_module.get_all_backups()
        dates = [r["backup_datetime"] for r in records]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_limit_parameter(self):
        records = db_module.get_all_backups(limit=2)
        self.assertEqual(len(records), 2)

    def test_returns_dicts(self):
        records = db_module.get_all_backups()
        self.assertIsInstance(records[0], dict)
        self.assertIn("status", records[0])


class TestGetStats(unittest.TestCase):
    def setUp(self):
        db_module.init_db()
        db_module.log_backup(files_uploaded=3, commit_message="A", status="success")
        db_module.log_backup(files_uploaded=2, commit_message="B", status="success")
        db_module.log_backup(files_uploaded=0, commit_message="C", status="failed")
        db_module.log_backup(files_uploaded=0, commit_message="D", status="no_changes")

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_total_backups(self):
        stats = db_module.get_stats()
        self.assertEqual(stats["total_backups"], 4)

    def test_successful_count(self):
        stats = db_module.get_stats()
        self.assertEqual(stats["successful"], 2)

    def test_failed_count(self):
        stats = db_module.get_stats()
        self.assertEqual(stats["failed"], 1)

    def test_total_files(self):
        stats = db_module.get_stats()
        self.assertEqual(stats["total_files_uploaded"], 5)

    def test_success_rate(self):
        stats = db_module.get_stats()
        self.assertEqual(stats["success_rate"], 50.0)

    def test_last_backup_not_none(self):
        stats = db_module.get_stats()
        self.assertIsNotNone(stats["last_backup"])


class TestDeleteBackup(unittest.TestCase):
    def setUp(self):
        db_module.init_db()
        self.record = db_module.log_backup(
            files_uploaded=1, commit_message="Test", status="success"
        )

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_delete_existing(self):
        result = db_module.delete_backup(self.record.id)
        self.assertTrue(result)
        records = db_module.get_all_backups()
        self.assertEqual(len(records), 0)

    def test_delete_nonexistent(self):
        result = db_module.delete_backup(9999)
        self.assertFalse(result)


class TestGetBackupDataframe(unittest.TestCase):
    def setUp(self):
        db_module.init_db()

    def tearDown(self):
        from database import Base
        Base.metadata.drop_all(bind=_test_engine)

    def test_empty_returns_dataframe(self):
        import pandas as pd
        df = db_module.get_backup_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("status", df.columns)

    def test_has_records(self):
        db_module.log_backup(files_uploaded=2, commit_message="Test", status="success")
        df = db_module.get_backup_dataframe()
        self.assertEqual(len(df), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
