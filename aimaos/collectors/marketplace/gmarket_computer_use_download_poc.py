from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path

from dotenv import load_dotenv

from aimaos.collectors.marketplace.base_collector import ensure_writable_directory
from aimaos.collectors.marketplace.browser_session import open_manual_collection_browser
from aimaos.collectors.marketplace.download_watcher import list_completed_report_downloads
from aimaos.collectors.marketplace.profiles import gmarket_legacy
from aimaos.pipeline import run_analysis_pipeline
from aimaos.storage.collection_log import CollectionLogRecord, append_collection_log
from aimaos.validators.raw_media_audit import audit_media_file


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = PROJECT_ROOT / "data" / "collection_poc" / "marketplace" / "gmarket_legacy"
REPORT_PATH = PROJECT_ROOT / "docs" / "GMARKET_COMPUTER_USE_DOWNLOAD_POC.md"
STRATEGY_PATH = PROJECT_ROOT / "docs" / "COMPUTER_USE_CONNECTOR_STRATEGY.md"
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


@dataclass(frozen=True)
class GmarketPowerclickPocResult:
    collection_id: str
    checked_at: str
    final_status: str
    error_code: str
    error_message: str
    computer_use_available: bool
    browser_fallback_available: bool
    scope: str
    download_dir: str
    browser_profile_dir: str
    detected_files: list[str]
    selected_file: str
    file_size: int
    audit_status: str
    audit_row_count: int
    pipeline_status: str
    action_issue_count: int | None
    report_paths: dict[str, str]
    stages: dict[str, str]


def completed_report_files(download_dir: Path, after: datetime | None = None) -> list[Path]:
    files = list_completed_report_downloads(download_dir, after)
    valid_files = [
        path
        for path in files
        if path.suffix.lower() in ALLOWED_EXTENSIONS and path.stat().st_size > 0
    ]
    return sorted(set(valid_files), key=lambda item: item.stat().st_mtime, reverse=True)


def classify_launch_failure(detail: str) -> tuple[str, str, str]:
    if "ERR_NETWORK_ACCESS_DENIED" in detail:
        return (
            "blocked_by_environment",
            "NETWORK_ACCESS_DENIED",
            "광고센터 접속이 현재 실행 환경에서 제한되었습니다. 사용자 실제 PC 또는 접속 가능한 브라우저 환경에서 재검증이 필요합니다.",
        )
    return (
        "failed",
        "BROWSER_LAUNCH_FAILED",
        "전용 수집 브라우저 실행 또는 광고센터 접속 중 오류가 발생했습니다.",
    )


def count_today_action_rows(excel_path: Path) -> int | None:
    try:
        import pandas as pd

        xls = pd.ExcelFile(excel_path)
        target_sheet = next((sheet for sheet in xls.sheet_names if "오늘" in sheet and "일" in sheet), "")
        if not target_sheet:
            return None
        frame = pd.read_excel(excel_path, sheet_name=target_sheet)
        return len(frame)
    except Exception:  # noqa: BLE001
        return None


def run_pipeline_for_file(target_file: Path) -> tuple[str, int, str, int | None, dict[str, str], str, str]:
    try:
        audit = audit_media_file(target_file)
    except Exception as error:  # noqa: BLE001
        return "failed", 0, "not_run", None, {}, "AUDIT_FAILED", str(error)

    if audit.load_status != "성공":
        return audit.load_status, audit.row_count, "not_run", None, {}, "AUDIT_NOT_SUCCESS", audit.error

    try:
        output_dir = EVIDENCE_DIR / "g_daily_analysis_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        pipeline = run_analysis_pipeline(target_file, output_dir, advertiser="G마켓 파워클릭")
        report_paths = {
            "markdown": str(pipeline.report_paths.markdown),
            "text": str(pipeline.report_paths.text),
            "excel": str(pipeline.report_paths.excel),
        }
        action_count = count_today_action_rows(pipeline.report_paths.excel)
        return "성공", audit.row_count, "success", action_count, report_paths, "", ""
    except Exception as error:  # noqa: BLE001
        return "성공", audit.row_count, "failed", None, {}, "PIPELINE_FAILED", str(error)


