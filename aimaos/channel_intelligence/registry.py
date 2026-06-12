from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

import pandas as pd


CHANNEL_GROUPS = ["광고매체", "오픈마켓", "커머스 플랫폼", "글로벌 채널"]


@dataclass(frozen=True)
class ChannelRecord:
    channel_name: str
    channel_group: str
    purpose: str
    metrics: str
    brand_color: str
    is_active: bool = True
    display_order: int = 100


DEFAULT_CHANNELS = [
    ChannelRecord("네이버 검색광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#03C75A", True, 10),
    ChannelRecord("네이버 쇼핑광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#03C75A", True, 11),
    ChannelRecord("네이버 브랜드검색", "광고매체", "브랜드 검색 결과 상단 노출 및 브랜드 수요 방어 분석", "노출수,클릭수,CTR,광고비,전환수,CPA,ROAS,브랜드 키워드", "#03C75A", True, 12),
    ChannelRecord("카카오 광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#FEE500", True, 13),
    ChannelRecord("구글 광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#4285F4", True, 14),
    ChannelRecord("메타 광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#0081FB", True, 15),
    ChannelRecord("틱톡 광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#000000", True, 16),
    ChannelRecord("유튜브 광고", "광고매체", "광고 집행 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS", "#FF0000", True, 17),
    ChannelRecord("당근 광고", "광고매체", "동네 기반 검색, 피드, 카탈로그 광고 성과 분석", "노출수,클릭수,CTR,CPC,광고비,전환수,CPA,ROAS,지역,문의수", "#FF6F0F", True, 18),
    ChannelRecord("쿠팡", "오픈마켓", "판매채널 성과 분석", "매출,주문수,취소율,반품율,광고비,ROAS,객단가,판매수량", "#E52528", True, 20),
    ChannelRecord("G마켓", "오픈마켓", "판매채널 성과 분석", "매출,주문수,취소율,반품율,광고비,ROAS,객단가,판매수량", "#00C400", True, 21),
    ChannelRecord("옥션", "오픈마켓", "판매채널 성과 분석", "매출,주문수,취소율,반품율,광고비,ROAS,객단가,판매수량", "#E60012", True, 22),
    ChannelRecord("11번가", "오픈마켓", "판매채널 성과 분석", "매출,주문수,취소율,반품율,광고비,ROAS,객단가,판매수량", "#F43142", True, 23),
    ChannelRecord("스마트스토어", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#03C75A", True, 30),
    ChannelRecord("SSG닷컴", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#EF3340", True, 31),
    ChannelRecord("롯데온", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#DA291C", True, 32),
    ChannelRecord("컬리", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#5F0080", True, 33),
    ChannelRecord("오늘의집", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#35C5F0", True, 34),
    ChannelRecord("무신사", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#111111", True, 35),
    ChannelRecord("토스쇼핑", "커머스 플랫폼", "신규 성장 채널 분석", "매출,주문수,신규고객,재구매율,광고비,전환율,객단가", "#0064FF", True, 36),
    ChannelRecord("알리익스프레스", "글로벌 채널", "해외 판매 및 신흥 채널 분석", "매출,주문수,국가별 매출,광고비,전환율,객단가", "#E62E04", True, 40),
    ChannelRecord("테무", "글로벌 채널", "해외 판매 및 신흥 채널 분석", "매출,주문수,국가별 매출,광고비,전환율,객단가", "#FB7701", True, 41),
    ChannelRecord("아마존", "글로벌 채널", "해외 판매 및 신흥 채널 분석", "매출,주문수,국가별 매출,광고비,전환율,객단가", "#FF9900", True, 42),
    ChannelRecord("쇼피", "글로벌 채널", "해외 판매 및 신흥 채널 분석", "매출,주문수,국가별 매출,광고비,전환율,객단가", "#EE4D2D", True, 43),
    ChannelRecord("큐텐", "글로벌 채널", "해외 판매 및 신흥 채널 분석", "매출,주문수,국가별 매출,광고비,전환율,객단가", "#1D4ED8", True, 44),
]


def initialize_channel_registry(db_path: str | Path) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL UNIQUE,
                channel_group TEXT NOT NULL,
                purpose TEXT NOT NULL,
                metrics TEXT NOT NULL,
                brand_color TEXT NOT NULL DEFAULT '#64748B',
                is_active INTEGER NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 100,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        if count == 0:
            connection.executemany(
                """
                INSERT INTO channels (
                    channel_name,
                    channel_group,
                    purpose,
                    metrics,
                    brand_color,
                    is_active,
                    display_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        channel.channel_name,
                        channel.channel_group,
                        channel.purpose,
                        channel.metrics,
                        channel.brand_color,
                        int(channel.is_active),
                        channel.display_order,
                    )
                    for channel in DEFAULT_CHANNELS
                ],
            )
        connection.commit()
    return path


def load_channels(db_path: str | Path, include_inactive: bool = True) -> pd.DataFrame:
    path = initialize_channel_registry(db_path)
    query = "SELECT * FROM channels"
    if not include_inactive:
        query += " WHERE is_active = 1"
    query += " ORDER BY display_order, channel_group, channel_name"
    with sqlite3.connect(path) as connection:
        return pd.read_sql_query(query, connection)


def add_channel(
    db_path: str | Path,
    channel_name: str,
    channel_group: str,
    purpose: str,
    metrics: str,
    brand_color: str,
    is_active: bool,
    display_order: int,
) -> None:
    path = initialize_channel_registry(db_path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO channels (
                channel_name,
                channel_group,
                purpose,
                metrics,
                brand_color,
                is_active,
                display_order
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (channel_name, channel_group, purpose, metrics, brand_color, int(is_active), display_order),
        )
        connection.commit()


def update_channel(
    db_path: str | Path,
    channel_id: int,
    channel_name: str,
    channel_group: str,
    purpose: str,
    metrics: str,
    brand_color: str,
    is_active: bool,
    display_order: int,
) -> None:
    path = initialize_channel_registry(db_path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            UPDATE channels
            SET channel_name = ?,
                channel_group = ?,
                purpose = ?,
                metrics = ?,
                brand_color = ?,
                is_active = ?,
                display_order = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                channel_name,
                channel_group,
                purpose,
                metrics,
                brand_color,
                int(is_active),
                display_order,
                channel_id,
            ),
        )
        connection.commit()
