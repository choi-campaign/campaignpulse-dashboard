from __future__ import annotations

import base64
from datetime import date, datetime, timedelta
from html import escape
import json
from pathlib import Path
import re
import sys
import tempfile

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aimaos.analyzers.custom_period_analyzer import (
    PERIOD_PRESETS,
    aggregate_by_dimension,
    build_comparison_comments,
    compare_periods,
    date_bounds,
    filter_period,
    preset_period,
)
from aimaos.analyzers.performance_analyzer import analyze_performance, calculate_metrics
from aimaos.channel_intelligence.registry import (
    CHANNEL_GROUPS,
    add_channel,
    initialize_channel_registry,
    load_channels,
    update_channel,
)
from aimaos.parsers.excel_loader import load_ad_file
from aimaos.pipeline import run_analysis_pipeline
from aimaos.recommenders.action_engine import OperatingActionIssue, build_operating_action_issues
from aimaos.reports.formatting import (
    column_description,
    format_by_metric,
    format_count,
    format_dataframe_for_display,
    format_money,
    format_percent,
    format_ratio,
    metric_label,
)
from aimaos.transformers.standardizer import standardize_ad_data
from aimaos.validators.raw_media_audit import (
    ALIASES_ADDED_FOR_MARKETPLACE,
    UNMAPPED_MARKETPLACE_METADATA,
    MediaFileAudit,
    audit_media_file,
)
from aimaos.storage.retention_cleanup import build_cleanup_plan
from aimaos.storage.collection_log import collection_status_by_media


REPO_ROOT = PROJECT_ROOT.parents[1] if len(PROJECT_ROOT.parents) > 1 else PROJECT_ROOT
BRAND_ASSET_DIR = REPO_ROOT / "public" / "assets" / "brand"
BRAND_KO = "캠페인펄스"
BRAND_EN = "CampaignPulse"
BRAND_TAGLINE = "광고 성과의 맥박을 읽고, 지금 해야 할 일을 보여줍니다."


st.set_page_config(page_title="캠페인펄스 | 광고 운영 대시보드", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --cp-primary: #172B4D;
        --cp-blue: #2563EB;
        --cp-cyan: #06B6D4;
        --cp-bg: #F8FAFC;
        --cp-white: #FFFFFF;
        --cp-text: #0F172A;
        --cp-text-muted: #64748B;
        --cp-border: #E2E8F0;
        --cp-success: #16A34A;
        --cp-warning: #F59E0B;
        --cp-danger: #DC2626;
        --cp-neutral: #94A3B8;
    }
    .stApp {
        background: var(--cp-bg);
        color: var(--cp-text);
        font-family: Pretendard, "Noto Sans KR", SUIT, system-ui, sans-serif;
    }
    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.88);
        border-bottom: 1px solid rgba(226, 232, 240, 0.72);
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, h4,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--cp-text);
        letter-spacing: 0;
    }
    [data-testid="stCaptionContainer"],
    .stCaption,
    p {
        color: var(--cp-text-muted);
    }
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] label,
    [data-testid="stWidgetLabel"],
    [data-testid="stExpander"] summary {
        color: var(--cp-text);
    }
    [data-testid="stCaptionContainer"],
    .stCaption,
    [data-testid="stMarkdownContainer"] small {
        color: var(--cp-text-muted) !important;
    }
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown li,
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] li {
        line-height: 2.0 !important;
    }
    [data-testid="stExpander"] li {
        margin-bottom: 0.35rem !important;
    }
    .aima-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem;
    }
    .aima-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem;
    }
    .aima-summary-card,
    .aima-alert-card,
    .aima-media-card,
    .aima-kpi-card,
    .aima-status-panel {
        border: 1px solid var(--cp-border);
        border-radius: 8px;
        padding: 1.15rem;
        background: var(--cp-white);
        color: var(--cp-text);
        line-height: 1.8;
        min-height: 180px;
        box-shadow: 0 14px 40px rgba(15, 23, 42, 0.06);
    }
    .aima-status-panel {
        display: grid;
        grid-template-columns: minmax(180px, 0.8fr) minmax(260px, 1.4fr);
        gap: 1.25rem;
        align-items: center;
        margin: 1rem 0 1.5rem;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(239, 246, 255, 0.92));
    }
    .aima-health-score {
        font-size: 4rem;
        font-weight: 850;
        line-height: 1;
    }
    .aima-health-status {
        display: inline-flex;
        border-radius: 999px;
        padding: 0.18rem 0.72rem;
        font-weight: 800;
        margin-top: 0.7rem;
    }
    .aima-section-lead {
        color: var(--cp-text-muted);
        font-size: 1rem;
        max-width: 980px;
        line-height: 2;
        margin-bottom: 0.5rem;
    }
    .aima-kpi-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .aima-summary-label,
    .aima-card-label,
    .aima-kpi-label {
        color: var(--cp-text-muted);
        font-size: 0.86rem;
        margin-bottom: 0.25rem;
    }
    .aima-summary-value,
    .aima-kpi-value {
        font-size: 1.55rem;
        font-weight: 760;
        color: var(--cp-text);
    }
    .aima-kpi-value {
        font-size: 1.9rem;
    }
    .aima-kpi-change {
        margin-top: 0.7rem;
        font-size: 0.95rem;
        font-weight: 760;
    }
    .aima-summary-note,
    .aima-card-note {
        color: var(--cp-text-muted);
        font-size: 0.9rem;
        margin-top: 0.35rem;
    }
    .aima-media-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        border-radius: 999px;
        padding: 0.18rem 0.58rem;
        font-weight: 760;
        border: 1px solid rgba(148, 163, 184, 0.24);
        white-space: nowrap;
    }
    .aima-media-dot {
        width: 0.7rem;
        height: 0.7rem;
        border-radius: 999px;
        display: inline-block;
    }
    .aima-bar-track {
        width: 100%;
        height: 0.65rem;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.18);
        overflow: hidden;
        margin-top: 0.55rem;
    }
    .aima-bar-fill {
        height: 100%;
        border-radius: 999px;
    }
    .aima-alert-card {
        border-left: 6px solid var(--accent);
    }
    .aima-todo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem;
    }
    .aima-todo-card {
        border: 1px solid var(--cp-border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 170px;
        background: var(--cp-white);
        line-height: 1.85;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
    }
    .aima-todo-rank {
        width: 2rem;
        height: 2rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        font-weight: 850;
        margin-bottom: 0.6rem;
        background: rgba(37, 99, 235, 0.12);
        color: var(--cp-blue);
    }
    .aima-action-row {
        border-top: 1px solid var(--cp-border);
        padding-top: 0.55rem;
        margin-top: 0.55rem;
    }
    .aima-action-label {
        color: var(--cp-text-muted);
        font-size: 0.78rem;
        font-weight: 780;
        letter-spacing: 0;
    }
    .aima-action-value {
        color: var(--cp-text);
        font-size: 0.94rem;
        font-weight: 650;
    }
    .aima-action-value ul {
        margin: 0.25rem 0 0;
        padding-left: 1.15rem;
    }
    .aima-action-value li {
        margin-bottom: 0.2rem;
    }
    .aima-action-row details summary {
        cursor: pointer;
        color: var(--cp-blue);
        list-style-position: inside;
        padding-top: 0.1rem;
    }
    .aima-action-row details[open] summary {
        margin-bottom: 0.55rem;
    }
    .aima-coach-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem;
    }
    .aima-coach-column {
        border: 1px solid var(--cp-border);
        border-radius: 8px;
        padding: 1rem;
        min-height: 220px;
        background: var(--cp-white);
    }
    .aima-coach-heading {
        font-size: 1.04rem;
        font-weight: 820;
        margin-bottom: 0.7rem;
    }
    .aima-coach-item {
        border-top: 1px solid var(--cp-border);
        padding: 0.75rem 0 0.2rem;
        line-height: 1.9;
    }
    .aima-onboarding {
        border: 1px solid rgba(37, 99, 235, 0.18);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0 1.5rem;
        background: rgba(37, 99, 235, 0.06);
    }
    .aima-alert-title {
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .aima-alert-meta {
        color: var(--cp-text-muted);
        font-size: 0.92rem;
        margin-bottom: 0.35rem;
    }
    .aima-pill {
        display: inline-flex;
        border-radius: 999px;
        padding: 0.12rem 0.55rem;
        font-weight: 760;
        font-size: 0.82rem;
        margin-right: 0.35rem;
    }
    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 0%, rgba(6, 182, 212, 0.18), transparent 34%),
            linear-gradient(180deg, #07111F 0%, #0B1220 46%, #172B4D 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        line-height: 1.65 !important;
    }
    .aima-menu-label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        width: 100%;
    }
    .aima-menu-name {
        color: #E5E7EB;
        font-weight: 820;
    }
    .aima-menu-badge {
        min-width: 2rem;
        text-align: center;
        border-radius: 999px;
        padding: 0.15rem 0.48rem;
        color: #BFDBFE;
        background: rgba(37, 99, 235, 0.18);
        border: 1px solid rgba(96, 165, 250, 0.24);
        font-size: 0.78rem;
        font-weight: 840;
    }
    .aima-sidebar-brand {
        border: 1px solid rgba(96, 165, 250, 0.28);
        border-radius: 8px;
        padding: 1.12rem;
        margin: 0.35rem 0 1.35rem;
        background: linear-gradient(145deg, rgba(23, 43, 77, 0.90), rgba(15, 23, 42, 0.72));
        box-shadow: 0 18px 40px rgba(2, 6, 23, 0.22);
    }
    .campaignpulse-sidebar-logo-img {
        width: 100%;
        max-width: 210px;
        display: block;
        margin-bottom: 0.65rem;
    }
    .aima-sidebar-logo {
        font-size: 1.62rem;
        font-weight: 900;
        color: #F8FAFC;
        letter-spacing: 0;
        line-height: 1.05;
    }
    .aima-sidebar-subtitle {
        margin-top: 0.35rem;
        color: #A5F3FC;
        font-size: 0.76rem;
        font-weight: 760;
        line-height: 1.55;
    }
    .aima-sidebar-tag {
        display: inline-flex;
        margin-top: 0.7rem;
        border-radius: 999px;
        padding: 0.22rem 0.58rem;
        background: rgba(6, 182, 212, 0.13);
        border: 1px solid rgba(6, 182, 212, 0.30);
        color: #67E8F9;
        font-size: 0.78rem;
        font-weight: 820;
    }
    .aima-sidebar-section-title {
        margin: 1.25rem 0 0.65rem;
        color: #CBD5E1;
        font-size: 0.92rem;
        font-weight: 860;
    }
    .aima-brief-card,
    .aima-data-card {
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 8px;
        padding: 0.86rem;
        background: rgba(15, 23, 42, 0.52);
        margin-bottom: 0.85rem;
    }
    .aima-brief-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.55rem;
    }
    .aima-brief-item {
        border-radius: 8px;
        padding: 0.58rem;
        background: rgba(30, 41, 59, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.12);
    }
    .aima-brief-label {
        color: #94A3B8;
        font-size: 0.74rem;
        font-weight: 760;
    }
    .aima-brief-value {
        color: #F8FAFC;
        font-size: 1.08rem;
        font-weight: 900;
        margin-top: 0.12rem;
    }
    .aima-data-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.65rem;
        padding: 0.46rem 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.10);
    }
    .aima-data-row:last-child {
        border-bottom: 0;
    }
    .aima-data-name {
        color: #E5E7EB;
        font-size: 0.9rem;
        font-weight: 760;
    }
    .aima-data-status {
        border-radius: 999px;
        padding: 0.12rem 0.48rem;
        font-size: 0.72rem;
        font-weight: 820;
        white-space: nowrap;
    }
    .cp-sidebar-menu-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 2.2rem;
        height: 2.2rem;
        border-radius: 999px;
        margin-top: 0.2rem;
        color: #67E8F9;
        background: rgba(6, 182, 212, 0.16);
        border: 1px solid rgba(6, 182, 212, 0.28);
        font-size: 0.78rem;
        font-weight: 860;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 52px;
        border-radius: 12px;
        padding: 0 14px;
        justify-content: flex-start;
        text-align: left;
        gap: 8px;
        margin-bottom: 10px;
        font-size: 15px;
        font-weight: 780;
        color: #F8FAFC;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(148, 163, 184, 0.25);
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        color: #F8FAFC;
        background: rgba(37, 99, 235, 0.18);
        border-color: rgba(37, 99, 235, 0.55);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        color: #FFFFFF !important;
        background: linear-gradient(135deg, #172B4D, #2563EB) !important;
        border: 1px solid #2563EB !important;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.22);
    }
    [data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .stButton > button p {
        color: #F8FAFC !important;
        font-size: 15px !important;
        font-weight: 780 !important;
        letter-spacing: 0;
        text-align: left;
    }
    .cp-dashboard-quick-note {
        margin-top: -0.35rem;
        margin-bottom: 0.8rem;
        color: #64748B;
        font-size: 0.88rem;
        line-height: 1.7;
    }
    .aima-data-status-hero {
        border: 1px solid var(--cp-border);
        border-radius: 8px;
        padding: 1.25rem;
        margin: 1rem 0 1.4rem;
        background: var(--cp-white);
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
    }
    .aima-data-status-title {
        color: var(--cp-text-muted);
        font-size: 0.88rem;
        font-weight: 820;
    }
    .aima-data-status-value {
        font-size: 2.4rem;
        font-weight: 900;
        line-height: 1.15;
        margin-top: 0.25rem;
        color: var(--cp-text);
    }
    .aima-status-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.18rem 0.68rem;
        font-weight: 860;
        border: 1px solid rgba(148, 163, 184, 0.24);
        margin-top: 0.6rem;
    }
    .aima-channel-table {
        border: 1px solid var(--cp-border);
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0 1.5rem;
    }
    .aima-channel-row {
        display: grid;
        grid-template-columns: 1.1fr 1fr 1fr 1fr 1fr;
        gap: 0.8rem;
        padding: 0.85rem 1rem;
        border-bottom: 1px solid var(--cp-border);
        align-items: center;
    }
    .aima-channel-row:last-child {
        border-bottom: 0;
    }
    .aima-channel-head {
        color: #94A3B8;
        font-size: 0.82rem;
        font-weight: 820;
        background: rgba(37, 99, 235, 0.06);
    }
    .aima-channel-name {
        color: var(--cp-text);
        font-weight: 860;
    }
    .aima-freshness-card {
        border: 1px solid rgba(245, 158, 11, 0.28);
        border-radius: 8px;
        padding: 1rem;
        background: rgba(245, 158, 11, 0.08);
        margin: 0.75rem 0 1.25rem;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, var(--cp-blue), var(--cp-cyan)) !important;
        border: 1px solid rgba(147, 197, 253, 0.42) !important;
        color: #FFFFFF !important;
        min-height: 3rem;
        font-weight: 860;
        border-radius: 8px;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1D4ED8, #0284C7) !important;
        border-color: rgba(191, 219, 254, 0.72) !important;
    }
    [data-testid="stMain"] .stButton > button[kind="secondary"],
    [data-testid="stMain"] .stDownloadButton > button {
        background: var(--cp-white) !important;
        border: 1px solid var(--cp-border) !important;
        color: var(--cp-text) !important;
    }
    [data-testid="stMain"] .stButton > button[kind="secondary"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] .stButton > button[kind="secondary"] p,
    [data-testid="stMain"] .stDownloadButton > button [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] .stDownloadButton > button p {
        color: var(--cp-text) !important;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --cp-bg: #0B1220;
            --cp-white: #111827;
            --cp-text: #F8FAFC;
            --cp-text-muted: #CBD5E1;
            --cp-border: rgba(148, 163, 184, 0.28);
        }
        [data-testid="stHeader"] {
            background: rgba(11, 18, 32, 0.9);
            border-bottom: 1px solid rgba(148, 163, 184, 0.24);
        }
        .aima-status-panel {
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(15, 23, 42, 0.94));
        }
        .aima-channel-head {
            background: rgba(37, 99, 235, 0.14);
            color: #CBD5E1;
        }
        .cp-dashboard-quick-note {
            color: var(--cp-text-muted);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MAIN_MENU_ITEMS = ["종합 대시보드", "우선 처리 이슈", "운영 현황", "광고 성과 분석", "쇼핑몰/매체 분석", "보고서 센터", "채널 관리", "설정"]
MENU_ICONS = {
    "종합 대시보드": "01",
    "우선 처리 이슈": "02",
    "운영 현황": "03",
    "광고 성과 분석": "04",
    "쇼핑몰/매체 분석": "05",
    "보고서 센터": "06",
    "채널 관리": "07",
    "설정": "08",
}
VIEW_MODES = ["기본 모드", "전문가 모드"]
CORE_METRICS = ["cost", "revenue", "orders", "roas"]
EXPERT_METRICS = ["impressions", "clicks", "ctr", "cpc", "conversions", "cvr", "cpa"]
DIMENSION_COLUMNS = ["platform", "campaign_name", "ad_group_name", "keyword", "product_name", "period_label", "period_start", "period_end"]
REPORT_PROFILES = {
    "대표 보고서": {
        "audience": "대표와 의사결정자",
        "tone": "짧고 결론 중심",
        "fields": "총 광고비, 총 매출, 주문수, ROAS, 우선 처리 이슈",
        "use": "광고가 돈을 벌고 있는지 빠르게 판단할 때 사용합니다.",
    },
    "광고주 보고서": {
        "audience": "광고주와 팀 공유용",
        "tone": "성과와 개선안을 균형 있게 설명",
        "fields": "핵심 KPI, 매체별 성과, 운영 점검 포인트, 추천 행동",
        "use": "광고주에게 이번 성과와 다음 액션을 설명할 때 사용합니다.",
    },
    "실무자 보고서": {
        "audience": "광고 운영 담당자",
        "tone": "원인과 조치 중심",
        "fields": "CTR, CPC, CVR, CPA, 캠페인, 광고그룹, 키워드",
        "use": "실제 계정에서 무엇을 수정할지 정할 때 사용합니다.",
    },
    "대행사 보고서": {
        "audience": "대행사 담당자와 팀장",
        "tone": "광고주 설득과 운영 근거 중심",
        "fields": "성과 요약, 긴급 이슈, 확대기회, 예상 효과, 보고용 코멘트",
        "use": "월간 보고나 운영 제안 미팅에 사용합니다.",
    },
    "요약 보고서": {
        "audience": "빠른 공유용",
        "tone": "가장 짧고 쉬운 표현",
        "fields": "광고 건강도, 총 광고비, 총 매출, ROAS, 3개 액션",
        "use": "메신저나 짧은 회의에서 빠르게 공유할 때 사용합니다.",
    },
}

BASE_DIR = PROJECT_ROOT
PHASE2_SAMPLE_DIR = BASE_DIR / "data" / "phase2_samples"
AD_SAMPLE_PATH = BASE_DIR / "data" / "raw" / "test_ads_full_visible.csv"
DEMO_DATA_PATH = BASE_DIR / "samples" / "demo_data" / "campaignpulse_demo_ads.csv"
CHANNEL_DB_PATH = BASE_DIR / "data" / "channel_registry.sqlite"
DEMO_DATA_MODE_KEY = "campaignpulse_demo_data_enabled"
UPLOADED_SNAPSHOT_KEY = "campaignpulse_uploaded_snapshot"
DEMO_DATA_NOTICE = "현재 화면은 기능 시연을 위한 데모 데이터 기준입니다. 실제 광고주 데이터가 아닙니다."
METRIC_ENGLISH_LABELS = {
    "impressions": "Impressions",
    "clicks": "Clicks",
    "ctr": "CTR",
    "cpc": "CPC",
    "conversions": "Conversions",
    "cvr": "CVR",
    "cpa": "CPA",
    "roas": "ROAS",
}
MEDIA_BRAND_STYLES = {
    "네이버": {"color": "#03C75A", "short": "N", "text": "#06140A"},
    "구글": {"color": "#4285F4", "short": "G", "text": "#FFFFFF"},
    "카카오": {"color": "#FEE500", "short": "K", "text": "#111827"},
    "메타": {"color": "#0081FB", "short": "M", "text": "#FFFFFF"},
}
DEFAULT_MEDIA_STYLE = {"color": "#64748B", "short": "AD", "text": "#FFFFFF"}
ALERT_STYLES = {
    "high": {"label": "긴급 점검", "color": "#EF4444", "background": "rgba(239, 68, 68, 0.14)"},
    "medium": {"label": "개선 필요", "color": "#F59E0B", "background": "rgba(245, 158, 11, 0.14)"},
    "opportunity": {"label": "확대기회", "color": "#22C55E", "background": "rgba(34, 197, 94, 0.14)"},
}


def brand_asset_data_uri(filename: str) -> str:
    path = BRAND_ASSET_DIR / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def render_brand_logo_img(filename: str, class_name: str, alt: str = "캠페인펄스") -> str:
    src = brand_asset_data_uri(filename)
    if not src:
        return f'<div class="aima-sidebar-logo">{escape(BRAND_KO)}</div>'
    return f'<img class="{class_name}" src="{src}" alt="{escape(alt)}" />'


def current_active_menu() -> str:
    active = st.session_state.get("active_page")
    if active not in MAIN_MENU_ITEMS:
        active = MAIN_MENU_ITEMS[0]
        st.session_state["active_page"] = active
    return str(active)


def navigate_to(menu_name: str) -> None:
    if menu_name not in MAIN_MENU_ITEMS:
        return
    st.session_state["active_page"] = menu_name
    st.rerun()


def navigation_button(label: str, target: str, key: str, *, button_type: str = "secondary") -> None:
    if st.button(label, key=key, type=button_type, use_container_width=True):
        navigate_to(target)


def ensure_demo_data_default() -> None:
    if DEMO_DATA_MODE_KEY not in st.session_state:
        st.session_state[DEMO_DATA_MODE_KEY] = DEMO_DATA_PATH.exists()


def demo_data_mode_enabled() -> bool:
    ensure_demo_data_default()
    return bool(st.session_state.get(DEMO_DATA_MODE_KEY, False))


def active_sample_data_path() -> tuple[Path | None, str]:
    if DEMO_DATA_PATH.exists() and demo_data_mode_enabled():
        return DEMO_DATA_PATH, "demo"
    if AD_SAMPLE_PATH.exists():
        return AD_SAMPLE_PATH, "sample"
    return None, "none"


def using_demo_data() -> bool:
    if st.session_state.get(UPLOADED_SNAPSHOT_KEY) is not None:
        return False
    _, mode = active_sample_data_path()
    return mode == "demo"


def render_demo_data_notice() -> None:
    if using_demo_data():
        st.info(DEMO_DATA_NOTICE)


@st.cache_data(show_spinner=False)
def load_analysis_snapshot_from_path(path_text: str) -> tuple[pd.DataFrame, object]:
    raw = load_ad_file(Path(path_text))
    standardized, _ = standardize_ad_data(raw)
    analysis = analyze_performance(standardized)
    return standardized, analysis


def load_sample_analysis_snapshot() -> tuple[pd.DataFrame, object] | None:
    uploaded_snapshot = st.session_state.get(UPLOADED_SNAPSHOT_KEY)
    if uploaded_snapshot is not None:
        return uploaded_snapshot

    sample_path, _ = active_sample_data_path()
    if sample_path is None:
        return None
    return load_analysis_snapshot_from_path(str(sample_path))


DATA_STATUS_STYLES = {
    "최신": {"color": "#22C55E", "background": "rgba(34, 197, 94, 0.14)"},
    "주의": {"color": "#F59E0B", "background": "rgba(245, 158, 11, 0.14)"},
    "오래됨": {"color": "#EF4444", "background": "rgba(239, 68, 68, 0.14)"},
    "데모": {"color": "#2563EB", "background": "rgba(37, 99, 235, 0.14)"},
    "연결 안됨": {"color": "#94A3B8", "background": "rgba(148, 163, 184, 0.14)"},
}


def latest_mtime(paths: list[Path]) -> datetime | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return datetime.fromtimestamp(max(path.stat().st_mtime for path in existing))


def latest_file_mtime(root: Path, patterns: tuple[str, ...]) -> datetime | None:
    if not root.exists():
        return None
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in root.rglob(pattern) if path.is_file())
    if not files:
        return None
    return datetime.fromtimestamp(max(path.stat().st_mtime for path in files))