def build_result(
    *,
    started_at: datetime,
    final_status: str,
    error_code: str,
    error_message: str,
    detected_files: list[Path],
    selected_file: Path | None,
    audit_status: str = "not_run",
    audit_row_count: int = 0,
    pipeline_status: str = "not_run",
    action_issue_count: int | None = None,
    report_paths: dict[str, str] | None = None,
    browser_fallback_available: bool = False,
) -> GmarketPowerclickPocResult:
    profile = gmarket_legacy.get_profile(PROJECT_ROOT)
    collection_id = f"gmarket_computer_use_{started_at.strftime('%Y%m%d_%H%M%S')}"
    stages = {
        "scope": "gmarket_powerclick_g_daily_only",
        "file_created": "success" if selected_file else "not_passed",
        "file_detected": "success" if selected_file else "not_passed",
        "raw_media_audit": audit_status,
        "analysis_pipeline": pipeline_status,
        "today_actions": "checked" if action_issue_count is not None else "not_run",
        "report_generation": "checked" if report_paths else "not_run",
    }
    return GmarketPowerclickPocResult(
        collection_id=collection_id,
        checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        final_status=final_status,
        error_code=error_code,
        error_message=error_message,
        computer_use_available=True,
        browser_fallback_available=browser_fallback_available,
        scope="G마켓 파워클릭 G 일별 리포트 다운로드 POC 1개",
        download_dir=str(profile.download_dir),
        browser_profile_dir=str(profile.browser_profile_dir),
        detected_files=[str(path) for path in detected_files],
        selected_file=str(selected_file) if selected_file else "",
        file_size=selected_file.stat().st_size if selected_file else 0,
        audit_status=audit_status,
        audit_row_count=audit_row_count,
        pipeline_status=pipeline_status,
        action_issue_count=action_issue_count,
        report_paths=report_paths or {},
        stages=stages,
    )


def record_collection_log(result: GmarketPowerclickPocResult, started_at: datetime) -> None:
    normalized_status = (
        result.final_status
        if result.final_status in {"success", "partial", "no_data", "failed"}
        else "failed"
    )
    append_collection_log(
        CollectionLogRecord(
            collection_id=result.collection_id,
            advertiser_id="gmarket:account_pending",
            media="gmarket",
            started_at=started_at.strftime("%Y-%m-%d %H:%M:%S"),
            finished_at=result.checked_at,
            status=normalized_status,
            rows_collected=result.audit_row_count,
            file_count=len(result.detected_files),
            storage_used_mb=round(result.file_size / 1024 / 1024, 4),
            error_code=result.error_code,
            error_message=result.error_message,
        )
    )


def write_evidence(result: GmarketPowerclickPocResult) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_DIR / f"gmarket_computer_use_download_poc_{result.collection_id[-15:]}.json"
    evidence_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return evidence_path


