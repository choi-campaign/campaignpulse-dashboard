from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
import argparse
import sqlite3
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "storage" / "collection_log.sqlite3"


@dataclass(frozen=True)
class CollectionLogRecord:
    collection_id: str
    advertiser_id: str
    media: str
    started_at: str
    finished_at: str
    status: str
    rows_collected: int
    file_count: int
    storage_used_mb: float
    error_code: str
    error_message: str


COLLECTION_LOG_COLUMNS = [field.name for field in fields(CollectionLogRecord)]


def ensure_collection_log_db(db_path: Path = DEFAULT_DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS collection_log (
                collection_id TEXT PRIMARY KEY,
                advertiser_id TEXT NOT NULL,
                media TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                status TEXT NOT NULL,
                rows_collected INTEGER NOT NULL DEFAULT 0,
                file_count INTEGER NOT NULL DEFAULT 0,
                storage_used_mb REAL NOT NULL DEFAULT 0,
                error_code TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_log_media ON collection_log(media)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_log_started_at ON collection_log(started_at)")
    return db_path


def append_collection_log(record: CollectionLogRecord, db_path: Path = DEFAULT_DB_PATH) -> None:
    ensure_collection_log_db(db_path)
    values = [getattr(record, column) for column in COLLECTION_LOG_COLUMNS]
    placeholders = ", ".join("?" for _ in COLLECTION_LOG_COLUMNS)
    columns = ", ".join(COLLECTION_LOG_COLUMNS)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO collection_log ({columns}) VALUES ({placeholders})",
            values,
        )


def recent_collection_logs(limit: int = 20, db_path: Path = DEFAULT_DB_PATH) -> list[dict[str, object]]:
    ensure_collection_log_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows: Iterable[sqlite3.Row] = conn.execute(
            """
            SELECT *
            FROM collection_log
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
    return [dict(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the AIMAOS collection log database.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    db_path = ensure_collection_log_db(args.db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"collection_log ready: {db_path}")
    print(f"checked_at: {now}")
    print("columns: " + ", ".join(COLLECTION_LOG_COLUMNS))


if __name__ == "__main__":
    main()

