from __future__ import annotations

import base64
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import hashlib
import hmac
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from aimaos.storage.collection_log import (
    DEFAULT_DB_PATH,
    CollectionLogRecord,
    append_collection_log,
)


NAVER_SEARCHAD_BASE_URL = "https://api.searchad.naver.com"
NAVER_MEDIA_NAME = "네이버 검색광고"
RICH_STAT_FIELDS = ["clkCnt", "impCnt", "salesAmt", "ctr", "cpc", "avgRnk", "ccnt", "convAmt", "ror"]
BASIC_STAT_FIELDS = ["clkCnt", "impCnt", "salesAmt", "ctr", "cpc", "avgRnk", "ccnt"]
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class PocStepResult:
    name: str
    status: str
    detail: str
    evidence_path: str | None = None


@dataclass(frozen=True)
class NaverSearchAdCredentials:
    customer_id: str
    access_license: str
    secret_key: str
    account_alias: str
    advertiser: str


@dataclass(frozen=True)
class PocDateRange:
    start: date
    end: date
    source: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatsProbeOutcome:
    ok: bool
    payload: Any
    evidence_path: str | None
    target_name: str
    params: dict[str, Any]
    status_text: str
    attempted_files: list[str]


def load_naver_credentials_from_env() -> tuple[NaverSearchAdCredentials | None, list[str]]:
    required = {
        "NAVER_SEARCHAD_CUSTOMER_ID": os.getenv("NAVER_SEARCHAD_CUSTOMER_ID", "").strip(),
        "NAVER_SEARCHAD_ACCESS_LICENSE": os.getenv("NAVER_SEARCHAD_ACCESS_LICENSE", "").strip(),
        "NAVER_SEARCHAD_SECRET_KEY": os.getenv("NAVER_SEARCHAD_SECRET_KEY", "").strip(),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        return None, missing

    return (
        NaverSearchAdCredentials(
            customer_id=required["NAVER_SEARCHAD_CUSTOMER_ID"],
            access_license=required["NAVER_SEARCHAD_ACCESS_LICENSE"],
            secret_key=required["NAVER_SEARCHAD_SECRET_KEY"],
            account_alias=os.getenv("NAVER_SEARCHAD_ACCOUNT_ALIAS", NAVER_MEDIA_NAME).strip() or NAVER_MEDIA_NAME,
            advertiser=os.getenv("AIMAOS_POC_ADVERTISER", "POC 광고주").strip() or "POC 광고주",
        ),
        [],
    )


def load_poc_date_range_from_env(today: date | None = None) -> PocDateRange:
    today = today or date.today()
    default_end = today - timedelta(days=1)
    default_start = default_end - timedelta(days=29)
    raw_start = os.getenv("AIMAOS_POC_START_DATE", "").strip()
    raw_end = os.getenv("AIMAOS_POC_END_DATE", "").strip()
    warnings: list[str] = []

    if not raw_start and not raw_end:
        return PocDateRange(default_start, default_end, "기본값: 최근 30일")

    start = parse_env_date(raw_start, "AIMAOS_POC_START_DATE", warnings) if raw_start else None
    end = parse_env_date(raw_end, "AIMAOS_POC_END_DATE", warnings) if raw_end else None

    if start is None and end is None:
        return PocDateRange(default_start, default_end, "기본값: 최근 30일", tuple(warnings))
    if start is None and end is not None:
        start = end
        warnings.append("시작일이 없어 종료일과 같은 날짜로 조회합니다.")
    if end is None and start is not None:
        end = start
        warnings.append("종료일이 없어 시작일과 같은 날짜로 조회합니다.")
    if start and end and start > end:
        start, end = end, start
        warnings.append("시작일이 종료일보다 늦어 두 날짜를 바꿔 조회합니다.")

    return PocDateRange(start or default_start, end or default_end, "환경변수", tuple(warnings))


def parse_env_date(value: str, name: str, warnings: list[str]) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        warnings.append(f"{name} 값이 YYYY-MM-DD 형식이 아니어서 무시했습니다: {value}")
        return None


class NaverSearchAdPocClient:
    def __init__(
        self,
        credentials: NaverSearchAdCredentials,
        evidence_dir: Path,
        *,
        max_attempts: int | None = None,
        retry_delay_seconds: float | None = None,
    ) -> None:
        self.credentials = credentials
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.max_attempts = max(
            1,
            max_attempts
            if max_attempts is not None
            else env_int("AIMAOS_NAVER_API_MAX_ATTEMPTS", 3),
        )
        self.retry_delay_seconds = max(
            0,
            retry_delay_seconds
            if retry_delay_seconds is not None
            else env_float("AIMAOS_NAVER_API_RETRY_DELAY_SECONDS", 0.75),
        )

    def request_json(self, method: str, uri: str, params: dict[str, Any] | None = None) -> tuple[bool, Any, str]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url = f"{NAVER_SEARCHAD_BASE_URL}{uri}{query}"
        for attempt in range(1, self.max_attempts + 1):
            timestamp = str(int(time.time() * 1000))
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Timestamp": timestamp,
                "X-API-KEY": self.credentials.access_license,
                "X-Customer": self.credentials.customer_id,
                "X-Signature": self._signature(timestamp, method, uri),
            }
            request = Request(url=url, method=method, headers=headers)
            try:
                with urlopen(request, timeout=20) as response:  # noqa: S310
                    body = response.read().decode("utf-8")
                    data = json.loads(body) if body else {}
                    return True, data, f"HTTP {response.status}"
            except HTTPError as error:
                body = error.read().decode("utf-8", errors="replace")[:3000]
                if error.code in RETRYABLE_HTTP_STATUS and attempt < self.max_attempts:
                    time.sleep(self.retry_delay_seconds * attempt)
                    continue
                return False, {"status": error.code, "body": body, "attempts": attempt}, f"HTTP {error.code}"
            except URLError as error:
                if attempt < self.max_attempts:
                    time.sleep(self.retry_delay_seconds * attempt)
                    continue
                return False, {"reason": str(error.reason), "attempts": attempt}, "NETWORK_ERROR"
            except Exception as error:  # noqa: BLE001
                return False, {"reason": str(error), "attempts": attempt}, "ERROR"
        return False, {"reason": "재시도 횟수를 모두 사용했습니다."}, "ERROR"

    def _signature(self, timestamp: str, method: str, uri: str) -> str:
        message = f"{timestamp}.{method}.{uri}"
        digest = hmac.new(
            self.credentials.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def save_evidence(self, name: str, data: Any) -> str:
        path = self.evidence_dir / f"{name}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def run_naver_searchad_poc(evidence_root: Path) -> list[PocStepResult]:
    date_range = load_poc_date_range_from_env()
    credentials, missing = load_naver_credentials_from_env()
    if credentials is None:
        detail = "네이버 검색광고 API 연결 정보가 없어 실제 계정 호출을 실행하지 못했습니다: " + ", ".join(missing)
        results = [
            PocStepResult("조회 기간", "준비됨", format_date_range(date_range)),
            PocStepResult("Customer ID", "실행 불가", detail),
            PocStepResult("Access License", "실행 불가", detail),
            PocStepResult("Secret Key", "실행 불가", detail),
            PocStepResult("키워드 조회", "실행 불가", detail),
            PocStepResult("기간 성과 조회", "실행 불가", detail),
            PocStepResult("AIMAOS 표준 CSV 변환", "대기", "성과 데이터 수집 후 실행합니다."),
            PocStepResult("AIMAOS 기존 파이프라인 연결", "대기", "표준 CSV 생성 후 실행합니다."),
        ]
        write_date_range_stats_report(evidence_root, results, {"date_range": date_range})
        return results

    client = NaverSearchAdPocClient(credentials, evidence_root / "naver_searchad")
    context: dict[str, Any] = {
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "evidence_dir": str(client.evidence_dir),
        "date_range": date_range,
        "keyword_count": 0,
        "response_data_rows": None,
        "stats_attempts": [],
        "standard_csv_path": None,
        "standard_csv_rows": None,
        "data_shortage_metrics": [],
        "zero_guard_applied": None,
        "pipeline_output_dir": None,
        "action_issue_count": None,
        "report_paths": {},
        "collected_metrics": {},
    }
    results: list[PocStepResult] = [
        PocStepResult("조회 기간", "준비됨", format_date_range(date_range)),
        PocStepResult("Customer ID", "준비됨", "환경 변수에서 Customer ID를 확인했습니다."),
        PocStepResult("Access License", "준비됨", "환경 변수에서 Access License를 확인했습니다."),
        PocStepResult("Secret Key", "준비됨", "환경 변수에서 Secret Key를 확인했습니다."),
    ]

    campaign_ok, campaigns, campaign_status = client.request_json("GET", "/ncc/campaigns")
    campaign_path = client.save_evidence("campaigns", campaigns)
    results.append(
        PocStepResult(
            "캠페인 조회",
            "성공" if campaign_ok else "실패",
            f"네이버 캠페인 조회 응답: {campaign_status}, 조회 건수: {len(campaigns) if isinstance(campaigns, list) else '확인 필요'}",
            campaign_path,
        )
    )

    adgroup_ok, adgroups, adgroup_status = client.request_json("GET", "/ncc/adgroups")
    adgroup_path = client.save_evidence("adgroups", adgroups)
    results.append(
        PocStepResult(
            "광고그룹 조회",
            "성공" if adgroup_ok else "실패",
            f"네이버 광고그룹 조회 응답: {adgroup_status}, 조회 건수: {len(adgroups) if isinstance(adgroups, list) else '확인 필요'}",
            adgroup_path,
        )
    )

    keyword_step, keywords = fetch_keywords_by_adgroup(client, adgroups)
    context["keyword_count"] = len(keywords)
    results.append(keyword_step)

    stats_steps, stats_outcome = run_naver_stats_probe(client, campaigns, adgroups, keywords, date_range)
    context["stats_attempts"] = stats_outcome.attempted_files if stats_outcome else []
    if stats_outcome:
        context["response_data_rows"] = response_data_row_count(stats_outcome.payload)
    results.extend(stats_steps)

    if stats_outcome and stats_outcome.ok:
        csv_step, csv_path = write_standard_csv_from_stats(
            client=client,
            credentials=credentials,
            stats_payload=stats_outcome.payload,
            stats_params=stats_outcome.params,
            campaigns=campaigns,
            adgroups=adgroups,
            keywords=keywords,
            context=context,
        )
        context["standard_csv_path"] = str(csv_path) if csv_path else None
        results.append(csv_step)
        pipeline_steps = run_existing_pipeline(csv_path, credentials, evidence_root, context) if csv_path else [
            PocStepResult("AIMAOS 기존 파이프라인 연결", "대기", "표준 CSV가 생성되지 않아 실행하지 않았습니다."),
            PocStepResult("오늘 해야 할 일 생성", "대기", "기존 파이프라인 연결 후 확인합니다."),
            PocStepResult("보고서 자동 생성", "대기", "기존 파이프라인 연결 후 확인합니다."),
        ]
        results.extend(pipeline_steps)
    else:
        results.extend(
            [
                PocStepResult("AIMAOS 표준 CSV 변환", "대기", "stats API 성과 조회가 성공하면 표준 CSV로 변환합니다."),
                PocStepResult("AIMAOS 기존 파이프라인 연결", "대기", "표준 CSV 생성 후 기존 분석 파이프라인에 연결합니다."),
                PocStepResult("오늘 해야 할 일 생성", "대기", "기존 파이프라인 연결 후 확인합니다."),
                PocStepResult("보고서 자동 생성", "대기", "기존 파이프라인 연결 후 확인합니다."),
            ]
        )

    results.extend(
        [
            PocStepResult(
                "대행사 계정 사용 가능 여부",
                "조건부 확인" if campaign_ok or adgroup_ok else "확인 실패",
                "캠페인 또는 광고그룹 목록이 조회되면 해당 Customer ID 기준 접근 권한은 확인된 것으로 봅니다. 여러 광고주 접근 범위는 추가 Customer ID로 검증해야 합니다.",
            ),
            PocStepResult(
                "광고주 데이터 조회 가능 여부",
                "조건부 확인" if campaign_ok or adgroup_ok else "확인 실패",
                "캠페인/광고그룹/키워드 중 하나 이상 조회되면 광고주 데이터 접근 가능성이 높습니다.",
            ),
        ]
    )
    results.append(write_naver_collection_log(credentials, context, results))
    write_date_range_stats_report(evidence_root, results, context)
    return results


def write_naver_collection_log(
    credentials: NaverSearchAdCredentials,
    context: dict[str, Any],
    results: list[PocStepResult],
    db_path: Path = DEFAULT_DB_PATH,
) -> PocStepResult:
    try:
        status_by_name = {result.name: result for result in results}
        stats_step = status_by_name.get("기간 성과 조회")
        pipeline_step = status_by_name.get("AIMAOS 기존 파이프라인 연결")
        report_step = status_by_name.get("보고서 자동 생성")
        response_rows = context.get("response_data_rows")
        zero_guard = context.get("zero_guard_applied")

        if stats_step is None or stats_step.status in {"실패", "실행 불가"}:
            status = "failed"
            error_code = "NAVER_STATS_COLLECTION_FAILED"
            error_message = stats_step.detail if stats_step else "네이버 성과 조회 결과를 확인할 수 없습니다."
        elif response_rows == 0 or zero_guard is True:
            status = "no_data"
            error_code = "NAVER_STATS_NO_DATA"
            error_message = "선택 기간의 네이버 광고 성과 데이터가 없습니다."
        elif pipeline_step and report_step and pipeline_step.status == "성공" and report_step.status == "성공":
            status = "success"
            error_code = ""
            error_message = ""
        else:
            status = "partial"
            error_code = "NAVER_PIPELINE_PARTIAL"
            error_message = (
                pipeline_step.detail
                if pipeline_step and pipeline_step.status != "성공"
                else "네이버 데이터 수집 후 일부 처리 단계의 확인이 필요합니다."
            )

        finished_at = datetime.now()
        started_at = parse_collection_started_at(context.get("started_at")) or finished_at
        account_hash = hashlib.sha256(credentials.customer_id.encode("utf-8")).hexdigest()[:12]
        evidence_paths = [
            Path(path)
            for path in [
                context.get("standard_csv_path"),
                *context.get("report_paths", {}).values(),
            ]
            if path
        ]
        existing_paths = [path for path in evidence_paths if path.exists() and path.is_file()]
        storage_used_mb = sum(path.stat().st_size for path in existing_paths) / (1024 * 1024)
        record = CollectionLogRecord(
            collection_id=f"naver_{finished_at.strftime('%Y%m%d_%H%M%S_%f')}_{account_hash[:8]}",
            advertiser_id=f"naver:{account_hash}",
            media="naver_searchad",
            started_at=started_at.strftime("%Y-%m-%d %H:%M:%S"),
            finished_at=finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            status=status,
            rows_collected=int(context.get("standard_csv_rows") or response_rows or 0),
            file_count=len(existing_paths),
            storage_used_mb=round(storage_used_mb, 4),
            error_code=error_code,
            error_message=error_message,
        )
        append_collection_log(record, db_path)
        return PocStepResult(
            "수집 로그 기록",
            "성공",
            f"네이버 수집 결과를 {status} 상태로 기록했습니다.",
            str(db_path),
        )
    except Exception as error:  # noqa: BLE001
        return PocStepResult(
            "수집 로그 기록",
            "실패",
            f"네이버 수집 결과 로그 기록 중 오류: {error}",
            str(db_path),
        )


def parse_collection_started_at(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_date_range(date_range: PocDateRange) -> str:
    text = f"{date_range.start.isoformat()} ~ {date_range.end.isoformat()} ({date_range.source})"
    if date_range.warnings:
        text += " / " + " ".join(date_range.warnings)
    return text


def fetch_keywords_by_adgroup(client: NaverSearchAdPocClient, adgroups: Any) -> tuple[PocStepResult, list[dict[str, Any]]]:
    adgroup_items = adgroups if isinstance(adgroups, list) else []
    if not adgroup_items:
        payload = {"reason": "조회된 광고그룹이 없어 nccAdgroupId 기준 키워드 조회를 실행하지 않았습니다."}
        path = client.save_evidence("keywords", payload)
        return PocStepResult("키워드 조회", "실행 불가", payload["reason"], path), []

    keywords: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    evidence: list[str] = []
    for index, adgroup in enumerate(adgroup_items, start=1):
        adgroup_id = adgroup.get("nccAdgroupId") if isinstance(adgroup, dict) else None
        if not adgroup_id:
            continue
        ok, payload, status = client.request_json("GET", "/ncc/keywords", params={"nccAdgroupId": adgroup_id})
        evidence.append(client.save_evidence(f"keywords_adgroup_{index}", payload))
        if ok and isinstance(payload, list):
            keywords.extend([item for item in payload if isinstance(item, dict)])
        elif ok:
            errors.append({"nccAdgroupId": adgroup_id, "status": status, "payload": payload})
        else:
            errors.append({"nccAdgroupId": adgroup_id, "status": status, "payload": payload})

    combined_payload = {"keywords": keywords, "errors": errors, "evidence": evidence}
    combined_path = client.save_evidence("keywords", combined_payload)
    if errors and keywords:
        status = "부분 성공"
        detail = f"광고그룹 ID 기준 키워드 조회를 실행했습니다. 키워드 {len(keywords)}건 조회, 오류 {len(errors)}건."
    elif errors:
        status = "실패"
        detail = f"광고그룹 ID 기준 키워드 조회를 실행했지만 오류 {len(errors)}건이 발생했습니다."
    else:
        status = "성공"
        detail = f"광고그룹 ID 기준 키워드 조회 성공. 키워드 {len(keywords)}건 조회."
    return PocStepResult("키워드 조회", status, detail, combined_path), keywords


def run_naver_stats_probe(
    client: NaverSearchAdPocClient,
    campaigns: Any,
    adgroups: Any,
    keywords: Any,
    date_range: PocDateRange,
) -> tuple[list[PocStepResult], StatsProbeOutcome | None]:
    attempts = build_stats_attempts(campaigns, adgroups, keywords, date_range)
    if not attempts:
        return (
            [
                PocStepResult("기간 성과 조회", "실행 불가", "성과 조회에 사용할 캠페인/광고그룹/키워드 ID를 찾지 못했습니다."),
                PocStepResult("노출/클릭/광고비 수집", "실행 불가", "stats API를 실행하지 못했습니다."),
                PocStepResult("전환/매출/ROAS 수집", "실행 불가", "stats API를 실행하지 못했습니다."),
            ],
            None,
        )

    attempted_files: list[str] = []
    last_status = "실행 안 됨"
    last_payload: Any = None
    for index, attempt in enumerate(attempts, start=1):
        ok, payload, status_text = client.request_json("GET", "/stats", params=attempt["params"])
        evidence_path = client.save_evidence(f"stats_attempt_{index:02d}_{attempt['name']}", {"params": attempt["safe_params"], "response": payload})
        attempted_files.append(evidence_path)
        last_status = status_text
        last_payload = payload
        if ok:
            success_path = client.save_evidence(
                "date_range_stats",
                {
                    "target": attempt["label"],
                    "params": attempt["safe_params"],
                    "response": payload,
                },
            )
            metric_text = json.dumps(payload, ensure_ascii=False)
            data_rows = response_data_row_count(payload)
            has_basic_metrics = any(field in metric_text for field in ["impCnt", "clkCnt", "salesAmt"])
            has_conversion_metrics = any(field in metric_text for field in ["ccnt", "convAmt", "ror", "conversion", "conv"])
            return (
                [
                    PocStepResult(
                        "기간 성과 조회",
                        "성공",
                        f"{date_range.start.isoformat()} ~ {date_range.end.isoformat()} stats API 조회 성공. 성공 조합: {attempt['label']}, response.data {data_rows}행.",
                        success_path,
                    ),
                    PocStepResult(
                        "노출/클릭/광고비 수집",
                        "성공" if has_basic_metrics else "확인 필요",
                        "응답에서 impCnt/clkCnt/salesAmt 계열 지표를 확인했습니다." if has_basic_metrics else "응답은 성공했지만 기본 지표 필드 확인이 필요합니다.",
                        success_path,
                    ),
                    PocStepResult(
                        "전환/매출/ROAS 수집",
                        "조건부 확인" if has_conversion_metrics else "확인 필요",
                        "응답에서 전환/매출/ROAS 계열 필드를 확인했습니다." if has_conversion_metrics else "전환/매출/ROAS는 계정 추적 설정 또는 지원 필드에 따라 추가 확인이 필요합니다.",
                        success_path,
                    ),
                ],
                StatsProbeOutcome(
                    ok=True,
                    payload=payload,
                    evidence_path=success_path,
                    target_name=attempt["label"],
                    params=attempt["params"],
                    status_text=status_text,
                    attempted_files=attempted_files,
                ),
            )

    failure_path = client.save_evidence(
        "date_range_stats",
        {"status": last_status, "last_response": last_payload, "attempted_files": attempted_files},
    )
    return (
        [
            PocStepResult(
                "기간 성과 조회",
                "실패",
                f"{date_range.start.isoformat()} ~ {date_range.end.isoformat()} stats API 조회 실패. 마지막 응답: {last_status}",
                failure_path,
            ),
            PocStepResult("노출/클릭/광고비 수집", "실패", "stats API 성과 조회가 실패해 기본 지표를 수집하지 못했습니다.", failure_path),
            PocStepResult("전환/매출/ROAS 수집", "확인 필요", "stats API 성과 조회가 성공한 뒤 전환 추적 필드 지원 여부를 확인해야 합니다.", failure_path),
        ],
        StatsProbeOutcome(
            ok=False,
            payload=last_payload,
            evidence_path=failure_path,
            target_name="실패",
            params={},
            status_text=last_status,
            attempted_files=attempted_files,
        ),
    )


def build_stats_attempts(campaigns: Any, adgroups: Any, keywords: Any, date_range: PocDateRange) -> list[dict[str, Any]]:
    campaign_ids = collect_ids(campaigns, "nccCampaignId")
    adgroup_ids = collect_ids(adgroups, "nccAdgroupId")
    keyword_ids = collect_ids(keywords, "nccKeywordId")
    time_range = json.dumps({"since": date_range.start.isoformat(), "until": date_range.end.isoformat()}, separators=(",", ":"))

    target_sets: list[tuple[str, str, list[str]]] = []
    if campaign_ids and adgroup_ids:
        target_sets.append(("campaign_adgroup", "캠페인+광고그룹 반복 ids", campaign_ids[:10] + adgroup_ids[:10]))
    if campaign_ids:
        target_sets.append(("campaign", "캠페인 반복 ids", campaign_ids[:10]))
    if adgroup_ids:
        target_sets.append(("adgroup", "광고그룹 반복 ids", adgroup_ids[:10]))
    if keyword_ids:
        target_sets.append(("keyword", "키워드 반복 ids", keyword_ids[:10]))

    attempts: list[dict[str, Any]] = []
    for target_key, target_label, ids in target_sets:
        for field_key, fields in [("rich", RICH_STAT_FIELDS), ("basic", BASIC_STAT_FIELDS)]:
            params = {
                "ids": ids,
                "fields": json.dumps(fields, separators=(",", ":")),
                "timeRange": time_range,
            }
            attempts.append(
                {
                    "name": f"{target_key}_{field_key}",
                    "label": f"{target_label} / {field_key} fields",
                    "params": params,
                    "safe_params": {"ids": ids, "fields": fields, "timeRange": json.loads(time_range)},
                }
            )
    return attempts


def collect_ids(payload: Any, key: str) -> list[str]:
    found: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and item.get(key):
                found.append(str(item[key]))
    elif isinstance(payload, dict):
        for value in payload.values():
            found.extend(collect_ids(value, key))
    return found


def response_data_row_count(payload: Any) -> int | None:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return len(payload["data"])
    if isinstance(payload, dict) and isinstance(payload.get("response"), dict):
        return response_data_row_count(payload["response"])
    return None


def write_standard_csv_from_stats(
    client: NaverSearchAdPocClient,
    credentials: NaverSearchAdCredentials,
    stats_payload: Any,
    stats_params: dict[str, Any],
    campaigns: Any,
    adgroups: Any,
    keywords: Any,
    context: dict[str, Any] | None = None,
) -> tuple[PocStepResult, Path | None]:
    stat_rows = extract_stat_rows(stats_payload)
    used_empty_fallback = False
    if not stat_rows:
        stat_rows = build_empty_stat_rows_from_params(stats_params)
        used_empty_fallback = bool(stat_rows)
    if not stat_rows:
        path = client.save_evidence(
            "standard_csv_error",
            {"reason": "stats 응답과 요청 파라미터에서 표준 CSV로 변환할 ID를 찾지 못했습니다.", "payload": stats_payload, "params": stats_params},
        )
        return PocStepResult("AIMAOS 표준 CSV 변환", "실패", "stats 응답과 요청 파라미터에서 표준 CSV로 변환할 ID를 찾지 못했습니다.", path), None

    stat_rows = attach_request_ids_if_missing(stat_rows, stats_params)
    default_date = extract_target_date(stats_params)
    id_lookup = build_id_lookup(campaigns, adgroups, keywords)
    rows = [to_standard_row(row, default_date, credentials, id_lookup) for row in stat_rows]
    fieldnames = [
        "date",
        "advertiser",
        "media",
        "campaign",
        "ad_group",
        "keyword",
        "product_name",
        "impressions",
        "clicks",
        "cost",
        "conversions",
        "revenue",
        "roas",
        "cpc",
        "ctr",
        "orders",
    ]
    csv_path = client.evidence_dir / "naver_searchad_standard.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    shortages = data_shortage_metrics(rows)
    collected = collected_metric_summary(rows)
    zero_guard_applied = all_zero_performance(rows)
    summary = {
        "path": str(csv_path),
        "rows": len(rows),
        "columns": fieldnames,
        "empty_stats_fallback": used_empty_fallback,
        "zero_guard_applied": zero_guard_applied,
        "data_shortage_metrics": shortages,
        "collected_metrics": collected,
    }
    client.save_evidence("standard_csv_summary", summary)
    if context is not None:
        context["standard_csv_rows"] = len(rows)
        context["data_shortage_metrics"] = shortages
        context["zero_guard_applied"] = zero_guard_applied
        context["collected_metrics"] = collected

    detail = f"표준 CSV {len(rows)}행 생성 완료."
    if used_empty_fallback:
        detail += " stats 응답의 data가 비어 있어 요청 ID 기준 0 지표 행으로 생성했습니다."
    return PocStepResult("AIMAOS 표준 CSV 변환", "성공", detail, str(csv_path)), csv_path


def extract_stat_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            rows.extend(extract_stat_rows(item))
    elif isinstance(payload, dict):
        if isinstance(payload.get("response"), dict):
            rows.extend(extract_stat_rows(payload["response"]))
        if isinstance(payload.get("fields"), dict):
            flat = {key: value for key, value in payload.items() if key != "fields"}
            flat.update(payload["fields"])
            rows.append(flat)
            return rows
        if isinstance(payload.get("data"), dict):
            flat = {key: value for key, value in payload.items() if key != "data"}
            flat.update(payload["data"])
            rows.append(flat)
            return rows
        nested_lists = [payload.get(key) for key in ["data", "rows", "items", "result", "results"] if isinstance(payload.get(key), list)]
        if nested_lists:
            for nested in nested_lists:
                rows.extend(extract_stat_rows(nested))
            return rows
        if any(key in payload for key in ["id", "nccCampaignId", "nccAdgroupId", "nccKeywordId", "impCnt", "clkCnt", "salesAmt"]):
            rows.append(payload)
    return rows


def build_empty_stat_rows_from_params(stats_params: dict[str, Any]) -> list[dict[str, Any]]:
    raw_ids = stats_params.get("ids", [])
    if isinstance(raw_ids, str):
        ids = [raw_ids]
    elif isinstance(raw_ids, list):
        ids = [str(value) for value in raw_ids if value]
    else:
        ids = []
    return [{"id": stat_id, "impCnt": 0, "clkCnt": 0, "salesAmt": 0, "ccnt": 0, "convAmt": 0} for stat_id in ids]


def attach_request_ids_if_missing(rows: list[dict[str, Any]], stats_params: dict[str, Any]) -> list[dict[str, Any]]:
    ids = request_ids(stats_params)
    if not ids:
        return rows
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        copy = row.copy()
        has_id = any(copy.get(key) for key in ["id", "nccCampaignId", "nccAdgroupId", "nccKeywordId"])
        if not has_id and len(rows) == len(ids):
            copy["id"] = ids[index]
        elif not has_id and len(ids) == 1:
            copy["id"] = ids[0]
        enriched.append(copy)
    return enriched


def request_ids(stats_params: dict[str, Any]) -> list[str]:
    raw_ids = stats_params.get("ids", [])
    if isinstance(raw_ids, str):
        return [raw_ids]
    if isinstance(raw_ids, list):
        return [str(value) for value in raw_ids if value]
    return []


def extract_target_date(stats_params: dict[str, Any]) -> str:
    raw_time_range = stats_params.get("timeRange", "")
    if isinstance(raw_time_range, str):
        try:
            return str(json.loads(raw_time_range).get("since", ""))
        except json.JSONDecodeError:
            return ""
    if isinstance(raw_time_range, dict):
        return str(raw_time_range.get("since", ""))
    return ""


def build_id_lookup(campaigns: Any, adgroups: Any, keywords: Any) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    campaign_names: dict[str, str] = {}
    if isinstance(campaigns, list):
        for campaign in campaigns:
            if not isinstance(campaign, dict):
                continue
            campaign_id = str(campaign.get("nccCampaignId", ""))
            if not campaign_id:
                continue
            campaign_name = str(campaign.get("name", ""))
            campaign_names[campaign_id] = campaign_name
            lookup[campaign_id] = {"campaign_name": campaign_name, "ad_group_name": "", "keyword": ""}

    adgroup_names: dict[str, dict[str, str]] = {}
    if isinstance(adgroups, list):
        for adgroup in adgroups:
            if not isinstance(adgroup, dict):
                continue
            adgroup_id = str(adgroup.get("nccAdgroupId", ""))
            if not adgroup_id:
                continue
            campaign_id = str(adgroup.get("nccCampaignId", ""))
            item = {"campaign_name": campaign_names.get(campaign_id, ""), "ad_group_name": str(adgroup.get("name", "")), "keyword": ""}
            adgroup_names[adgroup_id] = item
            lookup[adgroup_id] = item

    if isinstance(keywords, list):
        for keyword in keywords:
            if not isinstance(keyword, dict):
                continue
            keyword_id = str(keyword.get("nccKeywordId", ""))
            if not keyword_id:
                continue
            adgroup_id = str(keyword.get("nccAdgroupId", ""))
            base = adgroup_names.get(adgroup_id, {"campaign_name": "", "ad_group_name": "", "keyword": ""})
            lookup[keyword_id] = {
                "campaign_name": base.get("campaign_name", ""),
                "ad_group_name": base.get("ad_group_name", ""),
                "keyword": str(keyword.get("keyword", "")),
            }
    return lookup


def to_standard_row(
    row: dict[str, Any],
    default_date: str,
    credentials: NaverSearchAdCredentials,
    id_lookup: dict[str, dict[str, str]],
) -> dict[str, Any]:
    row_id = str(row.get("id") or row.get("nccCampaignId") or row.get("nccAdgroupId") or row.get("nccKeywordId") or "")
    names = id_lookup.get(row_id, {"campaign_name": "", "ad_group_name": "", "keyword": ""})
    impressions = numeric_value(row, "impCnt", "impressions")
    clicks = numeric_value(row, "clkCnt", "clicks")
    cost = numeric_value(row, "salesAmt", "cost")
    conversions = numeric_value(row, "ccnt", "convCnt", "conversionCnt", "conversions")
    revenue = numeric_value(row, "convAmt", "revenue", "sales")
    return {
        "date": row_date(row, default_date),
        "advertiser": credentials.advertiser,
        "media": NAVER_MEDIA_NAME,
        "campaign": names.get("campaign_name", "") or row_id,
        "ad_group": names.get("ad_group_name", ""),
        "keyword": names.get("keyword", ""),
        "product_name": "",
        "impressions": impressions,
        "clicks": clicks,
        "cost": cost,
        "conversions": conversions,
        "orders": conversions,
        "revenue": revenue,
        "roas": numeric_value(row, "ror", "roas") or safe_divide(revenue, cost),
        "cpc": numeric_value(row, "cpc") or safe_divide(cost, clicks),
        "ctr": numeric_value(row, "ctr") or safe_divide(clicks, impressions),
    }


def row_date(row: dict[str, Any], default_date: str) -> str:
    for key in ["date", "statDate", "statDt", "period", "baseDate"]:
        value = row.get(key)
        if value:
            return str(value)
    return default_date


def numeric_value(row: dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value is None or value == "":
            continue
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            continue
    return 0.0


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def data_shortage_metrics(rows: list[dict[str, Any]]) -> list[str]:
    checks = {"전환수": "conversions", "매출": "revenue", "ROAS": "roas"}
    return [label for label, key in checks.items() if all(numeric_value(row, key) == 0 for row in rows)]


def collected_metric_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    metrics = ["impressions", "clicks", "cost", "conversions", "revenue", "roas", "cpc", "ctr"]
    return {metric: sum(numeric_value(row, metric) for row in rows) for metric in metrics}


def all_zero_performance(rows: list[dict[str, Any]]) -> bool:
    return all(collected_metric_summary(rows).get(metric, 0) <= 0 for metric in ["impressions", "clicks", "cost", "conversions", "revenue"])


def run_existing_pipeline(
    csv_path: Path,
    credentials: NaverSearchAdCredentials,
    evidence_root: Path,
    context: dict[str, Any],
) -> list[PocStepResult]:
    try:
        from aimaos.pipeline import run_analysis_pipeline
        from aimaos.recommenders.action_engine import build_operating_action_issues

        output_dir = evidence_root.parents[2] / "data" / "reports" / f"naver_api_range_poc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = run_analysis_pipeline(csv_path, output_dir, advertiser=credentials.advertiser)
        action_issues = build_operating_action_issues(result.analysis, advertiser=credentials.advertiser)
        context["pipeline_output_dir"] = str(result.output_dir)
        context["action_issue_count"] = len(action_issues)
        context["report_paths"] = {
            "markdown": str(result.report_paths.markdown),
            "text": str(result.report_paths.text),
            "excel": str(result.report_paths.excel),
        }
        return [
            PocStepResult("AIMAOS 기존 파이프라인 연결", "성공", f"기존 분석 파이프라인 실행 완료. 표준화 행 수: {result.rows}", str(result.output_dir)),
            PocStepResult("오늘 해야 할 일 생성", "성공", f"기존 엔진 기준 오늘 해야 할 일 {len(action_issues)}건 생성.", str(result.report_paths.excel)),
            PocStepResult("보고서 자동 생성", "성공", "Markdown/TXT/Excel 보고서 생성 완료.", str(result.report_paths.excel)),
        ]
    except Exception as error:  # noqa: BLE001
        error_path = evidence_root / "naver_searchad" / "pipeline_error.json"
        error_path.write_text(json.dumps({"error": str(error)}, ensure_ascii=False, indent=2), encoding="utf-8")
        return [
            PocStepResult("AIMAOS 기존 파이프라인 연결", "실패", f"기존 파이프라인 실행 중 오류: {error}", str(error_path)),
            PocStepResult("오늘 해야 할 일 생성", "대기", "기존 파이프라인 연결 실패로 실행하지 않았습니다.", str(error_path)),
            PocStepResult("보고서 자동 생성", "대기", "기존 파이프라인 연결 실패로 실행하지 않았습니다.", str(error_path)),
        ]


def write_date_range_stats_report(evidence_root: Path, results: list[PocStepResult], context: dict[str, Any]) -> None:
    project_root = evidence_root.parents[2]
    report_path = project_root / "docs" / "NAVER_API_DATE_RANGE_STATS_RESULT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    date_range = context.get("date_range")
    if not isinstance(date_range, PocDateRange):
        date_range = load_poc_date_range_from_env()
    status_by_name = {result.name: result for result in results}
    stats_result = status_by_name.get("기간 성과 조회")
    csv_result = status_by_name.get("AIMAOS 표준 CSV 변환")
    pipeline_result = status_by_name.get("AIMAOS 기존 파이프라인 연결")
    action_result = status_by_name.get("오늘 해야 할 일 생성")
    report_result = status_by_name.get("보고서 자동 생성")
    network_blocked = any("NETWORK_ERROR" in result.detail for result in results)

    lines = [
        "# NAVER API Date Range Stats Result",
        "",
        f"작성일: {context.get('started_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
        "",
        "## 1. 조회 기간",
        "",
        f"- {date_range.start.isoformat()} ~ {date_range.end.isoformat()}",
        f"- 기간 출처: {date_range.source}",
        *[f"- 기간 경고: {warning}" for warning in date_range.warnings],
        "",
        "## 2. response.data 행 수",
        "",
        f"- {context.get('response_data_rows') if context.get('response_data_rows') is not None else '확인 필요'}",
        render_environment_line(network_blocked),
        "",
        "## 3. 생성된 표준 CSV 경로",
        "",
        render_step(csv_result),
        f"- CSV: {context.get('standard_csv_path') or '생성 안 됨'}",
        "",
        "## 4. 표준 CSV 행 수",
        "",
        f"- {context.get('standard_csv_rows') if context.get('standard_csv_rows') is not None else '확인 필요'}",
        "",
        "## 5. 수집된 실제 지표",
        "",
        *render_metric_lines(context.get("collected_metrics", {})),
        "",
        "## 6. 데이터 부족 지표",
        "",
        f"- {', '.join(context.get('data_shortage_metrics', [])) if context.get('data_shortage_metrics') else '없음'}",
        "",
        "## 7. 분석 파이프라인 연결 결과",
        "",
        render_step(pipeline_result),
        "",
        "## 8. 오늘 해야 할 일 생성 결과",
        "",
        render_step(action_result),
        f"- 생성 건수: {context.get('action_issue_count') if context.get('action_issue_count') is not None else '확인 필요'}",
        "",
        "## 9. 보고서 생성 결과",
        "",
        render_step(report_result),
        f"- Markdown: {context.get('report_paths', {}).get('markdown', '생성 안 됨')}",
        f"- TXT: {context.get('report_paths', {}).get('text', '생성 안 됨')}",
        f"- Excel: {context.get('report_paths', {}).get('excel', '생성 안 됨')}",
        "",
        "## 10. 다음 단계",
        "",
        render_zero_guard_line(context),
        "- response.data가 실제 성과 행을 반환한 날짜 범위를 최종 기준으로 저장합니다.",
        "- 캠페인 단위가 안정화되면 광고그룹 단위와 키워드 단위 성과 조회를 분리 검증합니다.",
        "- 전환/매출/ROAS가 계속 비어 있으면 네이버 전환 추적 설정 여부를 계정에서 확인합니다.",
        "",
        "## 실행 증거",
        "",
        f"- 증거 폴더: {context.get('evidence_dir', '-')}",
        "- stats 시도 파일:",
        *[f"  - {path}" for path in context.get("stats_attempts", [])],
        "",
        "## 전체 단계 결과",
        "",
        "| 단계 | 상태 | 설명 | 증거 |",
        "| --- | --- | --- | --- |",
        *[f"| {step.name} | {step.status} | {step.detail} | {step.evidence_path or '-'} |" for step in results],
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def render_step(step: PocStepResult | None) -> str:
    if step is None:
        return "- 확인 필요"
    evidence = f" 증거: `{step.evidence_path}`" if step.evidence_path else ""
    return f"- {step.status}: {step.detail}{evidence}"


def render_metric_lines(metrics: Any) -> list[str]:
    if not isinstance(metrics, dict) or not metrics:
        return ["- 확인 필요"]
    labels = {
        "impressions": "노출수",
        "clicks": "클릭수",
        "cost": "광고비",
        "conversions": "전환수",
        "revenue": "매출",
        "roas": "ROAS",
        "cpc": "CPC",
        "ctr": "CTR",
    }
    return [f"- {labels.get(key, key)}: {value}" for key, value in metrics.items()]


def render_environment_line(network_blocked: bool) -> str:
    if not network_blocked:
        return "- 실행 환경: 네이버 API 호출 가능"
    return "- 실행 환경: Codex 실행 세션에서 네이버 API 소켓 접근이 차단되어 실제 response.data 검증은 로컬 PowerShell 재실행이 필요합니다."


def render_zero_guard_line(context: dict[str, Any]) -> str:
    zero_guard = context.get("zero_guard_applied")
    rows = context.get("response_data_rows")
    if zero_guard is True:
        return "- 0 지표 방어 로직: 적용됨. 실제 성과 행이 없거나 모든 성과 지표가 0입니다."
    if zero_guard is False and rows and rows > 0:
        return "- 0 지표 방어 로직: 정상 데이터에는 적용되지 않았습니다."
    if zero_guard is False:
        return "- 0 지표 방어 로직: 적용되지 않았습니다."
    return "- 0 지표 방어 로직: 표준 CSV 생성 후 확인 가능합니다."


# 기존 이름을 참조하는 테스트나 수동 스크립트가 있어도 깨지지 않도록 유지합니다.
write_stats_collection_report = write_date_range_stats_report
