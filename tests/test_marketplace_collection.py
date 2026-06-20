from datetime import datetime, timedelta
from pathlib import Path
import os

from aimaos.collectors.marketplace.download_watcher import (
    list_completed_downloads,
    list_completed_report_downloads,
)
from aimaos.collectors.marketplace.gmarket_computer_use_download_poc import (
    completed_report_files,
    download_detection_cutoff,
)
from aimaos.collectors.marketplace import marketplace_collection_poc
from aimaos.collectors.marketplace.base_collector import (
    MarketplacePocResult,
    MarketplaceProfile,
    PROFILE_READY,
)
from aimaos.storage.collection_log import (
    CollectionLogRecord,
    append_collection_log,
    collection_status_by_media,
    latest_collection_event_times,
    recent_collection_logs,
)


def set_modified_at(path: Path, when: datetime) -> None:
    timestamp = when.timestamp()
    os.utime(path, (timestamp, timestamp))


def test_report_download_detection_supports_excel_and_csv(tmp_path):
    now = datetime.now()
    csv_path = tmp_path / "report.csv"
    xlsx_path = tmp_path / "report.xlsx"
    uppercase_path = tmp_path / "REPORT.XLSX"
    empty_path = tmp_path / "empty.xlsx"
    partial_path = tmp_path / "report.xlsx.crdownload"
    demo_path = tmp_path / "demo_gmarket_report.csv"
    csv_path.write_text("date,cost\n2026-06-01,1000\n", encoding="utf-8")
    xlsx_path.write_bytes(b"safe-test-placeholder")
    uppercase_path.write_bytes(b"safe-uppercase-placeholder")
    empty_path.write_bytes(b"")
    partial_path.write_bytes(b"incomplete")
    demo_path.write_text("date,cost\n2026-06-01,1000\n", encoding="utf-8")
    set_modified_at(csv_path, now)
    set_modified_at(xlsx_path, now)
    set_modified_at(uppercase_path, now)
    set_modified_at(empty_path, now)
    set_modified_at(partial_path, now)
    set_modified_at(demo_path, now)

    detected = list_completed_report_downloads(tmp_path)

    assert csv_path in detected
    assert xlsx_path in detected
    assert uppercase_path in detected
    assert empty_path not in detected
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


def test_watch_only_detection_uses_bounded_lookback_window():
    started_at = datetime(2026, 6, 20, 11, 0, 0)

    regular_cutoff = download_detection_cutoff(
        started_at,
        watch_downloads_only=False,
        lookback_minutes=10,
    )
    watch_cutoff = download_detection_cutoff(
        started_at,
        watch_downloads_only=True,
        lookback_minutes=10,
    )
    zero_cutoff = download_detection_cutoff(
        started_at,
        watch_downloads_only=True,
        lookback_minutes=-5,
    )

    assert regular_cutoff == started_at
    assert watch_cutoff == started_at - timedelta(minutes=10)
    assert zero_cutoff == started_at

def test_profile_evaluation_forwards_manual_session_start_time(tmp_path, monkeypatch):
    started_at = datetime.now()
    captured: dict[str, datetime | None] = {}
    profile = MarketplaceProfile(
        media_key="auction",
        media_name="옥션",
        profile_version="legacy",
        login_url_env_key="TEST_LOGIN_URL",
        report_url_env_key="TEST_REPORT_URL",
        default_login_url="https://example.com/login",
        default_report_url="https://example.com/report",
        download_dir=tmp_path / "downloads",
        browser_profile_dir=tmp_path / "browser",
        status=PROFILE_READY,
    )

    def fake_list(download_dir: Path, after: datetime | None = None, **_kwargs):
        captured["after"] = after
        return []

    monkeypatch.setattr(marketplace_collection_poc, "playwright_installed", lambda: True)
    monkeypatch.setattr(marketplace_collection_poc, "find_browser_executable", lambda: "browser.exe")
    monkeypatch.setattr(marketplace_collection_poc, "list_completed_report_downloads", fake_list)

    result = marketplace_collection_poc.evaluate_profile(
        profile,
        datetime.now(),
        True,
        "ready",
        downloaded_after=started_at,
    )

    assert captured["after"] == started_at
    assert result.detected_files == []


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

    status = collection_status_by_media(
        db_path,
        now=datetime(2026, 6, 19, 0, 0, 0),
    )
    auction = status["auction"]
    gmarket = status["gmarket"]

    assert auction["latest_status"] == "failed"
    assert auction["last_failure_at"] == datetime(2026, 6, 18, 11, 1, 0)
    assert auction["error_code"] == "DOWNLOAD_FILE_NOT_FOUND"
    assert auction["success_rate_30d"] == 0
    assert gmarket["latest_status"] == "success"
    assert gmarket["last_success_at"] == datetime(2026, 6, 18, 10, 1, 0)
    assert gmarket["success_rate_30d"] == 100


def test_collection_status_read_does_not_create_missing_database(tmp_path):
    db_path = tmp_path / "missing.sqlite3"

    assert collection_status_by_media(db_path) == {}
    assert db_path.exists() is False


