# CampaignPulse Overnight Hardening 2026-06-17

## 목적

Streamlit Cloud 온라인 데모에서 예시 데이터가 보이지 않는 문제와 라이트/다크 가독성 문제를 줄이고, 실제 광고주 데이터 없이도 기능 흐름을 확인할 수 있게 했다.

## 원격 반영 파일

- `.gitignore`
- `.streamlit/config.toml`
- `README.md`
- `data/raw/test_ads_full_visible.csv`
- `data/collection_poc/naver_demo_collection.csv`
- `data/collection_poc/marketplace/gmarket_legacy/downloads/demo_gmarket_report.csv`
- `data/collection_poc/marketplace/auction_legacy/downloads/demo_auction_report.csv`
- `data/reports/demo/report.md`
- `data/reports/demo/report.txt`
- `samples/.gitignore`
- `samples/demo_data/.gitignore`
- `samples/demo_data/campaignpulse_demo_ads.csv`
- `samples/demo_data/README.md`
- `docs/STREAMLIT_CLOUD_DEPLOY_CHECKLIST.md`

## 검증 결과

- GitHub 원격 저장소: `choi-campaign/campaignpulse-dashboard`
- 온라인 사이트 응답: HTTP 200
- Streamlit Cloud 화면 스크린샷 확인 완료
- 첫 화면 표시 성공
- 데모 광고주 수: 3
- 원본 파일 표시: 1
- 우선 처리 이슈 표시: 성공
- 데이터 상태: `연결 안됨`에서 `주의`로 개선

## 중요한 운영 기준

- 모든 데모 데이터는 가짜 데이터다.
- 실제 광고주 데이터, API 키, `.env`는 GitHub에 올리지 않는다.
- 현재 원격 앱은 `data/raw/test_ads_full_visible.csv`를 체험 데이터로 읽기 때문에 이 경로에 안전한 데모 CSV를 포함했다.

## 남은 개선점

현재 원격 `aimaos/app/streamlit_app.py`는 로컬 최신 데모 모드 코드보다 오래된 상태다. 이번 작업에서는 빈 화면 문제를 빠르게 해결하기 위해 원격 앱이 이미 읽는 경로에 데모 데이터를 추가했다.

다음 단계에서는 로컬 최신 `streamlit_app.py`를 원격에 정식 반영해 `samples/demo_data` 기준 데모 모드로 통일하는 것이 좋다.
