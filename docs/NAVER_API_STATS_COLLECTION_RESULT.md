# NAVER API Stats Collection Result

작성일: 2026-06-10 14:22:03

실행 환경: 네이버 API 호출 가능

## 1. 키워드 조회 성공 여부

- 성공: 광고그룹 ID 기준 키워드 조회 성공. 키워드 0건 조회. 증거: `C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\keywords.json`

## 2. stats API 성과 조회 성공 여부

- 성공: 전일(2026-06-09) stats API 조회 성공. 성공 조합: 캠페인 반복 ids / rich fields 증거: `C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\yesterday_stats.json`

## 3. 성공한 idType/fields 조합

- 공식 Python 샘플 기준으로 별도 idType 없이 ids 반복 파라미터와 fields JSON 문자열을 사용했습니다.
- 이번 모듈은 `캠페인+광고그룹`, `캠페인`, `광고그룹`, `키워드` 순서로 rich/basic fields 조합을 테스트합니다.
- 성공 조합: 전일(2026-06-09) stats API 조회 성공. 성공 조합: 캠페인 반복 ids / rich fields

## 4. 수집 가능한 지표

- 기본 지표: 노출수(impCnt), 클릭수(clkCnt), 광고비(salesAmt)
- 조건부 지표: 전환수(ccnt), 전환매출(convAmt), 광고수익률(ror)
- 전환/매출/광고수익률은 계정의 전환 추적 설정과 API 응답 필드 지원 여부에 따라 달라집니다.

## 5. 수집 불가능하거나 추가 설정이 필요한 지표

- 전환매출(convAmt) 또는 광고수익률(ror)이 응답에 없으면 AIMAOS에서는 매출/ROAS를 데이터 부족으로 봐야 합니다.
- 네이버 전환 추적이 연결되지 않은 계정은 전환/매출 기반 오늘 해야 할 일 품질이 제한됩니다.

## 6. 생성된 표준 CSV 경로

- 생성 안 됨

## 7. 기존 AIMAOS 분석 파이프라인 연결 여부

- 대기: 표준 CSV가 생성되지 않아 실행하지 않았습니다.

## 8. 오늘 해야 할 일 생성 여부

- 대기: 기존 파이프라인 연결 후 확인합니다.
- 생성 건수: 확인 필요

## 9. 보고서 생성 여부

- 대기: 기존 파이프라인 연결 후 확인합니다.

보고서 경로:
- Markdown: 생성 안 됨
- TXT: 생성 안 됨
- Excel: 생성 안 됨

## 10. 다음 수정 필요사항

- API 호출 성공 후 전환/매출 필드가 비어 있으면 네이버 전환 추적 설정 여부를 계정별로 점검해야 합니다.
- 여러 광고주 Customer ID를 순회하는 대행사 계정 구조는 별도 목록 조회와 권한 검증이 필요합니다.
- stats 응답 구조가 계정 유형별로 다르면 `extract_stat_rows` 변환 규칙을 추가해야 합니다.

## 실행 증거

- 증거 폴더: C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad
- stats 시도 파일:
  - C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\stats_attempt_01_campaign_adgroup_rich.json
  - C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\stats_attempt_02_campaign_adgroup_basic.json
  - C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\stats_attempt_03_campaign_rich.json

## 전체 단계 결과

| 단계 | 상태 | 설명 | 증거 |
| --- | --- | --- | --- |
| Customer ID | 준비됨 | 환경 변수에서 Customer ID를 확인했습니다. | - |
| Access License | 준비됨 | 환경 변수에서 Access License를 확인했습니다. | - |
| Secret Key | 준비됨 | 환경 변수에서 Secret Key를 확인했습니다. | - |
| 캠페인 조회 | 성공 | 네이버 캠페인 조회 응답: HTTP 200, 조회 건수: 1 | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\campaigns.json |
| 광고그룹 조회 | 성공 | 네이버 광고그룹 조회 응답: HTTP 200, 조회 건수: 2 | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\adgroups.json |
| 키워드 조회 | 성공 | 광고그룹 ID 기준 키워드 조회 성공. 키워드 0건 조회. | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\keywords.json |
| 전일 성과 조회 | 성공 | 전일(2026-06-09) stats API 조회 성공. 성공 조합: 캠페인 반복 ids / rich fields | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\yesterday_stats.json |
| 노출/클릭/광고비 수집 | 확인 필요 | 응답은 성공했지만 기본 지표 필드 확인이 필요합니다. | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\yesterday_stats.json |
| 전환/매출/ROAS 수집 | 확인 필요 | 전환/매출/ROAS는 계정 추적 설정 또는 지원 필드에 따라 추가 확인이 필요합니다. | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\yesterday_stats.json |
| AIMAOS 표준 CSV 변환 | 실패 | stats 응답에서 표준 CSV로 변환할 행을 찾지 못했습니다. | C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\20260610_142203\naver_searchad\standard_csv_error.json |
| AIMAOS 기존 파이프라인 연결 | 대기 | 표준 CSV가 생성되지 않아 실행하지 않았습니다. | - |
| 오늘 해야 할 일 생성 | 대기 | 기존 파이프라인 연결 후 확인합니다. | - |
| 보고서 자동 생성 | 대기 | 기존 파이프라인 연결 후 확인합니다. | - |
| 대행사 계정 사용 가능 여부 | 조건부 확인 | 캠페인 또는 광고그룹 목록이 조회되면 해당 Customer ID 기준 접근 권한은 확인된 것으로 봅니다. 여러 광고주 접근 범위는 추가 Customer ID로 검증해야 합니다. | - |
| 광고주 데이터 조회 가능 여부 | 조건부 확인 | 캠페인/광고그룹/키워드 중 하나 이상 조회되면 광고주 데이터 접근 가능성이 높습니다. | - |