def test_collection_status_uses_latest_attempt_and_preserves_prior_success(tmp_path):
    db_path = tmp_path / "collection_log.sqlite3"
    records = [
        CollectionLogRecord(
            collection_id="gmarket-success",
            advertiser_id="sample",
            media="gmarket",
            started_at="2026-06-18T09:00:00+09:00",
            finished_at="2026-06-18T09:01:00+09:00",
            status="success",
            rows_collected=20,
            file_count=1,
            storage_used_mb=0.5,
            error_code="",
            error_message="",
        ),
        CollectionLogRecord(
            collection_id="gmarket-failed",
            advertiser_id="sample",
            media="gmarket",
            started_at="2026-06-18T10:00:00+09:00",
            finished_at="2026-06-18T10:01:00+09:00",
            status="failed",
            rows_collected=0,
            file_count=0,
            storage_used_mb=0,
            error_code="LOGIN_REQUIRED",
            error_message="로그인 인증이 필요합니다.",
        ),
    ]
    for record in records:
        append_collection_log(record, db_path)

    gmarket = collection_status_by_media(
        db_path,
        now=datetime(2026, 6, 19, 0, 0, 0),
    )["gmarket"]

    assert gmarket["latest_status"] == "failed"
    assert gmarket["latest_finished_at"] == datetime(2026, 6, 18, 10, 1, 0)
    assert gmarket["last_success_at"] == datetime(2026, 6, 18, 9, 1, 0)
    assert gmarket["last_failure_at"] == datetime(2026, 6, 18, 10, 1, 0)
    assert gmarket["error_code"] == "LOGIN_REQUIRED"
    assert gmarket["success_rate_30d"] == 50


def test_manual_marketplace_attempt_without_download_records_failure(tmp_path):
    db_path = tmp_path / "collection_log.sqlite3"
    started_at = datetime(2026, 6, 19, 10, 0, 0)
    profile = MarketplaceProfile(
        media_key="auction",
        media_name="옥션",
        profile_version="legacy",
        login_url_env_key="TEST_LOGIN_URL",
        report_url_env_key="TEST_REPORT_URL",
        default_login_url="https://example.com/login",
        default_report_url="https://example.com/report",
        download_dir=tmp_path / "downloads",
        browser_profile_dir=tmp_path / "browser",
        status=PROFILE_READY,
    )
    result = MarketplacePocResult(
        profile=profile,
        checked_at=datetime(2026, 6, 19, 10, 5, 0),
        steps=[],
        detected_files=[],
    )

    marketplace_collection_poc.record_marketplace_collection_result(
        result,
        started_at,
        db_path,
    )

    row = recent_collection_logs(1, db_path)[0]
    assert row["media"] == "auction"
    assert row["status"] == "failed"
    assert row["error_code"] == "DOWNLOAD_FILE_NOT_FOUND"
    status = collection_status_by_media(db_path)["auction"]
    assert status["last_failure_at"] == datetime(2026, 6, 19, 10, 5, 0)


def test_marketplace_success_log_preserves_rows_and_file_size(tmp_path):
    db_path = tmp_path / "collection_log.sqlite3"
    report_file = tmp_path / "auction_report.csv"
    report_file.write_text(
        "date,cost\n" + ("2026-06-19,1000\n" * 100),
        encoding="utf-8",
    )
    profile = MarketplaceProfile(
        media_key="auction",
        media_name="옥션",
        profile_version="legacy",
        login_url_env_key="TEST_LOGIN_URL",
        report_url_env_key="TEST_REPORT_URL",
        default_login_url="https://example.com/login",
        default_report_url="https://example.com/report",
        download_dir=tmp_path / "downloads",
        browser_profile_dir=tmp_path / "browser",
        status=PROFILE_READY,
    )
    result = MarketplacePocResult(
        profile=profile,
        checked_at=datetime(2026, 6, 19, 11, 5, 0),
        steps=[],
        detected_files=[report_file],
        audit_status="성공",
        pipeline_status="success",
        action_issue_count=2,
        report_paths={"excel": str(tmp_path / "analysis.xlsx")},
        audit_row_count=37,
    )

    marketplace_collection_poc.record_marketplace_collection_result(
        result,
        datetime(2026, 6, 19, 11, 0, 0),
        db_path,
    )

    row = recent_collection_logs(1, db_path)[0]
    assert row["status"] == "success"
    assert row["rows_collected"] == 37
    assert row["file_count"] == 1
    assert row["storage_used_mb"] > 0


def test_latest_collection_event_times_keep_previous_success_after_failure():
    previous_success = datetime(2026, 6, 18, 9, 0, 0)
    latest_failure = datetime(2026, 6, 19, 9, 0, 0)
    status_by_media = {
        "naver_searchad": {
            "latest_status": "no_data",
            "last_success_at": previous_success,
            "last_failure_at": latest_failure,
        },
        "gmarket": {
            "latest_status": "failed",
            "last_success_at": None,
            "last_failure_at": datetime(2026, 6, 19, 8, 0, 0),
        },
    }

    last_success_at, last_failure_at = latest_collection_event_times(status_by_media)

    assert last_success_at == previous_success
    assert last_failure_at == latest_failure
