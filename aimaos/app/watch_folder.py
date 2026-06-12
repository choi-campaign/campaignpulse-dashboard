from __future__ import annotations

import argparse
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from aimaos.pipeline import run_analysis_pipeline
from aimaos.validators.file_validator import SUPPORTED_EXTENSIONS


def is_supported(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def wait_until_stable(path: Path, checks: int = 3, interval: float = 1.0) -> bool:
    last_size = -1
    stable_count = 0
    for _ in range(checks * 3):
        if not path.exists():
            return False
        current_size = path.stat().st_size
        if current_size == last_size:
            stable_count += 1
            if stable_count >= checks:
                return True
        else:
            stable_count = 0
            last_size = current_size
        time.sleep(interval)
    return False


def process_file(path: Path, output_root: Path, advertiser: str) -> None:
    if not is_supported(path):
        return

    if not wait_until_stable(path):
        print(f"파일 복사가 끝나지 않아 건너뜁니다: {path}")
        return

    output_dir = output_root / path.stem
    result = run_analysis_pipeline(path, output_dir, advertiser)
    print(f"분석 완료: {path.name} -> {result.report_paths.markdown}")


class RawFolderHandler(FileSystemEventHandler):
    def __init__(self, output_root: Path, advertiser: str) -> None:
        self.output_root = output_root
        self.advertiser = advertiser

    def on_created(self, event) -> None:  # noqa: ANN001
        if event.is_directory:
            return
        process_file(Path(event.src_path), self.output_root, self.advertiser)

    def on_moved(self, event) -> None:  # noqa: ANN001
        if event.is_directory:
            return
        process_file(Path(event.dest_path), self.output_root, self.advertiser)


def process_existing_files(input_dir: Path, output_root: Path, advertiser: str) -> None:
    for path in sorted(input_dir.iterdir()):
        process_file(path, output_root, advertiser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AIMAOS raw 폴더 감시 분석기")
    parser.add_argument("--input-dir", default="data/raw", help="감시할 원본 데이터 폴더")
    parser.add_argument("--output-dir", default="data/reports", help="보고서 저장 루트 폴더")
    parser.add_argument("--advertiser", default="광고주", help="보고서에 표시할 광고주명")
    parser.add_argument("--once", action="store_true", help="기존 파일만 한 번 분석하고 종료")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.once:
        process_existing_files(input_dir, output_dir, args.advertiser)
        return

    process_existing_files(input_dir, output_dir, args.advertiser)
    observer = Observer()
    observer.schedule(RawFolderHandler(output_dir, args.advertiser), str(input_dir), recursive=False)
    observer.start()
    print(f"AIMAOS 폴더 감시 시작: {input_dir.resolve()}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

