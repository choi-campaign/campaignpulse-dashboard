from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from aimaos.analyzers.performance_analyzer import METRIC_COLUMNS, RATE_COLUMNS, calculate_metrics


PERIOD_PRESETS = [
    "최근 7일",
    "어제",
    "지난주",
    "최근 15일",
    "이번 달",
    "지난달",
    "지난분기",
    "지난반기",
    "지난시즌",
    "임의 설정",
]

COMPARISON_METRICS = METRIC_COLUMNS + RATE_COLUMNS
LOWER_IS_BETTER = {"cost", "cpc", "cpa"}


def prepare_dated_frame(frame: pd.DataFrame) -> pd.DataFrame:
    dated = frame.copy()
    if "date" not in dated.columns:
        return pd.DataFrame()
    dated["date"] = pd.to_datetime(dated["date"], errors="coerce")
    return dated.dropna(subset=["date"]).copy()


def date_bounds(frame: pd.DataFrame) -> tuple[date, date] | None:
    dated = prepare_dated_frame(frame)
    if dated.empty:
        return None
    return dated["date"].min().date(), dated["date"].max().date()


def preset_period(base_date: date, preset: str) -> tuple[date, date]:
    if preset == "어제":
        target = base_date - timedelta(days=1)
        return target, target
    if preset == "최근 15일":
        return base_date - timedelta(days=14), base_date
    if preset == "이번 달":
        return base_date.replace(day=1), base_date
    if preset == "지난달":
        previous_month_end = base_date.replace(day=1) - timedelta(days=1)
        return previous_month_end.replace(day=1), previous_month_end
    if preset == "지난주":
        current_week_start = base_date - timedelta(days=base_date.weekday())
        previous_week_end = current_week_start - timedelta(days=1)
        previous_week_start = previous_week_end - timedelta(days=6)
        return previous_week_start, previous_week_end
    if preset == "지난분기":
        current_quarter_start_month = ((base_date.month - 1) // 3) * 3 + 1
        current_quarter_start = date(base_date.year, current_quarter_start_month, 1)
        previous_quarter_end = current_quarter_start - timedelta(days=1)
        previous_quarter_start_month = ((previous_quarter_end.month - 1) // 3) * 3 + 1
        return date(previous_quarter_end.year, previous_quarter_start_month, 1), previous_quarter_end
    if preset == "지난반기":
        current_half_start = date(base_date.year, 1 if base_date.month <= 6 else 7, 1)
        previous_half_end = current_half_start - timedelta(days=1)
        previous_half_start = date(previous_half_end.year, 1 if previous_half_end.month <= 6 else 7, 1)
        return previous_half_start, previous_half_end
    if preset == "지난시즌":
        current_season_start = _season_start(base_date)
        previous_season_end = current_season_start - timedelta(days=1)
        return _season_start(previous_season_end), previous_season_end
    return base_date - timedelta(days=6), base_date


def filter_period(frame: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    dated = prepare_dated_frame(frame)
    if dated.empty:
        return dated
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    return dated[(dated["date"] >= start) & (dated["date"] <= end)].copy()


def aggregate_by_dimension(frame: pd.DataFrame, dimension: str, limit: int = 20) -> pd.DataFrame:
    if frame.empty or dimension not in frame.columns:
        return pd.DataFrame()
    grouped = frame.groupby(dimension, dropna=False)[METRIC_COLUMNS].sum().reset_index()
    if grouped.empty:
        return grouped
    grouped = _add_rate_columns(grouped)
    return grouped.sort_values("cost", ascending=False).head(limit).reset_index(drop=True)


def compare_periods(
    frame: pd.DataFrame,
    first_start: date,
    first_end: date,
    second_start: date,
    second_end: date,
) -> pd.DataFrame:
    first = filter_period(frame, first_start, first_end)
    second = filter_period(frame, second_start, second_end)
    first_metrics = calculate_metrics(first) if not first.empty else {}
    second_metrics = calculate_metrics(second) if not second.empty else {}

    rows = []
    for metric in COMPARISON_METRICS:
        first_value = float(first_metrics.get(metric, 0))
        second_value = float(second_metrics.get(metric, 0))
        delta = second_value - first_value
        change_rate = delta / first_value if first_value else 0
        rows.append(
            {
                "metric": metric,
                "first_period": first_value,
                "second_period": second_value,
                "delta": delta,
                "change_rate": change_rate,
                "status": _status(metric, delta),
            }
        )
    return pd.DataFrame(rows)


def build_comparison_comments(comparison: pd.DataFrame) -> list[str]:
    if comparison.empty:
        return ["비교할 데이터가 없습니다."]

    comments = []
    roas = _metric_row(comparison, "roas")
    conversions = _metric_row(comparison, "conversions")
    cost = _metric_row(comparison, "cost")

    if roas is not None:
        direction = "개선" if roas["delta"] > 0 else "하락" if roas["delta"] < 0 else "유지"
        comments.append(f"광고수익률은 비교 기간 B에서 {direction}되었습니다.")
    if conversions is not None:
        direction = "증가" if conversions["delta"] > 0 else "감소" if conversions["delta"] < 0 else "유지"
        comments.append(f"전환수는 비교 기간 B에서 {direction}했습니다.")
    if cost is not None:
        direction = "증가" if cost["delta"] > 0 else "감소" if cost["delta"] < 0 else "유지"
        comments.append(f"광고비는 비교 기간 B에서 {direction}했습니다.")

    return comments


def _add_rate_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["ctr"] = result["clicks"].div(result["impressions"].mask(result["impressions"] == 0))
    result["cpc"] = result["cost"].div(result["clicks"].mask(result["clicks"] == 0))
    result["cvr"] = result["conversions"].div(result["clicks"].mask(result["clicks"] == 0))
    result["cpa"] = result["cost"].div(result["conversions"].mask(result["conversions"] == 0))
    result["roas"] = result["revenue"].div(result["cost"].mask(result["cost"] == 0))
    return result.fillna(0)


def _season_start(value: date) -> date:
    if value.month in {3, 4, 5}:
        return date(value.year, 3, 1)
    if value.month in {6, 7, 8}:
        return date(value.year, 6, 1)
    if value.month in {9, 10, 11}:
        return date(value.year, 9, 1)
    if value.month == 12:
        return date(value.year, 12, 1)
    return date(value.year - 1, 12, 1)


def _status(metric: str, delta: float) -> str:
    if abs(delta) < 1e-12:
        return "변화 없음"
    if metric in LOWER_IS_BETTER:
        return "개선" if delta < 0 else "악화"
    return "개선" if delta > 0 else "악화"


def _metric_row(frame: pd.DataFrame, metric: str) -> pd.Series | None:
    matched = frame[frame["metric"] == metric]
    if matched.empty:
        return None
    return matched.iloc[0]
