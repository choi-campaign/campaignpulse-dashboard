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
- `data/phase2_samples/commerce_sample.csv`
- `data/phase2_samples/search_sample.csv`
- `data/phase2_samples/ai_visibility_sample.csv`
- `samples/.gitignore`
- `samples/demo_data/.gitignore`
- `samples/demo_data/campaignpulse_demo_ads.csv`
- `samples/demo_data/README.md`
- `docs/STREAMLIT_CLOUD_DEPLOY_CHECKLIST.md`
- `docs/OVERNIGHT_HARDENING_20260617.md`

## 원격 저장소 확인

GitHub 저장소 `choi-campaign/campaignpulse-dashboard`의 `main` 브랜치에 아래 안전 데모 파일이 존재하는 것을 확인했다.

- `samples/demo_data/campaignpulse_demo_ads.csv`
- `data/raw/test_ads_full_visible.csv`
- `.streamlit/config.toml`
- `data/phase2_samples/commerce_sample.csv`

원격 파일은 모두 실제 광고주 데이터가 아니라 기능 시연용 가짜 데이터다.

## 온라인 화면 검증 결과

Playwright와 시스템 Chrome으로 Streamlit Cloud 화면을 확인했다.

- 온라인 사이트 응답: HTTP 200
- 첫 화면 표시: 성공
- 데모 광고주 수 표시: 3
- 원본 파일 표시: 1
- 우선 처리 이슈 표시: 성공
- 보고서 센터 데모 보고서 표시: 성공
- 쇼핑몰 분석 샘플 데이터 표시: 성공
- 데이터 상태: `연결 안됨`에서 `주의`로 개선

확인 스크린샷은 로컬 작업 폴더의 `data/logs/` 아래에 저장했다.

## 2026-06-17 온라인 재점검

Streamlit Cloud 온라인 사이트를 다시 열어 주요 화면을 스크린샷으로 검증했다.

- 온라인 응답: HTTP 200
- 종합 대시보드: 광고주 수 3, 주의 이슈 2, 보고서 예정 7 표시
- 광고 성과 분석: 체험 데이터 펼침 가능
- 광고 성과 분석 체험 데이터 실행: 우선 처리 이슈 카드 표시 성공
- 쇼핑몰/매체 분석: 운영 예시 데이터 표시 성공
- 보고서 센터: 데모 보고서 표시 성공
- 설정: 시스템 상태와 보호 중인 핵심 기능 표시 성공

확인 스크린샷:

- `data/logs/online_recheck/home.png`
- `data/logs/online_recheck/ad_analysis_expanded.png`
- `data/logs/online_recheck/ad_analysis_sample_result.png`
- `data/logs/online_recheck/commerce.png`
- `data/logs/online_recheck/reports.png`
- `data/logs/online_recheck/settings.png`

보고서 센터의 Excel 데모 파일이 빠져 있어 로컬에는 `data/reports/demo/analysis.xlsx`를 추가했다. 원격 바이너리 업로드는 커넥터 제한으로 중단되어 깨진 파일을 올리지 않고 보류했다. 현재 온라인 보고서 센터는 Markdown/TXT 데모 보고서 기준으로 표시된다.

## 로컬 검증 결과

로컬 최신 앱 기준으로 데모 데이터와 기본 실행 안정성을 다시 확인했다.

- `python -m compileall aimaos tests`: 성공
- `streamlit.testing.v1.AppTest`: 예외 0건, 오류 0건, 경고 0건
- `samples/demo_data/campaignpulse_demo_ads.csv`: 20행, 광고주 3개, 매체 4개
- 데모 CSV 필수 컬럼: 누락 없음
- 데모 CSV 빈 핵심 셀: 0건
- 데모 CSV 기반 `run_analysis_pipeline`: 성공
- 생성 산출물: Excel, Markdown, TXT 모두 생성 성공

`pytest`는 현재 가상환경에 설치되어 있지 않아 실행하지 못했다. 대신 컴파일, Streamlit AppTest, 파이프라인 직접 호출로 우선 검증했다.

## 중요한 운영 기준

- 모든 데모 데이터는 가짜 데이터다.
- 실제 광고주 데이터, API 키, `.env`는 GitHub에 올리지 않는다.
- 현재 원격 앱은 `data/raw/test_ads_full_visible.csv`를 체험 데이터로 읽기 때문에 이 경로에 안전한 데모 CSV를 포함했다.
- `.streamlit/config.toml`은 라이트 테마 기준으로 텍스트 대비가 확보되도록 설정했다.

## 남은 핵심 리스크

원격 `aimaos/app/streamlit_app.py`가 로컬 최신 데모 모드 코드보다 오래된 상태다. 현재는 원격 앱이 이미 읽는 경로에 안전 데모 파일을 추가하여 온라인 빈 화면 문제를 우회했다.

다음 안정화 단계에서는 로컬 최신 `streamlit_app.py` 전체를 원격 저장소에 정식 반영해야 한다. 이 작업이 완료되면 `samples/demo_data` 기준 데모 모드, 업로드 우선순위, 데이터 상태 센터 문구가 로컬과 온라인에서 완전히 동일해진다.

## 현재 판단

- 온라인 데모 빈 화면 문제: 임시 해결
- 예시 데이터 표시: 가능
- 실제 광고주 데이터 노출 위험: 낮음
- 앱 코드 완전 동기화: 미완료
- 다음 우선순위: 원격 `streamlit_app.py`를 로컬 최신본으로 동기화
