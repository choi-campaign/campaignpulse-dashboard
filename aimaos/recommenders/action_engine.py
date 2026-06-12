from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from aimaos.analyzers.performance_analyzer import AnalysisResult
from aimaos.reports.formatting import format_money, format_percent, format_ratio


MIN_ROWS_FOR_JUDGMENT = 3


@dataclass(frozen=True)
class OperatingActionIssue:
    severity: str
    priority_score: float
    advertiser: str
    media: str
    target: str
    problem: str
    evidence: str
    cause_hypothesis: str
    recommended_action: str
    expected_effect: str
    advertiser_message: str
    report_include: bool


def build_operating_action_issues(analysis: AnalysisResult, advertiser: str = "광고주") -> list[OperatingActionIssue]:
    if _has_insufficient_data(analysis):
        return [_insufficient_data_issue(analysis, advertiser)]

    issues = [_issue_from_anomaly(row, advertiser) for _, row in analysis.anomalies.iterrows()]

    if not issues:
        summary = analysis.summary
        issues.append(
            OperatingActionIssue(
                severity="low",
                priority_score=10,
                advertiser=advertiser,
                media="전체 매체",
                target="전체 계정",
                problem="긴급 점검 포인트는 없습니다",
                evidence=f"전체 광고수익률 {format_ratio(summary.get('roas', 0))}, 광고비 {format_money(summary.get('cost', 0))}",
                cause_hypothesis="현재 데이터 기준으로는 긴급한 낭비 징후가 뚜렷하지 않은 것으로 보입니다. 추가 확인은 필요합니다.",
                recommended_action="상위 비용 캠페인과 고성과 캠페인을 중심으로 유지 점검합니다.",
                expected_effect="성과 유지와 추가 개선 후보 발굴",
                advertiser_message=(
                    "현재 데이터에서는 즉시 중단이 필요한 위험 신호는 크지 않습니다. "
                    "다만 광고비 비중이 큰 캠페인과 성과가 좋은 캠페인을 중심으로 정기 점검을 이어가겠습니다."
                ),
                report_include=False,
            )
        )

    issues.extend(_supporting_issues(analysis, advertiser, len(issues)))
    return sorted(issues, key=lambda issue: issue.priority_score, reverse=True)


def _has_insufficient_data(analysis: AnalysisResult) -> bool:
    summary = analysis.summary
    rows = int(summary.get("rows", 0) or 0)
    cost = float(summary.get("cost", 0) or 0)
    impressions = float(summary.get("impressions", 0) or 0)
    clicks = float(summary.get("clicks", 0) or 0)
    return rows < MIN_ROWS_FOR_JUDGMENT or (cost <= 0 and impressions <= 0 and clicks <= 0)


def _insufficient_data_issue(analysis: AnalysisResult, advertiser: str) -> OperatingActionIssue:
    summary = analysis.summary
    rows = int(summary.get("rows", 0) or 0)
    cost = float(summary.get("cost", 0) or 0)
    is_zero_performance = all(float(summary.get(column, 0) or 0) <= 0 for column in ["impressions", "clicks", "cost", "conversions", "revenue"])
    media = _primary_media(analysis)
    zero_data_message = _zero_data_message(media)
    recommended_action = zero_data_message if is_zero_performance else "최근 데이터와 매체별 원본 파일을 추가로 업로드한 뒤 다시 분석합니다."
    advertiser_message = zero_data_message if is_zero_performance else "판단 불가: 데이터가 부족해 광고주 설명 문구를 생성하지 않습니다. 최신 데이터를 먼저 확보해 주세요."
    return OperatingActionIssue(
        severity="low",
        priority_score=1,
        advertiser=advertiser,
        media=media,
        target="전체 계정",
        problem="데이터 부족",
        evidence=f"분석 행 수 {rows:,}행, 광고비 {format_money(cost)}",
        cause_hypothesis="분석 가능한 데이터가 부족해 원인 추정이 어렵습니다.",
        recommended_action=recommended_action,
        expected_effect="분석 신뢰도 확보",
        advertiser_message=advertiser_message,
        report_include=False,
    )


def _primary_media(analysis: AnalysisResult) -> str:
    platform_table = analysis.segment_tables.get("platform", pd.DataFrame())
    if not platform_table.empty and "platform" in platform_table.columns:
        value = str(platform_table.iloc[0].get("platform", "")).strip()
        if value:
            return value
    return "전체 매체"


def _zero_data_message(media: str) -> str:
    if "네이버" in media:
        return "해당 기간의 네이버 광고 성과 데이터가 없습니다. 광고센터 기간 또는 계정 상태를 확인한 뒤 다시 수집해 주세요."
    return "해당 기간의 광고 성과 데이터가 없습니다. 광고센터 기간 또는 계정 상태를 확인한 뒤 다시 수집해 주세요."


