from __future__ import annotations

from pathlib import Path

from aimaos.collectors.marketplace.base_collector import (
    PROFILE_DEFERRED,
    MarketplaceProfile,
    profile_dirs,
)


def get_profile(project_root: Path) -> MarketplaceProfile:
    downloads, browser_profile = profile_dirs(project_root, "11st", "adoffice")
    return MarketplaceProfile(
        media_key="11st",
        media_name="11번가",
        profile_version="adoffice",
        login_url_env_key="AIMAOS_POC_11ST_LOGIN_URL",
        report_url_env_key="AIMAOS_POC_11ST_REPORT_URL",
        default_login_url="https://adoffice.11st.co.kr/",
        selectors={},
        date_picker_rule="실제 광고 리포트 화면과 파일 구조 확인 후 작성합니다.",
        download_button_selector="",
        expected_file_pattern="*.xls*",
        download_dir=downloads,
        browser_profile_dir=browser_profile,
        status=PROFILE_DEFERRED,
        notes=("이번 POC에서는 구조만 준비하고 실제 다운로드 검증은 보류합니다.",),
    )
