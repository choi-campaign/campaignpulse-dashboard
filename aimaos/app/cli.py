from __future__ import annotations

import argparse

from aimaos.pipeline import run_analysis_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AIMAOS MVP 1 광고 데이터 분석기")
    parser.add_argument("--input", required=True, help="분석할 엑셀 또는 CSV 파일 경로")
    parser.add_argument("--output", default="data/reports", help="보고서 저장 폴더")
    parser.add_argument("--advertiser", default="광고주", help="보고서에 표시할 광고주명")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    result = run_analysis_pipeline(
        input_path=args.input,
        output_dir=args.output,
        advertiser=args.advertiser,
    )

    print("AIMAOS 분석 완료")
    print(f"입력 파일: {result.input_path}")
    print(f"분석 행 수: {result.rows}")
    print(f"Markdown: {result.report_paths.markdown}")
    print(f"TXT: {result.report_paths.text}")
    print(f"XLSX: {result.report_paths.excel}")


if __name__ == "__main__":
    main()

