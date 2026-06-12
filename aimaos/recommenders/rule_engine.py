from __future__ import annotations

import pandas as pd

from aimaos.analyzers.performance_analyzer import AnalysisResult


def build_recommendations(analysis: AnalysisResult) -> pd.DataFrame:
    rows = []

    for _, anomaly in analysis.anomalies.iterrows():
        anomaly_type = anomaly["type"]
        if anomaly_type == "광고비 소진 대비 전환 없음":
            action = "입찰가/예산 하향 또는 검색어 제외 검토"
            priority = "P1"
            expected_effect = "불필요 광고비 절감"
        elif anomaly_type == "노출 대비 클릭률 저조":
            action = "소재 문구, 상품명, 키워드 매칭 방식 점검"
            priority = "P2"
            expected_effect = "클릭률 개선 및 품질 저하 방지"
        elif anomaly_type == "확대 가능 구간":
            action = "일 예산 확대 또는 유사 키워드/상품 확장"
            priority = "P2"
            expected_effect = "전환 규모 확대"
        else:
            action = "전문가 검토"
            priority = "P3"
            expected_effect = "운영 리스크 감소"

        rows.append(
            {
                "priority": priority,
                "target": anomaly["target"],
                "issue": anomaly_type,
                "recommended_action": action,
                "expected_effect": expected_effect,
                "risk_level": anomaly["severity"],
            }
        )

    if not rows:
        summary = analysis.summary
        if summary.get("cost", 0) > 0 and summary.get("conversions", 0) == 0:
            rows.append(
                {
                    "priority": "P1",
                    "target": "전체 계정",
                    "issue": "전환 데이터 없음",
                    "recommended_action": "전환 추적 설정과 기간/매체별 원본 데이터를 먼저 확인",
                    "expected_effect": "분석 신뢰도 확보",
                    "risk_level": "high",
                }
            )
        else:
            rows.append(
                {
                    "priority": "P3",
                    "target": "전체 계정",
                    "issue": "긴급 점검 포인트 없음",
                    "recommended_action": "상위 비용 캠페인과 광고수익률 상위 캠페인을 중심으로 전문가 검토",
                    "expected_effect": "성과 개선 후보 발굴",
                    "risk_level": "low",
                }
            )

    return pd.DataFrame(rows)
