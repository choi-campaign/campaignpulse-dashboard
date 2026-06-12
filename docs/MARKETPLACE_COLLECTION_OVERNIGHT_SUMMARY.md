# AIMAOS Marketplace Collection Overnight Summary

작성일: 2026-06-11

## 1. 오늘 밤 작업 요약

이번 작업의 기준은 UI 개선이 아니라 광고주가 파일을 직접 다운로드/업로드하지 않아도 되는 구조를 만드는 것이었습니다.

실행 중심으로 다음을 진행했습니다.

- G마켓/옥션 광고센터 진입 성공 상태를 문서에 반영
- G마켓/옥션 다운로드 검증 보류 사유 정리
- 전용 수집 브라우저, 전용 profile, 전용 다운로드 폴더 구조 유지
- 새 탭/팝업 감지 구조 보강
- 광고센터 진입만 검증하는 명령 추가
- 11번가 애드오피스 profile 준비
- 쿠팡 광고 profile 준비
- Command Center 사이드바 메뉴 UI 개선
- 전체 Python 컴파일 점검
- 네이버 POC 명령 재실행
- G마켓/옥션/11번가/쿠팡 진입 POC 명령 실행

## 2. 변경 파일 목록

### 코드

- `aimaos/app/streamlit_app.py`
- `aimaos/collectors/marketplace/browser_session.py`
- `aimaos/collectors/marketplace/marketplace_collection_poc.py`
- `aimaos/collectors/marketplace/profiles/elevenst_adoffice.py`
- `aimaos/collectors/marketplace/profiles/coupang_ads.py`

### 문서

- `docs/GMARKET_AUCTION_DOWNLOAD_POC_RESULT.md`
- `docs/GMARKET_AUCTION_AD_CENTER_ENTRY_POC.md`
- `docs/ELEVENST_ADOFFICE_COLLECTION_POC.md`
- `docs/COUPANG_ADS_COLLECTION_POC.md`
- `docs/MARKETPLACE_COLLECTION_OVERNIGHT_SUMMARY.md`

### 증거 파일

- `data/collection_poc/marketplace/gmarket_legacy/ad_center_entry_20260611_032336.json`
- `data/collection_poc/marketplace/auction_legacy/ad_center_entry_20260611_032334.json`
- `data/collection_poc/marketplace/11st_adoffice/ad_center_entry_20260611_032337.json`
- `data/collection_poc/marketplace/coupang_ads/ad_center_entry_20260611_032335.json`

## 3. G마켓 현재 상태

| 항목 | 상태 |
| --- | --- |
| 전용 수집 브라우저 | 성공 |
| ESM 로그인 | 성공 |
| 광고센터 진입 | 성공 |
| 새 창 처리 | 성공 |
| 리포트 메뉴 진입 | 광고 데이터 있는 계정으로 재검증 필요 |
| 기간 선택 | 미검증 |
| 조회 버튼 | 미검증 |
| 다운로드 버튼 | 미검증 |
| 다운로드 파일 생성 | 미검증 |
| 파일 자동 감지 | 미검증 |
| 분석 파이프라인 연결 | 다운로드 파일 확보 후 검증 |

판단: 조건부 가능.

## 4. 옥션 현재 상태

| 항목 | 상태 |
| --- | --- |
| 전용 수집 브라우저 | 성공 |
| ESM 로그인 | 성공 |
| 광고센터 진입 | 성공 |
| 새 창 처리 | 성공 |
| 리포트 메뉴 진입 | 광고 데이터 있는 계정으로 재검증 필요 |
| 기간 선택 | 미검증 |
| 조회 버튼 | 미검증 |
| 다운로드 버튼 | 미검증 |
| 다운로드 파일 생성 | 미검증 |
| 파일 자동 감지 | 미검증 |
| 분석 파이프라인 연결 | 다운로드 파일 확보 후 검증 |

판단: 조건부 가능.

## 5. 11번가 현재 상태

| 항목 | 상태 |
| --- | --- |
| 공식 진입 URL | `https://adoffice.11st.co.kr/` |
| AIMAOS profile | 준비 |
| 전용 브라우저 구조 | 준비 |
| 로그인 | 미검증 |
| 광고주 전환 | 미검증 |
| 리포트 메뉴 | 미검증 |
| 다운로드 구조 | 미검증 |
| 파일 구조 | 미검증 |

판단: POC 준비 완료, 실제 계정 검증 필요.

## 6. 쿠팡 현재 상태

| 항목 | 상태 |
| --- | --- |
| 광고센터 URL | `https://advertising.coupang.com/` |
| 광고 정보 사이트 | `https://ads.coupang.com/` |
| AIMAOS profile | 준비 |
| 전용 브라우저 구조 | 준비 |
| 로그인 | 미검증 |
| 광고 리포트 위치 | 미검증 |
| 다운로드 구조 | 미검증 |
| 보안 리스크 | 높음 |

판단: 위험 매체. 단기 MVP 우선순위는 낮음.

## 7. 사이드바 개선 내용

- 메뉴 앞 도형 기호 제거
- 메뉴 글씨 확대
- 클릭 영역 확대
- 메뉴 간격 확대
- 선택 메뉴 카드 강조
- 오늘 브리핑/데이터 상태 카드 유지
- 메뉴 전환 확인 완료

