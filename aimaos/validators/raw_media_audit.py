from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from aimaos.analyzers.performance_analyzer import analyze_performance
from aimaos.parsers.excel_loader import load_ad_file
from aimaos.recommenders.action_engine import build_operating_action_issues
from aimaos.transformers.column_mapper import map_columns, normalize_column_name
from aimaos.transformers.standardizer import standardize_ad_data


DATA_FILE_EXTENSIONS = {".csv", ".xlsx", ".xls"}
PRIORITY_MARKETPLACE_MEDIA = {"G마켓", "옥션", "G마켓/옥션"}
PROFILE_MEDIA = ("G마켓", "옥션")
DEFERRED_MEDIA_STATUS = {
    "네이버": "파일 미확보로 검증 보류",
    "11번가": "파일 미확보로 검증 보류",
}

OPTIONAL_SOURCE_ALIASES = {
    "cart_count": ["장바구니", "장바구니수", "장바구니 수", "cart", "cart count", "add to cart"],
    "roas": ["roas", "광고수익률", "수익률"],
    "cpc": ["cpc", "클릭당비용", "클릭당 비용"],
    "ctr": ["ctr", "클릭률"],
    "cvr": ["cvr", "전환율"],
}

REQUIRED_FIELD_LABELS = {
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

GMARKET_AUCTION_LEGACY_COLUMNS = [
    "일자",
    "광고매체",
    "계정명",
    "캠페인명",
    "광고그룹명",
    "상품명",
    "노출수",
    "클릭수",
    "광고비",
    "전환수",
    "매출",
    "주문수",
    "광고수익률",
    "클릭당비용",
    "클릭률",
    "전환율",
    "광고ID",
    "상품번호",
    "source_sheet",
]

LEGACY_PROFILE_NOTE = (
    "실제 XLSX 원본을 직접 읽은 결과가 아니라, 이전 대화에서 확인된 "
    "지마켓/옥션 리포트 파일명과 표준 연결 후보를 기준으로 만든 legacy 검증 프로필입니다."
)

ALIASES_ADDED_FOR_MARKETPLACE = {
    "date": ["집계일", "기준일", "광고일자", "보고기간", "월", "년월"],
    "platform": ["매체명", "사이트", "사이트명", "마켓", "마켓명", "판매채널", "광고채널"],
    "account_name": ["광고계정", "광고계정명", "판매자", "판매자명", "셀러명", "상점명", "브랜드명"],
    "campaign_name": ["광고명", "광고캠페인", "광고 캠페인", "광고캠페인명"],
    "ad_group_name": ["그룹명", "광고 그룹", "광고 그룹명"],
    "keyword": ["키워드명", "입찰키워드", "입찰 키워드", "구매키워드", "구매 키워드"],
    "product_name": ["광고상품", "광고상품명", "광고 상품명", "노출상품명", "노출 상품명"],
    "impressions": ["광고노출수", "광고 노출수", "노출 횟수", "노출수(회)"],
    "clicks": ["광고클릭수", "광고 클릭수", "클릭 횟수", "클릭수(회)"],
    "cost": ["광고 비용", "광고비(원)", "총광고비", "총 광고비", "소진 광고비", "과금액", "과금금액"],
    "conversions": ["전환건수", "전환 건수", "구매건수", "구매 건수", "전환주문수", "전환 주문수"],
    "revenue": ["광고매출", "광고 매출", "광고매출액", "총매출", "총 매출", "주문금액", "결제금액", "전환매출액", "매출액(원)"],
    "orders": ["주문건수", "주문 건수", "결제건수", "결제 건수"],
}

UNMAPPED_MARKETPLACE_METADATA = [
    "광고ID",
    "상품번호",
    "광고수익률",
    "클릭당비용",
    "클릭률",
    "전환율",
    "전환당비용",
    "source_sheet",
]


@dataclass(frozen=True)
class MediaFileAudit:
    path: Path
    load_status: str
    row_count: int
    column_count: int
    inferred_media: str
    original_columns: list[str]
    mapped_columns: dict[str, str]
    unmapped_columns: list[str]
    missing_standard_columns: list[str]
    required_status: dict[str, str]
    action_issue_count: int
    action_issue_preview: list[str]
    source_type: str = "실제 파일"
    report_version: str = "unknown"
    verification_note: str = ""
    error: str = ""


def discover_data_files(raw_dir: str | Path) -> list[Path]:
    root = Path(raw_dir)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in DATA_FILE_EXTENSIONS)


