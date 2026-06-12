# AIMAOS MVP 1 설계 문서

## 1. 현실성 평가

AIMAOS의 첫 수익화 지점은 광고 플랫폼을 직접 제어하는 거대한 자동화가 아니라, 광고주 데이터를 빠르게 분석해 보고서와 실행안을 만들어 주는 내부 운영 도구입니다.

광고 플랫폼 API는 제한적이고 실무 데이터와 맞지 않는 경우가 많으므로, MVP 1은 엑셀/CSV 수집과 브라우저 다운로드 파일을 기준으로 설계합니다. 캡차 우회, 보안 우회, 정책 위반 자동화는 범위에서 제외합니다.

## 2. MVP 정의

MVP 1은 광고 데이터 분석기입니다.

입력은 엑셀 또는 CSV 파일이고, 출력은 표준화 데이터, 운영 점검 포인트, 실행 권고, 광고주용 보고서입니다.

핵심 가치는 운영자가 매일 반복하는 “다운로드, 정리, 계산, 해석, 보고서 초안 작성” 시간을 줄이는 것입니다.

## 3. 아키텍처 설계

- Data Collection Layer: 브라우저 자동화 또는 수동 다운로드 파일을 `data/raw`에 저장합니다.
- Data Standardization Layer: 매체별 컬럼명을 공통 컬럼으로 매핑합니다.
- Intelligence Layer: CTR, CPC, CVR, CPA, ROAS와 기간 비교를 계산합니다.
- Recommendation Layer: 규칙 기반으로 즉시 실행 가능한 개선안을 만듭니다.
- Automation Layer: MVP 1에서는 직접 실행 대신 안전 검증 인터페이스만 둡니다.
- Knowledge Layer: 보고서와 실행 결과를 사례 자산으로 축적할 수 있게 저장합니다.
- Benchmark Layer: 업종별 평균값 축적을 위한 확장 지점을 둡니다.
- Association Layer: 회원사별 분석과 표준 보고서 확장을 위한 구조를 둡니다.

## 4. 폴더 구조

```text
aimaos/
  app/
  collectors/
  parsers/
  transformers/
  analyzers/
  recommenders/
  automations/
  validators/
  knowledge/
  benchmark/
  association/
  reports/
  configs/
data/
  raw/
  processed/
  reports/
  logs/
tests/
docs/
```

## 5. 데이터 스키마

공통 스키마는 다음 컬럼을 기준으로 합니다.

- `date`
- `platform`
- `account_name`
- `campaign_name`
- `ad_group_name`
- `keyword`
- `product_name`
- `impressions`
- `clicks`
- `cost`
- `conversions`
- `revenue`
- `orders`
- `ctr`
- `cpc`
- `cvr`
- `cpa`
- `roas`

## 6. 분석 로직

분석은 세 단계로 진행합니다.

1. 전체 계정 요약 지표 계산
2. 매체, 캠페인, 광고그룹, 키워드, 상품 단위 집계
3. 비용 과다, 전환 없음, CTR 저조, ROAS 우수 구간 탐지

## 7. 리포트 생성 로직

보고서는 Markdown, TXT, XLSX로 생성합니다.

Markdown과 TXT는 광고주 커뮤니케이션 초안으로 사용하고, XLSX는 내부 운영자가 세부 데이터를 검토하는 용도로 사용합니다.

## 8. 자동화 로직

MVP 1에서는 자동 실행보다 자동 분석을 우선합니다.

자동화 확장 시 Playwright 또는 Selenium으로 광고센터 로그인, 계정 선택, 기간 설정, 보고서 다운로드, 다운로드 검증까지 처리합니다. 입찰가 변경이나 예산 변경은 전문가 승인 후 실행하는 승인형 자동화로 설계합니다.

## 9. 자산화 전략

모든 원본 파일, 표준화 파일, 보고서, 운영 점검 포인트, 실행 권고, 실제 실행 결과를 누적합니다.

이 데이터가 쌓이면 협회 고유의 업종별 벤치마크와 운영 사례 검색 DB가 됩니다.

## 10. 협회 확장 전략

회원사별 정기 분석, 표준 진단 리포트, 컨설팅 패키지, 교육 자료, 업종별 벤치마크 리포트로 확장합니다.

초기 상품화는 “월간 광고 계정 진단”, “광고 대행사 운영 자동화 패키지”, “회원사 성과 리포트 자동 생성”이 적합합니다.

## 11. 유지보수 전략

컬럼 매핑 사전은 계속 업데이트합니다.

광고센터 화면 자동화는 선택자 변경에 취약하므로 수집 단계와 분석 단계를 분리합니다. 수집이 실패해도 수동 다운로드 파일만 있으면 분석은 계속 돌아가야 합니다.

## 12. 실제 코드 작성

현재 MVP 코드는 `aimaos` 패키지에 포함되어 있습니다.

주요 실행 파일은 `aimaos/app/cli.py`와 `aimaos/app/streamlit_app.py`입니다.
