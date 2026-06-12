from __future__ import annotations

from pathlib import Path

from aimaos.collectors.marketplace.base_collector import (
    PROFILE_NEEDS_URL,
    MarketplaceProfile,
    profile_dirs,
)


def get_profile(project_root: Path) -> MarketplaceProfile:
    downloads, browser_profile = profile_dirs(project_root, "gmarket", "legacy")
    return MarketplaceProfile(
        media_key="gmarket",
        media_name="G마켓",
        profile_version="legacy",
        login_url_env_key="AIMAOS_POC_GMARKET_LOGIN_URL",
        report_url_env_key="AIMAOS_POC_GMARKET_REPORT_URL",
        default_login_url="https://www.esmplus.com",
        selectors={
            "report_menu": "",
            "date_start": "",
            "date_end": "",
            "download_button": "",
        },
        date_picker_rule="리포트 화면 확인 후 profile에 기간 선택 규칙을 고정합니다.",
        download_button_selector="",
        expected_file_pattern="*.xls*",
        download_dir=downloads,
        browser_profile_dir=browser_profile,
        status=PROFILE_NEEDS_URL,
        notes=(
            "현재 G마켓 legacy 리포트 URL과 selector는 실제 화면에서 확인해야 합니다.",
            "신규 광고센터 전환 가능성이 있어 legacy와 next profile을 분리합니다.",
        ),
    )

