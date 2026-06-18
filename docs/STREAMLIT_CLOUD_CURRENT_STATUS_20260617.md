# CampaignPulse Streamlit Cloud 현재 상태 2026-06-17

## 결론

온라인 데모 사이트는 현재 빈 화면이 아니며, 기능 시연에 필요한 핵심 예시 데이터가 표시된다.

## 확인한 온라인 주소

```text
https://campaignpulse-dashboard-q58duahzapzaw423gqyrub.streamlit.app/
```

## 현재 정상 확인 항목

- 종합 대시보드 표시
- 광고주 수 3 표시
- 주의 이슈 2 표시
- 보고서 예정 7 표시
- 광고 성과 분석 화면 표시
- 체험 데이터 펼침 표시
- 체험 데이터 분석 실행 후 우선 처리 이슈 카드 표시
- 쇼핑몰/매체 분석 예시 데이터 표시
- 보고서 센터 Excel / Markdown / TXT 표시
- 설정 화면 표시
- 로컬 배포 준비 테스트 5개 통과
- GitHub push/PR 자동 검증 성공

## 반영된 안전 데모 데이터

- `samples/demo_data/campaignpulse_demo_ads.csv`
- `data/raw/test_ads_full_visible.csv`
- `data/phase2_samples/commerce_sample.csv`
- `data/phase2_samples/search_sample.csv`
- `data/phase2_samples/ai_visibility_sample.csv`
- `data/reports/demo/analysis.xlsx`
- `data/reports/demo/report.md`
- `data/reports/demo/report.txt`

## 실제 광고주 데이터 보호 상태

GitHub에 올린 데모 데이터는 모두 가짜 데이터다.

올리면 안 되는 항목:

- 실제 광고주 원본 CSV/XLSX
- 실제 매출/광고비 리포트
- `.env`
- API Key
- Secret Key
- 광고주 로그인 정보

## 현재 남은 리스크

원격 `aimaos/app/streamlit_app.py`는 로컬 최신본보다 오래된 상태다.

현재 온라인 데모는 구버전 원격 앱이 이미 읽는 경로에 안전한 가짜 데이터를 배치해서 화면 공백 문제를 해결했다.

## 왜 전체 상태가 아직 `주의`로 보이는가

원격 구버전 앱은 11번가와 쿠팡을 코드상 `연결 필요` 상태로 고정한다.

따라서 네이버, G마켓, 옥션 데모 데이터가 있어도 전체 상태는 `주의`로 표시될 수 있다. 이는 데모 데이터 누락 문제가 아니라 원격 앱 코드 동기화가 아직 끝나지 않았기 때문이다.

## 다음 우선순위

1. 로컬 최신 `aimaos/app/streamlit_app.py`를 원격 저장소에 안전하게 동기화한다.
2. 동기화 후 Streamlit Cloud를 재배포한다.
3. 데모 모드 안내 문구와 데이터 상태 센터가 로컬과 동일하게 표시되는지 확인한다.
4. 실제 광고주 파일 업로드가 데모 데이터보다 우선되는지 확인한다.

## 자동 검증

`.github/workflows/ci.yml`은 GitHub의 `main` push와 pull request마다 아래 항목을 검사한다.

- Python 소스 컴파일
- 안전한 데모 CSV 필수 컬럼과 데이터 개수
- Streamlit Cloud용 기존 체험 데이터 파일 존재
- 데모 보고서 Excel / Markdown / TXT 존재
- 데모 데이터의 기존 분석 파이프라인 통과

실제 광고주 데이터와 API 키는 검사 또는 업로드 대상으로 사용하지 않는다.

2026-06-18 원격 검증 결과:

```text
CampaignPulse checks #4
결과: 성공
소요 시간: 39초
커밋: ef2a3a3
```

초기 CI 실패 원인은 GitHub에서 제외된 `data/raw/sample_ads.csv`를 테스트가 참조한 것이었다. 테스트 입력을 GitHub에 포함된 안전한 가짜 데이터 `samples/demo_data/campaignpulse_demo_ads.csv`로 변경해 해결했다.

## 로컬 검증 명령

```powershell
.\.venv\Scripts\python.exe -m compileall aimaos tests
.\.venv\Scripts\python.exe -m pytest tests -q
```

현재 결과:

```text
5 passed
```

## 검증 스크린샷

로컬 작업 폴더 기준:

- `data/logs/online_recheck/home.png`
- `data/logs/online_recheck/ad_analysis_expanded.png`
- `data/logs/online_recheck/ad_analysis_sample_result.png`
- `data/logs/online_recheck/commerce.png`
- `data/logs/online_recheck/reports_after_excel.png`
- `data/logs/online_recheck/settings.png`
