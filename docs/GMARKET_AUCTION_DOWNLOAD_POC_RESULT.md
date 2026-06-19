# G마켓/옥션 반자동 리포트 수집 POC 결과

## 2026-06-19 수집 로그 안정화

- `--open-profile`로 사용자가 직접 실행한 매체만 `collection_log`에 기록합니다.
- 광고센터 진입 성공은 데이터 수집 성공으로 기록하지 않습니다.
- 실제 리포트 파일이 감지되고 분석·보고서 생성까지 완료된 경우에만 `success`로 기록합니다.
- 파일이 감지되지 않으면 `failed / DOWNLOAD_FILE_NOT_FOUND`로 기록하며 Data Status Center에 마지막 실패 시각과 원인이 표시됩니다.
- 인증 필요 또는 실행 환경 차단은 `error_code`와 사용자용 설명으로 보존합니다.

작성일: 2026-06-11 10:56:29

## 0. 최신 실제 테스트 결과

- G마켓/옥션 전용 수집 브라우저 실행: 성공
- ESM 로그인: 성공
- 광고센터 진입: 성공
- 새 창 처리: 성공
- 다운로드 검증: 최근 광고 데이터 없음으로 보류
- 다음 검증 조건: 최근 광고 집행 이력이 있는 광고주 계정 또는 조회 기간 필요

## 1. Playwright 설치/실행 상태

- Playwright 패키지: 설치됨
- 내장 Chromium 설치: 프로젝트 외부 AppData 권한 제한 및 네트워크 제한으로 미완료
- 기존 Chrome/Edge 사용 가능 여부: 가능
- 사용 브라우저 실행 파일: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- 전용 수집 브라우저 실행 테스트: 성공
- 실행 상세: Dedicated collection browser launched.

## 2. G마켓 POC 결과

- profile: `gmarket_legacy`
- 로그인 URL 상태: 확인됨
- 리포트 URL 상태: 미확보
- 다운로드 폴더: `data\collection_poc\marketplace\gmarket_legacy\downloads`
- 브라우저 프로필: `data\collection_poc\marketplace\gmarket_legacy\browser_profile`

| 점검 항목 | 상태 | 내용 |
| --- | --- | --- |
| 전용 다운로드 폴더 | 성공 | data\collection_poc\marketplace\gmarket_legacy\downloads |
| 전용 브라우저 프로필 | 성공 | data\collection_poc\marketplace\gmarket_legacy\browser_profile |
| Playwright 패키지 | 성공 | 설치됨 |
| Chrome/Edge 실행 파일 | 성공 | C:\Program Files\Google\Chrome\Application\chrome.exe |
| 수집 브라우저 실행 | 성공 | Dedicated collection browser launched. |
| 로그인 시작 URL | 준비됨 | 환경값 또는 기본값 확인됨 |
| 리포트 시작 URL | 정보 필요 | AIMAOS_POC_GMARKET_REPORT_URL 설정 필요 |
| 광고센터 진입 | 미실행 | 리포트 URL 미확보로 실제 화면 검증 전입니다. |
| 기간 선택 | 미실행 | 리포트 화면 확인 후 selector/profile 작성이 필요합니다. |
| Excel/CSV 다운로드 | 미실행 | 사용자 로그인 세션에서 실제 버튼 확인이 필요합니다. |
| 다운로드 파일 감지 | 미실행 | 아직 실제 다운로드 파일이 없습니다. |

## 3. 옥션 POC 결과

- profile: `auction_legacy`
- 로그인 URL 상태: 확인됨
- 리포트 URL 상태: 미확보
- 다운로드 폴더: `data\collection_poc\marketplace\auction_legacy\downloads`
- 브라우저 프로필: `data\collection_poc\marketplace\auction_legacy\browser_profile`

| 점검 항목 | 상태 | 내용 |
| --- | --- | --- |
| 전용 다운로드 폴더 | 성공 | data\collection_poc\marketplace\auction_legacy\downloads |
| 전용 브라우저 프로필 | 성공 | data\collection_poc\marketplace\auction_legacy\browser_profile |
| Playwright 패키지 | 성공 | 설치됨 |
| Chrome/Edge 실행 파일 | 성공 | C:\Program Files\Google\Chrome\Application\chrome.exe |
| 수집 브라우저 실행 | 성공 | Dedicated collection browser launched. |
| 로그인 시작 URL | 준비됨 | 환경값 또는 기본값 확인됨 |
| 리포트 시작 URL | 정보 필요 | AIMAOS_POC_AUCTION_REPORT_URL 설정 필요 |
| 광고센터 진입 | 미실행 | 리포트 URL 미확보로 실제 화면 검증 전입니다. |
| 기간 선택 | 미실행 | 리포트 화면 확인 후 selector/profile 작성이 필요합니다. |
| Excel/CSV 다운로드 | 미실행 | 사용자 로그인 세션에서 실제 버튼 확인이 필요합니다. |
| 다운로드 파일 감지 | 미실행 | 아직 실제 다운로드 파일이 없습니다. |

