from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path


PROFILE_READY = "ready"
PROFILE_NEEDS_URL = "needs_url"
PROFILE_NEEDS_LOGIN = "needs_login"
PROFILE_DEFERRED = "deferred"


@dataclass(frozen=True)
class MarketplaceProfile:
    media_key: str
    media_name: str
    profile_version: str
    login_url_env_key: str
    report_url_env_key: str
    default_login_url: str = ""
    default_report_url: str = ""
    selectors: dict[str, str] = field(default_factory=dict)
    date_picker_rule: str = ""
    download_button_selector: str = ""
    expected_file_pattern: str = "*.xls*"
    download_dir: Path = Path()
    browser_profile_dir: Path = Path()
    status: str = PROFILE_NEEDS_URL
    notes: tuple[str, ...] = ()

    @property
    def login_url(self) -> str:
        return os.getenv(self.login_url_env_key, self.default_login_url).strip()

    @property
    def report_url(self) -> str:
        return os.getenv(self.report_url_env_key, self.default_report_url).strip()

    @property
    def profile_id(self) -> str:
        return f"{self.media_key}_{self.profile_version}"


@dataclass(frozen=True)
class PocStep:
    name: str
    status: str
    detail: str
    evidence_path: str = ""


@dataclass(frozen=True)
class MarketplacePocResult:
    profile: MarketplaceProfile
    checked_at: datetime
    steps: list[PocStep]
    detected_files: list[Path] = field(default_factory=list)
    audit_status: str = "not_run"
    pipeline_status: str = "not_run"
    action_issue_count: int | None = None
    report_paths: dict[str, str] = field(default_factory=dict)


def profile_dirs(project_root: Path, media_key: str, profile_version: str) -> tuple[Path, Path]:
    base = project_root / "data" / "collection_poc" / "marketplace" / f"{media_key}_{profile_version}"
    return base / "downloads", base / "browser_profile"


def ensure_writable_directory(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".aimaos_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(path)
    except Exception as error:  # noqa: BLE001
        return False, str(error)

