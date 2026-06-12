from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from aimaos.collectors.marketplace.base_collector import (
    MarketplacePocResult,
    MarketplaceProfile,
    PocStep,
    ensure_writable_directory,
)
from aimaos.collectors.marketplace.browser_session import (
    find_browser_executable,
    open_manual_collection_browser,
    playwright_installed,
    smoke_launch_collection_browser,
    watch_ad_center_entry,
)
from aimaos.collectors.marketplace.download_watcher import list_completed_downloads
from aimaos.collectors.marketplace.profiles import (
    auction_legacy,
    auction_next,
    coupang_ads,
    elevenst_adoffice,
    gmarket_legacy,
    gmarket_next,
)
from aimaos.pipeline import run_analysis_pipeline
from aimaos.validators.raw_media_audit import audit_media_file


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = PROJECT_ROOT / "docs" / "GMARKET_AUCTION_DOWNLOAD_POC_RESULT.md"
AD_CENTER_ENTRY_REPORT_PATH = PROJECT_ROOT / "docs" / "GMARKET_AUCTION_AD_CENTER_ENTRY_POC.md"
ELEVENST_REPORT_PATH = PROJECT_ROOT / "docs" / "ELEVENST_ADOFFICE_COLLECTION_POC.md"
COUPANG_REPORT_PATH = PROJECT_ROOT / "docs" / "COUPANG_ADS_COLLECTION_POC.md"
EVIDENCE_ROOT = PROJECT_ROOT / "data" / "collection_poc" / "marketplace"


def load_marketplace_profiles(project_root: Path) -> list[MarketplaceProfile]:
    return [
        gmarket_legacy.get_profile(project_root),
        auction_legacy.get_profile(project_root),
        gmarket_next.get_profile(project_root),
        auction_next.get_profile(project_root),
        elevenst_adoffice.get_profile(project_root),
        coupang_ads.get_profile(project_root),
    ]


def run_marketplace_download_poc(project_root: Path = PROJECT_ROOT) -> list[MarketplacePocResult]:
    load_dotenv(project_root / ".env")
    checked_at = datetime.now()
    profiles = load_marketplace_profiles(project_root)

    smoke_download_dir = EVIDENCE_ROOT / "_browser_smoke_downloads"
    smoke_profile_dir = EVIDENCE_ROOT / "_browser_smoke_profile"
    browser_smoke = smoke_launch_collection_browser(
        smoke_profile_dir,
        smoke_download_dir,
        headless=False,
        target_url="about:blank",
    )

    results = [
        evaluate_profile(profile, checked_at, browser_smoke.status == "success", browser_smoke.detail)
        for profile in profiles
    ]
    write_json_evidence(results, browser_smoke.browser_executable)
    REPORT_PATH.write_text(build_report(results, browser_smoke), encoding="utf-8")
    return results


def run_manual_profile_session(profile_id: str, wait_seconds: int, project_root: Path = PROJECT_ROOT) -> None:
    load_dotenv(project_root / ".env")
    profiles = {profile.profile_id: profile for profile in load_marketplace_profiles(project_root)}
    if profile_id not in profiles:
        valid = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown profile_id '{profile_id}'. Valid profiles: {valid}")

    profile = profiles[profile_id]
    ensure_writable_directory(profile.download_dir)
    ensure_writable_directory(profile.browser_profile_dir)
    target_url = profile.report_url or profile.login_url or "about:blank"
    result = open_manual_collection_browser(
        profile.browser_profile_dir,
        profile.download_dir,
        target_url=target_url,
        wait_seconds=wait_seconds,
    )
    print(f"{profile.profile_id}: {result.status} - {result.detail}")


def run_ad_center_entry_check(
    profile_id: str,
    wait_seconds: int,
    entry_url: str = "",
    project_root: Path = PROJECT_ROOT,
) -> None:
    load_dotenv(project_root / ".env")
    profiles = {profile.profile_id: profile for profile in load_marketplace_profiles(project_root)}
    if profile_id not in profiles:
        valid = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown profile_id '{profile_id}'. Valid profiles: {valid}")

    profile = profiles[profile_id]
    ensure_writable_directory(profile.download_dir)
    ensure_writable_directory(profile.browser_profile_dir)
    target_url = entry_url or profile.report_url or profile.login_url or "about:blank"
    result = watch_ad_center_entry(
        profile.browser_profile_dir,
        profile.download_dir,
        target_url=target_url,
        wait_seconds=wait_seconds,
    )
    evidence_path = write_ad_center_entry_evidence(profile, result)
    report_path = entry_report_path(profile)
    report_path.write_text(
        build_ad_center_entry_report(profile, result, evidence_path),
        encoding="utf-8",
    )
    print(report_path)


