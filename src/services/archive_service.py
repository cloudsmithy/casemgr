"""Archive service for managing case archive status."""
import os
import sqlite3
from pathlib import Path
from typing import Optional


class ArchiveService:
    """归档服务 - 使用 SQLite 存储归档状态"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the archive service.
        
        Args:
            db_path: Path to the SQLite database file.
                    If None, uses default path in user's app data directory.
        """
        if db_path is None:
            # Use default path in user's home directory
            app_data_dir = Path.home() / ".aws-case-manager"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_data_dir / "archive.db")
        
        self._db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if needed."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archived_cases (
                    case_id TEXT PRIMARY KEY,
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self._db_path)

    def archive_case(self, case_id: str) -> None:
        """
        归档案例。
        
        Args:
            case_id: 案例 ID
            
        Requirements: 12.1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO archived_cases (case_id, archived_at)
                VALUES (?, CURRENT_TIMESTAMP)
                """,
                (case_id,),
            )
            conn.commit()

    def unarchive_case(self, case_id: str) -> None:
        """
        取消归档案例。
        
        Args:
            case_id: 案例 ID
            
        Requirements: 12.4
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM archived_cases WHERE case_id = ?",
                (case_id,),
            )
            conn.commit()

    def is_archived(self, case_id: str) -> bool:
        """
        检查案例是否已归档。
        
        Args:
            case_id: 案例 ID
            
        Returns:
            bool: 案例是否已归档
            
        Requirements: 12.2
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM archived_cases WHERE case_id = ?",
                (case_id,),
            )
            return cursor.fetchone() is not None

    def get_archived_case_ids(self) -> set[str]:
        """
        获取所有已归档案例 ID。
        
        Returns:
            set[str]: 已归档案例 ID 集合
            
        Requirements: 12.3
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT case_id FROM archived_cases")
            rows = cursor.fetchall()
            return {row[0] for row in rows}

    def clear_all(self) -> None:
        """
        清除所有归档记录（主要用于测试）。
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM archived_cases")
            conn.commit()
