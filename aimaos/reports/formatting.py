from __future__ import annotations

from typing import Any

import pandas as pd


COUNT_COLUMNS = {
    "rows",
    "impressions",
    "clicks",
    "conversions",
    "orders",
}

MONEY_COLUMNS = {
    "cost",
    "revenue",
    "cpc",
    "cpa",
}

PERCENT_COLUMNS = {
    "ctr",
    "cvr",
    "change_rate",
}

RATIO_COLUMNS = {
    "roas",
}

DATE_COLUMNS = {
    "date",
    "period_start",
    "period_end",
}

METRIC_LABELS = {
    "rows": "행 수",
    "impressions": "노출수",
    "clicks": "클릭수",
    "cost": "광고비",
    "conversions": "전환수",
    "revenue": "매출",
    "orders": "주문수",
    "ctr": "클릭률",
    "cpc": "클릭당 비용",
    "cvr": "전환율",
    "cpa": "전환당 비용",
    "roas": "광고수익률",
}

METRIC_ENGLISH_LABELS = {
    "rows": "Rows",
    "impressions": "Impressions",
    "clicks": "Clicks",
    "cost": "Ad Cost",
    "conversions": "Conversions",
    "revenue": "Revenue",
    "orders": "Orders",
    "ctr": "CTR",
    "cpc": "CPC",
    "cvr": "CVR",
    "cpa": "CPA",
    "roas": "ROAS",
}

COLUMN_LABELS = {
    "date": "날짜",
    "platform": "매체",
    "account_name": "계정명",
    "campaign_name": "캠페인명",
    "ad_group_name": "광고그룹명",
    "keyword": "키워드",
    "product_name": "상품명",
    "source_sheet": "원본 시트명",
    "period_label": "기간",
    "period_start": "시작일",
    "period_end": "종료일",
    "metric": "지표",
    "previous": "이전 기간",
    "current": "최근 기간",
    "first_period": "비교 기간 A",
    "second_period": "비교 기간 B",
    "delta": "변화량",
    "change_rate": "증감률",
    "status": "판단",
    "priority": "우선순위",
    "target": "대상",
    "issue": "진단 내용",
    "recommended_action": "추천 실행안",
    "expected_effect": "기대 효과",
    "risk_level": "위험도",
    "severity": "중요도",
    "type": "운영 포인트",
    "reason": "판단 근거",
    **METRIC_LABELS,
}

COLUMN_DESCRIPTIONS = {
    "date": "광고 성과가 집계된 날짜입니다.",
    "platform": "광고가 집행된 매체입니다. 예: 네이버, 구글, 카카오, 메타",
    "account_name": "광고 계정 또는 광고주 이름입니다.",
    "campaign_name": "광고 예산과 목표를 관리하는 상위 단위입니다.",
    "ad_group_name": "캠페인 안에서 키워드, 상품, 타겟을 묶는 운영 단위입니다.",
    "keyword": "광고가 노출되거나 클릭된 검색어 또는 운영 키워드입니다.",
    "product_name": "광고와 연결된 상품, 서비스, 소재 이름입니다.",
    "source_sheet": "엑셀 원본에서 데이터를 읽어온 시트 이름입니다.",
    "period_label": "성과를 묶어 본 기간 이름입니다. 예: 2026-05, 2026-W22",
    "period_start": "해당 집계 기간의 시작일입니다.",
    "period_end": "해당 집계 기간의 종료일입니다.",
    "rows": "분석에 사용된 원본 데이터 행 수입니다.",
    "impressions": "광고가 사용자 화면에 표시된 횟수입니다. 수치가 높을수록 광고가 더 자주 노출되었다는 뜻입니다.",
    "clicks": "사용자가 광고를 클릭한 횟수입니다.",
    "cost": "해당 기간 또는 항목에 사용된 광고비입니다.",
    "conversions": "구매, 문의, 신청 등 광고 목표로 잡은 행동이 발생한 횟수입니다.",
    "revenue": "광고를 통해 발생한 매출 또는 전환 가치입니다.",
    "orders": "광고를 통해 발생한 주문 수입니다.",
    "ctr": "노출 대비 클릭이 발생한 비율입니다. 계산식은 클릭수 ÷ 노출수입니다.",
    "cpc": "클릭 1회를 얻는 데 사용한 평균 광고비입니다. 계산식은 광고비 ÷ 클릭수입니다.",
    "cvr": "클릭 이후 구매, 문의, 신청 같은 성과로 이어진 비율입니다. 계산식은 전환수 ÷ 클릭수입니다.",
    "cpa": "전환 1건을 만드는 데 사용한 평균 광고비입니다. 계산식은 광고비 ÷ 전환수입니다.",
    "roas": "광고비 대비 매출 비율입니다. 계산식은 매출 ÷ 광고비입니다. 예를 들어 4.00은 400.00%로 표시합니다.",
    "metric": "비교하거나 요약하는 성과 지표의 이름입니다.",
    "previous": "비교 기준이 되는 이전 기간의 값입니다.",
    "current": "최근 기간 또는 현재 기간의 값입니다.",
    "first_period": "사용자가 직접 선택한 첫 번째 비교 기간의 값입니다.",
    "second_period": "사용자가 직접 선택한 두 번째 비교 기간의 값입니다.",
    "delta": "최근 기간 값에서 이전 기간 값을 뺀 변화량입니다.",
    "change_rate": "이전 기간 대비 얼마나 늘거나 줄었는지를 나타내는 비율입니다.",
    "status": "두 기간을 비교했을 때 개선, 악화, 변화 없음 중 어디에 해당하는지 보여줍니다.",
    "priority": "먼저 검토하거나 실행해야 하는 우선순위입니다.",
    "target": "진단 또는 추천 실행안이 적용되는 캠페인, 광고그룹, 키워드 등의 대상입니다.",
    "issue": "자동 분석기가 발견한 핵심 진단 내용입니다.",
    "recommended_action": "운영자가 검토할 수 있는 추천 실행안입니다.",
    "expected_effect": "추천 실행안을 적용했을 때 기대되는 효과입니다.",
    "risk_level": "운영상 주의가 필요한 정도입니다.",
    "severity": "운영자가 먼저 확인해야 하는 중요도입니다.",
    "type": "운영자가 확인할 포인트의 종류입니다.",
    "reason": "해당 진단이 나온 이유입니다.",
}

