# AIMAOS 데이터 아키텍처

## 1. 문서 목적

이 문서는 AIMAOS의 현재 광고 데이터 분석 MVP와 향후 Phase 2 Intelligence 모듈의 데이터 구조를 정의합니다.

현재 단계에서는 실제 크롤러, 로그인 자동화, 데이터 수집 구현을 하지 않습니다. 이 문서는 향후 확장을 위한 저장 구조와 연결 기준을 설계하는 문서입니다.

Phase 2 화면 테스트를 위해 샘플 데이터만 별도로 둡니다.

```text
data/phase2_samples
```

이 폴더의 데이터는 실제 수집 데이터가 아니라 화면과 구조를 확인하기 위한 테스트 샘플입니다.

## 2. 전체 데이터 계층

AIMAOS 데이터는 아래 계층으로 나눕니다.

| 계층 | 목적 | 현재 상태 |
| --- | --- | --- |
| 원본 데이터 | 광고센터 또는 외부 소스에서 받은 원본 파일 보존 | 구현됨 |
| 표준화 데이터 | 매체별 컬럼을 공통 기준으로 정리 | 구현됨 |
| 분석 결과 | 성과 지표, 운영 점검 포인트, 실행 권고 저장 | 구현됨 |
| 기간별 집계 | 일자, 주간, 월간, 분기, 반기, 연도, 시즌 기준 집계와 화면 내 사용자 지정 기간 비교 | 구현됨 |
| 외부 인텔리전스 | 커머스, 검색, AI 가시성 데이터 | 샘플 미리보기 |
| 채널 레지스트리 | 광고매체, 오픈마켓, 커머스 플랫폼, 글로벌 채널 관리 | 구현됨 |
| 지식 자산 | 성공 사례, 실패 사례, 운영 노하우 | 설계 단계 |
| 벤치마크 | 업종별 평균 성과와 시장 기준 | 설계 단계 |

## 3. 현재 광고 데이터 MVP 구조

### 3.1 원본 입력

현재 MVP는 엑셀 또는 CSV 파일을 입력으로 받습니다.

저장 위치:

```text
data/raw
```

### 3.2 표준 광고 성과 스키마

현재 광고 데이터 분석기의 내부 표준 컬럼은 아래와 같습니다.

| 내부 컬럼 | 사용자 표시명 | 설명 |
| --- | --- | --- |
| date | 날짜 | 광고 성과가 집계된 날짜 |
| platform | 매체 | 광고가 집행된 매체 |
| account_name | 계정명 | 광고 계정 또는 광고주 |
| campaign_name | 캠페인명 | 광고 운영 상위 단위 |
| ad_group_name | 광고그룹명 | 캠페인 안의 세부 운영 단위 |
| keyword | 키워드 | 검색어 또는 운영 키워드 |
| product_name | 상품명 | 광고와 연결된 상품 또는 서비스 |
| impressions | 노출수 | 광고가 보인 횟수 |
| clicks | 클릭수 | 광고가 클릭된 횟수 |
| cost | 광고비 | 사용한 광고 비용 |
| conversions | 전환수 | 구매, 문의, 신청 등 목표 행동 횟수 |
| revenue | 매출 | 광고를 통해 발생한 매출 또는 전환 가치 |
| orders | 주문수 | 광고를 통해 발생한 주문 수 |
| ctr | 클릭률 | 클릭수 ÷ 노출수 |
| cpc | 클릭당 비용 | 광고비 ÷ 클릭수 |
| cvr | 전환율 | 전환수 ÷ 클릭수 |
| cpa | 전환당 비용 | 광고비 ÷ 전환수 |
| roas | 광고수익률 | 매출 ÷ 광고비, 화면과 보고서에서는 퍼센트로 표시 |

## 4. Phase 2 확장 데이터 구조

## 4.0 Channel Intelligence Layer

채널 통합 관제는 광고매체, 오픈마켓, 커머스 플랫폼, 글로벌 채널을 하나의 관리 체계로 묶습니다.

현재 채널 목록은 화면 코드가 아니라 SQLite DB에서 관리합니다.

```text
data/channel_registry.sqlite
```

관리 테이블:

```text
channels
```

핵심 관리 항목:

- 채널명
- 채널 영역
- 관리 목적
- 분석 항목
- 대표 색상
- 활성/비활성 상태
- 표시 순서

이 구조를 통해 새로운 채널이 추가되어도 기존 분석 화면을 직접 수정하지 않고 관리자 화면에서 채널을 관리할 수 있습니다.

## 4.1 Commerce Intelligence

### 목적

커머스 플랫폼의 상품 경쟁력 데이터를 저장해 광고 성과 판단에 연결합니다.

### 대상

- 스마트스토어
- 쿠팡
- G마켓
- 옥션
- 11번가

### 향후 테이블 초안: commerce_products

| 컬럼 | 설명 |
| --- | --- |
| observed_date | 관측일 |
| platform | 커머스 플랫폼 |
| seller_name | 판매자명 |
| brand_name | 브랜드명 |
| product_name | 상품명 |
| product_url | 상품 URL |
| category_name | 카테고리명 |
| price | 가격 |
| review_count | 리뷰 수 |
| rating | 평점 |
| sales_volume | 판매량 또는 판매량 추정값 |
| competitor_group | 경쟁상품 묶음 |
| source_type | 수집 또는 입력 방식 |
| created_at | 저장 시각 |

