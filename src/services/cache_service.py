"""Cache service for storing case data locally."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.case import Case, CaseDetail


class CacheService:
    """缓存服务 - 使用 SQLite 存储缓存数据"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the cache service.
        
        Args:
            db_path: Path to the SQLite database file.
                    If None, uses default path in user's app data directory.
        """
        if db_path is None:
            app_data_dir = Path.home() / ".aws-case-manager"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_data_dir / "cache.db")
        
        self._db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if needed."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            # Table for cached cases list
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_cases (
                    case_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for cached case details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_case_details (
                    case_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for sync metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self._db_path)


    def save_cases(self, cases: list[Case]) -> None:
        """
        保存案例列表到缓存。
        
        Args:
            cases: 案例列表
            
        Requirements: 11.1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Clear existing cases and insert new ones
            cursor.execute("DELETE FROM cached_cases")
            for case in cases:
                data_json = json.dumps(case.to_dict())
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cached_cases (case_id, data, cached_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (case.case_id, data_json),
                )
            # Update last sync time
            cursor.execute(
                """
                INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
                VALUES ('last_cases_sync', ?, CURRENT_TIMESTAMP)
                """,
                (datetime.now().isoformat(),),
            )
            conn.commit()

    def get_cached_cases(self) -> list[Case]:
        """
        获取缓存的案例列表。
        
        Returns:
            list[Case]: 缓存的案例列表
            
        Requirements: 11.2
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM cached_cases ORDER BY cached_at DESC")
            rows = cursor.fetchall()
            cases = []
            for row in rows:
                data = json.loads(row[0])
                cases.append(Case.from_dict(data))
            return cases

    def save_case_detail(self, case_id: str, detail: CaseDetail) -> None:
        """
        保存案例详情到缓存。
        
        Args:
            case_id: 案例 ID
            detail: 案例详情
            
        Requirements: 11.1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            data_json = json.dumps(detail.to_dict())
            cursor.execute(
                """
                INSERT OR REPLACE INTO cached_case_details (case_id, data, cached_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (case_id, data_json),
            )
            conn.commit()

    def get_cached_case_detail(self, case_id: str) -> Optional[CaseDetail]:
        """
        获取缓存的案例详情。
        
        Args:
            case_id: 案例 ID
            
        Returns:
            CaseDetail | None: 缓存的案例详情，如果不存在则返回 None
            
        Requirements: 11.2
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM cached_case_details WHERE case_id = ?",
                (case_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            data = json.loads(row[0])
            return CaseDetail.from_dict(data)

    def get_last_sync_time(self) -> Optional[datetime]:
        """
        获取最后同步时间。
        
        Returns:
            datetime | None: 最后同步时间，如果从未同步则返回 None
            
        Requirements: 11.2
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM sync_metadata WHERE key = 'last_cases_sync'"
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return datetime.fromisoformat(row[0])

    def clear_cache(self) -> None:
        """
        清除所有缓存。
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cached_cases")
            cursor.execute("DELETE FROM cached_case_details")
            cursor.execute("DELETE FROM sync_metadata")
            conn.commit()