def audit_raw_media_files(raw_dir: str | Path) -> list[MediaFileAudit]:
    return [audit_media_file(path) for path in discover_data_files(raw_dir)]


def audit_priority_marketplace_files(raw_dir: str | Path) -> list[MediaFileAudit]:
    """Validate G마켓/옥션 first, using legacy profiles when real files are absent."""
    actual_audits = [
        audit for audit in audit_raw_media_files(raw_dir) if audit.inferred_media in PRIORITY_MARKETPLACE_MEDIA
    ]
    actual_media = {audit.inferred_media for audit in actual_audits if audit.load_status == "성공"}
    profile_media = [
        media for media in PROFILE_MEDIA if media not in actual_media and "G마켓/옥션" not in actual_media
    ]
    return actual_audits + audit_gmarket_auction_legacy_profiles(profile_media)


def audit_media_file(path: str | Path) -> MediaFileAudit:
    source = Path(path)
    try:
        raw = load_ad_file(source)
        return _audit_loaded_frame(
            raw,
            source,
            source_type="실제 파일",
            report_version=_report_version_from_path(source),
            verification_note="data/raw 하위에서 발견된 실제 파일 기준 검증입니다.",
        )
    except Exception as error:  # noqa: BLE001
        return MediaFileAudit(
            path=source,
            load_status="실패",
            row_count=0,
            column_count=0,
            inferred_media=_infer_media_from_name(source),
            original_columns=[],
            mapped_columns={},
            unmapped_columns=[],
            missing_standard_columns=[],
            required_status={key: "판단 불가" for key in REQUIRED_FIELD_LABELS},
            action_issue_count=0,
            action_issue_preview=[],
            source_type="실제 파일",
            report_version=_report_version_from_path(source),
            verification_note="파일 로드 단계에서 실패했습니다.",
            error=str(error),
        )


def audit_gmarket_auction_legacy_profiles(media_names: list[str] | tuple[str, ...] | None = None) -> list[MediaFileAudit]:
    targets = tuple(media_names) if media_names is not None else PROFILE_MEDIA
    return [
        _audit_loaded_frame(
            _legacy_profile_frame(media),
            Path(f"legacy_profile_{media}.xlsx"),
            source_type="legacy profile",
            report_version="gmarket_auction_legacy",
            verification_note=LEGACY_PROFILE_NOTE,
        )
        for media in targets
    ]


def _audit_loaded_frame(
    raw: pd.DataFrame,
    source: Path,
    *,
    source_type: str,
    report_version: str,
    verification_note: str,
) -> MediaFileAudit:
    mapping_result = map_columns(raw)
    standardized, _ = standardize_ad_data(raw)
    analysis = analyze_performance(standardized)
    issues = build_operating_action_issues(analysis, advertiser=_advertiser_name(standardized, source))
    return MediaFileAudit(
        path=source,
        load_status="성공",
        row_count=len(raw),
        column_count=len(raw.columns),
        inferred_media=_media_name(standardized, source),
        original_columns=[str(column) for column in raw.columns],
        mapped_columns=mapping_result.mapping,
        unmapped_columns=mapping_result.unmapped_columns,
        missing_standard_columns=mapping_result.missing_standard_columns,
        required_status=_required_field_status(raw, standardized, mapping_result.mapping),
        action_issue_count=len(issues),
        action_issue_preview=[f"{issue.problem} / {issue.evidence}" for issue in issues[:5]],
        source_type=source_type,
        report_version=report_version,
        verification_note=verification_note,
    )


