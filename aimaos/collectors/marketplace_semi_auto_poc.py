from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path

from aimaos.collectors.naver_searchad_poc import PocStepResult


@dataclass(frozen=True)
class MarketplacePocTarget:
    media: str
    env_url_key: str
    required_checks: tuple[str, ...]


MARKETPLACE_TARGETS = {
    "gmarket": MarketplacePocTarget(
        media="G마켓",
        env_url_key="AIMAOS_POC_GMARKET_REPORT_URL",
        required_checks=(
            "광고센터 진입 가능 여부",
            "광고주 선택 가능 여부",
            "리포트 메뉴 이동 가능 여부",
            "기간 선택 가능 여부",
            "Excel 다운로드 가능 여부",
            "다운로드 파일 자동 감지 가능 여부",
            "기존 분석 파이프라인 연결 가능 여부",
            "캡차 발생 여부",
            "2차 인증 발생 여부",
            "광고센터 구조 변경 대응 가능성",
        ),
    ),
    "auction": MarketplacePocTarget(
        media="옥션",
        env_url_key="AIMAOS_POC_AUCTION_REPORT_URL",
        required_checks=(
            "광고센터 진입 가능 여부",
            "광고주 선택 가능 여부",
            "리포트 메뉴 이동 가능 여부",
            "기간 선택 가능 여부",
            "Excel 다운로드 가능 여부",
            "다운로드 파일 자동 감지 가능 여부",
            "기존 분석 파이프라인 연결 가능 여부",
            "캡차 발생 여부",
            "2차 인증 발생 여부",
            "광고센터 구조 변경 대응 가능성",
        ),
    ),
    "11st": MarketplacePocTarget(
        media="11번가",
        env_url_key="AIMAOS_POC_11ST_REPORT_URL",
        required_checks=(
            "광고 리포트 다운로드 가능 여부",
            "광고주 전환 가능 여부",
            "파일 구조 분석",
            "기존 파이프라인 연결 가능 여부",
        ),
    ),
}


def run_marketplace_preflight_poc(media_key: str, project_root: Path) -> list[PocStepResult]:
    target = MARKETPLACE_TARGETS[media_key]
    results: list[PocStepResult] = []
    playwright_ready = importlib.util.find_spec("playwright") is not None
    report_url = os.getenv(target.env_url_key, "").strip()
    download_dir = project_root / "data" / "collection_poc" / media_key / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    if playwright_ready:
        results.append(PocStepResult("브라우저 자동화 실행 환경", "준비됨", "Playwright 패키지가 설치되어 있습니다."))
    else:
        results.append(PocStepResult("브라우저 자동화 실행 환경", "실행 불가", "Playwright 패키지가 설치되어 있지 않습니다."))

    if report_url:
        results.append(PocStepResult("리포트 시작 URL", "준비됨", f"{target.env_url_key} 값이 설정되어 있습니다."))
    else:
        results.append(PocStepResult("리포트 시작 URL", "실행 불가", f"{target.env_url_key} 환경변수에 광고센터 리포트 URL을 설정해야 합니다."))

    for check in target.required_checks:
        if not playwright_ready:
            results.append(PocStepResult(check, "실행 불가", "브라우저 자동화 실행 환경이 없어 실제 로그인/다운로드 검증을 실행하지 못했습니다."))
        elif not report_url:
            results.append(PocStepResult(check, "실행 불가", "광고센터 리포트 시작 URL이 없어 실제 화면 검증을 실행하지 못했습니다."))
        else:
            results.append(PocStepResult(check, "대기", "사용자 직접 로그인 세션에서 실제 화면을 열어 검증해야 합니다."))

    results.append(
        PocStepResult(
            "다운로드 감지 폴더",
            "준비됨",
            f"다운로드 감지 후보 폴더: {download_dir}",
            str(download_dir),
        )
    )
    return results
