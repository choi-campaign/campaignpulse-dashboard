from __future__ import annotations

from pathlib import Path

from aimaos.collectors.marketplace.base_collector import (
    PROFILE_DEFERRED,
    MarketplaceProfile,
    profile_dirs,
)


def get_profile(project_root: Path) -> MarketplaceProfile:
    downloads, browser_profile = profile_dirs(project_root, "coupang", "ads")
    return MarketplaceProfile(
        media_key="coupang",
        media_name="쿠팡",
        profile_version="ads",
        login_url_env_key="AIMAOS_POC_COUPANG_LOGIN_URL",
        report_url_env_key="AIMAOS_POC_COUPANG_REPORT_URL",
        default_login_url="https://advertising.coupang.com/",
        selectors={},
        date_picker_rule="인증/보안 정책 확인 전에는 자동화하지 않습니다.",
        download_button_selector="",
        expected_file_pattern="*.xls*",
        download_dir=downloads,
        browser_profile_dir=browser_profile,
        status=PROFILE_DEFERRED,
        notes=("보안 정책 리스크가 커서 이번 POC에서는 구조 검토만 기록합니다.",),
    )