def entry_report_path(profile: MarketplaceProfile) -> Path:
    if profile.media_key == "11st":
        return ELEVENST_REPORT_PATH
    if profile.media_key == "coupang":
        return COUPANG_REPORT_PATH
    return AD_CENTER_ENTRY_REPORT_PATH


def write_ad_center_entry_evidence(profile: MarketplaceProfile, result) -> Path:
    evidence_dir = EVIDENCE_ROOT / profile.profile_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"ad_center_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "profile_id": profile.profile_id,
        "media_name": profile.media_name,
        "status": result.status,
        "detail": result.detail,
        "browser_executable": result.browser_executable,
        "started_url": result.started_url,
        "popup_count": result.popup_count,
        "observed_pages": [asdict(page) for page in result.observed_pages],
    }
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return evidence_path


def build_ad_center_entry_report(profile: MarketplaceProfile, result, evidence_path: Path) -> str:
    observed_lines = []
    if result.observed_pages:
        observed_lines.extend(["| 구분 | 번호 | URL | 제목 |", "| --- | --- | --- | --- |"])
        for page in result.observed_pages:
            observed_lines.append(f"| {page.event} | {page.page_index} | `{page.url}` | {page.title or '-'} |")
    else:
        observed_lines.append("- 관찰된 페이지가 없습니다.")

    if profile.media_key in {"gmarket", "auction"}:
        actual_result_lines = [
            "- 전용 수집 브라우저 실행: 성공",
            "- ESM 로그인: 성공",
            "- 광고센터 진입: 성공",
            "- 새 창 처리: 성공",
            "- 리포트 다운로드: 최근 광고 데이터 없음으로 보류",
            "- 이번 단계 결론: 다운로드 자동화 전, 광고 집행 데이터가 있는 계정 또는 기간으로 재검증해야 합니다.",
        ]
        current_conclusion = (
            "조건부 가능입니다. 전용 브라우저, ESM 로그인, 광고센터 진입, 새 창 처리는 통과했습니다. "
            "다만 최근 광고 데이터가 없어 리포트 다운로드와 파일 감지는 아직 검증하지 못했습니다."
        )
    else:
        actual_result_lines = [
            "- 전용 수집 브라우저 실행: 검증 대상",
            f"- 공식 진입 URL: `{result.started_url}`",
            "- 로그인 인증: 미검증",
            "- 광고센터 진입: 미검증",
            "- 리포트 다운로드: 미검증",
            "- 이번 단계 결론: 실제 계정 로그인 전 구조 준비 단계입니다.",
        ]
        current_conclusion = (
            "구조 준비 단계입니다. 공식 진입 URL과 전용 브라우저 구조는 준비했지만, "
            "실제 로그인, 리포트 화면, 다운로드 파일 구조는 아직 계정 기반 검증이 필요합니다."
        )

    return "\n".join(
        [
            f"# {profile.media_name} 광고센터 진입 POC",
            "",
            f"작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 1. 현재 실제 테스트 결과 반영",
            "",
            *actual_result_lines,
            "",
            "## 2. 멈춘 단계",
            "",
            f"- 대상 profile: `{profile.profile_id}`",
            f"- 대상 매체: {profile.media_name}",
            f"- 시작 URL: `{result.started_url}`",
            f"- 관찰 상태: {result.status}",
            f"- 새 페이지/팝업 감지 수: {result.popup_count}",
            f"- 관찰 증거 파일: `{evidence_path}`",
            "",
            "## 3. 가능한 원인 후보",
            "",
            "| 원인 후보 | 현재 판단 | 확인 방법 |",
            "| --- | --- | --- |",
            "| 광고센터 URL 문제 | 가능성 있음 | ESM 로그인 후 광고센터 버튼의 실제 이동 URL을 확인합니다. |",
            "| 새 창/팝업 전환 문제 | 가능성 있음 | 광고센터 버튼 클릭 시 새 탭 또는 새 창이 열리는지 확인합니다. |",
            "| 로그인 세션 전달 문제 | 가능성 있음 | 로그인 완료 탭과 광고센터 탭의 도메인이 다른지 확인합니다. |",
            "| 대행사 권한 문제 | 가능성 있음 | 동일 계정으로 일반 브라우저에서 광고주 광고센터 진입이 가능한지 확인합니다. |",
            "| 별도 도메인/SSO 사용 | 가능성 있음 | 이동 URL의 도메인과 인증 쿠키 적용 범위를 확인합니다. |",
            "| 자동화 브라우저 차단 가능성 | 가능성 있음 | 일반 Chrome과 전용 수집 브라우저의 동작 차이를 비교합니다. |",
            "",
            "## 4. 사용자가 확인할 내용",
            "",
            "1. 전용 수집 브라우저에서 ESM에 로그인합니다.",
            "2. 광고센터 버튼을 직접 클릭합니다.",
            "3. 같은 탭에서 URL이 바뀌는지 확인합니다.",
            "4. 새 탭 또는 새 창이 열리는지 확인합니다.",
            "5. 광고센터 화면까지 들어가면 그 URL을 복사해 `AIMAOS_POC_GMARKET_REPORT_URL` 또는 `AIMAOS_POC_AUCTION_REPORT_URL`에 넣습니다.",
            "6. 광고센터 진입이 안 되면 화면에 표시되는 안내 문구 또는 권한 오류를 기록합니다.",
            "",
            "## 5. 새 탭/팝업 감지 보강",
            "",
            "- Playwright persistent browser context에서 `context.on('page')` 이벤트를 감지하도록 보강했습니다.",
            "- 개별 페이지의 `popup` 이벤트도 기록합니다.",
            "- 실행 중 관찰된 모든 탭의 URL과 제목을 JSON 증거 파일로 저장합니다.",
            "- 다운로드는 아직 시도하지 않습니다.",
            "",
            "## 6. 광고센터 URL 직접 이동 옵션",
            "",
            "- 환경변수 방식 유지:",
            "  - `AIMAOS_POC_GMARKET_REPORT_URL`",
            "  - `AIMAOS_POC_AUCTION_REPORT_URL`",
            "- 실행 인자 방식 추가:",
            "  - `--entry-url \"광고센터_URL\"`",
            "",
            "## 7. 광고센터 진입만 검증하는 명령",
            "",
            "```powershell",
            ".\\.venv\\Scripts\\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --wait-seconds 300",
            "```",
            "",
            "옥션은 아래처럼 실행합니다.",
            "",
            "```powershell",
            ".\\.venv\\Scripts\\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile auction_legacy --wait-seconds 300",
            "```",
            "",
            "광고센터 URL을 직접 넣어 확인할 때는 아래처럼 실행합니다.",
            "",
            "```powershell",
            ".\\.venv\\Scripts\\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --entry-url \"광고센터_URL\" --wait-seconds 300",
            "```",
            "",
            "## 8. 관찰된 페이지",
            "",
            *observed_lines,
            "",
            "## 9. 자동 실행 환경 한계",
            "",
            f"- 자동 관찰 상태: {result.status}",
            f"- 자동 관찰 상세: {result.detail}",
            "- Codex 실행 환경에서는 외부 광고센터 URL 이동이 네트워크 정책으로 막힐 수 있습니다.",
            "- 따라서 최종 판단은 사용자가 전용 수집 브라우저에서 직접 인증한 실제 테스트 결과를 우선합니다.",
            "- 자동 관찰 증거는 탭/팝업 감지 구조와 시작 URL 기록 용도로 사용합니다.",
            "",
            "## 10. 다음 판단 기준",
            "",
            "- 성공: 전용 수집 브라우저에서 광고센터 화면 진입 URL이 확인됨",
            "- 부분 성공: 새 창/팝업은 감지됐지만 권한 또는 SSO 문제로 진입 실패",
            "- 실패: 로그인 후에도 광고센터 버튼 이동이 감지되지 않음",
            "",
            "## 11. 보안 원칙",
            "",
            "- 광고주 비밀번호 저장 금지",
            "- 캡차 우회 금지",
            "- 2차 인증 우회 금지",
            "- 사용자가 직접 인증 처리",
            "- AIMAOS는 인증 이후 반복 이동과 감지만 담당",
            "",
            "## 12. 현재 결론",
            "",
            current_conclusion,
        ]
    ) + "\n"


