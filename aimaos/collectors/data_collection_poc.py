from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from aimaos.collectors.marketplace_semi_auto_poc import run_marketplace_preflight_poc
from aimaos.collectors.naver_searchad_poc import PocStepResult, run_naver_searchad_poc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "docs" / "DATA_COLLECTION_POC_REPORT.md"
EVIDENCE_ROOT = PROJECT_ROOT / "data" / "collection_poc" / datetime.now().strftime("%Y%m%d_%H%M%S")


def run_data_collection_poc() -> dict[str, list[PocStepResult]]:
    load_dotenv(PROJECT_ROOT / ".env")
    results = {
        "네이버 검색광고": run_naver_searchad_poc(EVIDENCE_ROOT),
        "G마켓": run_marketplace_preflight_poc("gmarket", PROJECT_ROOT),
        "옥션": run_marketplace_preflight_poc("auction", PROJECT_ROOT),
        "11번가": run_marketplace_preflight_poc("11st", PROJECT_ROOT),
    }
    write_json_evidence(results)
    REPORT_PATH.write_text(build_report(results), encoding="utf-8")
    return results


def write_json_evidence(results: dict[str, list[PocStepResult]]) -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {media: [asdict(step) for step in steps] for media, steps in results.items()}
    (EVIDENCE_ROOT / "poc_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_report(results: dict[str, list[PocStepResult]]) -> str:
    lines = [
        "# AIMAOS 데이터 수집 POC 보고서",
        "",
        f"작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. POC 목적",
        "",
        "광고주가 매일 광고센터에 로그인하고, 리포트를 다운로드하고, 파일을 업로드하는 행위를 제거할 수 있는지 검증한다.",
        "",
        "이번 POC는 UI, Rule Engine, 분석 로직, 보고서 로직을 수정하지 않고 데이터 수집 가능성만 확인한다.",
        "",
        "## 2. POC 성공 기준",
        "",
        "| 기준 | 목표 | 현재 판정 |",
        "| --- | --- | --- |",
        "| 전일 데이터 수집 | 자동 또는 반자동으로 성공 | " + overall_daily_collection_status(results) + " |",
        "| 광고주 파일 다운로드 없음 | 광고주가 직접 파일을 받지 않음 | " + overall_no_download_status(results) + " |",
        "| 광고주 파일 업로드 없음 | AIMAOS가 수집 파일을 직접 파이프라인에 연결 | " + overall_pipeline_status(results) + " |",
        "| 광고주 행동 1클릭 이하 | 연결 후 반복 수집은 1클릭 이하 | " + overall_one_click_status(results) + " |",
        "| 핵심 지표 수집 | 노출, 클릭, 광고비, 주문, 매출, ROAS | " + overall_metric_status(results) + " |",
        "| 오늘 해야 할 일 생성 | 기존 엔진으로 자동 생성 | " + overall_action_status(results) + " |",
        "| 보고서 자동 생성 | 기존 보고서 엔진으로 자동 생성 | " + overall_report_status(results) + " |",
        "",
        "## 3. 매체별 가능 여부",
        "",
        "| 매체 | 현재 판정 | 핵심 사유 |",
        "| --- | --- | --- |",
    ]
    for media, steps in results.items():
        lines.append(f"| {media} | {media_final_status(media, steps)} | {media_reason(steps)} |")

    lines.extend(
        [
            "",
            "## 4. 매체별 상세 결과",
            "",
        ]
    )
    for media, steps in results.items():
        lines.extend(render_steps(media, steps))

    failure_lines = render_failure_reasons(results)
    lines.extend(
        [
            "",
            "## 5. 실패 원인",
            "",
            *failure_lines,
            "",
            "## 6. 정책 리스크",
            "",
            "- 캡차 또는 2차 인증은 사용자가 직접 처리해야 한다.",
            "- 광고센터 화면 자동화는 화면 구조 변경에 취약하다.",
            "- G마켓/옥션/11번가 판매자 API가 존재하더라도 광고센터 리포트 API와 동일하다고 볼 수 없다.",
            "- 리포트 다운로드 자동화는 각 광고센터 이용약관과 운영 정책 검토가 필요하다.",
            "",
            "## 7. 보안 리스크",
            "",
            "- 광고주 비밀번호 저장은 금지한다.",
            "- API Key와 Secret Key는 암호화 저장이 필요하다.",
            "- 쿠키/세션 저장은 사용자 편의성에는 유리하지만 계정 탈취 리스크가 있어 별도 보안 검토가 필요하다.",
            "- 서버가 광고주 계정 정보를 저장하고 직접 로그인하는 방식은 MVP에서 제외한다.",
            "",
            "## 8. 세션 유지 가능성 검토",
            "",
            "| 항목 | 가능성 | 리스크 | POC 판단 |",
            "| --- | --- | --- | --- |",
            "| 세션 유지 | 조건부 가능 | 세션 만료, 계정 보안 정책 | 구현 전 정책 검토 필요 |",
            "| 쿠키 저장 | 기술적으로 가능 | 민감 정보 저장, 유출 위험 | MVP에서는 저장 제외 권장 |",
            "| 브라우저 세션 재사용 | 가능 | 사용자별 격리와 만료 관리 필요 | 대행사 내부 POC에서만 제한 검증 |",
            "| 매일 로그인 제거 | 네이버 API는 가능성 높음 | API 권한/전환 데이터 제한 | 1순위 검증 |",
            "| 커머스 매체 로그인 최소화 | 조건부 가능 | 캡차/2차 인증/세션 만료 | 2순위 검증 |",
            "",
            "## 9. AIMAOS Connector 검토",
            "",
            "| 방식 | 장점 | 단점 | 현재 판단 |",
            "| --- | --- | --- | --- |",
            "| 브라우저 확장 프로그램 | 다운로드 감지, 로그인 세션 활용, 자동 전송이 자연스럽다 | 설치/배포/권한 안내/유지보수 부담 | v1 POC 이후 검토 |",
            "| 서버 제어 브라우저 | 설치 없이 웹 기반 운영 가능 | 세션 보안, 원격 브라우저 관리 필요 | G마켓/옥션 1차 POC 후보 |",
            "| 로컬 보조 프로그램 | 사용자 PC 다운로드 폴더 감지가 쉽다 | 설치가 필요해 이탈 가능성 | 보류 |",
            "",
            "## 10. 사업성 평가",
            "",
            "- 네이버 API 자동 수집이 성공하면 AIMAOS의 매일 접속 이유가 강해진다.",
            "- G마켓/옥션/11번가가 매일 로그인 없이 안정 수집되지 않으면 판매 난이도가 높아진다.",
            "- 광고주 행동이 1클릭을 초과하면 운영자용 내부 시스템에는 가능하지만 광고주 SaaS로는 약해진다.",
            "- 수집 실패 원인을 사람이 이해할 수 있게 안내하는 기능은 필수다.",
            "",
            "## 11. 추천 구조",
            "",
            "1. 네이버는 API 읽기 전용 자동 수집을 먼저 검증한다.",
            "2. G마켓/옥션은 사용자가 직접 로그인한 서버 제어 브라우저에서 리포트 다운로드 자동화를 검증한다.",
            "3. 다운로드된 파일은 raw_media_audit.py로 진단하고 기존 분석 파이프라인에 연결한다.",
            "4. 11번가는 실제 원본 파일과 광고센터 접근 경로 확보 후 검증한다.",
            "5. 세션 저장은 MVP에서 제외하고, 수집 성공률이 확인된 뒤 별도 보안 검토로 넘긴다.",
            "",
            "## 12. 구현 우선순위",
            "",
            "| 순위 | 작업 | 목표 |",
            "| --- | --- | --- |",
            "| 1 | 네이버 API 키 입력 후 실제 호출 | 캠페인/광고그룹/키워드/전일 성과 확인 |",
            "| 2 | 네이버 성과 응답 표준 CSV 변환 | 기존 AIMAOS 파이프라인 연결 |",
            "| 3 | G마켓/옥션 Playwright 환경 준비 | 직접 로그인 세션에서 다운로드 감지 |",
            "| 4 | G마켓/옥션 다운로드 파일 자동 분석 | 오늘 해야 할 일과 보고서 생성 |",
            "| 5 | 11번가 원본 확보 및 구조 분석 | 지원 가능성 판단 |",
            "",
            "## 13. 최종 결론",
            "",
            final_conclusion(results),
            "",
            "## 14. 다음 실행 조건",
            "",
            "실제 POC를 완료하려면 아래 값 또는 환경이 필요하다.",
            "",
            "- NAVER_SEARCHAD_CUSTOMER_ID",
            "- NAVER_SEARCHAD_ACCESS_LICENSE",
            "- NAVER_SEARCHAD_SECRET_KEY",
            "- G마켓/옥션/11번가 광고센터 리포트 시작 URL",
            "- Playwright 설치 및 브라우저 실행 환경",
            "- 사용자가 직접 로그인 가능한 테스트 계정",
            "",
            f"실행 증거 저장 위치: `{EVIDENCE_ROOT}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_steps(media: str, steps: list[PocStepResult]) -> list[str]:
    lines = [
        f"### {media}",
        "",
        "| 검증 항목 | 상태 | 설명 | 증거 |",
        "| --- | --- | --- | --- |",
    ]
    for step in steps:
        evidence = step.evidence_path or "-"
        lines.append(f"| {step.name} | {step.status} | {step.detail} | {evidence} |")
    lines.append("")
    return lines


def render_failure_reasons(results: dict[str, list[PocStepResult]]) -> list[str]:
    lines: list[str] = []
    for media, steps in results.items():
        failures = [
            step.detail
            for step in steps
            if step.status in {"실패", "실행 불가"}
        ]
        if failures:
            unique_failures = list(dict.fromkeys(failures))
            lines.append(f"- {media}: {' / '.join(unique_failures[:3])}")
            continue

        success_count = sum(step.status == "성공" for step in steps)
        if success_count:
            lines.append(f"- {media}: 현재 실행 결과에서 실패 단계 없음. 성공 단계 {success_count}개.")
        else:
            lines.append(f"- {media}: 실제 계정 기반 성공 또는 실패 판정 전.")
    return lines


def step_succeeded(steps: list[PocStepResult], name: str) -> bool:
    return any(step.name == name and step.status == "성공" for step in steps)


def naver_technical_validation_succeeded(steps: list[PocStepResult]) -> bool:
    required_steps = {
        "캠페인 조회",
        "광고그룹 조회",
        "기간 성과 조회",
        "AIMAOS 표준 CSV 변환",
        "AIMAOS 기존 파이프라인 연결",
        "오늘 해야 할 일 생성",
        "보고서 자동 생성",
    }
    succeeded = {step.name for step in steps if step.status == "성공"}
    return required_steps.issubset(succeeded)


def media_final_status(media: str, steps: list[PocStepResult]) -> str:
    if media == "네이버 검색광고" and naver_technical_validation_succeeded(steps):
        return "기술 검증 성공"
    if any(step.status == "성공" for step in steps):
        return "부분 성공"
    return "조건부 가능"


def media_reason(steps: list[PocStepResult]) -> str:
    blockers = [step.detail for step in steps if step.status == "실행 불가"]
    if blockers:
        return blockers[0]
    failures = [step.detail for step in steps if step.status == "실패"]
    if failures:
        return failures[0]
    return "필수 사전 조건 충족 후 실제 계정 검증 필요"


def overall_daily_collection_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "기간 성과 조회"):
        return "네이버 기술 검증 성공, 커머스 매체 미검증"
    return "미검증"


def overall_no_download_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "기간 성과 조회"):
        return "네이버 API 기준 성공, 커머스 매체 미검증"
    return "네이버는 가능성 높음, 커머스 매체는 미검증"


def overall_pipeline_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "AIMAOS 기존 파이프라인 연결"):
        return "네이버 연결 성공, 커머스 매체 미검증"
    return "실제 수집 파일 확보 후 검증"


