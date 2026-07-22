from datetime import date
import csv
from io import BytesIO
import json
from urllib.error import HTTPError, URLError

from aimaos.collectors import naver_searchad_poc
from aimaos.collectors.data_collection_poc import build_report
from aimaos.collectors.naver_searchad_poc import (
    NaverSearchAdCredentials,
    NaverSearchAdPocClient,
    PocStepResult,
    PocDateRange,
    all_zero_performance,
    build_stats_attempts,
    extract_stat_rows,
    load_poc_date_range_from_env,
    write_naver_collection_log,
    write_standard_csv_from_stats,
)
from aimaos.storage.collection_log import collection_status_by_media, recent_collection_logs


def credentials() -> NaverSearchAdCredentials:
    return NaverSearchAdCredentials(
        customer_id="demo-customer",
        access_license="demo-access",
        secret_key="demo-secret",
        account_alias="데모 계정",
        advertiser="샘플 광고주",
    )


def test_default_date_range_is_previous_30_days(monkeypatch):
    monkeypatch.delenv("AIMAOS_POC_START_DATE", raising=False)
    monkeypatch.delenv("AIMAOS_POC_END_DATE", raising=False)

    result = load_poc_date_range_from_env(today=date(2026, 6, 18))

    assert result.start == date(2026, 5, 19)
    assert result.end == date(2026, 6, 17)
    assert result.source == "기본값: 최근 30일"


def test_reversed_date_range_is_normalized(monkeypatch):
    monkeypatch.setenv("AIMAOS_POC_START_DATE", "2026-06-10")
    monkeypatch.setenv("AIMAOS_POC_END_DATE", "2026-06-01")

    result = load_poc_date_range_from_env(today=date(2026, 6, 18))

    assert result.start == date(2026, 6, 1)
    assert result.end == date(2026, 6, 10)
    assert any("두 날짜를 바꿔" in warning for warning in result.warnings)


def test_future_date_range_is_clamped_to_previous_day(monkeypatch):
    monkeypatch.setenv("AIMAOS_POC_START_DATE", "2026-06-10")
    monkeypatch.setenv("AIMAOS_POC_END_DATE", "2026-06-25")

    result = load_poc_date_range_from_env(today=date(2026, 6, 20))

    assert result.start == date(2026, 6, 10)
    assert result.end == date(2026, 6, 19)
    assert any("조회 가능한 전일" in warning for warning in result.warnings)


def test_fully_future_date_range_becomes_previous_day(monkeypatch):
    monkeypatch.setenv("AIMAOS_POC_START_DATE", "2026-06-25")
    monkeypatch.setenv("AIMAOS_POC_END_DATE", "2026-06-30")

    result = load_poc_date_range_from_env(today=date(2026, 6, 20))

    assert result.start == date(2026, 6, 19)
    assert result.end == date(2026, 6, 19)
    assert any("전일 하루" in warning for warning in result.warnings)

def test_stats_attempt_uses_repeated_ids_and_json_fields():
    attempts = build_stats_attempts(
        campaigns=[{"nccCampaignId": "cmp-1"}],
        adgroups=[{"nccAdgroupId": "grp-1"}],
        keywords=[],
        date_range=PocDateRange(date(2026, 6, 1), date(2026, 6, 7), "테스트"),
    )

    campaign_attempt = next(item for item in attempts if item["name"] == "campaign_rich")

    assert campaign_attempt["params"]["ids"] == ["cmp-1"]
    assert "impCnt" in json.loads(campaign_attempt["params"]["fields"])
    assert json.loads(campaign_attempt["params"]["timeRange"]) == {
        "since": "2026-06-01",
        "until": "2026-06-07",
    }


def test_nested_stats_rows_are_flattened():
    payload = {
        "response": {
            "data": [
                {
                    "id": "cmp-1",
                    "fields": {
                        "impCnt": 1000,
                        "clkCnt": 25,
                        "salesAmt": 50000,
                    },
                }
            ]
        }
    }

    rows = extract_stat_rows(payload)

    assert rows == [
        {
            "id": "cmp-1",
            "impCnt": 1000,
            "clkCnt": 25,
            "salesAmt": 50000,
        }
    ]


def test_standard_csv_handles_real_rows_and_empty_response(tmp_path):
    client = NaverSearchAdPocClient(credentials(), tmp_path / "evidence")
    params = {
        "ids": ["cmp-1"],
        "timeRange": json.dumps({"since": "2026-06-01", "until": "2026-06-07"}),
    }
    campaigns = [{"nccCampaignId": "cmp-1", "name": "브랜드 캠페인"}]
    payload = {
        "data": [
            {
                "id": "cmp-1",
                "fields": {
                    "impCnt": 1000,
                    "clkCnt": 25,
                    "salesAmt": 50000,
                    "ccnt": 3,
                    "convAmt": 200000,
                },
            }
        ]
    }

    step, csv_path = write_standard_csv_from_stats(
        client,
        credentials(),
        payload,
        params,
        campaigns,
        [],
        [],
    )

    assert step.status == "성공"
    assert csv_path is not None
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["campaign"] == "브랜드 캠페인"
    assert float(rows[0]["impressions"]) == 1000
    assert float(rows[0]["revenue"]) == 200000
    assert all_zero_performance(rows) is False

    empty_step, empty_csv_path = write_standard_csv_from_stats(
        client,
        credentials(),
        {"data": []},
        params,
        campaigns,
        [],
        [],
    )

    assert empty_step.status == "성공"
    assert "0 지표 행" in empty_step.detail
    assert empty_csv_path is not None
    with empty_csv_path.open(encoding="utf-8-sig", newline="") as handle:
        empty_rows = list(csv.DictReader(handle))
    assert all_zero_performance(empty_rows) is True