확인한 메뉴:

- 오늘 해야 할 일
- 운영 현황
- 광고 분석
- 쇼핑몰 분석
- 보고서 센터
- 채널 관리
- 설정

## 8. 실제로 실행한 것

```powershell
.\.venv\Scripts\python.exe -m compileall aimaos
```

결과: 성공.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.data_collection_poc
```

결과: 성공. `docs/DATA_COLLECTION_POC_REPORT.md` 갱신.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc
```

결과: 성공. `docs/GMARKET_AUCTION_DOWNLOAD_POC_RESULT.md` 갱신.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --wait-seconds 0
```

결과: 실행됨. 자동 실행 환경에서는 외부 URL 이동이 네트워크 정책으로 제한됨.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile auction_legacy --wait-seconds 0
```

결과: 실행됨. 자동 실행 환경에서는 외부 URL 이동이 네트워크 정책으로 제한됨.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile 11st_adoffice --wait-seconds 0
```

결과: 실행됨. 구조 준비 증거 생성.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile coupang_ads --wait-seconds 0
```

결과: 실행됨. 구조 준비 증거 생성.

## 9. 문서만 있고 실행하지 못한 것

- G마켓/옥션 실제 리포트 다운로드
- G마켓/옥션 다운로드 파일 자동 감지
- G마켓/옥션 다운로드 파일의 `raw_media_audit.py` 연결
- G마켓/옥션 다운로드 파일의 분석 파이프라인 연결
- 11번가 실제 계정 로그인
- 11번가 리포트 다운로드
- 쿠팡 실제 계정 로그인
- 쿠팡 리포트 다운로드

이 항목들은 문서 정리가 아니라 실제 광고 데이터가 있는 계정이 필요해서 보류됐습니다.

## 10. 남은 치명 문제

1. G마켓/옥션 다운로드 파일 생성이 아직 검증되지 않았습니다.
2. 광고 데이터가 없는 계정에서는 수집 성공 여부를 판단할 수 없습니다.
3. 다운로드 파일이 없으면 광고주 파일 업로드 제거 목표를 아직 달성했다고 볼 수 없습니다.

## 11. 남은 보통 문제

1. 자동 실행 환경에서는 외부 광고센터 URL 이동이 제한됩니다.
2. G마켓/옥션 신규 광고센터 전환 시 selector/profile을 다시 잡아야 합니다.
3. 11번가 파일 구조가 아직 없습니다.
4. 쿠팡은 보안 리스크가 높아 별도 검토가 필요합니다.
5. 세션 유지 방식은 보안 검토 전까지 구현하지 않았습니다.

## 12. 다음 실행 명령

G마켓 실제 검증:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --wait-seconds 300
```

옥션 실제 검증:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile auction_legacy --wait-seconds 300
```

11번가 구조 검증:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile 11st_adoffice --wait-seconds 300
```

쿠팡 구조 검증:

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile coupang_ads --wait-seconds 300
```

## 13. 다음 사용자가 해야 할 행동

1. 최근 광고 집행 데이터가 있는 G마켓 또는 옥션 광고주 계정을 준비합니다.
2. 전용 수집 브라우저에서 로그인합니다.
3. 광고센터 리포트 메뉴로 이동합니다.
4. 최근 30일 또는 90일 기간을 선택합니다.
5. 조회 결과가 있는지 확인합니다.
6. 다운로드 버튼이 활성화되는지 확인합니다.
7. 다운로드된 파일이 AIMAOS 전용 다운로드 폴더에 생성되는지 확인합니다.
8. 파일이 생기면 `marketplace_collection_poc`를 다시 실행해 자동 감지와 분석 연결을 확인합니다.

## 14. 사업성 판단

| 질문 | 판단 |
| --- | --- |
| G마켓/옥션은 주 1회 반자동 수집이 가능한가? | 조건부 가능 |
| 11번가는 POC 준비가 되었는가? | YES |
| 쿠팡은 위험 매체인가? | YES |
| 광고주가 파일 다운로드를 안 해도 되는가? | 아직 NO |
| 광고주가 파일 업로드를 안 해도 되는가? | 아직 NO |
| 현재 상태가 실제 판매 가능한 MVP에 가까워졌는가? | YES, 수집 병목이 더 명확해짐 |

최종 사업성 판단: 조건부 가능.

## 15. 가장 큰 리스크

AIMAOS 판매를 막는 가장 큰 병목은 여전히 광고주가 데이터를 얼마나 귀찮지 않게 가져올 수 있는가입니다.

현재 분석, Rule Engine, 보고서 생성은 작동합니다. 남은 핵심 병목은 G마켓/옥션에서 실제 리포트 파일을 자동으로 받아 AIMAOS 분석 파이프라인까지 연결하는 것입니다.

## 16. 내일의 우선순위

1. 광고 데이터가 있는 G마켓/옥션 계정으로 리포트 다운로드 성공 여부를 확인합니다.
2. 다운로드 파일이 전용 폴더에 감지되는지 확인합니다.
3. 감지 파일을 `raw_media_audit.py`로 진단합니다.
4. 기존 분석 파이프라인에 연결합니다.
5. 오늘 해야 할 일과 보고서 생성까지 이어지는지 확인합니다.
