"""
database.py — SQLite Database Layer
=====================================
Defines the SQLAlchemy ORM model for backup logs and provides
CRUD helpers used by backup.py and the Streamlit dashboard.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DB_PATH

logger = logging.getLogger(__name__)

# ── Engine Setup ─────────────────────────────────────────────────────────────
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── ORM Base ─────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Model ─────────────────────────────────────────────────────────────────────
class Backup(Base):
    """
    Represents a single backup attempt.

    Columns
    -------
    id                  : Auto-incrementing primary key
    backup_datetime     : When the backup started (UTC)
    files_uploaded      : Number of files added / modified
    commit_message      : The git commit message used
    status              : 'success' | 'failed' | 'no_changes'
    error_message       : Exception text if status == 'failed'
    repository_name     : Remote repository name (owner/repo)
    duration_seconds    : How long the backup took
    """

    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    backup_datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    files_uploaded = Column(Integer, default=0)
    commit_message = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)          # success | failed | no_changes
    error_message = Column(Text, nullable=True)
    repository_name = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Backup id={self.id} date={self.backup_datetime} "
            f"status={self.status} files={self.files_uploaded}>"
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "backup_datetime": self.backup_datetime,
            "files_uploaded": self.files_uploaded,
            "commit_message": self.commit_message,
            "status": self.status,
            "error_message": self.error_message,
            "repository_name": self.repository_name,
            "duration_seconds": self.duration_seconds,
        }


# ── Initialisation ────────────────────────────────────────────────────────────
def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised at %s", DB_PATH)


# ── CRUD Helpers ──────────────────────────────────────────────────────────────
def log_backup(
    *,
    files_uploaded: int,
    commit_message: str,
    status: str,
    error_message: Optional[str] = None,
    repository_name: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    backup_datetime: Optional[datetime] = None,
) -> Backup:
    """
    Insert a backup record and return the persisted object.

    Parameters
    ----------
    files_uploaded  : Number of files committed
    commit_message  : Git commit message
    status          : 'success' | 'failed' | 'no_changes'
    error_message   : Exception string (if any)
    repository_name : e.g. 'user/assignments'
    duration_seconds: Elapsed time for the backup
    backup_datetime : Override timestamp (defaults to now)
    """
    with SessionLocal() as session:
        record = Backup(
            backup_datetime=backup_datetime or datetime.now(timezone.utc),
            files_uploaded=files_uploaded,
            commit_message=commit_message,
            status=status,
            error_message=error_message,
            repository_name=repository_name,
            duration_seconds=duration_seconds,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        logger.info("Backup log saved: id=%d status=%s", record.id, status)
        return record


def get_all_backups(limit: Optional[int] = None) -> List[Dict]:
    """
    Retrieve all backup records, newest first.
    Returns a list of plain dicts (safe to pass to pandas / Streamlit).
    """
    with SessionLocal() as session:
        query = session.query(Backup).order_by(Backup.backup_datetime.desc())
        if limit:
            query = query.limit(limit)
        return [b.to_dict() for b in query.all()]


def get_backup_dataframe() -> pd.DataFrame:
    """Return backup history as a pandas DataFrame."""
    records = get_all_backups()
    if not records:
        return pd.DataFrame(columns=[
            "id", "backup_datetime", "files_uploaded",
            "commit_message", "status", "error_message",
            "repository_name", "duration_seconds",
        ])
    df = pd.DataFrame(records)
    df["backup_datetime"] = pd.to_datetime(df["backup_datetime"])
    return df


def get_stats() -> Dict:
    """
    Return aggregated statistics for the dashboard home page.

    Returns
    -------
    dict with keys:
        total_backups, successful, failed, no_changes,
        total_files_uploaded, last_backup (Backup | None),
        success_rate (float 0–100)
    """
    with SessionLocal() as session:
        total = session.query(func.count(Backup.id)).scalar() or 0
        successful = (
            session.query(func.count(Backup.id))
            .filter(Backup.status == "success")
            .scalar() or 0
        )
        failed = (
            session.query(func.count(Backup.id))
            .filter(Backup.status == "failed")
            .scalar() or 0
        )
        no_changes = (
            session.query(func.count(Backup.id))
            .filter(Backup.status == "no_changes")
            .scalar() or 0
        )
        total_files = (
            session.query(func.sum(Backup.files_uploaded)).scalar() or 0
        )
        last = (
            session.query(Backup)
            .order_by(Backup.backup_datetime.desc())
            .first()
        )

        return {
            "total_backups": total,
            "successful": successful,
            "failed": failed,
            "no_changes": no_changes,
            "total_files_uploaded": int(total_files),
            "last_backup": last.to_dict() if last else None,
            "success_rate": round((successful / total * 100) if total else 0, 1),
        }


def delete_backup(backup_id: int) -> bool:
    """Delete a single backup record by ID. Returns True if deleted."""
    with SessionLocal() as session:
        record = session.query(Backup).filter(Backup.id == backup_id).first()
        if record:
            session.delete(record)
            session.commit()
            return True
        return False


def clear_all_backups() -> int:
    """Delete ALL backup records. Returns number of rows deleted."""
    with SessionLocal() as session:
        count = session.query(Backup).delete()
        session.commit()
        return count
