from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time


PARTIAL_SUFFIXES = (".crdownload", ".tmp", ".part")


def list_completed_downloads(download_dir: Path, pattern: str = "*.xls*", after: datetime | None = None) -> list[Path]:
    if not download_dir.exists():
        return []

    files = []
    for path in download_dir.glob(pattern):
        if not path.is_file() or path.suffix.lower() in PARTIAL_SUFFIXES:
            continue
        if after and datetime.fromtimestamp(path.stat().st_mtime) < after:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)


def wait_for_completed_download(
    download_dir: Path,
    pattern: str = "*.xls*",
    *,
    after: datetime | None = None,
    timeout_seconds: int = 30,
) -> Path | None:
    deadline = time.monotonic() + timeout_seconds
    last_size: dict[Path, int] = {}
    while time.monotonic() < deadline:
        for path in list_completed_downloads(download_dir, pattern, after):
            current_size = path.stat().st_size
            if last_size.get(path) == current_size and current_size > 0:
                return path
            last_size[path] = current_size
        time.sleep(1)
    return None