def overall_one_click_status(results: dict[str, list[PocStepResult]]) -> str:
    return "네이버는 가능성 높음, 커머스 매체는 세션 유지 검증 필요"


def overall_metric_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "노출/클릭/광고비 수집"):
        return "네이버 기본 지표 수집 성공, 전환 지표는 계정 설정에 따라 조건부"
    return "실제 API/리포트 응답 확보 전 미검증"


def overall_action_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "오늘 해야 할 일 생성"):
        return "네이버 표준 CSV 기준 생성 성공"
    return "기존 엔진 연결 구조는 있음, 실제 수집 데이터 기준 미검증"


def overall_report_status(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if step_succeeded(naver_steps, "보고서 자동 생성"):
        return "네이버 표준 CSV 기준 생성 성공"
    return "기존 보고서 엔진 연결 구조는 있음, 실제 수집 데이터 기준 미검증"


def final_conclusion(results: dict[str, list[PocStepResult]]) -> str:
    naver_steps = results.get("네이버 검색광고", [])
    if naver_technical_validation_succeeded(naver_steps):
        return "네이버 API 수집은 기술 검증 성공이다. G마켓/옥션/11번가는 실제 리포트 파일 다운로드와 파이프라인 연결 검증이 남아 있다."
    if any(step.status == "성공" for steps in results.values() for step in steps):
        return "조건부 가능: 일부 실제 호출 또는 다운로드 검증이 성공했다. 남은 매체는 계정 조건과 보안 조건을 추가 확인해야 한다."
    return "조건부 가능: 구조상 가능성은 있으나 현재 환경에는 실제 계정/API 정보와 브라우저 자동화 실행 환경이 없어 성공 판정은 보류한다."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AIMAOS data collection POC.")
    parser.add_argument("--start-date", dest="start_date", help="Naver stats start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", dest="end_date", help="Naver stats end date, YYYY-MM-DD.")
    args = parser.parse_args()
    if args.start_date:
        os.environ["AIMAOS_POC_START_DATE"] = args.start_date
    if args.end_date:
        os.environ["AIMAOS_POC_END_DATE"] = args.end_date
    run_data_collection_poc()
    print(f"POC report written: {REPORT_PATH}")