### 향후 테이블 초안: commerce_competitors

| 컬럼 | 설명 |
| --- | --- |
| observed_date | 관측일 |
| base_product_name | 기준 상품명 |
| competitor_product_name | 경쟁상품명 |
| competitor_platform | 경쟁상품 플랫폼 |
| competitor_price | 경쟁상품 가격 |
| competitor_review_count | 경쟁상품 리뷰 수 |
| competitor_rating | 경쟁상품 평점 |
| difference_note | 비교 메모 |

## 4.2 Search Intelligence

### 목적

검색 키워드 수요, 경쟁도, 검색 결과 노출 정보를 저장해 광고 운영 판단에 연결합니다.

### 대상

- 네이버
- 구글
- 카카오다음
- 네이트

### 향후 테이블 초안: search_keywords

| 컬럼 | 설명 |
| --- | --- |
| observed_date | 관측일 |
| search_engine | 검색엔진 |
| keyword | 키워드 |
| search_volume | 검색량 |
| competition_level | 경쟁도 |
| category_name | 업종 또는 카테고리 |
| season_label | 시즌 |
| memo | 운영 메모 |
| created_at | 저장 시각 |

### 향후 테이블 초안: search_results

| 컬럼 | 설명 |
| --- | --- |
| observed_date | 관측일 |
| search_engine | 검색엔진 |
| keyword | 키워드 |
| rank_position | 노출 순위 |
| result_title | 검색 결과 제목 |
| result_url | 검색 결과 URL |
| result_type | 광고, 쇼핑, 블로그, 뉴스, 일반문서 등 |
| brand_name | 노출 브랜드명 |
| competitor_name | 경쟁사명 |
| is_competitor_visible | 경쟁사 노출 여부 |

## 4.3 AI Visibility Intelligence

### 목적

생성형 AI 답변에서 브랜드와 경쟁사가 어떻게 언급되고 추천되는지 저장합니다.

### 대상

- ChatGPT
- Claude
- Gemini
- Perplexity

### 향후 테이블 초안: ai_visibility_queries

| 컬럼 | 설명 |
| --- | --- |
| query_id | 질문 ID |
| query_text | 질문 내용 |
| category_name | 업종 또는 주제 |
| brand_name | 기준 브랜드 |
| competitor_group | 경쟁사 묶음 |
| intent_type | 정보 탐색, 비교, 추천, 구매 고려 등 |
| created_at | 생성 시각 |

### 향후 테이블 초안: ai_visibility_observations

| 컬럼 | 설명 |
| --- | --- |
| observed_date | 관측일 |
| ai_platform | AI 플랫폼 |
| query_id | 질문 ID |
| brand_mentioned | 브랜드 언급 여부 |
| competitor_mentioned | 경쟁사 언급 여부 |
| recommended | 추천 여부 |
| answer_summary | 답변 요약 |
| cited_sources | 답변 출처 |
| source_urls | 출처 URL 목록 |
| position_note | 답변 내 노출 위치 또는 맥락 |
| created_at | 저장 시각 |

## 5. 공통 키 설계

Phase 2 데이터는 광고 데이터와 바로 합치기 어렵기 때문에 공통 연결 키를 설계해야 합니다.

| 연결 기준 | 설명 |
| --- | --- |
| 광고주명 | 광고 데이터와 외부 인텔리전스를 묶는 기본 기준 |
| 브랜드명 | 커머스, 검색, AI Visibility 공통 기준 |
| 상품명 | 광고 상품과 커머스 상품 연결 기준 |
| 키워드 | 광고 키워드와 검색 수요 연결 기준 |
| 업종/카테고리 | 벤치마크와 시즌성 분석 기준 |
| 관측일 | 외부 데이터가 언제 관측되었는지 비교하는 기준 |

## 6. 저장소 설계 방향

현재 MVP는 파일 기반 결과물을 우선 사용합니다.

향후 확장 시 권장 구조는 아래와 같습니다.

| 저장소 | 용도 |
| --- | --- |
| CSV/XLSX | 초기 수동 업로드, 광고주 공유용 |
| SQLite | 단일 PC 또는 내부 운영 MVP 저장소 |
| DuckDB | 대용량 분석과 기간별 집계 |
| Markdown | 보고서, 운영 메모, 지식 문서 |
| 파일 폴더 | 원본 파일 보존과 증빙 |

## 7. 데이터 수집 원칙

향후 수집 기능을 구현하더라도 아래 원칙을 지킵니다.

- 캡차 우회 금지
- 보안 우회 금지
- 정책 위반 자동화 금지
- 로그인 자동화는 승인형 내부 운영 도구로만 검토
- 수집 실패 시 수동 업로드로 대체 가능해야 함
- 원본 파일과 분석 결과를 분리 보관해야 함

## 8. 현재 단계에서의 결론

현재 AIMAOS의 핵심 자산은 광고 데이터 분석 MVP입니다.

Commerce Intelligence, Search Intelligence, AI Visibility Intelligence는 현재 Placeholder 상태로 두고, 먼저 데이터 구조와 저장 기준을 확정한 뒤 실제 수집 기능을 검토합니다.