def evaluate_profile(
    profile: MarketplaceProfile,
    checked_at: datetime,
    browser_smoke_ok: bool,
    browser_smoke_detail: str,
) -> MarketplacePocResult:
    steps: list[PocStep] = []

    download_ok, download_detail = ensure_writable_directory(profile.download_dir)
    profile_ok, profile_detail = ensure_writable_directory(profile.browser_profile_dir)
    steps.append(PocStep("전용 다운로드 폴더", "success" if download_ok else "failed", download_detail, download_detail))
    steps.append(PocStep("전용 브라우저 프로필", "success" if profile_ok else "failed", profile_detail, profile_detail))
    steps.append(PocStep("Playwright 패키지", "success" if playwright_installed() else "failed", "설치됨" if playwright_installed() else "미설치"))

    browser_path = find_browser_executable()
    steps.append(PocStep("Chrome/Edge 실행 파일", "success" if browser_path else "failed", browser_path or "찾지 못함"))
    steps.append(PocStep("수집 브라우저 실행", "success" if browser_smoke_ok else "failed", browser_smoke_detail))

    if profile.login_url:
        steps.append(PocStep("로그인 시작 URL", "ready", "환경값 또는 기본값 확인됨"))
    else:
        steps.append(PocStep("로그인 시작 URL", "needs_info", f"{profile.login_url_env_key} 설정 필요"))

    if profile.report_url:
        steps.append(PocStep("리포트 시작 URL", "ready", f"{profile.report_url_env_key} 확인됨"))
    else:
        steps.append(PocStep("리포트 시작 URL", "needs_info", f"{profile.report_url_env_key} 설정 필요"))

    if profile.status == "deferred":
        steps.append(PocStep("실제 다운로드 검증", "deferred", "이번 POC 우선순위 밖입니다. 구조만 준비했습니다."))
        return MarketplacePocResult(profile, checked_at, steps)

    if not profile.report_url:
        steps.extend(
            [
                PocStep("광고센터 진입", "not_run", "리포트 URL 미확보로 실제 화면 검증 전입니다."),
                PocStep("기간 선택", "not_run", "리포트 화면 확인 후 selector/profile 작성이 필요합니다."),
                PocStep("Excel/CSV 다운로드", "not_run", "사용자 로그인 세션에서 실제 버튼 확인이 필요합니다."),
            ]
        )
    else:
        steps.extend(
            [
                PocStep("광고센터 진입", "ready", "사용자 직접 로그인 후 실제 화면에서 확인해야 합니다."),
                PocStep("기간 선택", "ready", "selector 확정 전까지는 수동/반자동 검증 단계입니다."),
                PocStep("Excel/CSV 다운로드", "ready", "다운로드 감지 폴더가 준비되어 있습니다."),
            ]
        )

    detected_files = list_completed_downloads(profile.download_dir, profile.expected_file_pattern)
    if detected_files:
        steps.append(PocStep("다운로드 파일 감지", "success", f"{len(detected_files)}개 파일 감지", str(detected_files[0])))
        return run_audit_and_pipeline(profile, checked_at, steps, detected_files)

    steps.append(PocStep("다운로드 파일 감지", "not_run", "아직 실제 다운로드 파일이 없습니다.", str(profile.download_dir)))
    return MarketplacePocResult(profile, checked_at, steps, detected_files=detected_files)


