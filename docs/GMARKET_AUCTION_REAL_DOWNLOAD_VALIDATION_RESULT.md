# G마켓/옥션 실제 리포트 다운로드 검증 결과

작성일: 2026-06-11

## 1. 검증 목적

이번 단계의 목표는 기능 추가가 아니라 실제 G마켓/옥션 광고 리포트가 다운로드되고 AIMAOS가 감지할 수 있는지 확인하는 것이다.

성공 기준은 다음과 같다.

- 광고센터 진입만으로 성공 처리하지 않는다.
- 실제 Excel 또는 CSV 리포트 파일이 다운로드 폴더에 생성되어야 한다.
- AIMAOS가 해당 파일을 감지해야 한다.
- 감지된 파일을 `raw_media_audit.py`로 진단해야 한다.
- 기존 분석 파이프라인, 오늘 해야 할 일, 보고서 생성까지 연결되어야 한다.

## 2. 수정 금지 영역 보존

이번 검증에서는 아래 영역을 수정하지 않았다.

- Rule Engine
- KPI 계산 로직
- 보고서 생성 로직
- 데이터 표준화 로직
- 컬럼 매핑 로직
- 오늘 해야 할 일 생성 로직
- UI 추가 개발

## 3. 실제 실행한 것

### 다운로드 폴더 확인

G마켓:

```text
data/collection_poc/marketplace/gmarket_legacy/downloads
```

옥션:

```text
data/collection_poc/marketplace/auction_legacy/downloads
```

결과:

- G마켓 감지 파일 수: 0
- 옥션 감지 파일 수: 0

### 전용 수집 브라우저 실행 시도

G마켓:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --open-profile gmarket_legacy --wait-seconds 60
```

옥션:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --open-profile auction_legacy --wait-seconds 60
```

결과:

- 현재 자동 실행 환경에서 `https://www.esmplus.com/` 접속이 `net::ERR_NETWORK_ACCESS_DENIED`로 차단됨
- 사용자 직접 로그인 단계까지 도달하지 못함
- 리포트 화면 진입, 기간 선택, 조회, 다운로드 버튼 검증은 진행하지 못함

## 4. 성공한 것

- 전용 수집 브라우저 실행 명령 확인
- G마켓/옥션 다운로드 폴더 확인
- 다운로드 파일 감지 로직 실행
- 실제 파일이 없으면 성공 처리하지 않는 기준 확인
- collection_log에 실패 결과 기록
- Data Status Center에서 G마켓/옥션을 최신 수집 성공으로 표시하지 않는 것 확인

## 5. 실패한 것

- 현재 자동 실행 환경에서 ESM 접속 실패
- 사용자 직접 로그인 단계 미도달
- 광고센터 리포트 화면 진입 미검증
- 기간 선택 가능 여부 미검증
- 조회 버튼 실행 가능 여부 미검증
- Excel/CSV 다운로드 미검증
- 실제 리포트 파일 생성 실패
- `raw_media_audit.py` 실제 파일 진단 미실행
- 기존 분석 파이프라인 연결 미실행
- 오늘 해야 할 일 생성 미검증
- 보고서 생성 미검증

## 6. 보류된 것

다음 항목은 실제 광고 집행 이력이 있는 계정에서 사용자가 직접 인증해야 검증 가능하다.

- G마켓/옥션 광고센터 로그인
- 광고주 계정 선택
- 최근 30~90일 리포트 조회
- Excel 또는 CSV 다운로드
- 다운로드 파일 감지
- raw_media_audit 연결
- 분석 파이프라인 연결
- 오늘 해야 할 일 생성
- 보고서 생성

## 7. 사용자 직접 확인이 필요한 것

1. 전용 수집 브라우저가 열린 상태에서 ESM 로그인이 가능한지 확인
2. 광고센터 리포트 메뉴까지 이동 가능한지 확인
3. 최근 30~90일 기간 선택이 가능한지 확인
4. 조회 버튼이 정상 동작하는지 확인
5. Excel 또는 CSV 다운로드 버튼이 있는지 확인
6. 다운로드 후 아래 폴더에 파일이 생성되는지 확인

G마켓:

```text
data\collection_poc\marketplace\gmarket_legacy\downloads
```

옥션:

```text
data\collection_poc\marketplace\auction_legacy\downloads
```

## 8. 다음 검증 조건

다운로드 검증을 성공시키려면 다음 조건이 필요하다.

1. 최근 30~90일 광고 집행 이력이 있는 G마켓/옥션 계정
2. 사용자가 직접 로그인 및 2차 인증 처리
3. 광고센터 리포트 화면 진입
4. 조회 가능한 성과 데이터 존재
5. Excel 또는 CSV 다운로드 실행
6. 다운로드 파일이 전용 다운로드 폴더에 저장됨

## 9. 생성된 실제 파일 경로

실제 광고 리포트 파일:

- G마켓: 없음
- 옥션: 없음

검증 증거 파일:

```text
data/collection_poc/marketplace/gmarket_legacy/download_validation_20260611_105703.json
data/collection_poc/marketplace/auction_legacy/download_validation_20260611_105703.json
```

## 10. collection_log 기록 여부

기록 완료.

G마켓:

```text
collection_id: gmarket_download_20260611_105703
status: failed
error_code: DOWNLOAD_FILE_NOT_FOUND
file_count: 0
rows_collected: 0
```

옥션:

```text
collection_id: auction_download_20260611_105703
status: failed
error_code: DOWNLOAD_FILE_NOT_FOUND
file_count: 0
rows_collected: 0
```

실패 사유:

```text
전용 수집 브라우저에서 실제 리포트 다운로드 파일이 감지되지 않았습니다.
현재 자동 실행 환경에서는 ESM 접속이 네트워크 제한으로 막혔습니다.
```

## 11. Data Status Center 반영 여부

반영 확인.

브라우저에서 확인한 상태:

- Data Status Center 표시됨
- G마켓 상태: 연결 안됨
- 옥션 상태: 연결 안됨
- G마켓 마지막 확인: 2026-06-11 10:57
- 옥션 마지막 확인: 2026-06-11 10:57
- 마지막 실패 시각 표시됨
- 실패 원인 표시됨

정상 판단:

실제 다운로드 파일이 없으므로 G마켓/옥션을 수집 성공 또는 최신 상태로 표시하지 않는 것이 맞다.

## 12. 최종 판단

이번 검증은 다운로드 수집 성공이 아니다.

현재 판정:

```text
실패 / 사용자 직접 인증 필요 / 실제 파일 다운로드 검증 대기
```

다음 단계의 성공 기준:

```text
다운로드 파일 생성 + AIMAOS 감지 + raw_media_audit 진단 + 기존 분석 파이프라인 연결
```