def _legacy_profile_frame(media: str) -> pd.DataFrame:
    prefix = "GM" if media == "G마켓" else "AC"
    rows = [
        {
            "일자": "2026-06-01",
            "광고매체": media,
            "계정명": "뉴트리원",
            "캠페인명": f"{media} 전환 점검 캠페인",
            "광고그룹명": "건강식품 주요상품",
            "상품명": "프로바이오틱스 기획전",
            "노출수": 48000,
            "클릭수": 180,
            "광고비": 620000,
            "전환수": 0,
            "매출": 0,
            "주문수": 0,
            "광고수익률": "0%",
            "클릭당비용": 3444,
            "클릭률": "0.38%",
            "전환율": "0%",
            "광고ID": f"{prefix}-AD-001",
            "상품번호": f"{prefix}-PRD-001",
            "source_sheet": "AdId",
        },
        {
            "일자": "2026-06-02",
            "광고매체": media,
            "계정명": "뉴트리원",
            "캠페인명": f"{media} 클릭률 점검 캠페인",
            "광고그룹명": "인지도 확장",
            "상품명": "루테인 브랜드검색",
            "노출수": 72000,
            "클릭수": 110,
            "광고비": 260000,
            "전환수": 3,
            "매출": 360000,
            "주문수": 3,
            "광고수익률": "138.46%",
            "클릭당비용": 2364,
            "클릭률": "0.15%",
            "전환율": "2.73%",
            "광고ID": f"{prefix}-AD-002",
            "상품번호": f"{prefix}-PRD-002",
            "source_sheet": "daily",
        },
        {
            "일자": "2026-06-03",
            "광고매체": media,
            "계정명": "뉴트리원",
            "캠페인명": f"{media} 확대 후보 캠페인",
            "광고그룹명": "고효율 리마케팅",
            "상품명": "콜라겐 베스트셀러",
            "노출수": 25000,
            "클릭수": 520,
            "광고비": 380000,
            "전환수": 36,
            "매출": 3420000,
            "주문수": 34,
            "광고수익률": "900%",
            "클릭당비용": 731,
            "클릭률": "2.08%",
            "전환율": "6.92%",
            "광고ID": f"{prefix}-AD-003",
            "상품번호": f"{prefix}-PRD-003",
            "source_sheet": "group",
        },
        {
            "일자": "2026-06-04",
            "광고매체": media,
            "계정명": "뉴트리원",
            "캠페인명": f"{media} 안정 운영 캠페인",
            "광고그룹명": "월간 리포트",
            "상품명": "멀티비타민 정기구매",
            "노출수": 31000,
            "클릭수": 460,
            "광고비": 430000,
            "전환수": 18,
            "매출": 1720000,
            "주문수": 17,
            "광고수익률": "400%",
            "클릭당비용": 935,
            "클릭률": "1.48%",
            "전환율": "3.91%",
            "광고ID": f"{prefix}-AD-004",
            "상품번호": f"{prefix}-PRD-004",
            "source_sheet": "monthly",
        },
    ]
    return pd.DataFrame(rows, columns=GMARKET_AUCTION_LEGACY_COLUMNS)


def _report_version_from_path(path: Path) -> str:
    text = normalize_column_name(str(path))
    if "gmarket auction" in text or "gmarket" in text or "auction" in text or "지마켓" in text or "옥션" in text:
        return "gmarket_auction_legacy_candidate"
    if "nutirone report" in text:
        return "gmarket_auction_legacy_candidate"
    return "unknown"


def write_audit_report(audits: list[MediaFileAudit], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_audit_markdown(audits), encoding="utf-8")
    return destination


