from __future__ import annotations

import pandas as pd

from aimaos.configs.default_schema import DIMENSION_COLUMNS, NUMERIC_COLUMNS, STANDARD_COLUMNS
from aimaos.transformers.column_mapper import ColumnMappingResult, map_columns


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    divisor = denominator.astype(float).mask(denominator.astype(float) == 0)
    result = numerator.astype(float).div(divisor)
    return result.fillna(0)


def standardize_ad_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, ColumnMappingResult]:
    mapping_result = map_columns(frame)
    standardized = mapping_result.frame.copy()

    for column in STANDARD_COLUMNS:
        if column not in standardized.columns:
            standardized[column] = pd.NA

    standardized = standardized[STANDARD_COLUMNS + [c for c in standardized.columns if c not in STANDARD_COLUMNS]]

    if "date" in standardized.columns:
        standardized["date"] = pd.to_datetime(standardized["date"], errors="coerce")

    for column in NUMERIC_COLUMNS:
        standardized[column] = (
            standardized[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("원", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        standardized[column] = pd.to_numeric(standardized[column], errors="coerce").fillna(0)

    for column in DIMENSION_COLUMNS:
        standardized[column] = standardized[column].fillna("미분류").astype(str).str.strip()
        standardized.loc[standardized[column] == "", column] = "미분류"

    standardized["ctr"] = _safe_divide(standardized["clicks"], standardized["impressions"])
    standardized["cpc"] = _safe_divide(standardized["cost"], standardized["clicks"])
    standardized["cvr"] = _safe_divide(standardized["conversions"], standardized["clicks"])
    standardized["cpa"] = _safe_divide(standardized["cost"], standardized["conversions"])
    standardized["roas"] = _safe_divide(standardized["revenue"], standardized["cost"])

    return standardized, mapping_result
