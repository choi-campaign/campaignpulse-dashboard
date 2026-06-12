from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


METRIC_COLUMNS = ["impressions", "clicks", "cost", "conversions", "revenue", "orders"]
RATE_COLUMNS = ["ctr", "cpc", "cvr", "cpa", "roas"]
CORE_ACTIVITY_COLUMNS = ["impressions", "clicks", "cost", "conversions", "revenue"]


@dataclass(frozen=True)
class AnalysisResult:
    summary: dict[str, float | int | str]
    segment_tables: dict[str, pd.DataFrame]
    period_tables: dict[str, pd.DataFrame]
    period_comparison: pd.DataFrame
    anomalies: pd.DataFrame


def calculate_metrics(frame: pd.DataFrame) -> dict[str, float | int | str]:
    impressions = float(frame["impressions"].sum())
    clicks = float(frame["clicks"].sum())
    cost = float(frame["cost"].sum())
    conversions = float(frame["conversions"].sum())
    revenue = float(frame["revenue"].sum())
    orders = float(frame["orders"].sum())

    return {
        "rows": int(len(frame)),
        "impressions": impressions,
        "clicks": clicks,
        "cost": cost,
        "conversions": conversions,
        "revenue": revenue,
        "orders": orders,
        "ctr": clicks / impressions if impressions else 0,
        "cpc": cost / clicks if clicks else 0,
        "cvr": conversions / clicks if clicks else 0,
        "cpa": cost / conversions if conversions else 0,
        "roas": revenue / cost if cost else 0,
    }


