from pathlib import Path

from aimaos.pipeline import run_analysis_pipeline


def test_pipeline_generates_reports(tmp_path):
    sample = Path("samples/demo_data/campaignpulse_demo_ads.csv")
    result = run_analysis_pipeline(sample, tmp_path, "테스트 광고주")

    assert result.rows >= 12
    assert result.report_paths.markdown.exists()
    assert result.report_paths.text.exists()
    assert result.report_paths.excel.exists()
    assert result.analysis.summary["cost"] > 0

