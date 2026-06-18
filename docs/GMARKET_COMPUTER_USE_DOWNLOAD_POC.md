# G마켓 Computer Use 다운로드 POC

작성일: 2026-06-12 00:02:58

## 1. 이번 작업 목적

G마켓 파워클릭 G 일별 리포트가 실제 Excel 또는 CSV 파일로 생성되고 AIMAOS 다운로드 폴더에서 감지되는지 검증한다.

## 2. 작업 범위 제한

- 이번 구현 범위는 G마켓 파워클릭 G 일별 POC 1개로 제한
- 옥션, 11번가, 쿠팡, Google, Meta, Kakao 구현 없음
- 기존 분석/보고/Rule Engine/UI 로직 수정 없음

## 3. API 우선 / Computer Use 보조 원칙

공식 API가 가능한 매체는 API를 우선한다. G마켓처럼 API 활용이 제한적인 매체는 사용자가 직접 인증한 화면에서 리포트 다운로드를 보조하는 방식으로 검증한다.

## 4. 실제 수정한 파일

- `aimaos/collectors/marketplace/gmarket_computer_use_download_poc.py`
- `docs/GMARKET_COMPUTER_USE_DOWNLOAD_POC.md`
- `docs/COMPUTER_USE_CONNECTOR_STRATEGY.md`

## 5. 새로 추가한 파일

- `data\collection_poc\marketplace\gmarket_legacy\gmarket_computer_use_download_poc_20260612_000233.json`

## 6. Computer Use 실제 사용 가능 여부

- 인앱 브라우저 기반 화면 확인 가능 여부: 가능
- 대체 전용 브라우저 실행 가능 여부: 제한 또는 실패

## 7. 확인한 리포트 타입

- G마켓 파워클릭 G 일별

## 8. 다운로드 파일

- 다운로드 폴더: `data\collection_poc\marketplace\gmarket_legacy\downloads`
- 감지 파일 수: 0
- 선택 파일: `-`
- 파일 크기: 0 bytes

## 9. 후속 검증

- raw_media_audit.py 실행 여부: not_run
- 분석 파이프라인 연결 여부: not_run
- 오늘 해야 할 일 생성 확인: 미실행
- 보고서 생성 여부: 미실행

## 10. collection_log 기록 내용

- collection_id: `gmarket_computer_use_20260612_000233`
- status: `blocked_by_environment`
- error_code: `NETWORK_ACCESS_DENIED`
- error_message: 광고센터 접속이 현재 실행 환경에서 제한되었습니다. 사용자 실제 PC 또는 접속 가능한 브라우저 환경에서 재검증이 필요합니다.

## 11. Data Status Center 반영 여부

collection_log와 증거 파일은 기록되었다. Data Status Center는 다운로드 파일이 없으면 G마켓을 최신 수집 성공으로 표시하지 않아야 한다.

## 12. 실패 원인

- 광고센터 접속이 현재 실행 환경에서 제한되었습니다. 사용자 실제 PC 또는 접속 가능한 브라우저 환경에서 재검증이 필요합니다.

## 13. 다음 검증 조건

1. 사용자가 직접 ESM에 로그인
2. G마켓 광고센터 파워클릭 리포트 화면 진입
3. G 일별 선택
4. 최근 30일 또는 90일 조회
5. 조회 결과 1건 이상 확인
6. Excel 또는 CSV 다운로드
7. AIMAOS 다운로드 폴더에서 파일 감지

## 14. 보안/정책 리스크

- 비밀번호 저장 없음
- 로그인 자동 입력 없음
- 2차 인증 우회 없음
- 캡차 우회 없음
- 광고비/입찰/예산/상품 수정 없음

## 15. 최종 판정

`blocked_by_environment`

## 16. 실제 검증 요약

이번 검증은 G마켓 파워클릭 G 일별 리포트 다운로드 POC 1개로 제한했다.

실제 확인 결과:

- 인앱 브라우저 기반 Computer Use: ESM 로그인 화면 접근 가능
- 확인 URL: `https://signin.esmplus.com/login`
- 상태: 사용자 직접 로그인 또는 인증 필요
- 로컬 전용 Playwright 브라우저: `net::ERR_NETWORK_ACCESS_DENIED`로 접속 제한
- 다운로드 폴더 감지 파일 수: 0
- raw_media_audit.py: 파일 없음으로 미실행
- 기존 분석 파이프라인: 파일 없음으로 미실행
- 오늘 해야 할 일 생성: 파일 없음으로 미검증
- 보고서 생성: 파일 없음으로 미검증

## 17. collection_log 기록

기록된 주요 시도:

```text
gmarket_computer_use_20260612_000218
status: failed
error_code: DOWNLOAD_FILE_NOT_FOUND
```

```text
gmarket_computer_use_20260612_000233
status: blocked_by_environment
error_code: NETWORK_ACCESS_DENIED
```

```text
gmarket_computer_use_20260612_000404
status: needs_user_authentication
error_code: USER_AUTH_REQUIRED
```

## 18. 최종 판정

```text
needs_user_authentication
```

사유:

Computer Use 기반 인앱 브라우저에서는 ESM 로그인 화면까지 접근했지만, 사용자가 직접 로그인 또는 인증을 완료해야 다음 단계인 파워클릭 G 일별 리포트 조회와 다운로드 검증을 계속할 수 있다.

주의:

이번 단계에서는 실제 Excel/CSV 파일이 생성되지 않았으므로 success가 아니다.

다음 성공 조건:

1. 사용자가 직접 로그인 및 인증 완료
2. G마켓 파워클릭 G 일별 리포트 화면 진입
3. 최근 30일 또는 90일 조회
4. Excel 또는 CSV 다운로드
5. AIMAOS 다운로드 폴더에서 파일 감지
6. raw_media_audit.py 진단
7. 기존 분석 파이프라인 연결
8. 오늘 해야 할 일 생성 확인
9. 보고서 생성 확인