SHEET_NAMES = {
    "guide": "이용가이드",
    "standardized": "표준화데이터",
    "summary": "전체요약",
    "recommendations": "실행권고",
    "today_actions": "오늘해야할일",
    "anomalies": "운영점검포인트",
    "period_compare": "기간비교",
    "platform": "매체별성과",
    "campaign": "캠페인별성과",
    "ad_group": "광고그룹별성과",
    "keyword": "키워드별성과",
    "product": "상품별성과",
    "daily": "일자별성과",
    "weekly": "주간별성과",
    "monthly": "월별성과",
    "quarterly": "분기별성과",
    "half_year": "반기별성과",
    "yearly": "연도별성과",
    "seasonal": "시즌별성과",
}

VALUE_LABELS = {
    "high": "높음",
    "medium": "보통",
    "low": "낮음",
    "opportunity": "확대 기회",
    "P1": "긴급",
    "P2": "중요",
    "P3": "검토",
}

LABEL_TO_COLUMN = {label: column for column, label in COLUMN_LABELS.items()}
METRIC_LABEL_TO_KEY = {label: metric for metric, label in METRIC_LABELS.items()}

EXCEL_NUMBER_FORMATS = {
    "count": "#,##0",
    "money": "#,##0",
    "percent": "0.00%",
    "ratio": "0.00%",
    "date": "yyyy-mm-dd",
}


def metric_label(metric: str) -> str:
    return METRIC_LABELS.get(metric, metric)


def metric_label_with_english(metric: str) -> str:
    label = metric_label(metric)
    english = METRIC_ENGLISH_LABELS.get(metric)
    if english is None:
        return label
    return f"{label} ({english})"


def column_label(column: str) -> str:
    return COLUMN_LABELS.get(column, column)


def column_key(label_or_column: str | None) -> str | None:
    if label_or_column is None:
        return None
    return LABEL_TO_COLUMN.get(label_or_column, label_or_column)


def column_description(label_or_column: str | None) -> str:
    key = column_key(label_or_column)
    if key is None:
        return ""
    return COLUMN_DESCRIPTIONS.get(key, "")


def sheet_name(key: str) -> str:
    return SHEET_NAMES.get(key, key)[:31]


def value_label(value: Any) -> Any:
    return VALUE_LABELS.get(value, value)


def metric_key(label_or_metric: str | None) -> str | None:
    if label_or_metric is None:
        return None
    return METRIC_LABEL_TO_KEY.get(label_or_metric, label_or_metric)


def format_count(value: Any) -> str:
    number = _to_float(value)
    return f"{number:,.0f}"


def format_money(value: Any) -> str:
    number = _to_float(value)
    return f"{number:,.0f}원"


def format_percent(value: Any) -> str:
    number = _to_float(value)
    return f"{number * 100:,.2f}%"


def format_ratio(value: Any) -> str:
    number = _to_float(value)
    return f"{number * 100:,.2f}%"


def format_by_metric(metric: str, value: Any) -> str:
    if metric in COUNT_COLUMNS:
        return format_count(value)
    if metric in MONEY_COLUMNS:
        return format_money(value)
    if metric in PERCENT_COLUMNS:
        return format_percent(value)
    if metric in RATIO_COLUMNS:
        return format_ratio(value)
    return str(value)


def format_by_column(column: str, value: Any) -> str:
    if pd.isna(value):
        return ""
    if column in DATE_COLUMNS:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    if column in COUNT_COLUMNS:
        return format_count(value)
    if column in MONEY_COLUMNS:
        return format_money(value)
    if column in PERCENT_COLUMNS:
        return format_percent(value)
    if column in RATIO_COLUMNS:
        return format_ratio(value)
    return str(value)


def format_dataframe_for_display(frame: pd.DataFrame) -> pd.DataFrame:
    displayed = frame.copy()
    for column in displayed.columns:
        if column in DATE_COLUMNS | COUNT_COLUMNS | MONEY_COLUMNS | PERCENT_COLUMNS | RATIO_COLUMNS:
            displayed[column] = displayed[column].map(lambda value, col=column: format_by_column(col, value))
    if "metric" in displayed.columns:
        displayed["metric"] = displayed["metric"].map(metric_label)
    for column in ["severity", "risk_level", "priority"]:
        if column in displayed.columns:
            displayed[column] = displayed[column].map(value_label)
    displayed = displayed.rename(columns={column: column_label(column) for column in displayed.columns})
    return displayed


def localize_dataframe_for_excel(frame: pd.DataFrame) -> pd.DataFrame:
    localized = frame.copy()
    if "metric" in localized.columns:
        localized["metric"] = localized["metric"].map(metric_label)
    for column in ["severity", "risk_level", "priority"]:
        if column in localized.columns:
            localized[column] = localized[column].map(value_label)
    return localized.rename(columns={column: column_label(column) for column in localized.columns})


def _to_float(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)