def build_audit_markdown(audits: list[MediaFileAudit]) -> str:
    actual_count = sum(1 for audit in audits if audit.source_type == "실제 파일")
    profile_count = sum(1 for audit in audits if audit.source_type == "legacy profile")
    lines = [
        "# G마켓/옥션 우선 매핑 및 오늘 해야 할 일 엔진 검증 리포트",
        "",
        f"작성일: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "## 1. 전체 요약",
        "",
    ]
    if not audits:
        lines.extend(
            [
                "- `data/raw` 폴더에서 테스트 가능한 G마켓/옥션 CSV/XLSX 광고 파일을 찾지 못했습니다.",
                "- legacy profile 검증도 생성되지 않았으므로 검증 구성을 확인해야 합니다.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "- 검증 범위: G마켓/옥션 우선 지원 매체",
            f"- 실제 파일 기준 검증: {actual_count:,}개",
            f"- legacy profile 기준 검증: {profile_count:,}개",
            f"- 로드 성공: {sum(1 for audit in audits if audit.load_status == '성공'):,}개",
            f"- 로드 실패: {sum(1 for audit in audits if audit.load_status != '성공'):,}개",
            "- 네이버/11번가: 파일 미확보로 이번 검증 범위에서 보류",
            "",
            "| 검증 대상 | 기준 | 추정 매체 | 버전 | 로드 | 행 수 | 컬럼 수 | 오늘 해야 할 일 이슈 수 |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for audit in audits:
        lines.append(
            f"| {audit.path.name} | {audit.source_type} | {audit.inferred_media} | {audit.report_version} | {audit.load_status} | "
            f"{audit.row_count:,} | {audit.column_count:,} | {audit.action_issue_count:,} |"
        )

    lines.extend(
        [
            "",
            "## 2. 매체별 검증 상태",
            "",
            "| 매체 | 상태 | 사유 |",
            "| --- | --- | --- |",
            f"| G마켓 | {_media_validation_status(audits, 'G마켓')} | 실제 파일이 없으면 legacy profile 기준으로 매핑과 Rule Engine을 검증합니다. |",
            f"| 옥션 | {_media_validation_status(audits, '옥션')} | 실제 파일이 없으면 legacy profile 기준으로 매핑과 Rule Engine을 검증합니다. |",
        ]
    )
    for media, reason in DEFERRED_MEDIA_STATUS.items():
        lines.append(f"| {media} | {reason} | 현재 실제 원본 파일 미확보로 이번 검증 범위에서 제외했습니다. |")

    lines.extend(["", "## 3. G마켓/옥션 상세", ""])
    for audit in audits:
        lines.extend(_audit_detail_lines(audit))

    lines.extend(
        [
            "",
            "## 4. 추가한 COLUMN_ALIASES",
            "",
            "| 표준 필드 | 추가 alias |",
            "| --- | --- |",
        ]
    )
    for field, aliases in ALIASES_ADDED_FOR_MARKETPLACE.items():
        lines.append(f"| {field} | {', '.join(aliases)} |")

    lines.extend(
        [
            "",
            "## 5. 아직 표준 스키마에 넣지 않은 컬럼",
            "",
            "- 아래 항목은 실제 XLSX 구조 확인 전까지 원본 메타데이터 또는 계산 보조값으로만 봅니다.",
        ]
    )
    for column in UNMAPPED_MARKETPLACE_METADATA:
        lines.append(f"- {column}")

    lines.extend(
        [
            "",
            "## 6. legacy / next 구분 판단",
            "",
            "- 현재 사용자가 설명한 G마켓/옥션 리포트는 기존 광고센터 기준이므로 `legacy`로 분류합니다.",
            "- 새 G마켓/옥션 광고센터가 예정되어 있으므로 현재 구조에 강하게 고정하면 위험합니다.",
            "- 신규 광고센터 파일을 확보하면 `next` profile을 별도로 만들고 legacy alias와 분리해야 합니다.",
            "",
            "## 7. 현재 확인된 한계",
            "",
            "- J: 드라이브의 뉴트리원 XLSX 원본은 현재 실행 환경에서 접근 권한이 없어 직접 헤더를 추출하지 못했습니다.",
            "- 따라서 이 리포트의 G마켓/옥션 컬럼은 실제 파일 헤더가 아니라 이전 대화에서 확인된 리포트 구조 기반의 legacy 검증 프로필입니다.",
            "- 장바구니 수는 현재 기본 표준 스키마에 포함되어 있지 않아 실제 파일에 컬럼이 있어도 별도 확장이 필요합니다.",
            "- ROAS, CPC, CTR, CVR은 원본 컬럼이 없더라도 노출수, 클릭수, 광고비, 전환수, 매출이 있으면 계산 가능합니다.",
            "- 실제 G마켓/옥션 XLSX 파일이 `data/raw/gmarket_auction/nutirone/`에 들어오면 이 리포트는 실제 컬럼 기준으로 다시 생성해야 합니다.",
            "",
        ]
    )
    return "\n".join(lines)


def _audit_detail_lines(audit: MediaFileAudit) -> list[str]:
    lines = [
        f"### {audit.path.name}",
        "",
        f"- 파일 경로: `{audit.path}`",
        f"- 검증 기준: {audit.source_type}",
        f"- 리포트 버전: {audit.report_version}",
        f"- 추정 매체: {audit.inferred_media}",
        f"- 로드 상태: {audit.load_status}",
    ]
    if audit.verification_note:
        lines.append(f"- 검증 메모: {audit.verification_note}")
    if audit.error:
        lines.extend(["", f"- 오류: `{audit.error}`", ""])
        return lines

    lines.extend(
        [
            f"- 행 수: {audit.row_count:,}",
            f"- 컬럼 수: {audit.column_count:,}",
            "",
            "#### 필수 지표 표준화 상태",
            "",
            "| 항목 | 상태 |",
            "| --- | --- |",
        ]
    )
    for key, label in REQUIRED_FIELD_LABELS.items():
        lines.append(f"| {label} | {audit.required_status.get(key, '판단 불가')} |")

    lines.extend(["", "#### 기준 컬럼명", ""])
    if audit.original_columns:
        for column in audit.original_columns:
            lines.append(f"- `{column}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "#### 매핑 성공 컬럼", ""])
    if audit.mapped_columns:
        for source, target in audit.mapped_columns.items():
            lines.append(f"- `{source}` -> `{target}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "#### 미매핑 컬럼", ""])
    if audit.unmapped_columns:
        for column in audit.unmapped_columns:
            lines.append(f"- `{column}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "#### 필수 표준 컬럼 중 매핑 실패", ""])
    if audit.missing_standard_columns:
        for column in audit.missing_standard_columns:
            lines.append(f"- `{column}`")
    else:
        lines.append("- 없음")

    lines.extend(["", "#### 오늘 해야 할 일 이슈 미리보기", ""])
    if audit.action_issue_preview:
        for item in audit.action_issue_preview:
            lines.append(f"- {item}")
    else:
        lines.append("- 현재 Rule Engine 기준 주요 조치 필요 항목 없음")
    lines.append("")
    return lines


def _media_validation_status(audits: list[MediaFileAudit], media: str) -> str:
    media_audits = [audit for audit in audits if audit.inferred_media == media]
    if any(audit.source_type == "실제 파일" and audit.load_status == "성공" for audit in media_audits):
        return "실제 파일 기준 검증 완료"
    if any(audit.source_type == "legacy profile" and audit.load_status == "성공" for audit in media_audits):
        return "legacy profile 기준 검증 완료"
    return "파일 미확보로 실제 검증 보류"


def _required_field_status(raw: pd.DataFrame, standardized: pd.DataFrame, mapping: dict[str, str]) -> dict[str, str]:
    status = {
        "date": _mapped_data_status(standardized, "date", mapping),
        "account_name": _mapped_text_status(standardized, "account_name", mapping),
        "platform": _mapped_text_status(standardized, "platform", mapping),
        "campaign_name": _mapped_text_status(standardized, "campaign_name", mapping),
        "ad_group_name": _mapped_text_status(standardized, "ad_group_name", mapping),
        "product_or_keyword": _product_or_keyword_status(standardized, mapping),
        "impressions": _mapped_numeric_status(standardized, "impressions", mapping),
        "clicks": _mapped_numeric_status(standardized, "clicks", mapping),
        "cost": _mapped_numeric_status(standardized, "cost", mapping),
        "conversions": _mapped_numeric_status(standardized, "conversions", mapping),
        "revenue": _mapped_numeric_status(standardized, "revenue", mapping),
        "cart_count": _optional_source_status(raw, "cart_count"),
        "roas": _derived_status(standardized, ["revenue", "cost"], "roas"),
        "cpc": _derived_status(standardized, ["cost", "clicks"], "cpc"),
        "ctr": _derived_status(standardized, ["clicks", "impressions"], "ctr"),
        "cvr": _derived_status(standardized, ["conversions", "clicks"], "cvr"),
    }
    return status


def _mapped_data_status(frame: pd.DataFrame, column: str, mapping: dict[str, str]) -> str:
    if column not in mapping.values():
        return "매핑 실패"
    if frame[column].notna().sum() == 0:
        return "판단 불가"
    return "성공"


def _mapped_text_status(frame: pd.DataFrame, column: str, mapping: dict[str, str]) -> str:
    if column not in mapping.values():
        return "매핑 실패"
    valid = frame[column].astype(str).str.strip()
    if valid.empty or (valid == "미분류").all():
        return "판단 불가"
    return "성공"


def _mapped_numeric_status(frame: pd.DataFrame, column: str, mapping: dict[str, str]) -> str:
    if column not in mapping.values():
        return "매핑 실패"
    if float(frame[column].sum()) == 0:
        return "판단 불가"
    return "성공"


def _product_or_keyword_status(frame: pd.DataFrame, mapping: dict[str, str]) -> str:
    product = _mapped_text_status(frame, "product_name", mapping)
    keyword = _mapped_text_status(frame, "keyword", mapping)
    if "성공" in {product, keyword}:
        return "성공"
    if "판단 불가" in {product, keyword}:
        return "판단 불가"
    return "매핑 실패"


def _optional_source_status(raw: pd.DataFrame, key: str) -> str:
    aliases = {normalize_column_name(value) for value in OPTIONAL_SOURCE_ALIASES.get(key, [])}
    normalized_columns = {normalize_column_name(column): column for column in raw.columns}
    matched = [normalized_columns[column] for column in aliases if column in normalized_columns]
    if not matched:
        return "판단 불가"
    series = raw[matched[0]]
    return "성공" if pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0).sum() > 0 else "판단 불가"


def _derived_status(frame: pd.DataFrame, base_columns: list[str], derived_column: str) -> str:
    if any(column not in frame.columns for column in base_columns + [derived_column]):
        return "판단 불가"
    denominator = frame[base_columns[-1]]
    if float(denominator.sum()) == 0:
        return "판단 불가"
    return "성공"


def _advertiser_name(frame: pd.DataFrame, path: Path) -> str:
    if "account_name" in frame.columns:
        values = frame["account_name"].astype(str).str.strip()
        values = values[(values != "") & (values != "미분류")]
        if not values.empty:
            return values.iloc[0]
    return path.stem


def _media_name(frame: pd.DataFrame, path: Path) -> str:
    if "platform" in frame.columns:
        values = frame["platform"].astype(str).str.strip()
        values = values[(values != "") & (values != "미분류")]
        if not values.empty:
            return values.iloc[0]
    return _infer_media_from_name(path)


def _infer_media_from_name(path: Path) -> str:
    text = normalize_column_name(str(path))
    if "naver" in text or "네이버" in text:
        return "네이버"
    if ("gmarket" in text or "g 마켓" in text or "지마켓" in text) and ("auction" in text or "옥션" in text):
        return "G마켓/옥션"
    if "gmarket" in text or "g 마켓" in text or "지마켓" in text:
        return "G마켓"
    if "auction" in text or "옥션" in text:
        return "옥션"
    if "11" in text or "11번가" in text:
        return "11번가"
    return "매체 미분류"
