from pathlib import Path

import pandas as pd

from aimaos.pipeline import run_analysis_pipeline


DEMO_DATA = Path("samples/demo_data/campaignpulse_demo_ads.csv")
LEGACY_SAMPLE = Path("data/raw/test_ads_full_visible.csv")
DEMO_REPORT_DIR = Path("data/reports/demo")
STREAMLIT_APP = Path("aimaos/app/streamlit_app.py")


def test_safe_demo_data_exists_and_is_not_empty():
    assert DEMO_DATA.exists()
    data = pd.read_csv(DEMO_DATA)

    required_columns = {
        "date",
        "platform",
        "account_name",
        "campaign_name",
        "impressions",
        "clicks",
        "cost",
        "conversions",
        "revenue",
        "status",
        "recommended_action",
        "report_include",
    }

    assert required_columns.issubset(set(data.columns))
    assert len(data) >= 12
    assert data["account_name"].nunique() >= 3
    assert data["platform"].nunique() >= 4
    assert not data[list(required_columns)].isna().any().any()


def test_legacy_streamlit_sample_exists_for_cloud_fallback():
    assert LEGACY_SAMPLE.exists()
    data = pd.read_csv(LEGACY_SAMPLE)

    assert len(data) >= 8
    assert "platform" in data.columns or "매체" in data.columns
    assert "account_name" in data.columns or "계정명" in data.columns


def test_demo_report_artifacts_exist_for_report_center():
    assert (DEMO_REPORT_DIR / "analysis.xlsx").exists()
    assert (DEMO_REPORT_DIR / "report.md").exists()
    assert (DEMO_REPORT_DIR / "report.txt").exists()


def test_demo_data_can_run_through_existing_pipeline(tmp_path):
    result = run_analysis_pipeline(DEMO_DATA, tmp_path, "Demo Advertiser")

    assert result.rows >= 12
    assert result.report_paths.excel.exists()
    assert result.report_paths.markdown.exists()
    assert result.report_paths.text.exists()
    assert result.analysis.summary["cost"] > 0
    assert result.analysis.summary["revenue"] > 0


def test_streamlit_cloud_demo_mode_is_explicit_and_uploads_take_priority():
    source = STREAMLIT_APP.read_text(encoding="utf-8")

    assert "현재 화면은 기능 시연을 위한 데모 데이터 기준입니다. 실제 광고주 데이터가 아닙니다." in source
    assert 'DEMO_DATA_PATH = BASE_DIR / "samples" / "demo_data" / "campaignpulse_demo_ads.csv"' in source
    assert 'UPLOADED_SNAPSHOT_KEY = "campaignpulse_uploaded_snapshot"' in source
    assert "st.session_state[UPLOADED_SNAPSHOT_KEY]" in source
    assert "현재 세션은 업로드 데이터가 우선 적용됩니다." in source