def latest_file_path(root: Path, patterns: tuple[str, ...]) -> Path | None:
    if not root.exists():
        return None
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in root.rglob(pattern) if path.is_file())
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def marketplace_entry_reason(profile_root: Path, fallback_reason: str) -> str:
    latest_entry = latest_file_path(
        profile_root,
        (
            "gmarket_computer_use_auth_required_*.json",
            "gmarket_computer_use_download_poc_*.json",
            "download_validation_*.json",
            "ad_center_entry_*.json",
        ),
    )
    if latest_entry is None:
        return fallback_reason
    try:
        payload = json.loads(latest_entry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback_reason
    final_status = str(payload.get("final_status", ""))
    error_code = str(payload.get("error_code", ""))
    error_message = str(payload.get("error_message", ""))
    if final_status == "blocked_by_environment" or error_code == "NETWORK_ACCESS_DENIED":
        return "광고센터 접속 제한. 사용자 실제 PC 또는 접속 가능한 브라우저 환경에서 재검증 필요"
    if final_status == "needs_user_authentication":
        return "사용자 직접 로그인 또는 인증 필요"
    if final_status == "no_data":
        return "선택 기간에 조회 가능한 광고 성과 데이터 없음"
    if error_code == "DOWNLOAD_FILE_NOT_FOUND":
        return "다운로드 파일 미감지. 리포트 다운로드 실행 필요"
    if error_message:
        return error_message
    detail = str(payload.get("detail", ""))
    status = str(payload.get("status", ""))
    if status == "failed" and "ERR_NETWORK_ACCESS_DENIED" in detail:
        return "현재 PC에서 광고센터 연결 확인 제한. 전용 수집 브라우저에서 사용자 인증 후 재확인 필요"
    if status == "failed":
        return "광고센터 연결 확인 필요"
    return fallback_reason


def freshness_status(last_at: datetime | None, connected: bool = True, success: bool = True) -> str:
    if not connected or not success or last_at is None:
        return "연결 안됨"
    age_hours = (datetime.now() - last_at).total_seconds() / 3600
    if age_hours <= 24:
        return "최신"
    if age_hours <= 72:
        return "주의"
    return "오래됨"


def apply_collection_log_status(
    channels: list[dict[str, object]],
    log_status: dict[str, dict[str, object]],
) -> None:
    media_keys = {
        "네이버": ("naver", "naver_searchad"),
        "G마켓": ("gmarket",),
        "옥션": ("auction",),
        "11번가": ("11st", "elevenst"),
        "쿠팡": ("coupang",),
    }
    for channel in channels:
        entry = next(
            (
                log_status[key]
                for key in media_keys.get(str(channel["media"]), ())
                if key in log_status
            ),
            None,
        )
        if entry is None:
            continue

        latest_status = str(entry.get("latest_status", "")).lower()
        latest_finished_at = entry.get("latest_finished_at")
        last_success_at = entry.get("last_success_at")
        rate = entry.get("success_rate_30d")
        channel["last_check_at"] = latest_finished_at
        channel["success_rate"] = f"{float(rate):.1f}%" if rate is not None else "기록 없음"

        if latest_status == "success":
            channel["connection"] = "연결 완료"
            channel["last_at"] = last_success_at or latest_finished_at
            channel["success"] = True
            channel["note"] = "최근 수집 로그 기준"
            channel["failure_reason"] = "-"
            continue

        channel["success"] = False
        channel["last_at"] = last_success_at
        message = str(entry.get("error_message", "")).strip()
        code = str(entry.get("error_code", "")).strip()
        if latest_status == "partial":
            channel["status_override"] = "주의"
            channel["failure_reason"] = message or "일부 데이터만 수집되어 확인 필요"
        elif latest_status == "no_data":
            channel["status_override"] = "연결 안됨"
            channel["failure_reason"] = message or "선택 기간에 수집된 데이터 없음"
        else:
            channel["status_override"] = "연결 안됨"
            channel["failure_reason"] = message or code or "최근 데이터 수집 실패"


def format_status_time(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def status_style(status: str) -> dict[str, str]:
    return DATA_STATUS_STYLES.get(status, DATA_STATUS_STYLES["연결 안됨"])


def data_status_badge(status: str) -> str:
    style = status_style(status)
    return (
        f'<span class="aima-status-badge" style="color:{style["color"]};'
        f'background:{style["background"]};border-color:{hex_to_rgba(style["color"], 0.34)};">'
        f'{escape(status)}</span>'
    )


def collect_data_status_snapshot() -> dict[str, object]:
    collection_root = BASE_DIR / "data" / "collection_poc"
    raw_root = BASE_DIR / "data" / "raw"
    report_root = BASE_DIR / "data" / "reports"
    demo_root = BASE_DIR / "samples" / "demo_data"
    collection_log_status = collection_status_by_media()

    last_collection_at = latest_file_mtime(collection_root, ("*.csv", "*.xlsx", "*.xls"))
    raw_latest_at = latest_file_mtime(raw_root, ("*.csv", "*.xlsx", "*.xls"))
    if raw_latest_at and (last_collection_at is None or raw_latest_at > last_collection_at):
        last_collection_at = raw_latest_at
    logged_collection_times = [
        entry.get("latest_finished_at")
        for entry in collection_log_status.values()
        if isinstance(entry.get("latest_finished_at"), datetime)
    ]
    if logged_collection_times:
        latest_logged_collection = max(logged_collection_times)
        if last_collection_at is None or latest_logged_collection > last_collection_at:
            last_collection_at = latest_logged_collection
    demo_latest_at = latest_file_mtime(demo_root, ("*.csv", "*.json")) if using_demo_data() else None
    if demo_latest_at and last_collection_at is None:
        last_collection_at = demo_latest_at

    last_analysis_at = latest_file_mtime(report_root, ("*.md", "*.txt", "*.xlsx"))

    marketplace_root = collection_root / "marketplace"
    gmarket_root = marketplace_root / "gmarket_legacy"
    auction_root = marketplace_root / "auction_legacy"
    elevenst_root = marketplace_root / "11st_adoffice"
    coupang_root = marketplace_root / "coupang_ads"
    gmarket_download_at = latest_file_mtime(gmarket_root / "downloads", ("*.xls*", "*.csv"))
    auction_download_at = latest_file_mtime(auction_root / "downloads", ("*.xls*", "*.csv"))
    gmarket_check_at = latest_file_mtime(gmarket_root, ("ad_center_entry_*.json", "*.json"))
    auction_check_at = latest_file_mtime(auction_root, ("ad_center_entry_*.json", "*.json"))
    elevenst_check_at = latest_file_mtime(elevenst_root, ("ad_center_entry_*.json", "*.json"))
    coupang_check_at = latest_file_mtime(coupang_root, ("ad_center_entry_*.json", "*.json"))
    gmarket_reason = marketplace_entry_reason(
        gmarket_root,
        "최근 광고 데이터가 없어 리포트 다운로드 검증 대기",
    )
    auction_reason = marketplace_entry_reason(
        auction_root,
        "최근 광고 데이터가 없어 리포트 다운로드 검증 대기",
    )
    elevenst_reason = marketplace_entry_reason(elevenst_root, "실제 계정 연결 검증 대기")
    coupang_reason = marketplace_entry_reason(coupang_root, "광고센터 구조와 보안 정책 검증 대기")
    channels = [
        {
            "media": "네이버",
            "connection": "연결 완료",
            "last_at": latest_file_mtime(collection_root, ("*naver*",)),
            "last_check_at": latest_file_mtime(collection_root, ("*naver*",)),
            "success": True,
            "success_rate": "100%",
            "note": "계정 연동 수집 검증 성공",
            "failure_reason": "-",
        },
        {
            "media": "G마켓",
            "connection": "광고센터 진입 완료",
            "last_at": gmarket_download_at,
            "last_check_at": gmarket_check_at,
            "success": gmarket_download_at is not None,
            "success_rate": "다운로드 미검증",
            "note": "최근 광고 데이터 있는 계정 필요",
            "failure_reason": gmarket_reason,
        },
        {
            "media": "옥션",
            "connection": "광고센터 진입 완료",
            "last_at": auction_download_at,
            "last_check_at": auction_check_at,
            "success": auction_download_at is not None,
            "success_rate": "다운로드 미검증",
            "note": "최근 광고 데이터 있는 계정 필요",
            "failure_reason": auction_reason,
        },
        {
            "media": "11번가",
            "connection": "연결 필요",
            "last_at": None,
            "last_check_at": elevenst_check_at,
            "success": False,
            "success_rate": "미연결",
            "note": "실제 계정 로그인 필요",
            "failure_reason": elevenst_reason,
        },
        {
            "media": "쿠팡",
            "connection": "연결 필요",
            "last_at": None,
            "last_check_at": coupang_check_at,
            "success": False,
            "success_rate": "미연결",
            "note": "보안 리스크 검토 필요",
            "failure_reason": coupang_reason,
        },
    ]
    apply_collection_log_status(channels, collection_log_status)
    for channel in channels:
        channel["status"] = channel.pop(
            "status_override",
            freshness_status(
                channel["last_at"],
                connected=channel["connection"] != "연결 필요",
                success=bool(channel["success"]),
            ),
        )

    if using_demo_data():
        demo_at = demo_latest_at or latest_file_mtime(demo_root, ("*.csv", "*.json"))
        for channel in channels:
            if channel["media"] in {"네이버", "G마켓", "옥션", "11번가"}:
                channel.update(
                    {
                        "connection": "데모 데이터",
                        "last_at": demo_at,
                        "last_check_at": demo_at,
                        "success": True,
                        "success_rate": "데모",
                        "note": "기능 시연용 가짜 데이터",
                        "failure_reason": "-",
                        "status": "데모",
                    }
                )
        overall_status = "데모"
        last_success_at = demo_at
        last_failure_at = None
        failure_reason = "데모 데이터 기준으로 화면을 표시 중"
    else:
        all_statuses = [channel["status"] for channel in channels]
        connected_statuses = [channel["status"] for channel in channels if channel["connection"] != "연결 필요"]
        if all(status == "연결 안됨" for status in all_statuses):
            overall_status = "연결 안됨"
        elif "오래됨" in connected_statuses:
            overall_status = "오래됨"
        elif "주의" in connected_statuses or "연결 안됨" in all_statuses:
            overall_status = "주의"
        elif all(status == "최신" for status in connected_statuses):
            overall_status = "최신"
        else:
            overall_status = "주의"

        success_times = [
            channel["last_at"]
            for channel in channels
            if channel["success"] and channel["last_at"] is not None
        ]
        failure_times = [
            channel["last_check_at"]
            for channel in channels
            if not channel["success"] and channel["last_check_at"] is not None
        ]
        last_success_at = max(success_times) if success_times else None
        last_failure_at = max(failure_times) if failure_times else None
        failure_reasons = [
            f'{channel["media"]}: {channel["failure_reason"]}'
            for channel in channels
            if not channel["success"]
        ]
        failure_reason = " / ".join(failure_reasons[:2])
        if len(failure_reasons) > 2:
            failure_reason += f" 외 {len(failure_reasons) - 2}건"
        if not failure_reason:
            failure_reason = "-"

    return {
        "overall_status": overall_status,
        "last_collection_at": last_collection_at,
        "last_analysis_at": last_analysis_at,
        "last_success_at": last_success_at,
        "last_failure_at": last_failure_at,
        "failure_reason": failure_reason,
        "channels": channels,
    }


def render_integrated_dashboard() -> None:
    status = collect_data_status_snapshot()
    stats = sidebar_command_center_stats()
    reports = collect_report_records(BASE_DIR / "data" / "reports")
    non_fresh_channels = sum(1 for channel in status["channels"] if channel["status"] != "최신")

    st.title("종합 대시보드")
    st.caption("캠페인펄스의 전체 운영 상태를 한 화면에서 확인합니다.")
    render_demo_data_notice()
    st.markdown(
        '<div class="aima-section-lead">'
        "데이터 상태, 우선 처리 이슈, 광고 성과 흐름, 보고서 상태, 채널 연결 상태를 요약합니다. "
        "자세한 확인이 필요한 항목은 아래 버튼으로 해당 메뉴로 이동하세요."
        "</div>",
        unsafe_allow_html=True,
    )

    st.info(
        f"오늘은 긴급 이슈 {stats['critical_issues']:,}건, 주의 이슈 {stats['warning_issues']:,}건, "
        f"보고서 반영 후보 {stats['report_due']:,}건이 있습니다."
    )
    render_data_status_warning(str(status["overall_status"]))

    st.subheader("오늘의 핵심 요약")
    cards = [
        ("광고주 수", f"{stats['advertisers']:,}", "현재 체험/수집 데이터에서 확인된 광고주", "운영 현황"),
        ("긴급 이슈", f"{stats['critical_issues']:,}", "바로 확인할 우선 처리 항목", "우선 처리 이슈"),
        ("주의 이슈", f"{stats['warning_issues']:,}", "성과 변화 확인이 필요한 항목", "우선 처리 이슈"),
        ("보고서 예정", f"{stats['report_due']:,}", "보고서 반영 후보 이슈", "보고서 센터"),
        ("데이터 확인 필요", f"{non_fresh_channels:,}", "최신 상태가 아닌 매체 수", "채널 관리"),
        ("연결 채널", f"{stats['channels']:,}", "등록되어 관리 중인 채널", "채널 관리"),
        ("최근 업로드 파일", f"{stats['raw_files']:,}", "분석 가능한 원본 파일", "광고 성과 분석"),
        ("최근 보고서", f"{stats['reports']:,}", "최근 생성된 보고서 폴더", "보고서 센터"),
    ]
    render_dashboard_action_cards(cards)

    st.subheader("데이터 상태 요약")
    status_cards = [
        ("전체 상태", str(status["overall_status"]), "최신 데이터 기준으로 판단합니다."),
        ("마지막 수집", format_status_time(status["last_collection_at"]), "최근 데이터가 들어온 시각"),
        ("마지막 분석", format_status_time(status["last_analysis_at"]), "보고서 또는 분석 결과가 갱신된 시각"),
        ("최근 실패 원인", str(status["failure_reason"]), "수집 실패가 있으면 원인을 먼저 확인합니다."),
    ]
    st.markdown(render_summary_cards(status_cards), unsafe_allow_html=True)
    with st.expander("매체별 데이터 상태 보기"):
        st.markdown(render_channel_status_table(status["channels"]), unsafe_allow_html=True)

    st.subheader("우선 처리 이슈 요약")
    snapshot = load_sample_analysis_snapshot()
    if snapshot is None:
        st.warning("운영 예시 데이터를 찾을 수 없습니다. 광고 성과 분석 메뉴에서 파일을 업로드해 주세요.")
        navigation_button("광고 데이터 업로드", "광고 성과 분석", "dashboard_upload_missing", button_type="primary")
    else:
        _, analysis = snapshot
        render_dashboard_issue_preview(analysis)

        st.subheader("성과 흐름 요약")
        render_dashboard_performance_summary(analysis)

    st.subheader("보고서 상태")
    latest_report = reports[0]["보고서명"] if reports else "생성된 보고서 없음"
    latest_report_date = reports[0]["생성일"] if reports else "-"
    report_cards = [
        ("최근 보고서", str(latest_report), f"생성일 {latest_report_date}"),
        ("다운로드 가능", f"{len(reports):,}개", "최근 보고서 목록 기준"),
        ("다음 행동", "보고서 확인", "광고주 공유 전 요약을 확인합니다."),
    ]
    st.markdown(render_summary_cards(report_cards), unsafe_allow_html=True)
    navigation_button("보고서 센터로 이동", "보고서 센터", "dashboard_go_report_center", button_type="primary")


def render_dashboard_action_cards(cards: list[tuple[str, str, str, str]]) -> None:
    columns = st.columns(4)
    for index, (label, value, note, target) in enumerate(cards):
        with columns[index % 4]:
            st.markdown(
                (
                    '<div class="aima-summary-card">'
                    f'<div class="aima-summary-label">{escape(label)}</div>'
                    f'<div class="aima-summary-value">{escape(value)}</div>'
                    f'<div class="aima-summary-note">{escape(note)}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            navigation_button("자세히 보기", target, f"dashboard_card_{index}_{target}")


def render_dashboard_issue_preview(analysis) -> None:  # noqa: ANN001
    issues = build_operating_action_issues(analysis, advertiser="광고주 A")[:3]
    if not issues:
        st.info("현재 운영 판단 기준으로는 주요 조치 필요 항목이 없습니다.")
        return

    for index, issue in enumerate(issues, start=1):
        color = severity_color(issue.severity)
        st.markdown(
            (
                f'<div class="aima-alert-card" style="--accent: {color};">'
                f'<div class="aima-alert-title">[{escape(severity_label(issue.severity))}] {escape(action_oriented_issue_title(issue))}</div>'
                f'<div class="aima-alert-meta">매체 {escape(operator_display_text(issue.media))} · 대상 {escape(operator_display_text(issue.target))}</div>'
                f'<div class="aima-card-note">추천 액션: {escape(primary_action_text(issue.recommended_action))}</div>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    navigation_button("우선 처리 이슈 전체 보기", "우선 처리 이슈", "dashboard_go_priority_issues", button_type="primary")


def render_dashboard_performance_summary(analysis) -> None:  # noqa: ANN001
    summary = analysis.summary
    cards = [
        ("광고비", format_money(float(summary.get("cost", 0))), "전체 광고비 기준"),
        ("매출", format_money(float(summary.get("revenue", 0))), "광고 성과 매출 기준"),
        ("ROAS", format_ratio(float(summary.get("roas", 0))), "매출 ÷ 광고비"),
        ("클릭률", format_percent(float(summary.get("ctr", 0))), "노출 대비 클릭 반응"),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)
    navigation_button("광고 성과 자세히 보기", "광고 성과 분석", "dashboard_go_ad_analysis", button_type="primary")


def render_data_status_center() -> None:
    status = collect_data_status_snapshot()
    overall = str(status["overall_status"])
    st.title("데이터 최신성 점검")
    st.caption("분석보다 먼저 최신 데이터가 준비되어 있는지 확인합니다.")
    st.markdown(
        '<div class="aima-section-lead">'
        "캠페인펄스는 최신 데이터가 확보된 뒤 우선 처리 이슈와 보고서를 신뢰할 수 있습니다. "
        "먼저 데이터 연결 상태와 마지막 수집 시각을 확인해 주세요."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.1, 1.1, 1.2])
    with col1:
        st.markdown(
            '<div class="aima-data-status-hero">'
            '<div class="aima-data-status-title">마지막 데이터 수집 시각</div>'
            f'<div class="aima-data-status-value">{escape(format_status_time(status["last_collection_at"]))}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="aima-data-status-hero">'
            '<div class="aima-data-status-title">마지막 분석 시각</div>'
            f'<div class="aima-data-status-value">{escape(format_status_time(status["last_analysis_at"]))}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="aima-data-status-hero">'
            '<div class="aima-data-status-title">전체 상태</div>'
            f'<div class="aima-data-status-value">{escape(overall)}</div>'
            f'{data_status_badge(overall)}'
            "</div>",
            unsafe_allow_html=True,
        )

    col4, col5 = st.columns([1, 1.4])
    with col4:
        st.markdown(
            '<div class="aima-data-status-hero">'
            '<div class="aima-data-status-title">마지막 성공 시각</div>'
            f'<div class="aima-data-status-value">{escape(format_status_time(status["last_success_at"]))}</div>'
            '<div class="aima-summary-note">실제 수집 데이터가 확인된 마지막 시각</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            '<div class="aima-data-status-hero">'
            '<div class="aima-data-status-title">마지막 실패 시각 / 실패 원인</div>'
            f'<div class="aima-data-status-value">{escape(format_status_time(status["last_failure_at"]))}</div>'
            f'<div class="aima-summary-note">{escape(str(status["failure_reason"]))}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    if st.button("최신 데이터 수집", type="primary", use_container_width=True):
        st.info(
            "네이버는 계정 연동 수집을 실행하고, G마켓/옥션은 전용 수집 화면에서 인증 후 리포트 다운로드를 확인해야 합니다. "
            "현재 화면에서는 수집 상태를 확인하고 다음 행동을 안내합니다."
        )

    render_data_status_warning(overall)
    st.subheader("매체별 데이터 상태")
    st.markdown(render_channel_status_table(status["channels"]), unsafe_allow_html=True)

    st.subheader("광고주 연결 상태")
    connection_cards = [
        (channel["media"], channel["connection"], channel["note"])
        for channel in status["channels"]
    ]
    st.markdown(render_summary_cards(connection_cards), unsafe_allow_html=True)

    st.subheader("최근 30일 수집 성공률")
    success_cards = [
        (channel["media"], channel["success_rate"], channel["status"])
        for channel in status["channels"]
    ]
    st.markdown(render_summary_cards(success_cards), unsafe_allow_html=True)

    st.subheader("저장 용량과 정리 예정")
    st.markdown(render_storage_status_cards(), unsafe_allow_html=True)

    st.info("데이터가 최신이면 우선 처리 이슈, 운영 현황, 보고서 센터를 그대로 사용하면 됩니다. 오래된 경우 먼저 최신 데이터 수집을 권장합니다.")


def render_storage_status_cards() -> str:
    plan = build_cleanup_plan()
    target_lookup = {str(item["group"]): item for item in plan["targets"]}
    next_cleanup = "-"
    if plan["delete_candidate_count"]:
        next_cleanup = "정리 필요"
    elif target_lookup:
        next_cleanup = "정책 기준 정상"
    cards = [
        ("전체 저장 용량", f'{float(plan["total_storage_mb"]):,.2f}MB', "광고주 100명/1000명 확장 시 추적 기준"),
        ("삭제 예정 파일 수", f'{int(plan["delete_candidate_count"]):,}개', "보관 기간을 넘긴 파일"),
        ("삭제 예정 용량", f'{float(plan["delete_candidate_mb"]):,.2f}MB', "정리 실행 전 예상 절감"),
        ("다음 정리 상태", next_cleanup, "자동 정리 명령으로 확인 가능"),
    ]
    return render_summary_cards(cards)


def render_channel_status_table(channels: object) -> str:
    rows = [
        '<div class="aima-channel-table">',
        '<div class="aima-channel-row aima-channel-head">'
        "<div>매체</div><div>연결 상태</div><div>마지막 수집</div><div>마지막 확인</div><div>상태</div>"
        "</div>",
    ]
    for channel in channels:
        status = str(channel["status"])
        last_at = format_status_time(channel["last_at"])
        last_check_at = format_status_time(channel.get("last_check_at"))
        rows.append(
            '<div class="aima-channel-row">'
            f'<div class="aima-channel-name">{escape(str(channel["media"]))}</div>'
            f'<div>{escape(str(channel["connection"]))}</div>'
            f'<div>{escape(last_at)}</div>'
            f'<div>{escape(last_check_at)}</div>'
            f'<div>{data_status_badge(status)}</div>'
            "</div>"
        )
    rows.append("</div>")
    return "".join(rows)


def render_data_status_warning(overall_status: str) -> None:
    if overall_status == "주의":
        st.warning("최신 데이터 수집을 권장합니다. 일부 데이터가 24시간을 초과했을 수 있습니다.")
    elif overall_status == "오래됨":
        st.error("데이터가 오래되었습니다. 분석을 보기 전 최신 데이터 수집을 먼저 권장합니다.")
    elif overall_status == "연결 안됨":
        st.error("먼저 데이터 연결이 필요합니다. 연결된 매체가 없으면 우선 처리 이슈와 보고서 신뢰도가 낮습니다.")


def render_data_access_notice(menu_name: str) -> bool:
    status = collect_data_status_snapshot()
    overall = str(status["overall_status"])
    if using_demo_data():
        st.info(DEMO_DATA_NOTICE)
        return True
    if overall == "최신":
        return True
    if overall == "주의":
        st.warning("최신 데이터 수집을 권장합니다. 현재 화면은 기존 데이터 기준으로 표시됩니다.")
        return True
    if overall == "오래됨":
        st.error("데이터가 오래되었습니다.")
        st.markdown(
            '<div class="aima-freshness-card">'
            f"<b>{escape(menu_name)}</b> 화면은 기존 데이터로 계속 볼 수 있지만, 먼저 최신 데이터 수집을 권장합니다."
            "</div>",
            unsafe_allow_html=True,
        )
        left, right = st.columns(2)
        with left:
            st.button("최신 데이터 수집", type="primary", use_container_width=True, key=f"refresh_{menu_name}")
        with right:
            st.button("기존 데이터로 계속 보기", use_container_width=True, key=f"continue_{menu_name}")
        return True
    st.error("먼저 데이터 연결이 필요합니다.")
    st.markdown(
        '<div class="aima-freshness-card">'
        "우선 처리 이슈, 운영 현황, 보고서 센터는 연결된 데이터가 있어야 신뢰할 수 있습니다. "
        "종합 대시보드에서 매체 연결 상태를 먼저 확인해 주세요."
        "</div>",
        unsafe_allow_html=True,
    )
    return False


def render_home_dashboard() -> None:
    st.title("우선 처리 이슈")
    st.caption("캠페인펄스 광고 운영 관제실")
    if not render_data_access_notice("우선 처리 이슈"):
        return
    st.markdown(
        '<div class="aima-section-lead">'
        "광고 데이터를 보는 곳이 아니라 광고 운영 결정을 내리는 곳입니다. 오늘 처리해야 할 광고 운영 이슈를 우선순위 기준으로 정리합니다."
        "</div>",
        unsafe_allow_html=True,
    )

    snapshot = load_sample_analysis_snapshot()
    if snapshot is None:
        render_onboarding_start()
        st.warning("운영 예시 데이터를 찾을 수 없습니다. 광고 성과 분석 메뉴에서 파일을 업로드해 주세요.")
        return

    _, analysis = snapshot

    st.subheader("우선 처리 이슈")
    render_todays_action_items(analysis, advertiser="광고주 A")

    st.subheader("오늘의 운영 브리핑")
    render_ai_operating_coach(analysis, advertiser="광고주 A")

    st.info("성과 요약, KPI, 벤치마크, 매체별 성과는 왼쪽 메뉴의 `운영 현황`에서 확인합니다.")


def render_operating_status_dashboard() -> None:
    st.title("운영 현황")
    st.caption("성과 상태와 기준 지표를 확인하는 화면입니다.")
    if not render_data_access_notice("운영 현황"):
        return

    snapshot = load_sample_analysis_snapshot()
    if snapshot is None:
        st.warning("운영 현황을 표시할 예시 데이터를 찾을 수 없습니다. 광고 성과 분석 메뉴에서 파일을 업로드해 주세요.")
        return

    standardized, analysis = snapshot

    score, status, status_color, status_note = calculate_ad_health_status(analysis)
    st.subheader("전체 상태")
    render_health_status_panel(score, status, status_color, status_note, analysis)

    st.subheader("데이터 최신성")
    render_data_freshness_status(standardized)

    st.subheader("핵심 KPI")
    st.caption("기본 화면은 대표와 판매자가 먼저 보는 4개 지표만 보여줍니다.")
    render_kpi_cards(analysis, "기본 모드")

    st.subheader("내 업종 벤치마크")
    render_industry_benchmark_value(analysis)

    st.subheader("매체별 성과")
    render_media_performance(analysis.segment_tables["platform"], view_mode="기본 모드", show_table=False)

    st.subheader("협회 자산")
    render_association_asset_status()

    with st.expander("전문가용 빠른 진단 보기"):
        render_segment_analysis_tables(analysis, "전문가 모드", compact=True)


def render_onboarding_start() -> None:
    content = (
        '<div class="aima-onboarding">'
        '<div class="aima-summary-label">처음 오셨다면</div>'
        '<div class="aima-summary-value">3분 시작하기</div>'
        '<div class="aima-card-grid">'
        '<div><b>STEP 1</b><br>광고 데이터 업로드</div>'
        '<div><b>STEP 2</b><br>AI 분석 실행</div>'
        '<div><b>STEP 3</b><br>운영 점검 확인</div>'
        '<div><b>STEP 4</b><br>보고서 생성</div>'
        "</div>"
        '<div class="aima-summary-note">파일이 없어도 아래 체험 데이터로 캠페인펄스의 운영 흐름을 바로 확인할 수 있습니다.</div>'
        "</div>"
    )
    st.markdown(content, unsafe_allow_html=True)
    if st.button("체험 데이터로 3분 시작", type="primary", use_container_width=True):
        st.session_state["sample_experience_started"] = True
    if st.session_state.get("sample_experience_started"):
        st.success("체험 데이터 기준으로 우선 처리 이슈와 운영 브리핑을 표시하고 있습니다.")


def calculate_ad_health_status(analysis) -> tuple[int, str, str, str]:  # noqa: ANN001
    summary = analysis.summary
    anomalies = analysis.anomalies
    high_count = int((anomalies.get("severity", pd.Series(dtype=str)) == "high").sum())
    medium_count = int((anomalies.get("severity", pd.Series(dtype=str)) == "medium").sum())
    opportunity_count = int((anomalies.get("severity", pd.Series(dtype=str)) == "opportunity").sum())
    roas = float(summary.get("roas", 0))
    ctr = float(summary.get("ctr", 0))
    score = 58 + min(roas * 7, 30) + min(ctr * 500, 8) + min(opportunity_count * 2, 8) - high_count * 10 - medium_count * 4
    score = int(max(0, min(round(score), 100)))
    if score >= 80:
        return score, "좋음", "#22C55E", "성과 유지와 확대 후보를 먼저 검토할 수 있습니다."
    if score >= 60:
        return score, "보통", "#F59E0B", "성과는 유지되고 있으나 일부 캠페인은 점검이 필요합니다."
    return score, "위험", "#EF4444", "광고비 낭비 가능성이 있어 긴급 점검 항목부터 확인해야 합니다."


def render_health_status_panel(score: int, status: str, color: str, note: str, analysis) -> None:  # noqa: ANN001
    summary = analysis.summary
    content = (
        '<div class="aima-status-panel">'
        "<div>"
        '<div class="aima-summary-label">광고 건강도</div>'
        f'<div class="aima-health-score" style="color: {color};">{score}점</div>'
        f'<div class="aima-health-status" style="background: {hex_to_rgba(color, 0.18)}; color: {color};">{escape(status)}</div>'
        "</div>"
        "<div>"
        '<div class="aima-summary-label">전체 상태</div>'
        f'<div class="aima-summary-value">광고수익률 {escape(format_ratio(summary["roas"]))} · 매출 {escape(format_money(summary["revenue"]))}</div>'
        f'<div class="aima-summary-note">{escape(note)}</div>'
        '<div class="aima-summary-note">이 점수는 운영 우선순위를 빠르게 보기 위한 요약입니다.</div>'
        "</div>"
        "</div>"
    )
    st.markdown(content, unsafe_allow_html=True)


def render_todays_action_items(analysis, advertiser: str = "광고주") -> None:  # noqa: ANN001
    items = build_operating_action_issues(analysis, advertiser=advertiser)
    cards = []
    for index, item in enumerate(items[:3], start=1):
        media = operator_display_text(item.media)
        advertiser_name = operator_display_text(item.advertiser)
        target = operator_display_text(item.target)
        action_title = action_oriented_issue_title(item)
        cards.append(
            (
                '<div class="aima-todo-card">'
                f'<div class="aima-todo-rank">{index}</div> '
                f'<span class="aima-pill" style="background: {hex_to_rgba(severity_color(item.severity), 0.18)}; color: {severity_color(item.severity)};">{escape(severity_label(item.severity))}</span>'
                f'<div class="aima-alert-title">{escape(action_title)}</div>'
                f'<div class="aima-card-note">광고주: {escape(advertiser_name)}<br>매체: {escape(media)}</div>'
                '<div class="aima-action-row">'
                '<div class="aima-action-label">추천 액션</div>'
                f'<div class="aima-action-value">{escape(primary_action_text(item.recommended_action))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">예상시간</div>'
                f'<div class="aima-action-value">{escape(estimated_action_time(item.severity))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<details><summary class="aima-action-label">자세히 보기</summary>'
                '<div class="aima-action-row">'
                '<div class="aima-action-label">대상</div>'
                f'<div class="aima-action-value">{escape(target)}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">근거 데이터</div>'
                f'<div class="aima-action-value">{escape(operator_display_text(item.evidence))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">원인 가능성</div>'
                f'<div class="aima-action-value">{escape(operator_display_text(item.cause_hypothesis))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">추천 액션 전체</div>'
                f'<div class="aima-action-value">{render_action_bullets(item.recommended_action)}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">예상 효과</div>'
                f'<div class="aima-action-value">{escape(operator_display_text(item.expected_effect))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">광고주 설명</div>'
                f'<div class="aima-action-value">{escape(operator_display_text(item.advertiser_message))}</div>'
                "</div>"
                '<div class="aima-action-row">'
                '<div class="aima-action-label">보고서 반영</div>'
                f'<div class="aima-action-value">{"반영 권장" if item.report_include else "필요 시 반영"}</div>'
                "</div></details>"
                "</div>"
                "</div>"
            )
        )
    st.markdown(f'<div class="aima-todo-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def severity_color(severity: str) -> str:
    return {"high": "#EF4444", "medium": "#F59E0B", "opportunity": "#22C55E", "low": "#94A3B8"}.get(severity, "#94A3B8")


def severity_label(severity: str) -> str:
    return {"high": "긴급", "medium": "주의", "opportunity": "확대기회", "low": "일반"}.get(severity, "점검")


def operator_display_text(value: object) -> str:
    text = str(value)
    replacements = {
        "매체 미분류": "데이터 확인 필요",
        "미분류": "데이터 확인 필요",
        "판단 불가": "데이터 부족",
        "Rule Engine": "운영 판단 기준",
        "MVP": "핵심 기능",
        "P0": "핵심",
        "API": "계정 연동",
        "자동 다운로드 에이전트": "자동 수집 준비",
        "테스트": "검증",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def render_action_bullets(action_text: str) -> str:
    normalized = operator_display_text(action_text)
    parts = [part.strip(" .") for part in re.split(r",|·|/", normalized) if part.strip(" .")]
    if len(parts) <= 1:
        return escape(normalized)
    return "<ul>" + "".join(f"<li>{escape(part)}</li>" for part in parts[:4]) + "</ul>"


def primary_action_text(action_text: str) -> str:
    normalized = operator_display_text(action_text)
    parts = [part.strip(" .") for part in re.split(r",|·|/", normalized) if part.strip(" .")]
    return parts[0] if parts else normalized


def action_oriented_issue_title(issue: OperatingActionIssue) -> str:
    problem = operator_display_text(issue.problem)
    action = primary_action_text(issue.recommended_action)
    lower_problem = problem.lower()
    if "전환" in problem and ("없" in problem or "하락" in problem or "낮" in problem):
        return "광고주에게 전환 성과 하락 원인 설명 필요"
    if "클릭률" in problem or "ctr" in lower_problem:
        return "광고 소재와 노출 키워드 점검 필요"
    if "광고수익률" in problem or "roas" in lower_problem:
        return "광고주에게 광고수익률 변화 원인 설명 필요"
    if "광고비" in problem and ("증가" in problem or "과다" in problem or "사용" in problem):
        return "광고비 조정 필요 여부 검토"
    if "데이터 부족" in problem or "확인 필요" in problem:
        return "추가 데이터 확인 필요"
    if action and action != "데이터 부족":
        return f"{action} 검토 필요"
    return problem


def estimated_action_time(severity: str) -> str:
    return {"high": "10분", "medium": "15분", "opportunity": "20분", "low": "10분"}.get(severity, "10분")


def render_industry_benchmark_value(analysis) -> None:  # noqa: ANN001
    summary = analysis.summary
    current_roas = float(summary.get("roas", 0))
    current_cpc = float(summary.get("cpc", 0))
    industry_roas = 4.10
    industry_cpc = 980.0
    roas_gap = current_roas - industry_roas
    cpc_gap = (current_cpc - industry_cpc) / industry_cpc if industry_cpc else 0
    tier = "상위 15%" if current_roas >= industry_roas * 1.2 else "평균 이상" if current_roas >= industry_roas else "점검 필요"
    cards = [
        ("업종", "건강식품", "현재 예시 기준 업종 벤치마크입니다."),
        ("현재 ROAS", format_ratio(current_roas), f"업종 평균 {format_ratio(industry_roas)} · {tier}"),
        ("현재 CPC", format_money(current_cpc), f"업종 평균 {format_money(industry_cpc)} · 평균 대비 {format_percent(cpc_gap)}"),
        ("판단", "잘하고 있는가?", "ROAS는 평균 대비 양호하고 CPC는 낮출 여지가 있는 구조입니다." if current_roas >= industry_roas else "ROAS를 업종 평균까지 끌어올리는 개선이 우선입니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def render_data_freshness_status(frame: pd.DataFrame | None) -> None:
    if frame is None or frame.empty:
        st.info("데이터 최신성을 확인할 원본 날짜 데이터가 없습니다.")
        return

    bounds = date_bounds(frame)
    if bounds is None:
        st.warning("날짜 컬럼을 확인할 수 없어 데이터 최신성 상태를 표시하지 못했습니다.")
        return

    min_date, max_date = bounds
    lag_days = max((date.today() - max_date).days, 0)
    if lag_days <= 1:
        freshness_status = "최신"
        status_note = "오늘 운영 판단에 바로 사용할 수 있습니다."
    elif lag_days <= 7:
        freshness_status = "주의"
        status_note = "최근 며칠 데이터가 비어 있을 수 있어 최신 다운로드 여부를 확인합니다."
    else:
        freshness_status = "오래됨"
        status_note = "운영 판단 전에 최신 데이터를 다시 수집하거나 업로드해야 합니다."

    missing_rows = int(frame["date"].isna().sum()) if "date" in frame.columns else 0
    cards = [
        ("마지막 데이터 기준일", max_date.strftime("%Y-%m-%d"), f"현재 기준 {lag_days:,}일 전 데이터"),
        ("데이터 최신성", freshness_status, status_note),
        ("분석 기간", f"{min_date:%Y-%m-%d} ~ {max_date:%Y-%m-%d}", "업로드된 파일 기준 기간입니다."),
        ("누락 데이터", f"{missing_rows:,}행", "날짜가 비어 있으면 기간 비교 신뢰도가 낮아질 수 있습니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)
    render_collection_channel_status()


def render_collection_channel_status() -> None:
    cards = [
        ("연동 준비 채널", "네이버 검색광고", "추후 계정 연결 시 자동으로 최신 데이터를 확인할 수 있게 준비합니다."),
        ("수동 확인 채널", "G마켓 · 옥션 · 11번가", "현재는 광고센터 파일 업로드 기준으로 확인합니다."),
        ("현재 수집 방식", "파일 업로드", "광고센터에서 내려받은 파일을 올리면 바로 분석합니다."),
        ("수집 실패/누락", "확인 필요", "최신 파일이 없으면 최근 성과 판단이 제한될 수 있습니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def render_ad_data_analyzer() -> None:
    st.title("광고 성과 분석")
    st.caption("광고 Excel 또는 CSV를 분석해 운영 이슈와 보고서 결과를 생성합니다.")
    render_demo_data_notice()
    view_mode = render_view_mode_selector("ad_analysis")

    advertiser = st.text_input("광고주명", value="광고주")

    with st.expander("처음 보는 분을 위한 지표 설명", expanded=False):
        st.markdown(
            "\n".join(
                [
                    f"- **{metric_label_with_english('impressions')}**: {column_description('impressions')}",
                    f"- **{metric_label_with_english('clicks')}**: {column_description('clicks')}",
                    f"- **{metric_label_with_english('ctr')}**: {column_description('ctr')}",
                    f"- **{metric_label_with_english('cpc')}**: {column_description('cpc')}",
                    f"- **{metric_label_with_english('conversions')}**: {column_description('conversions')}",
                    f"- **{metric_label_with_english('cvr')}**: {column_description('cvr')}",
                    f"- **{metric_label_with_english('cpa')}**: {column_description('cpa')}",
                    f"- **{metric_label_with_english('roas')}**: {column_description('roas')}",
                ]
            )
        )

    st.subheader("1단계 광고 데이터 업로드")
    uploaded = st.file_uploader(
        "광고 성과 엑셀 또는 CSV 업로드",
        type=["xlsx", "xls", "csv"],
        key="analysis_file_upload",
    )

    if uploaded is None:
        st.info("광고센터에서 내려받은 원본 파일을 먼저 업로드해 주세요.")
    else:
        st.success(f"업로드 완료: {uploaded.name}")

    st.subheader("2단계 원본 파일 진단")
    st.caption("분석 전에 컬럼 구조와 데이터 부족 항목을 먼저 확인합니다.")
    if uploaded is None:
        st.info("파일을 업로드하면 원본 파일 진단을 실행할 수 있습니다.")
    elif st.button("업로드 파일 진단 실행", use_container_width=True, key="analysis_upload_diagnostic_button"):
        run_uploaded_file_diagnostic(uploaded)

    st.subheader("3단계 분석 실행")
    analysis_result = None
    if uploaded is None:
        st.info("파일 업로드 후 분석을 실행할 수 있습니다.")
    elif st.button("분석 실행", type="primary", use_container_width=True, key="analysis_upload_run_button"):
        temp_path: Path | None = None
        try:
            temp_path = write_uploaded_file_to_temp(uploaded)
            output_dir = BASE_DIR / "data" / "reports" / temp_path.stem
            analysis_result = run_pipeline_safely(temp_path, output_dir, advertiser)
            if analysis_result is not None:
                st.session_state[UPLOADED_SNAPSHOT_KEY] = (
                    analysis_result.standardized,
                    analysis_result.analysis,
                )
                st.success("업로드 데이터 분석 결과를 현재 세션의 우선 데이터로 사용합니다.")
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    st.subheader("4단계 분석 결과")
    if uploaded is None:
        st.info("파일을 업로드하고 분석을 실행하면 결과가 여기에 표시됩니다.")
    elif analysis_result is None:
        st.info("분석 실행 버튼을 누르면 우선 처리 이슈, 운영 브리핑, 보고서 다운로드가 표시됩니다.")
    else:
        render_analysis_result(analysis_result, view_mode, advertiser=advertiser)

    with st.expander("체험 데이터로 흐름 보기"):
        render_sample_analysis_preview(view_mode)


def run_uploaded_file_diagnostic(uploaded_file) -> None:  # noqa: ANN001
    saved_path: Path | None = None
    should_cleanup = False
    try:
        saved_path, should_cleanup = persist_uploaded_file_for_diagnostic(uploaded_file, keep_original=False)
        audit = audit_media_file(saved_path)
        render_raw_file_audit_result(audit)
    except Exception as error:  # noqa: BLE001
        st.error("원본 파일 진단 중 문제가 발생했습니다. 파일 형식과 시트 구조를 확인해 주세요.")
        with st.expander("진단 오류 자세히 보기"):
            st.exception(error)
    finally:
        if should_cleanup and saved_path is not None and saved_path.exists():
            saved_path.unlink(missing_ok=True)


def write_uploaded_file_to_temp(uploaded_file) -> Path:  # noqa: ANN001
    safe_name = safe_upload_filename(uploaded_file.name)
    suffix = Path(safe_name).suffix or ".xlsx"
    prefix = f"aimaos_analysis_{Path(safe_name).stem}_"
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as temp:
        temp.write(uploaded_file.getbuffer())
        return Path(temp.name)


def render_sample_analysis_preview(view_mode: str) -> None:
    sample_path, sample_mode = active_sample_data_path()
    if sample_path is None:
        st.warning("체험 데이터 파일을 찾을 수 없습니다.")
        return

    if sample_mode == "demo":
        if using_demo_data():
            st.info(DEMO_DATA_NOTICE)
        else:
            st.caption("현재 분석에는 업로드 데이터가 우선 적용됩니다. 아래 데이터는 체험용으로만 사용됩니다.")
        preview_advertiser = "샘플 데모 광고주"
        report_folder = "demo_streamlit"
        button_label = "데모 데이터 분석 실행"
    else:
        preview_advertiser = "광고주 A"
        report_folder = "sample_streamlit"
        button_label = "체험 데이터 분석 실행"

    st.caption("업로드 전에 전체 흐름을 확인할 수 있는 체험 데이터입니다. 실제 광고주 데이터는 업로드 후 분석해 주세요.")
    if st.button(button_label, use_container_width=True, key="sample_analysis_preview_button"):
        output_dir = BASE_DIR / "data" / "reports" / report_folder
        result = run_pipeline_safely(sample_path, output_dir, preview_advertiser)
        if result is not None:
            render_analysis_result(result, view_mode, advertiser=preview_advertiser)

    st.caption("체험 데이터는 상위 50행만 미리보기로 표시합니다.")
    try:
        sample = pd.read_csv(sample_path)
        st.dataframe(sample.head(50), use_container_width=True, hide_index=True)
    except Exception as error:  # noqa: BLE001
        st.error("체험 데이터를 읽지 못했습니다.")
        with st.expander("체험 데이터 오류 자세히 보기"):
            st.exception(error)


def run_pipeline_safely(input_path: str | Path, output_dir: str | Path, advertiser: str):  # noqa: ANN001
    try:
        return run_analysis_pipeline(input_path=input_path, output_dir=output_dir, advertiser=advertiser)
    except Exception as error:  # noqa: BLE001
        st.error("분석 중 문제가 발생했습니다. 파일 형식, 날짜, 숫자 컬럼을 확인해 주세요.")
        with st.expander("문제 원인 자세히 보기"):
            st.exception(error)
        return None


def render_raw_file_diagnostics() -> None:
    st.subheader("원본 파일 진단")
    st.caption(
        "분석 실행 전에 원본 파일 구조만 확인합니다. 이 단계에서는 성과 보고서를 만들지 않습니다."
    )

    with st.expander("원본 파일 진단이 필요한 이유"):
        st.markdown(
            "\n".join(
                [
                    "- J: 드라이브처럼 직접 접근이 막힌 파일도 브라우저 업로드로 구조를 확인할 수 있습니다.",
                    "- G마켓, 옥션, 네이버, 11번가 파일의 컬럼명이 캠페인펄스 공통 컬럼과 맞는지 먼저 확인합니다.",
                    "- 원본 전체 행은 화면에 렌더링하지 않고, 컬럼명과 매핑 결과만 표시합니다.",
                    "- 진단이 끝난 뒤 필요할 때만 실제 분석을 실행하면 됩니다.",
                ]
            )
        )

    diagnostic_upload = st.file_uploader(
        "진단할 원본 파일 업로드",
        type=["xlsx", "xls", "csv"],
        key="raw_file_diagnostic_upload",
        help="광고센터에서 내려받은 원본 파일을 그대로 올려 주세요. 이 단계에서는 분석 보고서를 만들지 않습니다.",
    )
    keep_original = st.checkbox(
        "진단 후 원본 파일을 data/raw/uploaded_diagnostics 폴더에 보관",
        value=False,
        help="체크하지 않으면 임시 진단 후 파일을 삭제합니다.",
    )

    if diagnostic_upload is None:
        st.info("G마켓, 옥션, 네이버, 11번가 원본 파일을 올리면 즉시 컬럼 매핑 진단을 볼 수 있습니다.")
        return

    saved_path: Path | None = None
    should_cleanup = False
    try:
        saved_path, should_cleanup = persist_uploaded_file_for_diagnostic(diagnostic_upload, keep_original)
        audit = audit_media_file(saved_path)
        if keep_original:
            st.success(f"원본 파일을 보관했습니다: {saved_path}")
        render_raw_file_audit_result(audit)
    except Exception as error:  # noqa: BLE001
        st.error("원본 파일 진단 중 문제가 발생했습니다. 파일 형식과 시트 구조를 확인해 주세요.")
        with st.expander("진단 오류 자세히 보기"):
            st.exception(error)
    finally:
        if should_cleanup and saved_path is not None and saved_path.exists():
            saved_path.unlink(missing_ok=True)


def persist_uploaded_file_for_diagnostic(uploaded_file, keep_original: bool) -> tuple[Path, bool]:  # noqa: ANN001
    safe_name = safe_upload_filename(uploaded_file.name)
    suffix = Path(safe_name).suffix or ".xlsx"
    if keep_original:
        destination_dir = BASE_DIR / "data" / "raw" / "uploaded_diagnostics"
        destination_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = destination_dir / f"{timestamp}_{safe_name}"
        destination.write_bytes(uploaded_file.getbuffer())
        return destination, False

    prefix = f"aimaos_audit_{Path(safe_name).stem}_"
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as temp:
        temp.write(uploaded_file.getbuffer())
        return Path(temp.name), True


def safe_upload_filename(filename: str) -> str:
    path_name = Path(filename).name
    stem = Path(path_name).stem
    suffix = Path(path_name).suffix
    safe_stem = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", stem).strip("._-")
    if not safe_stem:
        safe_stem = "uploaded_ad_report"
    return f"{safe_stem}{suffix.lower()}"


def render_raw_file_audit_result(audit: MediaFileAudit) -> None:
    profile = diagnostic_profile_label(audit)
    action_status, action_note = action_generation_status(audit)
    unavailable_labels = unavailable_required_labels(audit)
    cards = [
        ("추정 매체", audit.inferred_media, "파일명과 매체 컬럼을 기준으로 판단합니다."),
        ("적용 기준", profile, "현재는 실제 파일 구조를 기준으로 진단합니다."),
        ("읽은 컬럼", f"{audit.column_count:,}개", f"데이터 행 수 {audit.row_count:,}행. 원본 전체 행은 화면에 표시하지 않습니다."),
        ("우선 처리 이슈", action_status, action_note),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)

    if audit.error:
        st.error("파일을 읽지 못했습니다.")
        with st.expander("오류 자세히 보기"):
            st.code(audit.error)
        return

    tab_columns, tab_mapping, tab_judgment = st.tabs(["읽은 컬럼명", "매핑 결과", "판단 결과"])
    with tab_columns:
        st.caption("업로드 파일에서 읽은 컬럼명입니다. 원본 데이터 행은 표시하지 않습니다.")
        st.dataframe(pd.DataFrame({"읽은 컬럼명": audit.original_columns}), use_container_width=True, hide_index=True)

    with tab_mapping:
        col1, col2 = st.columns(2)
        with col1:
            st.caption("매핑 성공 컬럼")
            st.dataframe(mapping_success_frame(audit), use_container_width=True, hide_index=True)
        with col2:
            st.caption("매핑 실패 컬럼")
            st.dataframe(mapping_failure_frame(audit), use_container_width=True, hide_index=True)

        st.caption("추가해야 할 컬럼 연결 후보")
        candidate_frame = alias_candidate_frame(audit)
        if candidate_frame.empty:
            st.success("현재 기준 추가 alias 후보가 없습니다.")
        else:
            st.dataframe(candidate_frame, use_container_width=True, hide_index=True)

    with tab_judgment:
        st.caption("필수 지표별 진단 상태")
        st.dataframe(required_status_frame(audit), use_container_width=True, hide_index=True)

        if unavailable_labels:
            st.warning("데이터 부족 지표: " + ", ".join(unavailable_labels))
        else:
            st.success("현재 필수 지표는 모두 진단 가능합니다.")

        st.caption("우선 처리 예상 이슈")
        if audit.action_issue_preview:
            for item in audit.action_issue_preview:
                st.markdown(f"- {operator_display_text(item)}")
        else:
            st.info("현재 운영 판단 기준으로는 주요 조치 필요 항목이 없습니다.")


def diagnostic_profile_label(audit: MediaFileAudit) -> str:
    media = audit.inferred_media
    if media in {"G마켓", "옥션", "G마켓/옥션"}:
        return "G마켓/옥션 기존 광고센터 리포트 후보"
    if media in {"네이버", "11번가"}:
        return "실제 파일 기준 자동 진단"
    if audit.report_version != "unknown":
        return audit.report_version
    return "공통 광고 파일 진단"


def action_generation_status(audit: MediaFileAudit) -> tuple[str, str]:
    if audit.load_status != "성공":
        return "불가", "파일을 읽지 못해 운영 이슈 확인이 어렵습니다."
    if not audit.action_issue_preview:
        return "제한적", "파일은 읽었지만 주요 조치 이슈가 생성되지 않았습니다."
    if any(item.startswith("판단 불가") for item in audit.action_issue_preview):
        return "데이터 부족", "데이터 행 수 또는 핵심 수치가 부족해 판단을 보류합니다."
    core_statuses = [audit.required_status.get(key) for key in ["impressions", "clicks", "cost", "conversions", "revenue"]]
    if all(status == "성공" for status in core_statuses):
        return "가능", f"예상 이슈 {audit.action_issue_count:,}개를 생성할 수 있습니다."
    return "제한적", "일부 핵심 지표가 부족해 생성 품질이 제한될 수 있습니다."


def unavailable_required_labels(audit: MediaFileAudit) -> list[str]:
    return [
        label
        for key, label in {
            "date": "날짜",
            "account_name": "광고주명",
            "platform": "매체",
            "campaign_name": "캠페인명",
            "ad_group_name": "광고그룹명",
            "product_or_keyword": "상품명 또는 키워드",
            "impressions": "노출수",
            "clicks": "클릭수",
            "cost": "광고비",
            "conversions": "전환수",
            "revenue": "매출",
            "cart_count": "장바구니 수",
            "roas": "ROAS",
            "cpc": "CPC",
            "ctr": "CTR",
            "cvr": "CVR",
        }.items()
        if audit.required_status.get(key) == "판단 불가"
    ]


def mapping_success_frame(audit: MediaFileAudit) -> pd.DataFrame:
    if not audit.mapped_columns:
        return pd.DataFrame({"원본 컬럼": ["없음"], "표준 컬럼": ["없음"]})
    return pd.DataFrame(
        [{"원본 컬럼": source, "표준 컬럼": target} for source, target in audit.mapped_columns.items()]
    )


def mapping_failure_frame(audit: MediaFileAudit) -> pd.DataFrame:
    if not audit.unmapped_columns:
        return pd.DataFrame({"매핑 실패 컬럼": ["없음"]})
    return pd.DataFrame({"매핑 실패 컬럼": audit.unmapped_columns})


def required_status_frame(audit: MediaFileAudit) -> pd.DataFrame:
    labels = {
        "date": "날짜",
        "account_name": "광고주명",
        "platform": "매체",
        "campaign_name": "캠페인명",
        "ad_group_name": "광고그룹명",
        "product_or_keyword": "상품명 또는 키워드",
        "impressions": "노출수",
        "clicks": "클릭수",
        "cost": "광고비",
        "conversions": "전환수",
        "revenue": "매출",
        "cart_count": "장바구니 수",
        "roas": "ROAS",
        "cpc": "CPC",
        "ctr": "CTR",
        "cvr": "CVR",
    }
    return pd.DataFrame(
        [{"필수 지표": label, "진단 상태": operator_display_text(audit.required_status.get(key, "판단 불가"))} for key, label in labels.items()]
    )


def alias_candidate_frame(audit: MediaFileAudit) -> pd.DataFrame:
    rows = [alias_candidate_for_column(column) for column in audit.unmapped_columns]
    rows = [row for row in rows if row is not None]
    return pd.DataFrame(rows)


def alias_candidate_for_column(column: str) -> dict[str, str] | None:
    text = column.strip()
    normalized = text.lower().replace(" ", "")
    known_metadata = {value.lower().replace(" ", "") for value in UNMAPPED_MARKETPLACE_METADATA}
    if normalized in known_metadata or normalized in {"source_sheet", "sourcesheet"}:
        return {"원본 컬럼": text, "추천 연결": "메타데이터 보류", "처리 의견": "실제 파일 구조 확인 후 별도 보조 컬럼으로 보관 검토"}

    rules = [
        (["장바구니", "cart"], "cart_count", "현재 표준 스키마에는 없어 확장 검토 필요"),
        (["노출", "impression", "impr"], "impressions", "컬럼 연결 후보"),
        (["클릭수", "click"], "clicks", "컬럼 연결 후보"),
        (["광고비", "소진", "비용", "과금", "spend", "cost"], "cost", "컬럼 연결 후보"),
        (["전환수", "구매수", "전환건수", "conversion"], "conversions", "컬럼 연결 후보"),
        (["매출", "주문금액", "결제금액", "revenue", "sales"], "revenue", "컬럼 연결 후보"),
        (["주문수", "주문건수", "결제수", "order"], "orders", "컬럼 연결 후보"),
        (["상품명", "상품", "소재", "product", "item"], "product_name", "컬럼 연결 후보"),
        (["키워드", "검색어", "keyword", "query"], "keyword", "컬럼 연결 후보"),
        (["캠페인", "campaign"], "campaign_name", "컬럼 연결 후보"),
        (["그룹", "adgroup"], "ad_group_name", "컬럼 연결 후보"),
        (["roas", "수익률", "광고수익률"], "roas", "계산 지표라 원본 연결은 보류 가능"),
        (["cpc", "클릭당"], "cpc", "계산 지표라 원본 연결은 보류 가능"),
        (["ctr", "클릭률"], "ctr", "계산 지표라 원본 연결은 보류 가능"),
        (["cvr", "전환율"], "cvr", "계산 지표라 원본 연결은 보류 가능"),
    ]
    for needles, target, note in rules:
        if any(needle.lower().replace(" ", "") in normalized for needle in needles):
            return {"원본 컬럼": text, "추천 연결": target, "처리 의견": note}
    if text in {alias for aliases in ALIASES_ADDED_FOR_MARKETPLACE.values() for alias in aliases}:
        return None
    return {"원본 컬럼": text, "추천 연결": "검토 필요", "처리 의견": "실제 의미 확인 후 alias 추가 여부 결정"}


def metric_label_with_english(metric: str) -> str:
    english = METRIC_ENGLISH_LABELS.get(metric)
    if english is None:
        return metric_label(metric)
    return f"{metric_label(metric)} ({english})"


def render_view_mode_selector(key_prefix: str) -> str:
    return st.segmented_control(
        "보기 모드",
        options=VIEW_MODES,
        default="기본 모드",
        key=f"{key_prefix}_view_mode",
        help="기본 모드는 대표와 판매자용 핵심 지표만 보여주고, 전문가 모드는 세부 운영 지표를 추가로 보여줍니다.",
    )


def render_analysis_result(result, view_mode: str = "기본 모드", advertiser: str = "광고주") -> None:  # noqa: ANN001
    st.subheader("우선 처리 이슈")
    render_todays_action_items(result.analysis, advertiser=advertiser)

    st.subheader("오늘의 운영 브리핑")
    render_ai_operating_coach(result.analysis, advertiser=advertiser)

    st.subheader("전체 상태")
    score, status, status_color, status_note = calculate_ad_health_status(result.analysis)
    render_health_status_panel(score, status, status_color, status_note, result.analysis)

    standardized = standardized_from_result(result)
    if standardized is not None:
        st.subheader("데이터 최신성")
        render_data_freshness_status(standardized)

    st.subheader("핵심 KPI")
    render_kpi_cards(result.analysis, view_mode)

    st.subheader("내 업종 벤치마크")
    render_industry_benchmark_value(result.analysis)

    st.subheader("매체별 성과")
    render_media_performance(result.analysis.segment_tables["platform"], view_mode=view_mode)

    render_segment_analysis_tables(result.analysis, view_mode)

    st.subheader("기간별 성과")
    period_tabs = st.tabs(["일자별", "주간별", "월별", "분기별", "반기별", "연도별", "시즌별"])
    period_keys = ["daily", "weekly", "monthly", "quarterly", "half_year", "yearly", "seasonal"]
    for tab, key in zip(period_tabs, period_keys, strict=False):
        with tab:
            table = result.analysis.period_tables.get(key)
            if table is None or table.empty:
                st.info("날짜 데이터가 없어 표시할 수 없습니다.")
            else:
                st.dataframe(format_analysis_table_for_mode(table, view_mode), use_container_width=True, hide_index=True)

    if standardized is None:
        st.info("표준화된 원본 데이터를 확인할 수 없어 사용자 지정 기간 분석을 표시하지 못했습니다.")
    else:
        render_custom_period_analysis(standardized, view_mode)
    render_report_downloads(result)


def render_kpi_cards(analysis, view_mode: str) -> None:  # noqa: ANN001
    summary = analysis.summary
    comparison = comparison_lookup(analysis.period_comparison)
    metrics = CORE_METRICS + (EXPERT_METRICS if view_mode == "전문가 모드" else [])
    cards = []
    for metric in metrics:
        value = format_by_metric(metric, summary.get(metric, 0))
        change = comparison.get(metric)
        change_text, change_color = format_change_text(change)
        note = kpi_note(metric)
        cards.append(
            (
                '<div class="aima-kpi-card">'
                "<div>"
                f'<div class="aima-kpi-label">{escape(metric_label_with_english(metric))}</div>'
                f'<div class="aima-kpi-value">{escape(value)}</div>'
                "</div>"
                "<div>"
                f'<div class="aima-kpi-change" style="color: {change_color};">{escape(change_text)}</div>'
                f'<div class="aima-summary-note">{escape(note)}</div>'
                "</div>"
                "</div>"
            )
        )
    st.markdown(f'<div class="aima-kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def comparison_lookup(comparison: pd.DataFrame) -> dict[str, float]:
    if comparison.empty or "metric" not in comparison.columns or "change_rate" not in comparison.columns:
        return {}
    return {str(row["metric"]): float(row["change_rate"]) for _, row in comparison.iterrows()}


def format_change_text(change_rate: float | None) -> tuple[str, str]:
    if change_rate is None:
        return "이전 기간 비교 데이터 없음", "#94A3B8"
    if change_rate > 0:
        return f"이전 기간 대비 +{format_percent(change_rate)}", "#22C55E"
    if change_rate < 0:
        return f"이전 기간 대비 {format_percent(change_rate)}", "#EF4444"
    return "이전 기간 대비 변화 없음", "#94A3B8"


def kpi_note(metric: str) -> str:
    notes = {
        "cost": "광고 운영에 사용한 전체 비용입니다.",
        "revenue": "광고 성과로 집계된 전체 매출입니다.",
        "orders": "광고를 통해 발생한 주문 수입니다.",
        "roas": "100.00%는 광고비와 같은 매출을 의미합니다.",
        "impressions": "광고가 사용자 화면에 표시된 횟수입니다.",
        "clicks": "광고 클릭 반응입니다.",
        "ctr": "노출 대비 클릭 반응입니다.",
        "cpc": "클릭 1회를 얻는 평균 비용입니다.",
        "conversions": "구매, 문의, 신청 등 목표 행동 수입니다.",
        "cvr": "클릭 이후 성과로 이어진 비율입니다.",
        "cpa": "전환 1건을 만드는 평균 비용입니다.",
    }
    return notes.get(metric, "")


def render_ai_operating_coach(analysis, advertiser: str = "광고주") -> None:  # noqa: ANN001
    issues = build_operating_action_issues(analysis, advertiser=advertiser)
    if not issues:
        st.success("현재 데이터에서는 즉시 점검할 운영 포인트가 발견되지 않았습니다.")
        return

    groups = [
        ("긴급", "#EF4444", [issue for issue in issues if issue.severity == "high"], "광고비 낭비 가능성이 있어 먼저 확인합니다."),
        ("확대기회", "#22C55E", [issue for issue in issues if issue.severity == "opportunity"], "성과가 좋아 예산 확대를 검토할 수 있습니다."),
        ("주의", "#F59E0B", [issue for issue in issues if issue.severity in {"medium", "low"}], "소재, 키워드, 랜딩 흐름을 점검합니다."),
    ]
    columns = []
    for title, color, issue_group, empty_note in groups:
        items = []
        for issue in issue_group[:2]:
            items.append(
                (
                    '<div class="aima-coach-item">'
                    f'<div class="aima-alert-meta">광고주: {escape(operator_display_text(issue.advertiser))} · 매체: {escape(operator_display_text(issue.media))} · 대상: {escape(operator_display_text(issue.target))}</div>'
                    '<div class="aima-action-row">'
                    '<div class="aima-action-label">점검할 일</div>'
                    f'<div class="aima-action-value">{escape(action_oriented_issue_title(issue))}</div>'
                    "</div>"
                    '<div class="aima-action-row">'
                    '<div class="aima-action-label">바로 할 일</div>'
                    f'<div class="aima-action-value">{escape(operator_display_text(issue.recommended_action))}</div>'
                    "</div>"
                    '<div class="aima-action-row">'
                    '<div class="aima-action-label">예상 효과</div>'
                    f'<div class="aima-action-value">{escape(operator_display_text(issue.expected_effect))}</div>'
                    "</div>"
                    "</div>"
                )
            )
        if not items:
            items.append(f'<div class="aima-card-note">{escape(empty_note)}</div>')
        columns.append(
            (
                f'<div class="aima-coach-column" style="border-top: 5px solid {color};">'
                f'<div class="aima-coach-heading" style="color: {color};">{escape(title)}</div>'
                f'{"".join(items)}'
                "</div>"
            )
        )
    st.markdown(f'<div class="aima-coach-grid">{"".join(columns)}</div>', unsafe_allow_html=True)

    with st.expander("운영 점검 상세표 보기"):
        st.dataframe(format_operational_issues_for_display(issues), use_container_width=True, hide_index=True)


def render_overview_summary(analysis) -> None:  # noqa: ANN001
    summary = analysis.summary
    platform_table = analysis.segment_tables.get("platform", pd.DataFrame())
    top_cost_platform = top_row_label(platform_table, "cost", "platform")
    top_roas_platform = top_row_label(platform_table[platform_table["cost"] > 0], "roas", "platform")
    alert_count = len(analysis.anomalies)
    opportunity_count = int((analysis.anomalies.get("severity", pd.Series(dtype=str)) == "opportunity").sum())

    cards = [
        ("총 광고비", format_money(summary["cost"]), f"가장 많이 사용한 매체: {top_cost_platform}"),
        ("총 매출", format_money(summary["revenue"]), "광고 성과로 집계된 전체 매출입니다."),
        ("광고수익률 (ROAS)", format_ratio(summary["roas"]), "100.00%는 광고비와 같은 매출을 의미합니다."),
        ("전환수", format_count(summary["conversions"]), "구매, 문의, 신청 등 목표 행동 수입니다."),
        ("클릭률 (CTR)", format_percent(summary["ctr"]), "노출 대비 클릭 반응입니다."),
        ("점검 포인트", f"{alert_count:,}건", f"확대기회 {opportunity_count:,}건 포함"),
    ]

    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)
    st.markdown(
        "\n".join(
            [
                f"- 전체 광고비는 **{format_money(summary['cost'])}**, 매출은 **{format_money(summary['revenue'])}**입니다.",
                f"- 전체 광고수익률은 **{format_ratio(summary['roas'])}**이며, 가장 효율이 높은 매체는 **{top_roas_platform}**입니다.",
                f"- 운영자가 먼저 볼 항목은 **{alert_count:,}건**이며, 이 중 확장 검토 후보는 **{opportunity_count:,}건**입니다.",
            ]
        )
    )


def render_media_performance(platform_table: pd.DataFrame, view_mode: str = "기본 모드", show_table: bool = True) -> None:
    if platform_table.empty:
        st.info("매체별로 표시할 데이터가 없습니다.")
        return

    st.caption("각 매체는 브랜드 대표 색상으로 표시했습니다. 로고 대신 색상 배지를 사용해 권리 이슈 없이 구분성을 높였습니다.")
    max_cost = float(platform_table["cost"].max()) if not platform_table.empty else 0
    cards = []
    for _, row in platform_table.sort_values("cost", ascending=False).iterrows():
        platform = str(row["platform"])
        style = media_style(platform)
        cost_width = safe_width(row["cost"], max_cost)
        cards.append(
            (
                '<div class="aima-media-card">'
                f"{media_chip(platform)}"
                f'<div class="aima-card-note">광고비 {escape(format_money(row["cost"]))} · 매출 {escape(format_money(row["revenue"]))}</div>'
                f'<div class="aima-card-note">전환수 {escape(format_count(row["conversions"]))} · 광고수익률 {escape(format_ratio(row["roas"]))}</div>'
                '<div class="aima-bar-track" title="광고비 비중">'
                f'<div class="aima-bar-fill" style="width: {cost_width:.1f}%; background: {style["color"]};"></div>'
                "</div></div>"
            )
        )
    st.markdown(f'<div class="aima-card-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    if show_table:
        st.dataframe(format_media_table_for_display(platform_table, view_mode), use_container_width=True, hide_index=True)


def render_segment_analysis_tables(analysis, view_mode: str, compact: bool = False) -> None:  # noqa: ANN001
    labels = [
        ("campaign", "캠페인 분석"),
        ("ad_group", "광고그룹 분석"),
        ("keyword", "키워드 분석"),
    ]
    if compact:
        labels = labels[:2]
    tabs = st.tabs([label for _, label in labels])
    for tab, (key, label) in zip(tabs, labels, strict=False):
        with tab:
            table = analysis.segment_tables.get(key, pd.DataFrame())
            if table.empty:
                st.info(f"{label}에 표시할 데이터가 없습니다.")
            else:
                st.caption("기본 모드는 핵심 KPI만 표시합니다. 세부 운영 지표는 전문가 모드에서 확인할 수 있습니다.")
                st.dataframe(format_analysis_table_for_mode(table, view_mode), use_container_width=True, hide_index=True)


def format_analysis_table_for_mode(frame: pd.DataFrame, view_mode: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    if view_mode == "전문가 모드":
        return format_dataframe_for_display(frame)
    wanted = [column for column in DIMENSION_COLUMNS + CORE_METRICS if column in frame.columns]
    if not wanted:
        return format_dataframe_for_display(frame)
    return format_dataframe_for_display(frame[wanted])


def render_operational_signals(anomalies: pd.DataFrame) -> None:
    if anomalies.empty:
        st.success("현재 데이터에서 우선 확인할 운영 점검 포인트가 발견되지 않았습니다.")
        return

    st.caption("긴급 이슈와 확대기회를 함께 보여줍니다. 먼저 확인할 항목부터 카드 형태로 정리했습니다.")
    render_signal_distribution(anomalies)
    cards = []
    for _, row in anomalies.head(6).iterrows():
        severity = str(row.get("severity", "medium"))
        style = ALERT_STYLES.get(severity, ALERT_STYLES["medium"])
        title = signal_title(row)
        cards.append(
            (
                f'<div class="aima-alert-card" style="--accent: {style["color"]};">'
                f'<span class="aima-pill" style="background: {style["background"]}; color: {style["color"]};">{escape(style["label"])}</span>'
                f'<div class="aima-alert-title">{escape(title)}</div>'
                f'<div class="aima-alert-meta">{escape(str(row.get("target", "미분류")))}</div>'
                f'<div class="aima-card-note">{escape(str(row.get("reason", "")))}</div>'
                f'<div class="aima-card-note">광고비 {escape(format_money(row.get("cost", 0)))} · 클릭률 {escape(format_percent(row.get("ctr", 0)))} · 광고수익률 {escape(format_ratio(row.get("roas", 0)))}</div>'
                "</div>"
            )
        )
    st.markdown(f'<div class="aima-card-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    with st.expander("운영 점검 상세표 보기"):
        st.dataframe(format_operational_signal_table(anomalies), use_container_width=True, hide_index=True)


def render_summary_cards(cards: list[tuple[str, str, str]]) -> str:
    rendered = []
    for label, value, note in cards:
        rendered.append(
            (
                '<div class="aima-summary-card">'
                f'<div class="aima-summary-label">{escape(label)}</div>'
                f'<div class="aima-summary-value">{escape(value)}</div>'
                f'<div class="aima-summary-note">{escape(note)}</div>'
                "</div>"
            )
        )
    return f'<div class="aima-card-grid">{"".join(rendered)}</div>'


def top_row_label(frame: pd.DataFrame, metric: str, label_column: str) -> str:
    if frame.empty or metric not in frame.columns or label_column not in frame.columns:
        return "데이터 없음"
    sorted_frame = frame.sort_values(metric, ascending=False)
    if sorted_frame.empty:
        return "데이터 없음"
    return str(sorted_frame.iloc[0][label_column])


def media_style(platform: str) -> dict[str, str]:
    return MEDIA_BRAND_STYLES.get(platform, DEFAULT_MEDIA_STYLE)


def media_chip(platform: str) -> str:
    style = media_style(platform)
    background = hex_to_rgba(style["color"], 0.18)
    return (
        f'<span class="aima-media-chip" style="background: {background}; color: {style["text"]};">'
        f'<span class="aima-media-dot" style="background: {style["color"]};"></span>'
        f'{escape(platform)} <span style="opacity: 0.78;">{escape(style["short"])}</span>'
        "</span>"
    )


def safe_width(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0
    return max(min(float(value) / max_value * 100, 100), 2)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    color = hex_color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def format_media_table_for_display(platform_table: pd.DataFrame, view_mode: str = "기본 모드") -> pd.DataFrame:
    displayed = format_analysis_table_for_mode(platform_table, view_mode)
    if "매체" in displayed.columns:
        displayed["매체"] = displayed["매체"].map(lambda value: f"{value} ({media_style(str(value))['short']})")
    return displayed


def render_signal_distribution(anomalies: pd.DataFrame) -> None:
    counts = anomalies["severity"].value_counts().to_dict()
    total = max(sum(counts.values()), 1)
    rendered = []
    for severity in ["high", "medium", "opportunity"]:
        style = ALERT_STYLES[severity]
        count = int(counts.get(severity, 0))
        width = count / total * 100
        rendered.append(
            (
                '<div class="aima-summary-card">'
                f'<div class="aima-summary-label">{escape(style["label"])}</div>'
                f'<div class="aima-summary-value">{count:,}건</div>'
                '<div class="aima-bar-track">'
                f'<div class="aima-bar-fill" style="width: {width:.1f}%; background: {style["color"]};"></div>'
                "</div></div>"
            )
        )
    st.markdown(f'<div class="aima-card-grid">{"".join(rendered)}</div>', unsafe_allow_html=True)


def signal_title(row: pd.Series) -> str:
    signal_type = str(row.get("type", "운영 점검"))
    titles = {
        "광고비 소진 대비 전환 없음": "광고비는 사용됐지만 전환이 없습니다",
        "노출 대비 클릭률 저조": "노출은 충분하지만 클릭 반응이 약합니다",
        "확대 가능 구간": "성과가 좋아 확대를 검토할 수 있습니다",
    }
    return titles.get(signal_type, signal_type)


def format_operational_signal_table(anomalies: pd.DataFrame) -> pd.DataFrame:
    displayed = anomalies.copy()
    if "type" in displayed.columns:
        displayed["type"] = displayed.apply(signal_title, axis=1)
    return format_dataframe_for_display(displayed)


def format_operational_issues_for_display(issues: list[OperatingActionIssue]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "심각도": severity_label(issue.severity),
                "광고주": operator_display_text(issue.advertiser),
                "매체": operator_display_text(issue.media),
                "대상": operator_display_text(issue.target),
                "발견된 문제": operator_display_text(issue.problem),
                "근거 데이터": operator_display_text(issue.evidence),
                "원인 가능성": operator_display_text(issue.cause_hypothesis),
                "추천 액션": operator_display_text(issue.recommended_action),
                "예상 효과": operator_display_text(issue.expected_effect),
                "광고주 설명 문구": operator_display_text(issue.advertiser_message),
                "보고서 반영 여부": "반영 권장" if issue.report_include else "필요 시 반영",
            }
            for issue in issues
        ]
    )


def render_report_downloads(result) -> None:  # noqa: ANN001
    st.subheader("보고서 다운로드")
    markdown_col, text_col, excel_col = st.columns(3)
    markdown_col.download_button(
        "Markdown 보고서 다운로드",
        data=result.report_paths.markdown.read_text(encoding="utf-8"),
        file_name="aimaos_report.md",
        mime="text/markdown",
    )
    text_col.download_button(
        "TXT 보고서 다운로드",
        data=result.report_paths.text.read_text(encoding="utf-8"),
        file_name="aimaos_report.txt",
        mime="text/plain",
    )
    excel_col.download_button(
        "Excel 결과 파일 다운로드",
        data=result.report_paths.excel.read_bytes(),
        file_name="aimaos_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def standardized_from_result(result) -> pd.DataFrame | None:  # noqa: ANN001
    standardized = getattr(result, "standardized", None)
    if standardized is not None:
        return standardized
    input_path = getattr(result, "input_path", None)
    if input_path is None:
        return None
    try:
        raw = load_ad_file(input_path)
        standardized, _ = standardize_ad_data(raw)
        return standardized
    except Exception:  # noqa: BLE001
        return None


def render_custom_period_analysis(frame: pd.DataFrame, view_mode: str = "기본 모드") -> None:
    st.subheader("사용자 지정 기간 분석")
    bounds = date_bounds(frame)
    if bounds is None:
        st.info("날짜 컬럼이 없거나 날짜를 읽을 수 없어 기간 선택 분석을 표시할 수 없습니다.")
        return

    min_date, max_date = bounds
    st.caption(
        f"빠른 기간은 업로드된 데이터의 마지막 날짜인 {max_date:%Y-%m-%d} 기준으로 계산합니다. "
        "과거 광고 파일도 자연스럽게 비교할 수 있게 하기 위한 기준입니다."
    )

    preset = render_period_preset_buttons()
    if preset == "임의 설정":
        start_date, end_date = render_date_range_inputs(
            key_prefix="custom_period",
            min_date=min_date,
            max_date=max_date,
            default_start=min_date,
            default_end=max_date,
        )
    else:
        start_date, end_date = preset_period(max_date, preset)
        st.write(f"선택 기간: {start_date:%Y-%m-%d} ~ {end_date:%Y-%m-%d}")

    if start_date > end_date:
        st.warning("시작일은 종료일보다 늦을 수 없습니다.")
        return

    selected = filter_period(frame, start_date, end_date)
    if selected.empty:
        st.warning("선택한 기간에 포함되는 데이터가 없습니다. 다른 기간을 선택해 주세요.")
    else:
        render_period_summary(selected, view_mode)
        period_tabs = st.tabs(["캠페인별", "광고그룹별", "키워드별"])
        dimensions = [
            ("campaign_name", "선택 기간 캠페인별 성과"),
            ("ad_group_name", "선택 기간 광고그룹별 성과"),
            ("keyword", "선택 기간 키워드별 성과"),
        ]
        for tab, (dimension, title) in zip(period_tabs, dimensions, strict=False):
            with tab:
                st.markdown(f"**{title}**")
                table = aggregate_by_dimension(selected, dimension)
                if table.empty:
                    st.info("표시할 데이터가 없습니다.")
                else:
                    st.dataframe(format_analysis_table_for_mode(table, view_mode), use_container_width=True, hide_index=True)

    render_custom_period_comparison(frame, min_date, max_date)


def render_period_preset_buttons() -> str:
    st.write("빠른 기간 선택")
    if "selected_period_preset" not in st.session_state:
        st.session_state["selected_period_preset"] = PERIOD_PRESETS[0]

    columns = st.columns(5)
    for index, preset in enumerate(PERIOD_PRESETS):
        button_type = "primary" if st.session_state["selected_period_preset"] == preset else "secondary"
        if columns[index % 5].button(
            preset,
            key=f"period_preset_{index}",
            type=button_type,
            use_container_width=True,
        ):
            st.session_state["selected_period_preset"] = preset

    return st.session_state["selected_period_preset"]


def render_period_summary(frame: pd.DataFrame, view_mode: str = "기본 모드") -> None:
    summary = calculate_metrics(frame)
    metrics = CORE_METRICS + (["conversions", "ctr", "cpc", "cvr", "cpa"] if view_mode == "전문가 모드" else [])
    cards = [(metric_label_with_english(metric), format_by_metric(metric, summary.get(metric, 0)), kpi_note(metric)) for metric in metrics]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def render_custom_period_comparison(frame: pd.DataFrame, min_date: date, max_date: date) -> None:
    st.subheader("사용자 지정 기간 비교")
    first_start, first_end, second_start, second_end = default_comparison_ranges(min_date, max_date)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        first_start = st.date_input("비교 기간 A 시작일", value=first_start, min_value=min_date, max_value=max_date)
    with col2:
        first_end = st.date_input("비교 기간 A 종료일", value=first_end, min_value=min_date, max_value=max_date)
    with col3:
        second_start = st.date_input("비교 기간 B 시작일", value=second_start, min_value=min_date, max_value=max_date)
    with col4:
        second_end = st.date_input("비교 기간 B 종료일", value=second_end, min_value=min_date, max_value=max_date)

    if first_start > first_end or second_start > second_end:
        st.warning("각 비교 기간의 시작일은 종료일보다 늦을 수 없습니다.")
        return

    comparison = compare_periods(frame, first_start, first_end, second_start, second_end)
    st.dataframe(format_comparison_for_display(comparison), use_container_width=True, hide_index=True)

    with st.expander("자동 요약 코멘트"):
        for comment in build_comparison_comments(comparison):
            st.write(f"- {comment}")


def render_date_range_inputs(
    key_prefix: str,
    min_date: date,
    max_date: date,
    default_start: date,
    default_end: date,
) -> tuple[date, date]:
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=default_start,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_start",
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=default_end,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_end",
        )
    return start_date, end_date


def default_comparison_ranges(min_date: date, max_date: date) -> tuple[date, date, date, date]:
    total_days = max((max_date - min_date).days + 1, 1)
    half_days = max(total_days // 2, 1)
    first_start = min_date
    first_end = min(min_date + timedelta(days=half_days - 1), max_date)
    second_start = min(first_end + timedelta(days=1), max_date)
    second_end = max_date
    if second_start > second_end:
        second_start = first_start
    return first_start, first_end, second_start, second_end


def format_comparison_for_display(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in comparison.iterrows():
        metric = row["metric"]
        rows.append(
            {
                "지표": metric_label(metric),
                "비교 기간 A": format_by_metric(metric, row["first_period"]),
                "비교 기간 B": format_by_metric(metric, row["second_period"]),
                "변화량": format_by_metric(metric, row["delta"]),
                "증감률": format_percent(row["change_rate"]),
                "판단": row["status"],
            }
        )
    return pd.DataFrame(rows)


def render_channel_intelligence() -> None:
    st.title("채널 통합 관제")
    st.caption("광고 계정과 판매 채널 상태를 한 곳에서 확인합니다.")
    st.info("현재는 업로드 또는 등록된 데이터 기준으로 채널 운영 상태를 확인합니다.")

    initialize_channel_registry(CHANNEL_DB_PATH)
    channels = load_channels(CHANNEL_DB_PATH, include_inactive=False)
    if channels.empty:
        st.warning("활성화된 채널이 없습니다. 채널 관리자에서 채널을 추가하거나 활성화해 주세요.")
        return

    metrics = build_channel_sample_metrics(channels)
    st.subheader("전체 상태")
    render_channel_overview(channels, metrics)

    st.subheader("채널 운영 브리핑")
    render_channel_ai_review(metrics)

    render_channel_groups(channels)
    render_integrated_kpis(metrics)
    render_association_asset_status(channels)
    render_channel_benchmark(metrics)

    st.subheader("채널별 예시 성과")
    st.caption("아래 수치는 운영 흐름 확인용 예시입니다. 실제 의사결정은 광고주 원본 데이터 기준으로 진행합니다.")
    st.dataframe(format_channel_metrics_for_display(metrics), use_container_width=True, hide_index=True)


def render_channel_management() -> None:
    tab1, tab2 = st.tabs(["통합 관제", "채널 관리자"])
    with tab1:
        render_channel_intelligence()
    with tab2:
        render_channel_admin()


def render_channel_admin() -> None:
    st.title("채널 관리자")
    st.caption("광고 계정, 매체, 판매 채널의 관리 상태를 확인합니다.")
    st.info("새 채널을 추가하거나 기존 채널을 수정, 비활성화할 수 있습니다. 채널 연결은 운영 검증 후 단계적으로 적용합니다.")

    initialize_channel_registry(CHANNEL_DB_PATH)
    channels = load_channels(CHANNEL_DB_PATH, include_inactive=True)

    st.subheader("현재 등록 채널")
    st.dataframe(format_channel_registry_for_display(channels), use_container_width=True, hide_index=True)

    add_tab, edit_tab = st.tabs(["채널 추가", "채널 수정"])
    with add_tab:
        with st.form("channel_add_form"):
            channel_name = st.text_input("채널명")
            channel_group = st.selectbox("채널 영역", CHANNEL_GROUPS)
            purpose = st.text_input("목적", value="채널 성과 분석")
            metrics = st.text_area("분석 항목", value="매출,주문수,광고비,ROAS,전환율,객단가")
            brand_color = st.color_picker("대표 색상", value="#64748B")
            is_active = st.checkbox("활성화", value=True)
            display_order = st.number_input("표시 순서", min_value=1, max_value=999, value=100, step=1)
            submitted = st.form_submit_button("채널 추가")
            if submitted:
                if not channel_name.strip():
                    st.error("채널명을 입력해 주세요.")
                else:
                    try:
                        add_channel(
                            CHANNEL_DB_PATH,
                            channel_name.strip(),
                            channel_group,
                            purpose.strip() or "채널 성과 분석",
                            normalize_metrics(metrics),
                            brand_color,
                            is_active,
                            int(display_order),
                        )
                        st.success("채널을 추가했습니다.")
                        st.rerun()
                    except Exception as error:  # noqa: BLE001
                        st.error("채널 추가 중 문제가 발생했습니다. 같은 이름의 채널이 이미 있는지 확인해 주세요.")
                        with st.expander("오류 자세히 보기"):
                            st.exception(error)

    with edit_tab:
        if channels.empty:
            st.warning("수정할 채널이 없습니다.")
            return
        options = [f"{row.id} · {row.channel_name}" for row in channels.itertuples()]
        selected_label = st.selectbox("수정할 채널", options)
        selected_id = int(selected_label.split(" · ", 1)[0])
        selected = channels[channels["id"] == selected_id].iloc[0]
        with st.form("channel_edit_form"):
            channel_name = st.text_input("채널명", value=str(selected["channel_name"]))
            group_index = CHANNEL_GROUPS.index(selected["channel_group"]) if selected["channel_group"] in CHANNEL_GROUPS else 0
            channel_group = st.selectbox("채널 영역", CHANNEL_GROUPS, index=group_index)
            purpose = st.text_input("목적", value=str(selected["purpose"]))
            metrics = st.text_area("분석 항목", value=str(selected["metrics"]))
            brand_color = st.color_picker("대표 색상", value=str(selected["brand_color"]))
            is_active = st.checkbox("활성화", value=bool(selected["is_active"]))
            display_order = st.number_input(
                "표시 순서",
                min_value=1,
                max_value=999,
                value=int(selected["display_order"]),
                step=1,
            )
            submitted = st.form_submit_button("채널 수정 저장")
            if submitted:
                if not channel_name.strip():
                    st.error("채널명을 입력해 주세요.")
                else:
                    try:
                        update_channel(
                            CHANNEL_DB_PATH,
                            selected_id,
                            channel_name.strip(),
                            channel_group,
                            purpose.strip() or "채널 성과 분석",
                            normalize_metrics(metrics),
                            brand_color,
                            is_active,
                            int(display_order),
                        )
                        st.success("채널 정보를 수정했습니다.")
                        st.rerun()
                    except Exception as error:  # noqa: BLE001
                        st.error("채널 수정 중 문제가 발생했습니다.")
                        with st.expander("오류 자세히 보기"):
                            st.exception(error)


def render_channel_overview(channels: pd.DataFrame, metrics: pd.DataFrame) -> None:
    active_count = len(channels)
    group_count = channels["channel_group"].nunique()
    total_revenue = float(metrics["revenue"].sum())
    total_cost = float(metrics["ad_cost"].sum())
    total_roas = total_revenue / total_cost if total_cost else 0
    cards = [
        ("활성 채널", f"{active_count:,}개", f"{group_count:,}개 영역에서 관리 중"),
        ("총 매출", format_money(total_revenue), "광고매체와 판매채널을 합산한 예시 KPI"),
        ("총 광고비", format_money(total_cost), "채널별 광고비 또는 판매채널 광고비 합산"),
        ("통합 ROAS", format_ratio(total_roas), "전체 매출 ÷ 전체 광고비"),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def render_channel_groups(channels: pd.DataFrame) -> None:
    st.subheader("채널 영역")
    cards = []
    for group in CHANNEL_GROUPS:
        group_channels = channels[channels["channel_group"] == group]
        chips = " ".join(channel_chip(row.channel_name, row.brand_color) for row in group_channels.itertuples())
        cards.append(
            (
                '<div class="aima-summary-card">'
                f'<div class="aima-summary-label">{escape(group)}</div>'
                f'<div class="aima-summary-value">{len(group_channels):,}개</div>'
                f'<div class="aima-summary-note">{chips or "등록 채널 없음"}</div>'
                "</div>"
            )
        )
    st.markdown(f'<div class="aima-card-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_integrated_kpis(metrics: pd.DataFrame) -> None:
    st.subheader("통합 KPI")
    total_revenue = float(metrics["revenue"].sum())
    total_cost = float(metrics["ad_cost"].sum())
    total_orders = float(metrics["orders"].sum())
    total_conversions = float(metrics["conversions"].sum())
    total_new_customers = float(metrics["new_customers"].sum())
    total_roas = total_revenue / total_cost if total_cost else 0
    total_aov = total_revenue / total_orders if total_orders else 0
    total_cac = total_cost / total_new_customers if total_new_customers else 0
    total_ltv = total_aov * 2.6
    repeat_purchase_rate = float(metrics["repeat_purchase_rate"].mean())
    core_cards = [
        ("총 매출", format_money(total_revenue), "전체 채널 합산"),
        ("총 광고비", format_money(total_cost), "전체 채널 합산"),
        ("총 주문수", format_count(total_orders), "판매채널과 광고 전환 주문 합산"),
        ("총 ROAS", format_ratio(total_roas), "전체 매출 ÷ 전체 광고비"),
    ]
    detail_cards = [
        ("총 전환수", format_count(total_conversions), "광고 및 판매 전환 합산"),
        ("총 신규고객", format_count(total_new_customers), "예시 신규 고객 수"),
        ("총 재구매율", format_percent(repeat_purchase_rate), "채널 평균 재구매율"),
        ("총 객단가", format_money(total_aov), "총 매출 ÷ 총 주문수"),
        ("총 CAC", format_money(total_cac), "총 광고비 ÷ 신규고객"),
        ("총 LTV", format_money(total_ltv), "객단가 기반 예시 추정값"),
    ]
    st.markdown(render_summary_cards(core_cards), unsafe_allow_html=True)
    with st.expander("관리자용 상세 KPI 보기"):
        st.markdown(render_summary_cards(detail_cards), unsafe_allow_html=True)

    group_chart = (
        metrics.groupby("channel_group", as_index=False)
        .agg(revenue=("revenue", "sum"), ad_cost=("ad_cost", "sum"))
        .rename(columns={"channel_group": "채널 영역", "revenue": "매출", "ad_cost": "광고비"})
        .set_index("채널 영역")
    )
    st.bar_chart(group_chart)


def render_channel_benchmark(metrics: pd.DataFrame) -> None:
    st.subheader("채널 벤치마크")
    benchmark = build_channel_benchmark(metrics)
    render_channel_benchmark_value_cards(benchmark)
    with st.expander("채널 벤치마크 상세표 보기"):
        st.dataframe(format_channel_benchmark_for_display(benchmark), use_container_width=True, hide_index=True)


def render_channel_benchmark_value_cards(benchmark: pd.DataFrame) -> None:
    if benchmark.empty:
        st.info("표시할 벤치마크 데이터가 없습니다.")
        return
    best = benchmark.sort_values("gap", ascending=False).iloc[0]
    weak = benchmark.sort_values("gap", ascending=True).iloc[0]
    cards = [
        (
            "가장 우수한 채널",
            str(best["channel_name"]),
            f"현재 ROAS {format_ratio(best['current_roas'])} · 기준 {format_ratio(best['benchmark_roas'])}",
        ),
        (
            "가장 먼저 볼 채널",
            str(weak["channel_name"]),
            f"현재 ROAS {format_ratio(weak['current_roas'])} · 기준 {format_ratio(weak['benchmark_roas'])}",
        ),
        (
            "판단",
            "평균 대비 위치",
            "좋은 채널은 확대 후보로, 낮은 채널은 예산과 상품 경쟁력 점검 대상으로 분류합니다.",
        ),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def render_channel_ai_review(metrics: pd.DataFrame) -> None:
    active = metrics[metrics["ad_cost"] > 0].copy()
    if active.empty:
        st.info("점검할 채널 성과 데이터가 없습니다.")
        return
    best = active.sort_values("roas", ascending=False).iloc[0]
    weak = active.sort_values("roas", ascending=True).iloc[0]
    avg_roas = float(active["roas"].mean())
    cards = [
        (
            "위험",
            format_ratio(weak["roas"]),
            f"{weak['channel_name']} 채널은 평균 {format_ratio(avg_roas)}보다 낮아 예산과 상품 경쟁력을 점검합니다.",
        ),
        (
            "확대기회",
            format_ratio(best["roas"]),
            f"{best['channel_name']} 채널은 가장 우수한 성과를 보여 확대 검토 후보입니다.",
        ),
        (
            "행동 제안",
            "예산 재배분",
            f"낮은 ROAS 채널 비중을 줄이고 {best['channel_name']} 중심으로 검증 예산을 옮깁니다.",
        ),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def build_channel_sample_metrics(channels: pd.DataFrame) -> pd.DataFrame:
    group_profile = {
        "광고매체": {"revenue": 8_500_000, "roas": 4.2, "orders": 120, "new_customer_rate": 0.42},
        "오픈마켓": {"revenue": 13_000_000, "roas": 3.6, "orders": 260, "new_customer_rate": 0.32},
        "커머스 플랫폼": {"revenue": 9_800_000, "roas": 3.9, "orders": 190, "new_customer_rate": 0.38},
        "글로벌 채널": {"revenue": 6_200_000, "roas": 2.8, "orders": 105, "new_customer_rate": 0.48},
    }
    rows = []
    for index, row in enumerate(channels.itertuples(), start=1):
        profile = group_profile.get(row.channel_group, group_profile["커머스 플랫폼"])
        factor = 0.82 + (index % 7) * 0.07
        revenue = profile["revenue"] * factor
        roas = max(profile["roas"] + ((index % 5) - 2) * 0.28, 0.3)
        ad_cost = revenue / roas
        orders = max(int(profile["orders"] * factor), 1)
        conversions = max(int(orders * (0.82 + (index % 4) * 0.04)), 1)
        new_customers = max(int(orders * profile["new_customer_rate"]), 1)
        repeat_purchase_rate = min(0.12 + (index % 6) * 0.035, 0.62)
        aov = revenue / orders if orders else 0
        cpc = 620 + (index % 9) * 170
        ctr = 0.009 + (index % 6) * 0.004
        conversion_rate = conversions / max(orders * 3, 1)
        rows.append(
            {
                "channel_name": row.channel_name,
                "channel_group": row.channel_group,
                "brand_color": row.brand_color,
                "revenue": revenue,
                "orders": orders,
                "conversions": conversions,
                "new_customers": new_customers,
                "repeat_purchase_rate": repeat_purchase_rate,
                "ad_cost": ad_cost,
                "roas": roas,
                "aov": aov,
                "cac": ad_cost / new_customers if new_customers else 0,
                "ltv": aov * 2.6,
                "ctr": ctr,
                "cpc": cpc,
                "conversion_rate": conversion_rate,
            }
        )
    return pd.DataFrame(rows)


def build_channel_benchmark(metrics: pd.DataFrame) -> pd.DataFrame:
    benchmark_roas = {
        "광고매체": 4.2,
        "오픈마켓": 3.6,
        "커머스 플랫폼": 3.9,
        "글로벌 채널": 2.8,
    }
    rows = []
    for _, row in metrics.iterrows():
        average = benchmark_roas.get(row["channel_group"], 3.5)
        rows.append(
            {
                "channel_name": row["channel_name"],
                "channel_group": row["channel_group"],
                "current_roas": row["roas"],
                "benchmark_roas": average,
                "gap": row["roas"] - average,
                "status": "업종 평균 대비 우수" if row["roas"] >= average else "업종 평균 대비 점검",
            }
        )
    return pd.DataFrame(rows).sort_values("gap", ascending=False)


def format_channel_metrics_for_display(metrics: pd.DataFrame) -> pd.DataFrame:
    displayed = metrics.copy()
    displayed["revenue"] = displayed["revenue"].map(format_money)
    displayed["ad_cost"] = displayed["ad_cost"].map(format_money)
    displayed["orders"] = displayed["orders"].map(format_count)
    displayed["conversions"] = displayed["conversions"].map(format_count)
    displayed["new_customers"] = displayed["new_customers"].map(format_count)
    displayed["repeat_purchase_rate"] = displayed["repeat_purchase_rate"].map(format_percent)
    displayed["roas"] = displayed["roas"].map(format_ratio)
    displayed["aov"] = displayed["aov"].map(format_money)
    displayed["cac"] = displayed["cac"].map(format_money)
    displayed["ltv"] = displayed["ltv"].map(format_money)
    displayed["ctr"] = displayed["ctr"].map(format_percent)
    displayed["cpc"] = displayed["cpc"].map(format_money)
    displayed["conversion_rate"] = displayed["conversion_rate"].map(format_percent)
    return displayed.rename(
        columns={
            "channel_name": "채널명",
            "channel_group": "채널 영역",
            "brand_color": "대표 색상",
            "revenue": "매출",
            "orders": "주문수",
            "conversions": "전환수",
            "new_customers": "신규고객",
            "repeat_purchase_rate": "재구매율",
            "ad_cost": "광고비",
            "roas": "ROAS",
            "aov": "객단가",
            "cac": "CAC",
            "ltv": "LTV",
            "ctr": "CTR",
            "cpc": "CPC",
            "conversion_rate": "전환율",
        }
    )


def format_channel_benchmark_for_display(benchmark: pd.DataFrame) -> pd.DataFrame:
    displayed = benchmark.copy()
    displayed["current_roas"] = displayed["current_roas"].map(format_ratio)
    displayed["benchmark_roas"] = displayed["benchmark_roas"].map(format_ratio)
    displayed["gap"] = displayed["gap"].map(format_ratio)
    return displayed.rename(
        columns={
            "channel_name": "채널명",
            "channel_group": "채널 영역",
            "current_roas": "현재 ROAS",
            "benchmark_roas": "벤치마크 ROAS",
            "gap": "차이",
            "status": "판단",
        }
    )


def format_channel_registry_for_display(channels: pd.DataFrame) -> pd.DataFrame:
    displayed = channels.copy()
    if displayed.empty:
        return displayed
    displayed["is_active"] = displayed["is_active"].map(lambda value: "활성" if bool(value) else "비활성")
    return displayed[
        [
            "id",
            "channel_name",
            "channel_group",
            "purpose",
            "metrics",
            "brand_color",
            "is_active",
            "display_order",
        ]
    ].rename(
        columns={
            "id": "ID",
            "channel_name": "채널명",
            "channel_group": "채널 영역",
            "purpose": "목적",
            "metrics": "분석 항목",
            "brand_color": "대표 색상",
            "is_active": "상태",
            "display_order": "표시 순서",
        }
    )


def normalize_metrics(metrics: str) -> str:
    return ",".join(part.strip() for part in metrics.replace("\n", ",").split(",") if part.strip())


def render_association_asset_status(channels: pd.DataFrame | None = None) -> None:
    raw_files = list((BASE_DIR / "data" / "raw").glob("*.csv")) + list((BASE_DIR / "data" / "raw").glob("*.xlsx"))
    report_files = list((BASE_DIR / "data" / "reports").rglob("analysis*.xlsx"))
    channel_count = len(channels) if channels is not None else len(load_channels(CHANNEL_DB_PATH, include_inactive=False))
    cards = [
        ("누적 업종 수", "0개", "실제 업종 벤치마크 연결 전입니다."),
        ("누적 광고 데이터 수", f"{len(raw_files):,}개", "현재 raw 폴더 기준 파일 수입니다."),
        ("벤치마크 수", "0개", "업종별 기준값은 다음 단계에서 축적합니다."),
        ("운영 사례 수", f"{len(report_files):,}개", "생성된 Excel 분석 결과를 사례 후보로 봅니다."),
        ("관리 채널 수", f"{channel_count:,}개", "DB에 활성화된 채널 기준입니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def channel_chip(channel_name: str, color: str) -> str:
    return (
        f'<span class="aima-media-chip" style="background: {hex_to_rgba(color, 0.16)}; color: #E5E7EB;">'
        f'<span class="aima-media-dot" style="background: {color};"></span>{escape(channel_name)}</span>'
    )


def render_placeholder_page(
    title: str,
    subtitle: str,
    purpose: str,
    target_platforms: list[str],
    future_data_fields: list[str],
    roadmap_focus: list[str],
    sample_file: str,
    sample_metric_labels: list[str],
) -> None:
    st.title(title)
    st.caption(subtitle)
    st.info("현재는 업로드 또는 등록된 데이터 기준으로 운영 판단 흐름을 확인합니다.")
    st.write(purpose)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("대상")
        for platform in target_platforms:
            st.write(f"- {platform}")
    with col2:
        st.subheader("앞으로 관리할 데이터")
        for field in future_data_fields:
            st.write(f"- {field}")

    st.subheader("앞으로의 운영 방향")
    for item in roadmap_focus:
        st.write(f"- {item}")

    st.subheader("운영 예시 데이터")
    st.warning("아래 표는 기능 체험용 예시입니다. 실제 의사결정은 광고주 원본 데이터 업로드 후 진행합니다.")
    sample_path = PHASE2_SAMPLE_DIR / sample_file
    if sample_path.exists():
        sample = pd.read_csv(sample_path)
        metric_columns = st.columns(len(sample_metric_labels))
        for metric_column, metric_label in zip(metric_columns, sample_metric_labels, strict=False):
            metric_column.metric(metric_label, _sample_metric_value(sample, metric_label))
        st.caption("예시 데이터는 상위 50행만 미리보기로 표시합니다.")
        st.dataframe(sample.head(50), use_container_width=True, hide_index=True)
    else:
        st.warning("예시 데이터 파일을 찾을 수 없습니다.")

    st.subheader("현재 운영 범위")
    st.write("- 광고주가 제공한 데이터 기준으로 판단")
    st.write("- 계정 접속 없이 안전하게 운영 상태 확인")
    st.write("- 기존 광고 성과 계산 방식 유지")


def render_commerce_intelligence() -> None:
    render_placeholder_page(
        title="쇼핑몰/매체 분석",
        subtitle="쇼핑몰과 오픈마켓 성과를 함께 보는 운영 준비 화면",
        purpose="스마트스토어와 주요 오픈마켓의 상품, 가격, 리뷰, 경쟁상품 흐름을 광고 성과와 함께 비교하기 위한 확장 영역입니다.",
        target_platforms=["스마트스토어", "쿠팡", "G마켓", "옥션", "11번가"],
        future_data_fields=["상품명", "가격", "리뷰", "평점", "판매량", "경쟁상품"],
        roadmap_focus=[
            "상품 단위 경쟁 데이터를 한 곳에서 확인",
            "가격 변동과 리뷰 변화를 추적",
            "광고 성과와 상품 경쟁력을 함께 비교",
        ],
        sample_file="commerce_sample.csv",
        sample_metric_labels=["예시 상품 수", "대상 플랫폼 수", "평균 평점"],
    )


def render_report_center() -> None:
    st.title("보고서 센터")
    st.caption("분석 결과를 대상별 보고서로 정리하는 운영 화면입니다.")
    if not render_data_access_notice("보고서 센터"):
        return
    report_root = BASE_DIR / "data" / "reports"
    records = collect_report_records(report_root)
    if not records:
        st.info("아직 생성된 보고서가 없습니다. 광고 성과 분석 메뉴에서 체험 데이터 분석 또는 파일 업로드 분석을 먼저 실행해 주세요.")
        return

    st.subheader("보고서 유형 선택")
    report_type = st.segmented_control(
        "대상",
        options=list(REPORT_PROFILES.keys()),
        default="광고주 보고서",
        key="report_center_profile",
    )
    render_report_profile(report_type)

    st.subheader("최근 보고서")
    report_table = pd.DataFrame(records)
    st.dataframe(report_table[["보고서명", "생성일", "Excel", "Markdown", "TXT"]], use_container_width=True, hide_index=True)

    selected_name = st.selectbox("다운로드할 보고서 선택", report_table["보고서명"].tolist())
    selected = next(record for record in records if record["보고서명"] == selected_name)
    customized_report = build_customized_report_text(selected, report_type)
    st.subheader("맞춤 요약 미리보기")
    st.text_area("보고서 문체 미리보기", customized_report[:1800], height=260)

    col1, col2, col3, col4 = st.columns(4)
    col1.download_button(
        "맞춤 요약 TXT 받기",
        data=customized_report,
        file_name=f"campaignpulse_{report_type.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    if selected["excel_path"] is not None:
        col2.download_button(
            "Excel 받기",
            data=selected["excel_path"].read_bytes(),
            file_name=selected["excel_path"].name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    if selected["markdown_path"] is not None:
        col3.download_button(
            "Markdown 받기",
            data=selected["markdown_path"].read_text(encoding="utf-8"),
            file_name=selected["markdown_path"].name,
            mime="text/markdown",
            use_container_width=True,
        )
    if selected["text_path"] is not None:
        col4.download_button(
            "TXT 받기",
            data=selected["text_path"].read_text(encoding="utf-8"),
            file_name=selected["text_path"].name,
            mime="text/plain",
            use_container_width=True,
        )


def render_report_profile(report_type: str) -> None:
    profile = REPORT_PROFILES[report_type]
    cards = [
        ("대상", profile["audience"], "누가 읽는지에 따라 강조점을 바꿉니다."),
        ("문체", profile["tone"], "보고서 표현 방식을 조정합니다."),
        ("표시 항목", profile["fields"], "불필요한 지표 노출을 줄입니다."),
        ("사용처", profile["use"], "보고서가 쓰일 상황을 명확히 합니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def build_customized_report_text(selected: dict[str, object], report_type: str) -> str:
    profile = REPORT_PROFILES[report_type]
    base_text = ""
    markdown_path = selected.get("markdown_path")
    text_path = selected.get("text_path")
    if isinstance(markdown_path, Path) and markdown_path.exists():
        base_text = markdown_path.read_text(encoding="utf-8")
    elif isinstance(text_path, Path) and text_path.exists():
        base_text = text_path.read_text(encoding="utf-8")
    if not base_text:
        base_text = "원본 보고서 본문을 찾을 수 없습니다. Excel 결과 파일을 확인해 주세요."
    header = [
        f"# 캠페인펄스 {report_type}",
        "",
        f"- 대상: {profile['audience']}",
        f"- 문체: {profile['tone']}",
        f"- 우선 표시 항목: {profile['fields']}",
        f"- 사용처: {profile['use']}",
        "",
        "## 읽는 순서",
        "1. 전체 성과를 먼저 확인합니다.",
        "2. 우선 처리 이슈를 확인합니다.",
        "3. 긴급, 주의, 확대기회 항목을 나누어 실행합니다.",
        "4. 필요하면 원본 Excel에서 상세 지표를 확인합니다.",
        "",
        "## 원본 보고서 요약",
    ]
    action_section = build_report_action_section()
    return "\n".join(header) + "\n\n" + action_section + "\n\n" + base_text[:6000]


def build_report_action_section() -> str:
    snapshot = load_sample_analysis_snapshot()
    if snapshot is None:
        return "## 우선 처리 이슈 반영 후보\n\n- 체험 데이터를 찾을 수 없어 운영 이슈를 자동 첨부하지 못했습니다."
    _, analysis = snapshot
    issues = build_operating_action_issues(analysis, advertiser="광고주 A")[:3]
    lines = ["## 우선 처리 이슈 반영 후보"]
    for index, issue in enumerate(issues, start=1):
        lines.extend(
            [
                "",
                f"{index}. [{severity_label(issue.severity)}] {operator_display_text(issue.problem)}",
                f"- 광고주: {operator_display_text(issue.advertiser)}",
                f"- 매체: {operator_display_text(issue.media)}",
                f"- 대상: {operator_display_text(issue.target)}",
                f"- 근거 데이터: {operator_display_text(issue.evidence)}",
                f"- 추천 액션: {operator_display_text(issue.recommended_action)}",
                f"- 예상 효과: {operator_display_text(issue.expected_effect)}",
                f"- 광고주 설명 문구: {operator_display_text(issue.advertiser_message)}",
                f"- 보고서 반영 여부: {'반영 권장' if issue.report_include else '필요 시 반영'}",
            ]
        )
    return "\n".join(lines)


def collect_report_records(report_root: Path) -> list[dict[str, object]]:
    if not report_root.exists():
        return []
    rows = []
    for folder in sorted((path for path in report_root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True):
        excel_files = sorted(folder.glob("analysis*.xlsx"), key=lambda path: path.stat().st_mtime, reverse=True)
        markdown = folder / "report.md"
        text = folder / "report.txt"
        rows.append(
            {
                "보고서명": folder.name,
                "생성일": date.fromtimestamp(folder.stat().st_mtime).strftime("%Y-%m-%d"),
                "Excel": "있음" if excel_files else "없음",
                "Markdown": "있음" if markdown.exists() else "없음",
                "TXT": "있음" if text.exists() else "없음",
                "excel_path": excel_files[0] if excel_files else None,
                "markdown_path": markdown if markdown.exists() else None,
                "text_path": text if text.exists() else None,
            }
        )
    return rows[:20]


def render_settings_page() -> None:
    st.title("설정")
    st.caption("캠페인펄스의 핵심 분석 기능과 운영 준비 상태를 확인합니다.")
    initialize_channel_registry(CHANNEL_DB_PATH)
    protected = [
        "CSV 업로드",
        "Excel 업로드",
        "컬럼 자동 매핑",
        "표준화",
        "광고 성과 분석",
        "운영 점검 포인트",
        "기간 분석",
        "비교 분석",
        "보고서 생성",
    ]
    st.subheader("보호 중인 핵심 기능")
    st.markdown("\n".join(f"- {item}" for item in protected))

    st.subheader("시스템 상태")
    demo_status = "사용 중" if using_demo_data() else ("사용 가능" if DEMO_DATA_PATH.exists() else "없음")
    cards = [
        ("체험 데이터", "있음" if AD_SAMPLE_PATH.exists() else "없음", "업로드 전 흐름 확인용 데이터"),
        ("데모 데이터", demo_status, "온라인 시연에서 실제 광고주 데이터 없이 화면 흐름을 확인합니다."),
        ("채널 관리 데이터", "연결됨" if CHANNEL_DB_PATH.exists() else "생성 전", "채널 목록과 상태 관리"),
        ("계정 연결 상태", "파일 업로드 기준", "현재는 광고주가 제공한 파일 기준으로 운영 상태를 확인합니다."),
        ("현재 원칙", "핵심 기능 보호", "분석 결과는 유지하고 화면 사용성을 개선합니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)

    st.subheader("데이터 수집 구조")
    render_collection_channel_status()

    st.subheader("대용량 데이터 처리 원칙")
    large_data_cards = [
        ("1단계", "원본 파일 보관", "Excel/CSV 원본은 추적 가능한 상태로 보관합니다."),
        ("2단계", "공통 형식 변환", "매체별 컬럼을 캠페인펄스 공통 기준으로 정리합니다."),
        ("3단계", "운영 요약 생성", "일별, 매체별, 광고주별, 상품별 요약을 만듭니다."),
        ("4단계", "빠른 화면 확인", "대시보드는 원본 전체가 아니라 요약 결과를 우선 보여줍니다."),
        ("5단계", "필요 시 상세 확인", "문제가 있는 항목만 상세 데이터로 내려가 확인합니다."),
    ]
    st.markdown(render_summary_cards(large_data_cards), unsafe_allow_html=True)

    st.subheader("운영 개선 원칙")
    control_cards = [
        ("1단계", "기획", "수익화, 운영시간 절감, 자산화 기준을 먼저 검토합니다."),
        ("2단계", "작게 적용", "핵심 분석 결과를 건드리지 않는 범위에서 작게 반영합니다."),
        ("3단계", "검증", "체험 데이터와 실제 파일로 기존 결과가 유지되는지 확인합니다."),
        ("4단계", "실사용", "광고주 또는 운영자가 반복 사용할 수 있는지 봅니다."),
        ("5단계", "검증 후 다음 기능", "검증 전에는 새로운 기능을 동시에 늘리지 않습니다."),
    ]
    st.markdown(render_summary_cards(control_cards), unsafe_allow_html=True)

    st.subheader("수익화 검증")
    validation_cards = [
        ("3개월 내 수익화", "YES 필요", "보고서, 진단, 운영시간 절감과 직접 연결되는지 확인합니다."),
        ("운영시간 절감", "YES 필요", "반복 정리, 보고, 점검 시간을 줄여야 합니다."),
        ("협회 데이터 자산", "YES 필요", "업종, 채널, 사례 데이터로 남아야 합니다."),
        ("차별성", "검토", "경쟁사가 쉽게 따라 하기 어려운 운영 노하우가 들어가야 합니다."),
        ("반복 사용", "검토", "매주 또는 매월 다시 쓰는 기능이어야 우선합니다."),
    ]
    st.markdown(render_summary_cards(validation_cards), unsafe_allow_html=True)
    st.info("새로운 개선은 위 항목 중 3개 이상 YES일 때만 진행합니다. 아니면 보류합니다.")


def render_search_intelligence() -> None:
    render_placeholder_page(
        title="검색 인텔리전스",
        subtitle="Search Intelligence 운영 준비 화면",
        purpose="검색 키워드, 경쟁도, 검색 결과 노출 현황을 장기적으로 추적해 광고 운영 의사결정에 연결하기 위한 확장 모듈입니다.",
        target_platforms=["네이버", "구글", "카카오다음", "네이트"],
        future_data_fields=["키워드", "검색량", "경쟁도", "검색 결과", "경쟁사 노출"],
        roadmap_focus=[
            "키워드별 검색 수요와 광고 성과를 연결",
            "검색 결과 내 경쟁사 노출을 기록",
            "업종별 키워드 기준값을 축적",
        ],
        sample_file="search_sample.csv",
        sample_metric_labels=["예시 키워드 수", "대상 검색엔진 수", "경쟁사 노출 키워드"],
    )


def render_ai_visibility() -> None:
    render_placeholder_page(
        title="AI 검색 노출",
        subtitle="AI Visibility Intelligence 운영 준비 화면",
        purpose="생성형 AI 답변에서 브랜드와 경쟁사가 어떻게 언급되는지 추적하고, 향후 AI 검색 최적화 전략으로 연결하기 위한 확장 모듈입니다.",
        target_platforms=["ChatGPT", "Claude", "Gemini", "Perplexity"],
        future_data_fields=["브랜드 언급", "경쟁사 언급", "답변 출처", "추천 여부"],
        roadmap_focus=[
            "질문별 답변 결과를 기록",
            "브랜드 추천 여부와 답변 출처를 추적",
            "AI 답변 내 경쟁사 대비 노출 수준을 비교",
        ],
        sample_file="ai_visibility_sample.csv",
        sample_metric_labels=["예시 질문 수", "대상 AI 플랫폼 수", "브랜드 언급 수"],
    )


def render_experiment_lab() -> None:
    st.title("실험 기능")
    st.caption("검증 전 아이디어를 보관하는 영역입니다.")
    st.warning("이 화면은 실제 운영 기능이 아닙니다. 핵심 광고 성과 기능과 분리해서 관리합니다.")
    cards = [
        ("검토 기준", "3개 이상 YES", "수익화, 시간 절감, 자산화, 차별성, 반복 사용을 기준으로 판단합니다."),
        ("현재 상태", "보류함", "검증 전 기능은 최상위 메뉴에 올리지 않습니다."),
        ("금지", "동시 개발 금지", "한 기능을 실사용 검증한 뒤 다음 기능으로 이동합니다."),
    ]
    st.markdown(render_summary_cards(cards), unsafe_allow_html=True)


def _sample_metric_value(sample: pd.DataFrame, metric_label: str) -> str:
    if metric_label == "예시 상품 수":
        return f"{len(sample):,}"
    if metric_label == "예시 키워드 수":
        return f"{len(sample):,}"
    if metric_label == "예시 질문 수":
        return f"{len(sample):,}"
    if metric_label == "대상 플랫폼 수" and "플랫폼" in sample.columns:
        return f"{sample['플랫폼'].nunique():,}"
    if metric_label == "대상 검색엔진 수" and "검색엔진" in sample.columns:
        return f"{sample['검색엔진'].nunique():,}"
    if metric_label == "대상 AI 플랫폼 수" and "AI플랫폼" in sample.columns:
        return f"{sample['AI플랫폼'].nunique():,}"
    if metric_label == "평균 평점" and "평점" in sample.columns:
        return f"{sample['평점'].mean():.2f}점"
    if metric_label == "경쟁사 노출 키워드" and "경쟁사노출" in sample.columns:
        return f"{(sample['경쟁사노출'] == '있음').sum():,}"
    if metric_label == "브랜드 언급 수" and "브랜드언급" in sample.columns:
        return f"{(sample['브랜드언급'] == '있음').sum():,}"
    return "-"


def sidebar_command_center_stats() -> dict[str, int]:
    snapshot = load_sample_analysis_snapshot()
    advertiser_count = 0
    action_issues: list[OperatingActionIssue] = []
    if snapshot is not None:
        standardized, analysis = snapshot
        if "account_name" in standardized.columns:
            valid_accounts = standardized["account_name"].astype(str).str.strip()
            valid_accounts = valid_accounts[(valid_accounts != "") & (valid_accounts != "미분류")]
            advertiser_count = int(valid_accounts.nunique())
        action_issues = build_operating_action_issues(analysis, advertiser="광고주 A")

    report_records = collect_report_records(BASE_DIR / "data" / "reports")
    raw_files = [
        path
        for path in (BASE_DIR / "data" / "raw").rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls"}
    ]
    demo_file_count = 1 if using_demo_data() else 0
    channel_count = 0
    try:
        initialize_channel_registry(CHANNEL_DB_PATH)
        channel_count = len(load_channels(CHANNEL_DB_PATH, include_inactive=False))
    except Exception:  # noqa: BLE001
        channel_count = 0

    return {
        "advertisers": advertiser_count,
        "today_issues": len(action_issues),
        "critical_issues": sum(1 for issue in action_issues if issue.severity == "high"),
        "warning_issues": sum(1 for issue in action_issues if issue.severity == "medium"),
        "report_due": sum(1 for issue in action_issues if issue.report_include),
        "raw_files": len(raw_files) + demo_file_count,
        "reports": len(report_records),
        "channels": channel_count,
    }


def render_command_center_sidebar() -> str:
    ensure_demo_data_default()
    stats = sidebar_command_center_stats()
    logo = render_brand_logo_img("campaignpulse-logo-dark.svg", "campaignpulse-sidebar-logo-img")
    active_menu = current_active_menu()
    st.sidebar.markdown(
        f"""
        <div class="aima-sidebar-brand">
            {logo}
            <div class="aima-sidebar-subtitle">광고 캠페인의 성과 신호를 읽습니다</div>
            <div class="aima-sidebar-tag">광고 운영 대시보드</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_demo_data_sidebar_control()

    badges = {
        "종합 대시보드": sum(1 for channel in collect_data_status_snapshot()["channels"] if channel["status"] != "최신"),
        "우선 처리 이슈": stats["today_issues"],
        "운영 현황": stats["today_issues"],
        "광고 성과 분석": stats["raw_files"],
        "쇼핑몰/매체 분석": 0,
        "보고서 센터": stats["report_due"],
        "채널 관리": stats["channels"],
        "설정": 0,
    }
    st.sidebar.markdown('<div class="aima-sidebar-section-title">운영 메뉴</div>', unsafe_allow_html=True)
    for item in MAIN_MENU_ITEMS:
        render_sidebar_menu_button(item, badges[item], active_menu)

    render_sidebar_footer_status(stats)
    st.sidebar.caption("분석값은 유지하고, 운영자가 바로 판단할 수 있게 정리합니다.")
    return current_active_menu()


def render_demo_data_sidebar_control() -> None:
    if not DEMO_DATA_PATH.exists():
        return

    st.sidebar.markdown('<div class="aima-sidebar-section-title">데모 데이터</div>', unsafe_allow_html=True)
    has_uploaded_snapshot = st.session_state.get(UPLOADED_SNAPSHOT_KEY) is not None
    st.sidebar.checkbox(
        "데모 데이터 보기",
        key=DEMO_DATA_MODE_KEY,
        help="실제 광고주 데이터가 없는 온라인 데모 환경에서 가짜 샘플 데이터를 표시합니다.",
        disabled=has_uploaded_snapshot,
    )
    if has_uploaded_snapshot:
        st.sidebar.caption("현재 세션은 업로드 데이터가 우선 적용됩니다.")
    elif using_demo_data():
        st.sidebar.caption("기능 시연용 가짜 데이터가 표시됩니다.")


def render_sidebar_menu_button(item: str, badge_value: int, active_menu: str) -> None:
    left, right = st.sidebar.columns([0.82, 0.18], gap="small")
    button_type = "primary" if item == active_menu else "secondary"
    with left:
        if st.button(
            f"{MENU_ICONS[item]}  {item}",
            key=f"sidebar_menu_{MENU_ICONS[item]}",
            type=button_type,
            use_container_width=True,
        ):
            if st.session_state.get("active_page") != item:
                st.session_state["active_page"] = item
                st.rerun()
    with right:
        st.markdown(f'<div class="cp-sidebar-menu-badge">{badge_value:,}</div>', unsafe_allow_html=True)


def render_sidebar_footer_status(stats: dict[str, int]) -> None:
    briefing = (
        '<div class="aima-sidebar-section-title">오늘 브리핑</div>'
        '<div class="aima-brief-card"><div class="aima-brief-grid">'
        f'{sidebar_brief_item("광고주 수", stats["advertisers"])}'
        f'{sidebar_brief_item("긴급 이슈", stats["critical_issues"])}'
        f'{sidebar_brief_item("주의 이슈", stats["warning_issues"])}'
        f'{sidebar_brief_item("보고서 예정", stats["report_due"])}'
        "</div></div>"
    )
    data_status = (
        '<div class="aima-sidebar-section-title">데이터 상태</div>'
        f'<div class="aima-data-card">{render_sidebar_data_status_rows()}</div>'
    )
    st.sidebar.markdown(
        f'<div class="aima-sidebar-footer">{briefing}{data_status}</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="aima-sidebar-section-title">빠른 이동</div>', unsafe_allow_html=True)
    render_sidebar_quick_button("운영 현황 보기", "운영 현황", "sidebar_quick_status")
    render_sidebar_quick_button("이슈 확인", "우선 처리 이슈", "sidebar_quick_issues")
    render_sidebar_quick_button("보고서 센터", "보고서 센터", "sidebar_quick_reports")


def render_sidebar_quick_button(label: str, target: str, key: str) -> None:
    if st.sidebar.button(label, key=key, use_container_width=True):
        navigate_to(target)


def sidebar_brief_item(label: str, value: int) -> str:
    return (
        '<div class="aima-brief-item">'
        f'<div class="aima-brief-label">{escape(label)}</div>'
        f'<div class="aima-brief-value">{value:,}</div>'
        "</div>"
    )


def render_sidebar_data_status_rows() -> str:
    rows = [
        (
            channel["media"],
            channel["status"],
            status_style(str(channel["status"]))["color"],
            status_style(str(channel["status"]))["background"],
        )
        for channel in collect_data_status_snapshot()["channels"]
    ]
    rendered_rows = []
    for name, status, color, background in rows:
        rendered_rows.append(
            '<div class="aima-data-row">'
            f'<div class="aima-data-name">{escape(name)}</div>'
            f'<div class="aima-data-status" style="color: {color}; background: {background}; border: 1px solid {hex_to_rgba(color, 0.28)};">{escape(status)}</div>'
            "</div>"
        )
    return "".join(rendered_rows)


selected_menu = render_command_center_sidebar()

if selected_menu == "종합 대시보드":
    render_integrated_dashboard()
elif selected_menu == "우선 처리 이슈":
    render_home_dashboard()
elif selected_menu == "운영 현황":
    render_operating_status_dashboard()
elif selected_menu == "광고 성과 분석":
    render_ad_data_analyzer()
elif selected_menu == "쇼핑몰/매체 분석":
    render_commerce_intelligence()
elif selected_menu == "보고서 센터":
    render_report_center()
elif selected_menu == "채널 관리":
    render_channel_management()
else:
    render_settings_page()