def run_audit_and_pipeline(
    profile: MarketplaceProfile,
    checked_at: datetime,
    steps: list[PocStep],
    detected_files: list[Path],
) -> MarketplacePocResult:
    audit_status = "not_run"
    pipeline_status = "not_run"
    action_issue_count: int | None = None
    report_paths: dict[str, str] = {}
    target_file = detected_files[0]

    try:
        audit = audit_media_file(target_file)
        audit_status = audit.load_status
        steps.append(PocStep("raw_media_audit 연결", "success", audit.load_status, str(target_file)))
    except Exception as error:  # noqa: BLE001
        steps.append(PocStep("raw_media_audit 연결", "failed", str(error), str(target_file)))
        return MarketplacePocResult(profile, checked_at, steps, detected_files, "failed", pipeline_status)

    try:
        output_dir = PROFILE_OUTPUT_DIR(profile)
        pipeline = run_analysis_pipeline(target_file, output_dir, advertiser=profile.media_name)
        pipeline_status = "success"
        action_issue_count = _count_today_actions(pipeline.report_paths.excel)
        report_paths = {
            "markdown": str(pipeline.report_paths.markdown),
            "text": str(pipeline.report_paths.text),
            "excel": str(pipeline.report_paths.excel),
        }
        steps.append(PocStep("기존 분석 파이프라인 연결", "success", "보고서 생성 완료", str(output_dir)))
    except Exception as error:  # noqa: BLE001
        pipeline_status = "failed"
        steps.append(PocStep("기존 분석 파이프라인 연결", "failed", str(error), str(target_file)))

    return MarketplacePocResult(
        profile=profile,
        checked_at=checked_at,
        steps=steps,
        detected_files=detected_files,
        audit_status=audit_status,
        pipeline_status=pipeline_status,
        action_issue_count=action_issue_count,
        report_paths=report_paths,
    )


