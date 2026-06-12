from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CollectionResult:
    platform: str
    account_name: str
    downloaded_files: list[Path]
    log_path: Path | None = None


class CollectorNotImplementedError(NotImplementedError):
    pass

