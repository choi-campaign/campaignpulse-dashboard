# 네이버 API 날짜 범위 성과 조회 결과

상태 갱신: 2026-06-20

## 1. 문서 해석

2026-06-11의 Codex 실행 환경에서는 외부 소켓 제한으로 `NETWORK_ERROR`가 발생했다. 이 기록은 당시 실행 환경의 실패이며 네이버 API 최종 판정이 아니다.

이후 로컬 PowerShell에서 인증, 캠페인·광고그룹·키워드·stats 조회가 성공했으므로 네이버 API 수집은 기술 검증 성공으로 분류한다.

## 2. 날짜 범위 입력

지원 방식:

- 환경값 `AIMAOS_POC_START_DATE`
- 환경값 `AIMAOS_POC_END_DATE`
- 실행 인자 `--start-date YYYY-MM-DD`
- 실행 인자 `--end-date YYYY-MM-DD`

기본값은 실행일 기준 전일까지 최근 30일이다. 시작일과 종료일이 반대로 입력되면 자동으로 순서를 바꾼다.
종료일이 오늘 이후면 조회 가능한 전일로 조정한다. 입력 범위 전체가 미래라면 전일 하루로 축소하고 경고를 기록한다.

## 3. 확인된 결과

- 기간 지정 stats 요청 생성 성공
- 미래 날짜 범위의 안전한 전일 보정
- 캠페인 반복 `ids` 사용
- rich fields JSON 직렬화
- `response.data` 중첩·빈 배열 파싱
- 표준 CSV 생성
- 기존 분석 파이프라인 연결
- 0 지표 방어 적용
- 오늘 해야 할 일과 보고서 생성

## 4. 아직 부족한 증거

- 실제 양수 성과 행이 있는 날짜 범위의 `response.data`
- 광고그룹 단위 stats 안정성
- 키워드가 존재하는 계정의 키워드 단위 stats
- 전환·매출·ROAS 필드가 실제 값으로 반환되는 계정

## 5. 실행 명령

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.data_collection_poc --start-date 2026-06-01 --end-date 2026-06-07
```

실제 API 값은 `.env`에만 두고 GitHub에 올리지 않는다.

## 6. 현재 판정

```text
API 인증과 조회 구조: 기술 검증 성공
빈 응답 표준 CSV 처리: 성공
실제 양수 성과 행: 추가 검증 필요
운영 자동 수집: 스케줄·재시도·보안 설계 필요
```
