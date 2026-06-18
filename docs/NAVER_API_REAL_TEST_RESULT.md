# 네이버 검색광고 API 실제 연결 테스트 결과

작성일: 2026-06-10  
상태 갱신: 2026-06-19

## 최종 판정

**기술 검증 성공**

초기 Codex 실행 환경에서는 네트워크 소켓 제한으로 `NETWORK_ERROR`가 발생했지만, 로컬 PowerShell 재실행에서는 네이버 API 인증과 실제 조회가 성공했다.

따라서 네이버 API 연동 가능성을 실패로 분류하지 않는다.

## 실제 성공 항목

| 항목 | 결과 |
| --- | --- |
| Customer ID 인식 | 성공 |
| Access License 인식 | 성공 |
| Secret Key 인식 | 성공 |
| 캠페인 조회 | HTTP 200, 1건 |
| 광고그룹 조회 | HTTP 200, 2건 |
| 키워드 조회 | 성공, 0건 |
| stats 조회 | 성공 |
| 성공 조합 | 캠페인 반복 `ids` / rich fields |
| 표준 CSV 생성 | 성공 |
| 기존 분석 파이프라인 | 성공 |
| 오늘 해야 할 일 | 성공 |
| Excel/Markdown/TXT 보고서 | 성공 |

## 실제 증거

- `data/collection_poc/20260610_142203/naver_searchad/campaigns.json`
- `data/collection_poc/20260610_142203/naver_searchad/adgroups.json`
- `data/collection_poc/20260610_142203/naver_searchad/keywords.json`
- `data/collection_poc/20260610_142203/naver_searchad/yesterday_stats.json`
- `data/collection_poc/20260610_142203/naver_searchad/naver_searchad_standard.csv`

## stats 응답 상태

API 호출은 성공했지만 검증한 전일의 `response.data`는 빈 배열이었다.

이 상태는 인증 실패가 아니다. 해당 기간에 반환할 성과 행이 없었다는 의미다.

빈 배열은 요청 캠페인 ID 기준 0 지표 표준 행으로 변환했으며, AIMAOS는 이 데이터를 실제 운영 성과로 오해하지 않도록 `데이터 부족 / 최신 성과 확인 필요`로 처리한다.

## 현재 수집 가능성

- 캠페인/광고그룹/키워드 구조 조회: 가능
- 기간별 stats 요청: 가능
- 노출/클릭/광고비: 응답 행이 있는 기간에서 수집 가능
- 전환/매출/ROAS: 계정의 전환 추적 설정과 응답 필드에 따라 조건부
- 대행사 다계정 순회: Customer ID 목록과 접근 범위 추가 검증 필요

## 남은 검증

1. 실제 성과가 존재하는 날짜 범위의 `response.data` 행 확보
2. 광고그룹 단위 stats 안정성 확인
3. 키워드가 존재하는 계정의 키워드 단위 stats 확인
4. 대행사 계정의 여러 Customer ID 순회
5. 호출량 제한과 실패 재시도 정책

## 실행 명령

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.data_collection_poc --start-date 2026-06-01 --end-date 2026-06-07
```

API 키와 실제 광고주 정보는 `.env`에서만 관리하며 GitHub에 올리지 않는다.
