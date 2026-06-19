from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

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


def test_light_and_dark_mode_button_contrast_is_explicit():
    source = STREAMLIT_APP.read_text(encoding="utf-8")

    assert '[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"]' in source
    assert "color: #F8FAFC !important;" in source
    assert '[data-testid="stMain"] .stButton > button[kind="secondary"]' in source
    assert "background: var(--cp-white) !important;" in source
    assert "color: var(--cp-text) !important;" in source


def test_data_status_ui_distinguishes_demo_and_collection_attempts():
    source = STREAMLIT_APP.read_text(encoding="utf-8")

    assert 'return str(status) in {"주의", "오래됨", "연결 안됨"}' in source
    assert "마지막 수집 시도" in source
    assert "성공과 실패를 포함한 최근 수집 작업 종료 시각" in source
    assert "마지막 성공 수집" in source


def test_demo_dashboard_counts_only_channels_that_need_attention():
    app = AppTest.from_file(str(STREAMLIT_APP), default_timeout=60).run(timeout=60)
    dashboard_cards = [str(item.value) for item in app.get("markdown")]

    assert any(
        '<div class="aima-summary-label">데이터 확인 필요</div>'
        '<div class="aima-summary-value">1</div>' in card
        for card in dashboard_cards
    )
    assert any("마지막 수집 시도" in card for card in dashboard_cards)
    assert len(app.exception) == 0


def test_public_docs_do_not_expose_poc_identifiers_or_local_user_paths():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("docs").glob("*.md"))
    forbidden = (
        r"C:\Users\admin",
        "J:/내 드라이브",
        "cmp-a001-01-000000009693823",
        "CODIMA",
        "더블유아이티",
        "nutirone",
        "뉴트리원",
    )

    assert not any(value in combined for value in forbidden)

    public_source = Path("aimaos/validators/raw_media_audit.py").read_text(encoding="utf-8")
    assert not any(value in public_source for value in forbidden)


def test_all_primary_streamlit_pages_render_without_exceptions():
    app = AppTest.from_file(str(STREAMLIT_APP), default_timeout=60).run(timeout=60)

    for menu_key in (
        "sidebar_menu_01",
        "sidebar_menu_02",
        "sidebar_menu_03",
        "sidebar_menu_04",
        "sidebar_menu_05",
        "sidebar_menu_06",
        "sidebar_menu_07",
        "sidebar_menu_08",
    ):
        app.button(menu_key).click().run(timeout=60)
        assert len(app.exception) == 0, menu_key


def test_uploaded_file_replaces_demo_snapshot_in_streamlit_session():
    demo_notice = "현재 화면은 기능 시연을 위한 데모 데이터 기준입니다. 실제 광고주 데이터가 아닙니다."
    payload = DEMO_DATA.read_bytes()
    app = AppTest.from_file(str(STREAMLIT_APP), default_timeout=60).run(timeout=60)

    app.button("sidebar_menu_04").click().run(timeout=60)
    app.file_uploader("analysis_file_upload").upload(
        "safe_upload.csv",
        payload,
        "text/csv",
    ).run(timeout=60)
    app.button("analysis_upload_run_button").click().run(timeout=60)
    app.run(timeout=60)

    assert app.session_state["campaignpulse_uploaded_snapshot"] is not None
    assert demo_notice not in [message.value for message in app.info]
    assert app.checkbox("campaignpulse_demo_data_enabled").disabled is True
    assert len(app.exception) == 0