def write_report(result: GmarketPowerclickPocResult, evidence_path: Path) -> None:
    lines = [
        "# G마켓 Computer Use 다운로드 POC",
        "",
        f"작성일: {result.checked_at}",
        "",
        "## 1. 이번 작업 목적",
        "",
        "G마켓 파워클릭 G 일별 리포트가 실제 Excel 또는 CSV 파일로 생성되고 AIMAOS 다운로드 폴더에서 감지되는지 검증한다.",
        "",
        "## 2. 작업 범위 제한",
        "",
        "- 이번 구현 범위는 G마켓 파워클릭 G 일별 POC 1개로 제한",
        "- 옥션, 11번가, 쿠팡, Google, Meta, Kakao 구현 없음",
        "- 기존 분석/보고/Rule Engine/UI 로직 수정 없음",
        "",
        "## 3. API 우선 / Computer Use 보조 원칙",
        "",
        "공식 API가 가능한 매체는 API를 우선한다. G마켓처럼 API 활용이 제한적인 매체는 사용자가 직접 인증한 화면에서 리포트 다운로드를 보조하는 방식으로 검증한다.",
        "",
        "## 4. 실제 수정한 파일",
        "",
        "- `aimaos/collectors/marketplace/gmarket_computer_use_download_poc.py`",
        "- `docs/GMARKET_COMPUTER_USE_DOWNLOAD_POC.md`",
        "- `docs/COMPUTER_USE_CONNECTOR_STRATEGY.md`",
        "",
        "## 5. 새로 추가한 파일",
        "",
        f"- `{evidence_path}`",
        "",
        "## 6. Computer Use 실제 사용 가능 여부",
        "",
        f"- 인앱 브라우저 기반 화면 확인 가능 여부: {'가능' if result.computer_use_available else '불가'}",
        f"- 대체 전용 브라우저 실행 가능 여부: {'가능' if result.browser_fallback_available else '제한 또는 실패'}",
        "",
        "## 7. 확인한 리포트 타입",
        "",
        "- G마켓 파워클릭 G 일별",
        "",
        "## 8. 다운로드 파일",
        "",
        f"- 다운로드 폴더: `{result.download_dir}`",
        f"- 감지 파일 수: {len(result.detected_files)}",
        f"- 선택 파일: `{result.selected_file or '-'}`",
        f"- 파일 크기: {result.file_size:,} bytes",
        "",
        "## 9. 후속 검증",
        "",
        f"- raw_media_audit.py 실행 여부: {result.audit_status}",
        f"- 분석 파이프라인 연결 여부: {result.pipeline_status}",
        f"- 오늘 해야 할 일 생성 확인: {result.action_issue_count if result.action_issue_count is not None else '미실행'}",
        f"- 보고서 생성 여부: {'생성' if result.report_paths else '미실행'}",
        "",
        "## 10. collection_log 기록 내용",
        "",
        f"- collection_id: `{result.collection_id}`",
        f"- status: `{result.final_status}`",
        f"- error_code: `{result.error_code}`",
        f"- error_message: {result.error_message or '-'}",
        "",
        "## 11. Data Status Center 반영 여부",
        "",
        "collection_log와 증거 파일은 기록되었다. Data Status Center는 다운로드 파일이 없으면 G마켓을 최신 수집 성공으로 표시하지 않아야 한다.",
        "",
        "## 12. 실패 원인",
        "",
        f"- {result.error_message or '-'}",
        "",
        "## 13. 다음 검증 조건",
        "",
        "1. 사용자가 직접 ESM에 로그인",
        "2. G마켓 광고센터 파워클릭 리포트 화면 진입",
        "3. G 일별 선택",
        "4. 최근 30일 또는 90일 조회",
        "5. 조회 결과 1건 이상 확인",
        "6. Excel 또는 CSV 다운로드",
        "7. AIMAOS 다운로드 폴더에서 파일 감지",
        "",
        "## 14. 보안/정책 리스크",
        "",
        "- 비밀번호 저장 없음",
        "- 로그인 자동 입력 없음",
        "- 2차 인증 우회 없음",
        "- 캡차 우회 없음",
        "- 광고비/입찰/예산/상품 수정 없음",
        "",
        "## 15. 최종 판정",
        "",
        f"`{result.final_status}`",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_strategy_summary() -> None:
    STRATEGY_PATH.write_text(
        "\n".join(
            [
                "# Computer Use Connector Strategy",
                "",
                "## 원칙",
                "",
                "AIMAOS 데이터 수집 우선순위는 다음과 같다.",
                "",
                "1. 공식 API 수집",
                "2. 공식 리포트 다운로드 자동화",
                "3. Computer Use 기반 반자동 다운로드",
                "4. 수동 업로드",
                "",
                "## 이번 POC 범위",
                "",
                "이번 작업은 G마켓 파워클릭 G 일별 리포트 다운로드 검증 1개로 제한한다.",
                "",
                "## 적용하지 않는 것",
                "",
                "- 자동 로그인",
                "- 비밀번호 저장",
                "- 2차 인증 우회",
                "- 캡차 우회",
                "- 광고비/입찰/예산 변경",
                "- 광고 생성 또는 수정",
                "",
                "## 상태 기준",
                "",
                "- success: 파일 감지, 진단, 분석, 오늘 해야 할 일, 보고서 생성까지 통과",
                "- partial: 파일 생성 또는 진단 일부만 통과",
                "- no_data: 조회는 됐지만 결과 0건",
                "- failed: 화면 인식, 다운로드, 파일 진단, 파이프라인 중 실패",
                "- blocked_by_environment: 현재 실행 환경에서 광고센터 접속 제한",
                "- needs_user_authentication: 사용자 로그인 또는 인증 필요",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_poc(*, wait_seconds: int, watch_downloads_only: bool) -> GmarketPowerclickPocResult:
    load_dotenv(PROJECT_ROOT / ".env")
    started_at = datetime.now()
    profile = gmarket_legacy.get_profile(PROJECT_ROOT)
    ensure_writable_directory(profile.download_dir)
    ensure_writable_directory(profile.browser_profile_dir)

    if not watch_downloads_only:
        launch_result = open_manual_collection_browser(
            profile.browser_profile_dir,
            profile.download_dir,
            target_url=profile.report_url or profile.login_url or "https://www.esmplus.com",
            wait_seconds=wait_seconds,
        )
        if launch_result.status != "success":
            final_status, error_code, error_message = classify_launch_failure(launch_result.detail)
            result = build_result(
                started_at=started_at,
                final_status=final_status,
                error_code=error_code,
                error_message=error_message,
                detected_files=[],
                selected_file=None,
                browser_fallback_available=False,
            )
            record_collection_log(result, started_at)
            evidence_path = write_evidence(result)
            write_report(result, evidence_path)
            write_strategy_summary()
            return result

    detected_files = completed_report_files(
        profile.download_dir,
        after=None if watch_downloads_only else started_at,
    )
    selected_file = detected_files[0] if detected_files else None
    if selected_file is None:
        final_status = "needs_user_authentication" if not watch_downloads_only else "failed"
        error_code = "USER_AUTH_REQUIRED" if not watch_downloads_only else "DOWNLOAD_FILE_NOT_FOUND"
        error_message = (
            "사용자 직접 로그인 또는 인증 후 G마켓 파워클릭 G 일별 리포트 다운로드가 필요합니다."
            if not watch_downloads_only
            else "G마켓 파워클릭 G 일별 리포트 다운로드 파일이 감지되지 않았습니다."
        )
        result = build_result(
            started_at=started_at,
            final_status=final_status,
            error_code=error_code,
            error_message=error_message,
            detected_files=detected_files,
            selected_file=None,
            browser_fallback_available=True,
        )
        record_collection_log(result, started_at)
        evidence_path = write_evidence(result)
        write_report(result, evidence_path)
        write_strategy_summary()
        return result

    audit_status, row_count, pipeline_status, action_count, report_paths, error_code, error_message = run_pipeline_for_file(selected_file)
    if pipeline_status == "success" and action_count is not None and report_paths:
        final_status = "success"
    elif audit_status == "성공":
        final_status = "partial"
    else:
        final_status = "failed"

    result = build_result(
        started_at=started_at,
        final_status=final_status,
        error_code=error_code,
        error_message=error_message,
        detected_files=detected_files,
        selected_file=selected_file,
        audit_status=audit_status,
        audit_row_count=row_count,
        pipeline_status=pipeline_status,
        action_issue_count=action_count,
        report_paths=report_paths,
        browser_fallback_available=True,
    )
    record_collection_log(result, started_at)
    evidence_path = write_evidence(result)
    write_report(result, evidence_path)
    write_strategy_summary()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Gmarket Powerclick G daily download POC.")
    parser.add_argument("--profile", default="gmarket_legacy", choices=["gmarket_legacy"])
    parser.add_argument("--wait-seconds", type=int, default=300)
    parser.add_argument("--watch-downloads-only", action="store_true")
    args = parser.parse_args()
    result = run_poc(wait_seconds=args.wait_seconds, watch_downloads_only=args.watch_downloads_only)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
