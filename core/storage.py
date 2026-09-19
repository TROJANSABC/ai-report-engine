"""存储层：SQLite 保存历史报告与模板配置。"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime


class ReportStore:
    """轻量历史报告存储（初期使用 SQLite）。"""

    def __init__(self, db_path: str = "reports.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT    NOT NULL,
                    topic      TEXT    NOT NULL,
                    report_type TEXT   NOT NULL,
                    title      TEXT,
                    markdown   TEXT,
                    meta       TEXT
                )
                """
            )
            conn.commit()

    def save(
        self,
        topic: str,
        report_type: str,
        title: str,
        markdown: str,
        meta: dict | None = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO reports (created_at, topic, report_type, title, markdown, meta)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    topic,
                    report_type,
                    title,
                    markdown,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, topic, report_type, title"
                " FROM reports ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get(self, report_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return dict(row) if row else None
