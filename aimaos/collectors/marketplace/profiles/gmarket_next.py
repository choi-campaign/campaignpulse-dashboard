from __future__ import annotations

from pathlib import Path

from aimaos.collectors.marketplace.base_collector import (
    PROFILE_NEEDS_URL,
    MarketplaceProfile,
    profile_dirs,
)


def get_profile(project_root: Path) -> MarketplaceProfile:
    downloads, browser_profile = profile_dirs(project_root, "gmarket", "next")
    return MarketplaceProfile(
        media_key="gmarket",
        media_name="G마켓",
        profile_version="next",
        login_url_env_key="AIMAOS_POC_GMARKET_NEXT_LOGIN_URL",
        report_url_env_key="AIMAOS_POC_GMARKET_NEXT_REPORT_URL",
        selectors={},
        date_picker_rule="신규 광고센터 공개 후 별도 확인이 필요합니다.",
        download_button_selector="",
        expected_file_pattern="*.xls*",
        download_dir=downloads,
        browser_profile_dir=browser_profile,
        status=PROFILE_NEEDS_URL,
        notes=("신규 광고센터 대응용 placeholder profile입니다.",),
    )