def PROFILE_OUTPUT_DIR(profile: MarketplaceProfile) -> Path:
    out = EVIDENCE_ROOT / profile.profile_id / "analysis_output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _count_today_actions(excel_path: Path) -> int | None:
    try:
        import pandas as pd

        frame = pd.read_excel(excel_path, sheet_name="오늘해야할일")
        return len(frame)
    except Exception:  # noqa: BLE001
        return None


def write_json_evidence(results: list[MarketplacePocResult], browser_executable: str) -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "browser_executable": browser_executable,
        "results": [
            {
                "profile": {
                    **asdict(result.profile),
                    "download_dir": str(result.profile.download_dir),
                    "browser_profile_dir": str(result.profile.browser_profile_dir),
                    "login_url_set": bool(result.profile.login_url),
                    "report_url_set": bool(result.profile.report_url),
                },
                "checked_at": result.checked_at.isoformat(),
                "steps": [asdict(step) for step in result.steps],
                "detected_files": [str(path) for path in result.detected_files],
                "audit_status": result.audit_status,
                "pipeline_status": result.pipeline_status,
                "action_issue_count": result.action_issue_count,
                "report_paths": result.report_paths,
            }
            for result in results
        ],
    }
    (EVIDENCE_ROOT / "marketplace_download_poc_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_report(results: list[MarketplacePocResult], browser_smoke) -> str:
    primary = [result for result in results if result.profile.profile_id in {"gmarket_legacy", "auction_legacy"}]
    lines = [
        "# G마켓/옥션 반자동 리포트 수집 POC 결과",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 0. 최신 실제 테스트 결과",
        "",
        "- G마켓/옥션 전용 수집 브라우저 실행: 성공",
        "- ESM 로그인: 성공",
        "- 광고센터 진입: 성공",
        "- 새 창 처리: 성공",
        "- 다운로드 검증: 최근 광고 데이터 없음으로 보류",
        "- 다음 검증 조건: 최근 광고 집행 이력이 있는 광고주 계정 또는 조회 기간 필요",
        "",
        "## 1. Playwright 설치/실행 상태",
        "",
        f"- Playwright 패키지: {'설치됨' if playwright_installed() else '미설치'}",
        f"- 내장 Chromium 설치: 프로젝트 외부 AppData 권한 제한 및 네트워크 제한으로 미완료",
        f"- 기존 Chrome/Edge 사용 가능 여부: {'가능' if find_browser_executable() else '불가'}",
        f"- 사용 브라우저 실행 파일: `{browser_smoke.browser_executable or '없음'}`",
        f"- 전용 수집 브라우저 실행 테스트: {status_label(browser_smoke.status)}",
        f"- 실행 상세: {browser_smoke.detail}",
        "",
        "## 2. G마켓 POC 결과",
        "",
        *render_profile_summary(find_result(primary, "gmarket_legacy")),
        "",
        "## 3. 옥션 POC 결과",
        "",
        *render_profile_summary(find_result(primary, "auction_legacy")),
        "",
        "## 4. 11번가/쿠팡 보류 사유",
        "",
        "- 11번가: 실제 광고 리포트 URL, 로그인 흐름, 파일 구조가 아직 확인되지 않아 구조만 준비했습니다.",
        "- 쿠팡: 인증/보안 정책 리스크가 커서 이번 단계에서는 자동화 결론을 내리지 않습니다.",
        "- 두 매체 모두 실제 화면 확인 전까지는 브라우저 자동 조작을 진행하지 않습니다.",
        "",
        "## 5. 사용자 행동 수",
        "",
        "- 현재 검증 상태: 실제 광고센터 로그인 단계 전입니다.",
        "- 목표 행동 수: 최초 연결 시 사용자가 직접 로그인/2차 인증 1회, 이후 리포트 수집은 AIMAOS가 처리.",
        "- 현재 필요 행동: G마켓/옥션 리포트 URL 제공 또는 전용 수집 브라우저에서 직접 로그인 후 리포트 화면 확인.",
        "",
        "## 6. 캡차/2차 인증 발생 여부",
        "",
        "- 실제 로그인 화면을 통과하지 않았으므로 발생 여부는 아직 판단하지 않았습니다.",
        "- 캡차와 2차 인증이 발생하면 사용자가 직접 처리해야 합니다.",
        "- AIMAOS는 캡차 우회, 2차 인증 우회, 비밀번호 저장을 하지 않습니다.",
        "",
        "## 7. 다운로드 성공 여부",
        "",
        *render_download_status(primary),
        "",
        "## 8. 다운로드 파일 경로",
        "",
        *render_download_paths(primary),
        "",
        "## 9. raw_media_audit 연결",
        "",
        *render_audit_status(primary),
        "",
        "## 10. 분석 파이프라인 연결",
        "",
        *render_pipeline_status(primary),
        "",
        "## 11. 오늘 해야 할 일 생성",
        "",
        *render_action_status(primary),
        "",
        "## 12. 보고서 생성",
        "",
        *render_report_status(primary),
        "",
        "## 13. legacy/next profile 필요성",
        "",
        "- G마켓/옥션은 기존 광고센터와 신규 광고센터 전환 가능성을 분리해서 관리해야 합니다.",
        "- 현재는 `gmarket_legacy`, `auction_legacy` profile을 우선 검증 대상으로 둡니다.",
        "- 신규 광고센터 URL과 리포트 파일 구조가 확인되면 `gmarket_next`, `auction_next` profile에 selector와 다운로드 규칙을 별도 기록합니다.",
        "- 화면 selector는 코드 본문에 고정하지 않고 profile 파일에만 둡니다.",
        "",
        "## 14. 사업성 판단",
        "",
        business_judgement(primary, browser_smoke.status),
        "",
        "## 15. 다음 우선순위",
        "",
        "1. 실제 G마켓/옥션 광고센터 리포트 URL을 환경값으로 등록합니다.",
        "2. 전용 수집 브라우저에서 사용자가 직접 로그인하고 2차 인증을 처리합니다.",
        "3. 리포트 화면의 기간 선택과 다운로드 버튼 selector를 legacy profile에 기록합니다.",
        "4. 다운로드 파일이 감지되면 raw_media_audit와 기존 분석 파이프라인 연결을 재검증합니다.",
        "5. 성공 파일 기준으로 오늘 해야 할 일과 보고서 생성까지 한 번에 확인합니다.",
        "",
        "## 16. 최종 결론",
        "",
        final_judgement(primary, browser_smoke.status),
    ]
    return "\n".join(lines) + "\n"


def find_result(results: list[MarketplacePocResult], profile_id: str) -> MarketplacePocResult:
    for result in results:
        if result.profile.profile_id == profile_id:
            return result
    raise ValueError(profile_id)


def render_profile_summary(result: MarketplacePocResult) -> list[str]:
    lines = [
        f"- profile: `{result.profile.profile_id}`",
        f"- 로그인 URL 상태: {'확인됨' if result.profile.login_url else '미확보'}",
        f"- 리포트 URL 상태: {'확인됨' if result.profile.report_url else '미확보'}",
        f"- 다운로드 폴더: `{result.profile.download_dir}`",
        f"- 브라우저 프로필: `{result.profile.browser_profile_dir}`",
        "",
        "| 점검 항목 | 상태 | 내용 |",
        "| --- | --- | --- |",
    ]
    for step in result.steps:
        lines.append(f"| {step.name} | {status_label(step.status)} | {step.detail} |")
    return lines


def render_download_status(results: list[MarketplacePocResult]) -> list[str]:
    return [
        f"- {result.profile.media_name}: {'성공' if result.detected_files else '미검증'}"
        for result in results
    ]


def render_download_paths(results: list[MarketplacePocResult]) -> list[str]:
    lines = []
    for result in results:
        if result.detected_files:
            for path in result.detected_files:
                lines.append(f"- {result.profile.media_name}: `{path}`")
        else:
            lines.append(f"- {result.profile.media_name}: 아직 감지된 다운로드 파일 없음. 감지 폴더 `{result.profile.download_dir}`")
    return lines


def render_audit_status(results: list[MarketplacePocResult]) -> list[str]:
    return [f"- {result.profile.media_name}: {result.audit_status}" for result in results]


def render_pipeline_status(results: list[MarketplacePocResult]) -> list[str]:
    return [f"- {result.profile.media_name}: {result.pipeline_status}" for result in results]


def render_action_status(results: list[MarketplacePocResult]) -> list[str]:
    lines = []
    for result in results:
        if result.action_issue_count is None:
            lines.append(f"- {result.profile.media_name}: 실제 다운로드 파일이 없어 아직 생성 여부 미검증")
        else:
            lines.append(f"- {result.profile.media_name}: {result.action_issue_count}건")
    return lines


def render_report_status(results: list[MarketplacePocResult]) -> list[str]:
    lines = []
    for result in results:
        if not result.report_paths:
            lines.append(f"- {result.profile.media_name}: 실제 다운로드 파일이 없어 아직 보고서 생성 미검증")
            continue
        lines.append(f"- {result.profile.media_name}:")
        for name, path in result.report_paths.items():
            lines.append(f"  - {name}: `{path}`")
    return lines


def business_judgement(results: list[MarketplacePocResult], browser_status: str) -> str:
    if any(result.detected_files and result.pipeline_status == "success" for result in results):
        return "가능: 다운로드 파일 감지와 기존 분석 파이프라인 연결까지 확인되었습니다."
    if browser_status == "success":
        return "조건부 가능: 전용 수집 브라우저와 다운로드 감지 구조는 준비됐지만, 실제 광고센터 로그인/다운로드는 아직 계정 세션에서 검증해야 합니다."
    return "어려움: 브라우저 자동화 실행 환경부터 보완해야 합니다."


def final_judgement(results: list[MarketplacePocResult], browser_status: str) -> str:
    if any(result.detected_files and result.pipeline_status == "success" for result in results):
        return "가능. 단, 캡차/2차 인증은 사용자가 직접 처리하고 profile 유지보수 체계를 운영해야 합니다."
    if browser_status == "success":
        return "조건부 가능. 실행 환경은 통과했으며, 실제 리포트 URL과 로그인 세션에서 다운로드 성공 여부를 다음 단계에서 확인해야 합니다."
    return "어려움. 현재 환경에서는 수집 브라우저 실행이 안정적으로 확보되지 않았습니다."


def status_label(status: str) -> str:
    return {
        "success": "성공",
        "failed": "실패",
        "ready": "준비됨",
        "needs_info": "정보 필요",
        "not_run": "미실행",
        "deferred": "보류",
    }.get(status, status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AIMAOS marketplace download POC.")
    parser.add_argument("--report", action="store_true", help="Generate the POC report.")
    parser.add_argument(
        "--open-profile",
        help="Open a dedicated collection browser for manual login/download. Example: gmarket_legacy",
    )
    parser.add_argument(
        "--entry-check-profile",
        help="Open a dedicated collection browser and record ad center entry pages only. Example: gmarket_legacy",
    )
    parser.add_argument("--entry-url", default="", help="Optional ad center URL to open directly.")
    parser.add_argument("--wait-seconds", type=int, default=300, help="Seconds to keep the manual browser open.")
    args = parser.parse_args()
    if args.entry_check_profile:
        run_ad_center_entry_check(args.entry_check_profile, args.wait_seconds, args.entry_url)
        raise SystemExit(0)
    if args.open_profile:
        run_manual_profile_session(args.open_profile, args.wait_seconds)
    run_marketplace_download_poc()
    print(REPORT_PATH)