## 4. 11번가/쿠팡 보류 사유

- 11번가: 실제 광고 리포트 URL, 로그인 흐름, 파일 구조가 아직 확인되지 않아 구조만 준비했습니다.
- 쿠팡: 인증/보안 정책 리스크가 커서 이번 단계에서는 자동화 결론을 내리지 않습니다.
- 두 매체 모두 실제 화면 확인 전까지는 브라우저 자동 조작을 진행하지 않습니다.

## 5. 사용자 행동 수

- 현재 검증 상태: 실제 광고센터 로그인 단계 전입니다.
- 목표 행동 수: 최초 연결 시 사용자가 직접 로그인/2차 인증 1회, 이후 리포트 수집은 AIMAOS가 처리.
- 현재 필요 행동: G마켓/옥션 리포트 URL 제공 또는 전용 수집 브라우저에서 직접 로그인 후 리포트 화면 확인.

## 6. 캡차/2차 인증 발생 여부

- 실제 로그인 화면을 통과하지 않았으므로 발생 여부는 아직 판단하지 않았습니다.
- 캡차와 2차 인증이 발생하면 사용자가 직접 처리해야 합니다.
- AIMAOS는 캡차 우회, 2차 인증 우회, 비밀번호 저장을 하지 않습니다.

## 7. 다운로드 성공 여부

- G마켓: 미검증
- 옥션: 미검증

## 8. 다운로드 파일 경로

- G마켓: 아직 감지된 다운로드 파일 없음. 감지 폴더 `data\collection_poc\marketplace\gmarket_legacy\downloads`
- 옥션: 아직 감지된 다운로드 파일 없음. 감지 폴더 `data\collection_poc\marketplace\auction_legacy\downloads`

## 9. raw_media_audit 연결

- G마켓: not_run
- 옥션: not_run

## 10. 분석 파이프라인 연결

- G마켓: not_run
- 옥션: not_run

## 11. 오늘 해야 할 일 생성

- G마켓: 실제 다운로드 파일이 없어 아직 생성 여부 미검증
- 옥션: 실제 다운로드 파일이 없어 아직 생성 여부 미검증

## 12. 보고서 생성

- G마켓: 실제 다운로드 파일이 없어 아직 보고서 생성 미검증
- 옥션: 실제 다운로드 파일이 없어 아직 보고서 생성 미검증

## 13. legacy/next profile 필요성

- G마켓/옥션은 기존 광고센터와 신규 광고센터 전환 가능성을 분리해서 관리해야 합니다.
- 현재는 `gmarket_legacy`, `auction_legacy` profile을 우선 검증 대상으로 둡니다.
- 신규 광고센터 URL과 리포트 파일 구조가 확인되면 `gmarket_next`, `auction_next` profile에 selector와 다운로드 규칙을 별도 기록합니다.
- 화면 selector는 코드 본문에 고정하지 않고 profile 파일에만 둡니다.

## 14. 사업성 판단

조건부 가능: 전용 수집 브라우저와 다운로드 감지 구조는 준비됐지만, 실제 광고센터 로그인/다운로드는 아직 계정 세션에서 검증해야 합니다.

## 15. 다음 우선순위

1. 실제 G마켓/옥션 광고센터 리포트 URL을 환경값으로 등록합니다.
2. 전용 수집 브라우저에서 사용자가 직접 로그인하고 2차 인증을 처리합니다.
3. 리포트 화면의 기간 선택과 다운로드 버튼 selector를 legacy profile에 기록합니다.
4. 다운로드 파일이 감지되면 raw_media_audit와 기존 분석 파이프라인 연결을 재검증합니다.
5. 성공 파일 기준으로 오늘 해야 할 일과 보고서 생성까지 한 번에 확인합니다.

## 16. 최종 결론

조건부 가능. 실행 환경은 통과했으며, 실제 리포트 URL과 로그인 세션에서 다운로드 성공 여부를 다음 단계에서 확인해야 합니다.
