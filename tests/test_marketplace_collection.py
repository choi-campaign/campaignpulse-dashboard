from datetime import datetime, timedelta
from pathlib import Path
import os

from aimaos.collectors.marketplace.download_watcher import (
    list_completed_downloads,
    list_completed_report_downloads,
)
from aimaos.collectors.marketplace.gmarket_computer_use_download_poc import completed_report_files
from aimaos.storage.collection_log import (
    CollectionLogRecord,
    append_collection_log,
    recent_collection_logs,
)


def set_modified_at(path: Path, when: datetime) -> None:
    timestamp = when.timestamp()
    os.utime(path, (timestamp, timestamp))


def test_report_download_detection_supports_excel_and_csv(tmp_path):
    now = datetime.now()
    csv_path = tmp_path / "report.csv"
    xlsx_path = tmp_path / "report.xlsx"
    partial_path = tmp_path / "report.xlsx.crdownload"
    demo_path = tmp_path / "demo_gmarket_report.csv"
    csv_path.write_text("date,cost\n2026-06-01,1000\n", encoding="utf-8")
    xlsx_path.write_bytes(b"safe-test-placeholder")
    partial_path.write_bytes(b"incomplete")
    demo_path.write_text("date,cost\n2026-06-01,1000\n", encoding="utf-8")
    set_modified_at(csv_path, now)
    set_modified_at(xlsx_path, now)
    set_modified_at(partial_path, now)
    set_modified_at(demo_path, now)

    detected = list_completed_report_downloads(tmp_path)

    assert csv_path in detected
    assert xlsx_path in detected
    assert partial_path not in detected
    assert demo_path not in detected
    assert demo_path in list_completed_report_downloads(tmp_path, include_demo=True)


def test_new_collection_does_not_reuse_stale_download(tmp_path):
    old_file = tmp_path / "old_report.csv"
    new_file = tmp_path / "new_report.csv"
    old_file.write_text("old", encoding="utf-8")
    new_file.write_text("new", encoding="utf-8")
    started_at = datetime.now()
    set_modified_at(old_file, started_at - timedelta(minutes=10))
    set_modified_at(new_file, started_at + timedelta(seconds=1))

    detected = completed_report_files(tmp_path, after=started_at)

    assert detected == [new_file]
    assert list_completed_downloads(tmp_path, "*.csv", after=started_at) == [new_file]


def test_collection_log_preserves_success_and_failure_details(tmp_path):
    db_path = tmp_path / "collection_log.sqlite3"
    success = CollectionLogRecord(
        collection_id="success-1",
        advertiser_id="sample",
        media="gmarket",
        started_at="2026-06-18 10:00:00",
        finished_at="2026-06-18 10:01:00",
        status="success",
        rows_collected=12,
        file_count=1,
        storage_used_mb=0.5,
        error_code="",
        error_message="",
    )
    failure = CollectionLogRecord(
        collection_id="failure-1",
        advertiser_id="sample",
        media="auction",
        started_at="2026-06-18 11:00:00",
        finished_at="2026-06-18 11:01:00",
        status="failed",
        rows_collected=0,
        file_count=0,
        storage_used_mb=0,
        error_code="DOWNLOAD_FILE_NOT_FOUND",
        error_message="리포트 파일이 감지되지 않았습니다.",
    )

    append_collection_log(success, db_path)
    append_collection_log(failure, db_path)
    rows = recent_collection_logs(10, db_path)

    assert [row["collection_id"] for row in rows] == ["failure-1", "success-1"]
    assert rows[0]["error_code"] == "DOWNLOAD_FILE_NOT_FOUND"
    assert rows[1]["rows_collected"] == 12
