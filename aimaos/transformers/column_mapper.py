from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
import re

import pandas as pd

from aimaos.configs.default_schema import COLUMN_ALIASES


def normalize_column_name(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"[\(\)\[\]\{\}/\\:_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_alias_lookup() -> dict[str, str]:
    lookup = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        lookup[normalize_column_name(standard_name)] = standard_name
        for alias in aliases:
            lookup[normalize_column_name(alias)] = standard_name
    return lookup


@dataclass(frozen=True)
class ColumnMappingResult:
    frame: pd.DataFrame
    mapping: dict[str, str]
    unmapped_columns: list[str]
    missing_standard_columns: list[str]


def map_columns(frame: pd.DataFrame, minimum_similarity: float = 0.88) -> ColumnMappingResult:
    alias_lookup = build_alias_lookup()
    alias_keys = list(alias_lookup.keys())
    rename_map: dict[str, str] = {}
    unmapped: list[str] = []

    for original_column in frame.columns:
        normalized = normalize_column_name(original_column)
        standard = alias_lookup.get(normalized)

        if standard is None:
            match = get_close_matches(normalized, alias_keys, n=1, cutoff=minimum_similarity)
            standard = alias_lookup[match[0]] if match else None

        if standard is None:
            unmapped.append(str(original_column))
            continue

        if standard in rename_map.values():
            unmapped.append(str(original_column))
            continue

        rename_map[str(original_column)] = standard

    mapped = frame.rename(columns=rename_map).copy()
    missing = [standard for standard in COLUMN_ALIASES if standard not in mapped.columns]

    return ColumnMappingResult(
        frame=mapped,
        mapping=rename_map,
        unmapped_columns=unmapped,
        missing_standard_columns=missing,
    )

