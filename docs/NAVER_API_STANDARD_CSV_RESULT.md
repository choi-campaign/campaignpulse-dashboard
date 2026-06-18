# NAVER API Standard CSV Result

작성일: 2026-06-10

## 1. 실제 stats JSON 구조 요약

- 확인 파일: `data/collection_poc/20260610_142203/naver_searchad/yesterday_stats.json`
- 최상위 구조: `target`, `params`, `response`
- 성공 조합: `캠페인 반복 ids / rich fields`
- 요청 ID: `cmp-demo-redacted`
- 요청 기간: `2026-06-09` ~ `2026-06-09`
- 요청 fields: `clkCnt`, `impCnt`, `salesAmt`, `ctr`, `cpc`, `avgRnk`, `ccnt`, `convAmt`, `ror`
- 응답 구조: `response.data`, `response.compTm`, `response.cycleBaseTm`
- `response.data` 타입: list
- `response.data` 행 수: 0
- `compTm`: `202606101344`
- `cycleBaseTm`: `202606101300`

해석: 네이버 stats API 호출 자체는 성공했지만, 해당 전일 기준으로 반환된 성과 행이 없습니다.

## 2. 수정한 파싱 규칙

- `response.data`가 리스트이고 행이 있으면 내부 행을 AIMAOS 표준 CSV 행으로 변환합니다.
- `response.data`가 빈 리스트이면 실패로 처리하지 않고, 요청 파라미터의 `ids`를 기준으로 0 지표 행을 생성합니다.
- `fields` 또는 `data`가 딕셔너리로 중첩된 응답도 펼쳐서 행으로 변환하도록 보강했습니다.
- 응답에 없는 매출, 전환, ROAS는 임의 추정하지 않고 0으로 처리합니다.
- AIMAOS 기존 분석 파이프라인이 읽을 수 있도록 `advertiser`, `media`, `campaign`, `ad_group` 컬럼을 기존 컬럼 매핑 구조에 맞는 별칭으로 생성했습니다.

## 3. 생성된 표준 CSV 경로

`data\collection_poc\20260610_142203\naver_searchad\naver_searchad_standard.csv`

## 4. 표준 CSV 행 수

- 1행

## 5. 수집된 지표 목록

생성 컬럼:

- `date`
- `advertiser`
- `media`
- `campaign`
- `ad_group`
- `keyword`
- `product_name`
- `impressions`
- `clicks`
- `cost`
- `conversions`
- `revenue`
- `roas`
- `cpc`
- `ctr`
- `orders`

생성된 값:

- 날짜: `2026-06-09`
- 광고주: `샘플 광고주`
- 매체: `네이버 검색광고`
- 캠페인: `샘플 캠페인`
- 노출수: `0`
- 클릭수: `0`
- 광고비: `0`
- 전환수: `0`
- 매출: `0`
- ROAS: `0`
- CPC: `0`
- CTR: `0`

## 6. 데이터 부족 지표

- 전환수
- 매출
- ROAS

주의: 위 지표는 네이버 API가 실패한 것이 아니라, 전일 stats 응답의 `data`가 비어 있어 판단 가능한 성과 행이 없다는 의미입니다.

## 7. 기존 분석 파이프라인 연결 결과

- 결과: 성공
- 표준화 행 수: 1행
- 출력 폴더: `data\reports\naver_api_poc_20260610_144102`

## 8. 오늘 해야 할 일 생성 결과

- 결과: 성공
- 생성 건수: 1건
- 생성 내용: 데이터 부족으로 인한 `판단 불가`
- 해석: 성과 데이터가 모두 0이므로 운영 액션을 단정하지 않고, 최신 데이터 확보가 필요하다는 보수적 이슈가 생성되었습니다.

## 9. 보고서 생성 결과

- 결과: 성공
- Markdown: `data\reports\naver_api_poc_20260610_144102\report.md`
- TXT: `data\reports\naver_api_poc_20260610_144102\report.txt`
- Excel: `data\reports\naver_api_poc_20260610_144102\analysis.xlsx`

## 10. 다음 단계

1. 실제 성과가 있는 날짜 범위로 stats API를 다시 테스트합니다.
2. `response.data`에 실제 성과 행이 들어오는 경우의 구조를 추가 검증합니다.
3. 캠페인 단위 수집이 안정화되면 광고그룹 단위 stats 조회를 별도로 검증합니다.
4. 키워드가 없는 계정은 캠페인/광고그룹 단위 분석을 기본값으로 둡니다.
5. 전환/매출/ROAS가 필요한 계정은 네이버 전환 추적 설정 여부를 확인합니다.