def has_no_measurable_activity(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return True
    for column in CORE_ACTIVITY_COLUMNS:
        if column not in frame.columns:
            return False
    return all(float(frame[column].sum()) <= 0 for column in CORE_ACTIVITY_COLUMNS)


def summary_has_no_measurable_activity(summary: dict[str, float | int | str]) -> bool:
    rows = int(summary.get("rows", 0) or 0)
    if rows <= 0:
        return True
    return all(float(summary.get(column, 0) or 0) <= 0 for column in CORE_ACTIVITY_COLUMNS)


def _aggregate_by(frame: pd.DataFrame, dimension: str, limit: int = 20) -> pd.DataFrame:
    if dimension not in frame.columns:
        return pd.DataFrame()

    grouped = frame.groupby(dimension, dropna=False)[METRIC_COLUMNS].sum().reset_index()
    if grouped.empty:
        return grouped

    grouped = _add_rate_columns(grouped)
    return grouped.sort_values("cost", ascending=False).head(limit)


def _add_rate_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["ctr"] = result["clicks"].div(result["impressions"].mask(result["impressions"] == 0))
    result["cpc"] = result["cost"].div(result["clicks"].mask(result["clicks"] == 0))
    result["cvr"] = result["conversions"].div(result["clicks"].mask(result["clicks"] == 0))
    result["cpa"] = result["cost"].div(result["conversions"].mask(result["conversions"] == 0))
    result["roas"] = result["revenue"].div(result["cost"].mask(result["cost"] == 0))
    return result.fillna(0)


def build_period_tables(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dated = frame.dropna(subset=["date"]).copy()
    if dated.empty:
        return {}

    dated["date"] = pd.to_datetime(dated["date"])
    dated["daily"] = dated["date"].dt.strftime("%Y년 %m월 %d일")
    iso_calendar = dated["date"].dt.isocalendar()
    dated["weekly"] = iso_calendar["year"].astype(str) + "년 " + iso_calendar["week"].astype(str) + "주차"
    dated["monthly"] = dated["date"].dt.strftime("%Y년 %m월")
    dated["quarterly"] = dated["date"].dt.year.astype(str) + "년 " + dated["date"].dt.quarter.astype(str) + "분기"
    half_label = dated["date"].dt.month.map(lambda month: "상반기" if month <= 6 else "하반기")
    dated["half_year"] = dated["date"].dt.year.astype(str) + "년 " + half_label
    dated["yearly"] = dated["date"].dt.year.astype(str) + "년"
    dated["seasonal"] = dated["date"].dt.year.astype(str) + "년 " + dated["date"].dt.month.map(_season_name)

    return {
        "daily": _aggregate_period(dated, "daily"),
        "weekly": _aggregate_period(dated, "weekly"),
        "monthly": _aggregate_period(dated, "monthly"),
        "quarterly": _aggregate_period(dated, "quarterly"),
        "half_year": _aggregate_period(dated, "half_year"),
        "yearly": _aggregate_period(dated, "yearly"),
        "seasonal": _aggregate_period(dated, "seasonal"),
    }


def _aggregate_period(frame: pd.DataFrame, period_column: str) -> pd.DataFrame:
    grouped = (
        frame.groupby(period_column, dropna=False)
        .agg(
            period_start=("date", "min"),
            period_end=("date", "max"),
            rows=("date", "size"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            cost=("cost", "sum"),
            conversions=("conversions", "sum"),
            revenue=("revenue", "sum"),
            orders=("orders", "sum"),
        )
        .reset_index()
        .rename(columns={period_column: "period_label"})
    )
    grouped = _add_rate_columns(grouped)
    return grouped.sort_values(["period_start", "period_label"]).reset_index(drop=True)


def _season_name(month: int) -> str:
    if month in {3, 4, 5}:
        return "봄"
    if month in {6, 7, 8}:
        return "여름"
    if month in {9, 10, 11}:
        return "가을"
    return "겨울"


def compare_recent_periods(frame: pd.DataFrame) -> pd.DataFrame:
    dated = frame.dropna(subset=["date"]).copy()
    if dated.empty:
        return pd.DataFrame()

    start = dated["date"].min()
    end = dated["date"].max()
    total_days = max((end - start).days + 1, 1)
    half_days = max(total_days // 2, 1)
    split = end - pd.Timedelta(days=half_days - 1)

    previous = dated[dated["date"] < split]
    current = dated[dated["date"] >= split]

    previous_metrics = calculate_metrics(previous) if not previous.empty else {}
    current_metrics = calculate_metrics(current) if not current.empty else {}

    rows = []
    for metric in METRIC_COLUMNS + RATE_COLUMNS:
        previous_value = float(previous_metrics.get(metric, 0))
        current_value = float(current_metrics.get(metric, 0))
        delta = current_value - previous_value
        change_rate = delta / previous_value if previous_value else 0
        rows.append(
            {
                "metric": metric,
                "previous": previous_value,
                "current": current_value,
                "delta": delta,
                "change_rate": change_rate,
            }
        )

    return pd.DataFrame(rows)


def detect_anomalies(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if frame.empty:
        return pd.DataFrame(rows)
    if has_no_measurable_activity(frame):
        return pd.DataFrame(rows)

    high_cost_threshold = frame["cost"].quantile(0.75)
    no_conversion_cost_threshold = max(frame["cost"].quantile(0.25), frame["cost"].sum() * 0.05)
    high_impression_threshold = frame["impressions"].quantile(0.75)
    low_ctr_threshold = max(frame["ctr"].quantile(0.25), 0.001)

    for index, row in frame.iterrows():
        label = _row_label(row)
        if row["cost"] >= no_conversion_cost_threshold and row["conversions"] <= 0:
            rows.append(
                {
                    "severity": "high",
                    "type": "광고비 소진 대비 전환 없음",
                    "target": label,
                    "reason": "상위 비용 구간인데 전환이 없습니다.",
                    "cost": row["cost"],
                    "ctr": row["ctr"],
                    "cvr": row["cvr"],
                    "roas": row["roas"],
                }
            )

        if row["impressions"] >= high_impression_threshold and row["ctr"] <= low_ctr_threshold:
            rows.append(
                {
                    "severity": "medium",
                    "type": "노출 대비 클릭률 저조",
                    "target": label,
                    "reason": "노출은 충분하지만 클릭 반응이 낮습니다.",
                    "cost": row["cost"],
                    "ctr": row["ctr"],
                    "cvr": row["cvr"],
                    "roas": row["roas"],
                }
            )

        if row["cost"] > 0 and row["roas"] >= 4 and row["conversions"] > 0:
            rows.append(
                {
                    "severity": "opportunity",
                    "type": "확대 가능 구간",
                    "target": label,
                    "reason": "광고수익률과 전환수가 양호해 예산 확대 후보입니다.",
                    "cost": row["cost"],
                    "ctr": row["ctr"],
                    "cvr": row["cvr"],
                    "roas": row["roas"],
                }
            )

    return pd.DataFrame(rows)


def analyze_performance(frame: pd.DataFrame) -> AnalysisResult:
    summary = calculate_metrics(frame)
    segment_tables = {
        "platform": _aggregate_by(frame, "platform"),
        "campaign": _aggregate_by(frame, "campaign_name"),
        "ad_group": _aggregate_by(frame, "ad_group_name"),
        "keyword": _aggregate_by(frame, "keyword"),
        "product": _aggregate_by(frame, "product_name"),
    }

    anomaly_base = segment_tables["campaign"]
    if anomaly_base.empty:
        anomaly_base = frame

    return AnalysisResult(
        summary=summary,
        segment_tables=segment_tables,
        period_tables=build_period_tables(frame),
        period_comparison=compare_recent_periods(frame),
        anomalies=detect_anomalies(anomaly_base),
    )


def _row_label(row: pd.Series) -> str:
    for column in ["campaign_name", "ad_group_name", "keyword", "product_name", "platform"]:
        value = row.get(column)
        if pd.notna(value) and str(value).strip() and str(value) != "미분류":
            return str(value)
    return "미분류"
