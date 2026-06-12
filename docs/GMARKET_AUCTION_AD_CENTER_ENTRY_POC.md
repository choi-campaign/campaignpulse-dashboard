# 옥션 광고센터 진입 POC

작성일: 2026-06-11 04:22:57

## 1. 현재 실제 테스트 결과 반영

- 전용 수집 브라우저 실행: 성공
- ESM 로그인: 성공
- 광고센터 진입: 성공
- 새 창 처리: 성공
- 리포트 다운로드: 최근 광고 데이터 없음으로 보류
- 이번 단계 결론: 다운로드 자동화 전, 광고 집행 데이터가 있는 계정 또는 기간으로 재검증해야 합니다.

## 2. 멈춘 단계

- 대상 profile: `auction_legacy`
- 대상 매체: 옥션
- 시작 URL: `https://www.esmplus.com`
- 관찰 상태: failed
- 새 페이지/팝업 감지 수: 1
- 관찰 증거 파일: `C:\Users\admin\Documents\Codex\2026-06-07\aimaos-ai-marketing-association-operating-system\outputs\aimaos_mvp\data\collection_poc\marketplace\auction_legacy\ad_center_entry_20260611_042257.json`

## 3. 가능한 원인 후보

| 원인 후보 | 현재 판단 | 확인 방법 |
| --- | --- | --- |
| 광고센터 URL 문제 | 가능성 있음 | ESM 로그인 후 광고센터 버튼의 실제 이동 URL을 확인합니다. |
| 새 창/팝업 전환 문제 | 가능성 있음 | 광고센터 버튼 클릭 시 새 탭 또는 새 창이 열리는지 확인합니다. |
| 로그인 세션 전달 문제 | 가능성 있음 | 로그인 완료 탭과 광고센터 탭의 도메인이 다른지 확인합니다. |
| 대행사 권한 문제 | 가능성 있음 | 동일 계정으로 일반 브라우저에서 광고주 광고센터 진입이 가능한지 확인합니다. |
| 별도 도메인/SSO 사용 | 가능성 있음 | 이동 URL의 도메인과 인증 쿠키 적용 범위를 확인합니다. |
| 자동화 브라우저 차단 가능성 | 가능성 있음 | 일반 Chrome과 전용 수집 브라우저의 동작 차이를 비교합니다. |

## 4. 사용자가 확인할 내용

1. 전용 수집 브라우저에서 ESM에 로그인합니다.
2. 광고센터 버튼을 직접 클릭합니다.
3. 같은 탭에서 URL이 바뀌는지 확인합니다.
4. 새 탭 또는 새 창이 열리는지 확인합니다.
5. 광고센터 화면까지 들어가면 그 URL을 복사해 `AIMAOS_POC_GMARKET_REPORT_URL` 또는 `AIMAOS_POC_AUCTION_REPORT_URL`에 넣습니다.
6. 광고센터 진입이 안 되면 화면에 표시되는 안내 문구 또는 권한 오류를 기록합니다.

## 5. 새 탭/팝업 감지 보강

- Playwright persistent browser context에서 `context.on('page')` 이벤트를 감지하도록 보강했습니다.
- 개별 페이지의 `popup` 이벤트도 기록합니다.
- 실행 중 관찰된 모든 탭의 URL과 제목을 JSON 증거 파일로 저장합니다.
- 다운로드는 아직 시도하지 않습니다.

## 6. 광고센터 URL 직접 이동 옵션

- 환경변수 방식 유지:
  - `AIMAOS_POC_GMARKET_REPORT_URL`
  - `AIMAOS_POC_AUCTION_REPORT_URL`
- 실행 인자 방식 추가:
  - `--entry-url "광고센터_URL"`

## 7. 광고센터 진입만 검증하는 명령

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --wait-seconds 300
```

옥션은 아래처럼 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile auction_legacy --wait-seconds 300
```

광고센터 URL을 직접 넣어 확인할 때는 아래처럼 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m aimaos.collectors.marketplace.marketplace_collection_poc --entry-check-profile gmarket_legacy --entry-url "광고센터_URL" --wait-seconds 300
```

## 8. 관찰된 페이지

| 구분 | 번호 | URL | 제목 |
| --- | --- | --- | --- |
| new_page | 1 | `about:blank` | Loading https://www.esmplus.com/ |

## 9. 자동 실행 환경 한계

- 자동 관찰 상태: failed
- 자동 관찰 상세: Page.goto: net::ERR_NETWORK_ACCESS_DENIED at https://www.esmplus.com/
Call log:
  - navigating to "https://www.esmplus.com/", waiting until "load"

- Codex 실행 환경에서는 외부 광고센터 URL 이동이 네트워크 정책으로 막힐 수 있습니다.
- 따라서 최종 판단은 사용자가 전용 수집 브라우저에서 직접 인증한 실제 테스트 결과를 우선합니다.
- 자동 관찰 증거는 탭/팝업 감지 구조와 시작 URL 기록 용도로 사용합니다.

## 10. 다음 판단 기준

- 성공: 전용 수집 브라우저에서 광고센터 화면 진입 URL이 확인됨
- 부분 성공: 새 창/팝업은 감지됐지만 권한 또는 SSO 문제로 진입 실패
- 실패: 로그인 후에도 광고센터 버튼 이동이 감지되지 않음

## 11. 보안 원칙

- 광고주 비밀번호 저장 금지
- 캡차 우회 금지
- 2차 인증 우회 금지
- 사용자가 직접 인증 처리
- AIMAOS는 인증 이후 반복 이동과 감지만 담당

## 12. 현재 결론

조건부 가능입니다. 전용 브라우저, ESM 로그인, 광고센터 진입, 새 창 처리는 통과했습니다. 다만 최근 광고 데이터가 없어 리포트 다운로드와 파일 감지는 아직 검증하지 못했습니다.
## 10. 2026-06-11 Night Build 반영

현재 사용자의 실제 테스트 기준으로 다음 상태를 기록합니다.

- 전용 수집 브라우저 실행 성공
- ESM 로그인 성공
- 광고센터 진입 성공
- 새 창 처리 성공
- 리포트 다운로드 검증은 최근 광고 데이터가 없어 보류

현재 판정: 광고센터 진입 성공, 다운로드 검증 대기.

주의: 광고센터 진입 성공은 데이터 수집 성공이 아닙니다. 실제 리포트 파일이 다운로드되고 AIMAOS가 감지해야 수집 성공으로 봅니다.
