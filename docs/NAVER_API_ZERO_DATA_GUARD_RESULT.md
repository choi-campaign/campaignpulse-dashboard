# NAVER API Zero Data Guard Result

작성일: 2026-06-10

## 1. 수정 파일

- `aimaos/analyzers/performance_analyzer.py`
- `aimaos/pipeline.py`
- `aimaos/recommenders/action_engine.py`
- `aimaos/reports/report_generator.py`

## 2. 수정 이유

네이버 stats API 호출은 성공했지만 `response.data`가 빈 배열인 경우, AIMAOS가 생성한 표준 CSV는 모든 성과 지표가 0인 placeholder 행이 됩니다.

기존 구조에서는 이 0 지표 행을 실제 운영 문제로 오해해 아래 권고가 생성되었습니다.

- 입찰가/예산 하향 또는 검색어 제외 검토
- 소재 문구, 상품명, 키워드 매칭 방식 점검

이는 실제 성과 데이터가 없는 상태에서 생성된 과한 운영 권고이므로 방어 로직을 추가했습니다.

## 3. 0 지표 데이터 방어 조건

아래 핵심 지표가 모두 0이면 운영 개선 권고와 운영 점검 포인트를 생성하지 않습니다.

- `impressions = 0`
- `clicks = 0`
- `cost = 0`
- `conversions = 0`
- `revenue = 0`

적용 대상:

- 네이버 API `response.data`가 빈 배열이라 요청 ID 기준으로 생성된 placeholder 표준 CSV
- 성과 측정값이 전부 0인 CSV/Excel 데이터

## 4. 우선 실행 권고 미생성 여부

결과: 성공

검증 파일:

`data/collection_poc/20260610_142203/naver_searchad/naver_searchad_standard.csv`

검증 결과:

- 우선 실행 권고: 생성 안 됨
- 운영 점검 포인트: 생성 안 됨
- 기존 Rule Engine 전체 구조: 변경하지 않음
- 0 지표 데이터일 때만 Rule Engine 호출을 건너뜀

## 5. 오늘 해야 할 일 메시지

생성 결과:

- 문제: 데이터 부족
- 매체: 네이버 검색광고
- 추천 액션: 해당 기간의 네이버 광고 성과 데이터가 없습니다. 광고센터 기간 또는 계정 상태를 확인한 뒤 다시 수집해 주세요.
- 광고주 설명 문구: 해당 기간의 네이버 광고 성과 데이터가 없습니다. 광고센터 기간 또는 계정 상태를 확인한 뒤 다시 수집해 주세요.

## 6. 보고서 결과

생성 보고서:

- Markdown: `data/reports/naver_api_zero_guard_20260610_145500/report.md`
- TXT: `data/reports/naver_api_zero_guard_20260610_145500/report.txt`
- Excel: `data/reports/naver_api_zero_guard_20260610_145500/analysis.xlsx`

보고서 확인 결과:

- `우선 실행 권고` 섹션에 잘못된 권고 없음
- `오늘 해야 할 일` 섹션에 데이터 부족 메시지 1건 표시
- `운영 점검 포인트` 섹션에 `우선 확인할 운영 점검 포인트가 없습니다.` 표시

## 7. 기존 정상 데이터 분석 영향 여부

결과: 영향 없음

정상 성과 데이터 회귀 테스트:

- 입력 파일: `data/raw/test_ads_full_visible.csv`
- 분석 행 수: 48행
- 광고비: 26,470,000원
- 노출수: 1,603,400
- 이상징후: 5건 생성
- 우선 실행 권고: 5건 생성
- 오늘 해야 할 일: 5건 생성

해석: 이번 방어 로직은 성과 측정값이 전부 0인 데이터에만 적용되며, 정상 성과 데이터의 기존 분석 결과에는 영향을 주지 않습니다.
