from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class RetentionTarget:
    name: str
    path: Path
    days: int
    patterns: tuple[str, ...]


RETENTION_TARGETS = (
    RetentionTarget("raw", DATA_ROOT / "raw", 90, ("*.csv", "*.xlsx", "*.xls", "*.json")),
    RetentionTarget("processed", DATA_ROOT / "processed", 365, ("*.csv", "*.xlsx", "*.parquet", "*.duckdb")),
    RetentionTarget("reports", DATA_ROOT / "reports", 365, ("*.md", "*.txt", "*.xlsx", "*.pdf")),
    RetentionTarget("logs", DATA_ROOT / "logs", 180, ("*.log", "*.txt", "*.json")),
    RetentionTarget("screenshots", DATA_ROOT / "screenshots", 30, ("*.png", "*.jpg", "*.jpeg", "*.webp")),
)


def is_inside_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return False
    return True


def iter_target_files(target: RetentionTarget) -> list[Path]:
    if not target.path.exists():
        return []
    files: list[Path] = []
    for pattern in target.patterns:
        files.extend(path for path in target.path.rglob(pattern) if path.is_file())
    return sorted(set(files))


def file_age_days(path: Path, now: datetime) -> float:
    modified_at = datetime.fromtimestamp(path.stat().st_mtime)
    return (now - modified_at).total_seconds() / 86400


def build_cleanup_plan(now: datetime | None = None) -> dict[str, object]:
    now = now or datetime.now()
    target_summaries: list[dict[str, object]] = []
    delete_candidates: list[dict[str, object]] = []
    total_storage_mb = 0.0

    for target in RETENTION_TARGETS:
        files = iter_target_files(target)
        storage_mb = sum(path.stat().st_size for path in files) / 1024 / 1024
        total_storage_mb += storage_mb
        threshold_at = now - timedelta(days=target.days)
        due_files = []
        for path in files:
            age_days = file_age_days(path, now)
            if age_days > target.days:
                record = {
                    "group": target.name,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "age_days": round(age_days, 1),
                    "size_mb": round(path.stat().st_size / 1024 / 1024, 4),
                }
                due_files.append(record)
                delete_candidates.append(record)
        target_summaries.append(
            {
                "group": target.name,
                "path": str(target.path.relative_to(PROJECT_ROOT)),
                "retention_days": target.days,
                "file_count": len(files),
                "storage_mb": round(storage_mb, 4),
                "delete_candidate_count": len(due_files),
                "delete_candidate_mb": round(sum(item["size_mb"] for item in due_files), 4),
                "delete_before": threshold_at.strftime("%Y-%m-%d"),
            }
        )

    return {
        "checked_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(PROJECT_ROOT),
        "total_storage_mb": round(total_storage_mb, 4),
        "delete_candidate_count": len(delete_candidates),
        "delete_candidate_mb": round(sum(item["size_mb"] for item in delete_candidates), 4),
        "targets": target_summaries,
        "delete_candidates": delete_candidates,
    }


def write_plan(plan: dict[str, object], mode: str) -> Path:
    output_dir = DATA_ROOT / "storage"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"retention_cleanup_last_{mode}.json"
    output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def apply_cleanup(plan: dict[str, object]) -> int:
    removed = 0
    for item in plan["delete_candidates"]:
        candidate = PROJECT_ROOT / str(item["path"])
        if not is_inside_workspace(candidate):
            continue
        if candidate.exists() and candidate.is_file():
            candidate.unlink()
            removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect or apply the AIMAOS retention policy.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show cleanup candidates without deleting files.")
    mode.add_argument("--apply", action="store_true", help="Delete files that exceed the retention policy.")
    args = parser.parse_args()

    plan = build_cleanup_plan()
    if args.apply:
        removed = apply_cleanup(plan)
        plan["removed_count"] = removed
        output_path = write_plan(plan, "apply")
        print(f"cleanup applied: {removed} files")
    else:
        output_path = write_plan(plan, "dry_run")
        print("cleanup dry-run complete")
    print(f"summary_path: {output_path}")
    print(f"total_storage_mb: {plan['total_storage_mb']}")
    print(f"delete_candidate_count: {plan['delete_candidate_count']}")


if __name__ == "__main__":
    main()
