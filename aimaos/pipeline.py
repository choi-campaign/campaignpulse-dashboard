from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from aimaos.analyzers.performance_analyzer import AnalysisResult, analyze_performance, summary_has_no_measurable_activity
from aimaos.parsers.excel_loader import load_ad_file
from aimaos.recommenders.action_engine import build_operating_action_issues
from aimaos.recommenders.rule_engine import build_recommendations
from aimaos.reports.report_generator import ReportPaths, write_reports
from aimaos.transformers.standardizer import standardize_ad_data
from aimaos.validators.file_validator import ensure_output_dir, validate_input_file


RECOMMENDATION_COLUMNS = ["priority", "target", "issue", "recommended_action", "expected_effect", "risk_level"]


@dataclass(frozen=True)
class PipelineResult:
    input_path: Path
    output_dir: Path
    rows: int
    mapping: dict[str, str]
    unmapped_columns: list[str]
    missing_standard_columns: list[str]
    standardized: pd.DataFrame
    analysis: AnalysisResult
    report_paths: ReportPaths


def run_analysis_pipeline(input_path: str | Path, output_dir: str | Path, advertiser: str) -> PipelineResult:
    source = validate_input_file(input_path)
    destination = ensure_output_dir(output_dir)

    raw = load_ad_file(source)
    standardized, mapping_result = standardize_ad_data(raw)
    analysis = analyze_performance(standardized)
    if summary_has_no_measurable_activity(analysis.summary):
        recommendations = pd.DataFrame(columns=RECOMMENDATION_COLUMNS)
    else:
        recommendations = build_recommendations(analysis)
    action_issues = build_operating_action_issues(analysis, advertiser=advertiser)
    report_paths = write_reports(
        output_dir=destination,
        advertiser=advertiser,
        standardized=standardized,
        analysis=analysis,
        recommendations=recommendations,
        mapping=mapping_result.mapping,
        unmapped_columns=mapping_result.unmapped_columns,
        action_issues=action_issues,
    )

    return PipelineResult(
        input_path=source,
        output_dir=destination,
        rows=len(standardized),
        mapping=mapping_result.mapping,
        unmapped_columns=mapping_result.unmapped_columns,
        missing_standard_columns=mapping_result.missing_standard_columns,
        standardized=standardized,
        analysis=analysis,
        report_paths=report_paths,
    )
