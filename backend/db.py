"""
db.py

namdo.sqlite 연결.
"""

import sqlite3
from pathlib import Path

# backend/db.py 기준: 저장소 루트/data/processed/namdo.sqlite
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "namdo.sqlite"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"namdo.sqlite를 찾을 수 없습니다: {DB_PATH}\n"
            f"실제 위치가 다르면 db.py의 DB_PATH를 팀과 합의한 경로로 수정하세요."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