def _issue_from_anomaly(row: pd.Series, advertiser: str) -> OperatingActionIssue:
    signal_type = str(row.get("type", "운영 점검"))
    severity = str(row.get("severity", "medium"))
    target = str(row.get("target", "미분류"))
    media = str(row.get("platform", "판단 불가"))
    if not media.strip() or media == "매체 미분류":
        media = "판단 불가"
    cost = float(row.get("cost", 0) or 0)
    ctr = float(row.get("ctr", 0) or 0)
    cvr = float(row.get("cvr", 0) or 0)
    roas = float(row.get("roas", 0) or 0)

    if signal_type == "광고비 소진 대비 전환 없음":
        problem = "광고비는 사용됐지만 전환이 없습니다"
        cause = "키워드 의도 불일치, 랜딩 페이지 문제, 전환 추적 누락 가능성이 있습니다."
        action = "예산 축소, 제외 키워드 추가, 랜딩 페이지와 전환 추적을 먼저 점검합니다."
        effect = f"월 {format_money(cost * 0.15)} 안팎의 광고비 절감 여지가 있습니다."
        message = (
            "해당 항목은 광고비가 사용됐지만 전환이 확인되지 않았습니다. "
            "광고 자체 문제로 단정하기보다는 키워드 의도, 상품 경쟁력, 상세페이지, 전환 추적 설정을 함께 확인하는 것이 좋습니다. "
            "우선 비효율 검색어와 예산 비중을 정리해 낭비 가능성을 줄이겠습니다."
        )
    elif signal_type == "노출 대비 클릭률 저조":
        problem = "클릭률이 낮아 광고 반응이 약합니다"
        cause = "소재 피로도, 문구 매력도 부족, 키워드와 광고문안 불일치가 의심됩니다."
        action = "소재와 광고문안을 교체하고 핵심 키워드별 문구를 다시 맞춥니다."
        effect = "CTR 10~20% 개선을 기대할 수 있습니다."
        message = (
            "노출은 확보되고 있으나 클릭 반응이 낮습니다. "
            "이는 광고 노출량 부족보다는 소재, 문구, 상품명, 가격 조건의 매력도와 관련될 수 있습니다. "
            "먼저 광고문안과 상품 연결성을 점검하겠습니다."
        )
    elif signal_type == "확대 가능 구간":
        problem = "성과가 좋아 예산 확대를 검토할 수 있습니다"
        cause = "ROAS와 전환수가 함께 양호한 구간일 가능성이 있어 추가 예산 검토가 필요합니다."
        action = "예산을 10~20% 범위에서 단계적으로 확대 테스트합니다."
        effect = "매출 8~12% 증가 가능성을 검토할 수 있습니다."
        message = (
            "해당 항목은 광고수익률과 전환 흐름이 양호합니다. "
            "성과가 유지되는 범위에서 예산을 소폭 확대하면 매출 확대 가능성을 테스트할 수 있습니다."
        )
    else:
        problem = signal_type
        cause = str(row.get("reason", "성과 지표 변화를 추가 확인해야 합니다."))
        action = "담당자가 캠페인, 광고그룹, 키워드 단위로 원인을 확인합니다."
        effect = "불필요한 광고비와 보고 준비 시간을 줄일 수 있습니다."
        message = (
            "성과 지표에 확인이 필요한 변화가 있습니다. "
            "현재 단계에서는 원인을 단정하지 않고, 관련 지표와 상품 상태를 함께 확인하겠습니다."
        )

    evidence = f"광고비 {format_money(cost)}, 클릭률 {format_percent(ctr)}, 전환율 {format_percent(cvr)}, 광고수익률 {format_ratio(roas)}"
    return OperatingActionIssue(
        severity=severity,
        priority_score=_priority_score(severity, cost, roas),
        advertiser=advertiser,
        media=media,
        target=target,
        problem=problem,
        evidence=evidence,
        cause_hypothesis=cause,
        recommended_action=action,
        expected_effect=effect,
        advertiser_message=message,
        report_include=severity in {"high", "medium", "opportunity"},
    )


def _supporting_issues(analysis: AnalysisResult, advertiser: str, existing_count: int) -> list[OperatingActionIssue]:
    if existing_count >= 3:
        return []
    summary = analysis.summary
    issues = [
        OperatingActionIssue(
            severity="low",
            priority_score=5,
            advertiser=advertiser,
            media="전체 매체",
            target="이번 분석 결과",
            problem="광고주 보고서 공유가 필요합니다",
            evidence=f"전체 광고수익률 {format_ratio(summary.get('roas', 0))}",
            cause_hypothesis="광고주 대응 시간을 줄이기 위해 핵심 변화와 다음 액션을 먼저 정리할 필요가 있습니다.",
            recommended_action="보고서 센터에서 광고주 보고서 유형을 선택해 공유합니다.",
            expected_effect="보고 준비와 광고주 설명 시간을 줄일 수 있습니다.",
            advertiser_message="이번 분석 결과를 기준으로 핵심 성과와 다음 액션을 정리해 공유드리겠습니다.",
            report_include=False,
        ),
        OperatingActionIssue(
            severity="low",
            priority_score=4,
            advertiser=advertiser,
            media="전체 매체",
            target="업종 벤치마크",
            problem="업종 평균 대비 위치 확인이 필요합니다",
            evidence=f"현재 CPC {format_money(summary.get('cpc', 0))}, ROAS {format_ratio(summary.get('roas', 0))}",
            cause_hypothesis="성과가 좋아도 업종 평균 대비 CPC가 높으면 장기 효율 저하 가능성이 있습니다.",
            recommended_action="ROAS와 CPC가 업종 평균 대비 좋은지 확인합니다.",
            expected_effect="대표와 광고주에게 성과 수준을 더 쉽게 설명할 수 있습니다.",
            advertiser_message="광고 성과는 절대값뿐 아니라 업종 평균 대비 위치를 함께 확인하는 것이 중요합니다.",
            report_include=False,
        ),
    ]
    return issues[: max(0, 3 - existing_count)]


def _priority_score(severity: str, cost: float, roas: float) -> float:
    severity_score = {"high": 100, "medium": 70, "opportunity": 60, "low": 20}.get(severity, 40)
    cost_score = min(cost / 100_000, 30)
    roas_penalty = 20 if severity == "high" and roas <= 0 else 0
    return severity_score + cost_score + roas_penalty
