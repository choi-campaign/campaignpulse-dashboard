from datetime import date
import csv
import json

from aimaos.collectors.naver_searchad_poc import (
    NaverSearchAdCredentials,
    NaverSearchAdPocClient,
    PocDateRange,
    all_zero_performance,
    build_stats_attempts,
    extract_stat_rows,
    load_poc_date_range_from_env,
    write_standard_csv_from_stats,
)


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