def test_collection_report_uses_actual_execution_results():
    success_steps = [
        PocStepResult(name, "성공", f"{name} 성공")
        for name in (
            "캠페인 조회",
            "광고그룹 조회",
            "기간 성과 조회",
            "AIMAOS 표준 CSV 변환",
            "AIMAOS 기존 파이프라인 연결",
            "오늘 해야 할 일 생성",
            "보고서 자동 생성",
            "노출/클릭/광고비 수집",
        )
    ]
    results = {
        "네이버 검색광고": success_steps,
        "G마켓": [PocStepResult("리포트 다운로드", "실행 불가", "실제 다운로드 파일 없음")],
        "옥션": [],
        "11번가": [],
    }

    report = build_report(results)

    assert "네이버 검색광고 | 기술 검증 성공" in report
    assert "네이버 검색광고: 현재 실행 결과에서 실패 단계 없음" in report
    assert "G마켓: 실제 다운로드 파일 없음" in report
    assert "Customer ID, Access License, Secret Key가 현재 환경에 없어" not in report
    assert "네이버 API 수집은 기술 검증 성공" in report


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"data": [{"id": "cmp-1"}]}'


def test_naver_client_retries_temporary_network_error(monkeypatch, tmp_path):
    calls = []
    sleeps = []

    def fake_urlopen(_request, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise URLError("temporary")
        return FakeResponse()

    monkeypatch.setattr(naver_searchad_poc, "urlopen", fake_urlopen)
    monkeypatch.setattr(naver_searchad_poc.time, "sleep", sleeps.append)
    client = NaverSearchAdPocClient(
        credentials(),
        tmp_path / "evidence",
        max_attempts=3,
        retry_delay_seconds=0.1,
    )

    ok, payload, status = client.request_json("GET", "/stats")

    assert ok is True
    assert payload["data"][0]["id"] == "cmp-1"
    assert status == "HTTP 200"
    assert len(calls) == 2
    assert sleeps == [0.1]


def test_naver_client_retries_retryable_http_error(monkeypatch, tmp_path):
    calls = []
    sleeps = []

    def fake_urlopen(_request, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise HTTPError(
                url="https://api.searchad.naver.com/stats",
                code=429,
                msg="Too Many Requests",
                hdrs=None,
                fp=BytesIO(b'{"code":429}'),
            )
        return FakeResponse()

    monkeypatch.setattr(naver_searchad_poc, "urlopen", fake_urlopen)
    monkeypatch.setattr(naver_searchad_poc.time, "sleep", sleeps.append)
    client = NaverSearchAdPocClient(
        credentials(),
        tmp_path / "evidence",
        max_attempts=2,
        retry_delay_seconds=0.2,
    )

    ok, payload, status = client.request_json("GET", "/stats")

    assert ok is True
    assert payload["data"][0]["id"] == "cmp-1"
    assert status == "HTTP 200"
    assert len(calls) == 2
    assert sleeps == [0.2]


def test_naver_client_does_not_retry_non_retryable_http_error(monkeypatch, tmp_path):
    calls = []
    sleeps = []

    def fake_urlopen(_request, timeout):
        calls.append(timeout)
        raise HTTPError(
            url="https://api.searchad.naver.com/stats",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":"unauthorized"}'),
        )

    monkeypatch.setattr(naver_searchad_poc, "urlopen", fake_urlopen)
    monkeypatch.setattr(naver_searchad_poc.time, "sleep", sleeps.append)
    client = NaverSearchAdPocClient(
        credentials(),
        tmp_path / "evidence",
        max_attempts=3,
        retry_delay_seconds=0.1,
    )

    ok, payload, status = client.request_json("GET", "/stats")

    assert ok is False
    assert status == "HTTP 401"
    assert payload["status"] == 401
    assert payload["attempts"] == 1
    assert len(calls) == 1
    assert sleeps == []

def test_naver_collection_log_records_no_data_without_raw_customer_id(tmp_path):
    db_path = tmp_path / "collection_log.sqlite3"
    context = {
        "started_at": "2026-06-19 09:00:00",
        "response_data_rows": 0,
        "standard_csv_rows": 1,
        "zero_guard_applied": True,
        "standard_csv_path": None,
        "report_paths": {},
    }
    results = [
        PocStepResult("기간 성과 조회", "성공", "stats API 조회 성공"),
        PocStepResult("AIMAOS 기존 파이프라인 연결", "성공", "파이프라인 연결 성공"),
        PocStepResult("보고서 자동 생성", "성공", "보고서 생성 성공"),
    ]

    step = write_naver_collection_log(credentials(), context, results, db_path)

    assert step.status == "성공"
    rows = recent_collection_logs(10, db_path)
    assert rows[0]["status"] == "no_data"
    assert rows[0]["error_code"] == "NAVER_STATS_NO_DATA"
    assert rows[0]["rows_collected"] == 0
    assert rows[0]["advertiser_id"].startswith("naver:")
    assert "demo-customer" not in rows[0]["advertiser_id"]
    status = collection_status_by_media(db_path)["naver_searchad"]
    assert status["latest_status"] == "no_data"
