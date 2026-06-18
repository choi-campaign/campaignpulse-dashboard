# CampaignPulse Streamlit Cloud 배포 체크리스트

## 앱 실행 파일

```text
aimaos/app/streamlit_app.py
```

## 반드시 포함해야 하는 파일

- `aimaos/`
- `requirements.txt`
- `.streamlit/config.toml`
- `README.md`
- `samples/demo_data/campaignpulse_demo_ads.csv`
- `samples/demo_data/README.md`
- `data/raw/test_ads_full_visible.csv`
- `data/phase2_samples/commerce_sample.csv`
- `data/phase2_samples/search_sample.csv`
- `data/phase2_samples/ai_visibility_sample.csv`
- `data/reports/demo/report.md`
- `data/reports/demo/report.txt`

## 절대 포함하면 안 되는 파일

- `.env`
- `.venv/`
- `.playwright-browsers/`
- 실제 광고주 CSV/XLSX 파일
- 실제 광고주 리포트 원본
- API Key, Secret Key, 광고주 계정 정보

## 데모 데이터 확인

온라인 사이트에서 실제 광고주 데이터가 없어도 아래 가짜 데이터가 표시되어야 합니다.

- 샘플스토어 A
- 샘플브랜드 B
- 샘플몰 C
- 네이버 검색광고
- G마켓
- 옥션
- 11번가

화면에는 다음 안내 문구가 표시되어야 합니다.

```text
현재 화면은 기능 시연을 위한 데모 데이터 기준입니다. 실제 광고주 데이터가 아닙니다.
```

사용자가 실제 파일을 업로드하면 업로드 데이터가 데모 데이터보다 우선 적용되어야 합니다.

## 배포 후 확인 순서

1. Streamlit Cloud 앱을 재부팅하거나 재배포합니다.
2. 첫 화면이 비어 있지 않은지 확인합니다.
3. 우선 처리 이슈와 성과 흐름이 표시되는지 확인합니다.
4. 광고 성과 분석 화면에서 체험 데이터 분석이 가능한지 확인합니다.
5. 쇼핑몰/매체 분석 화면에서 운영 예시 데이터가 표시되는지 확인합니다.
6. 보고서 센터에서 데모 보고서가 표시되는지 확인합니다.
7. 실제 광고주 데이터나 `.env`가 GitHub에 올라가지 않았는지 확인합니다.

## 현재 검증 결과

- 온라인 응답: HTTP 200
- 종합 대시보드 데모 수치 표시: 성공
- 광고 성과 분석 체험 데이터 펼침: 성공
- 광고 성과 분석 체험 데이터 실행: 성공
- 쇼핑몰/매체 분석 운영 예시 데이터 표시: 성공
- 보고서 센터 Markdown/TXT 데모 보고서 표시: 성공
- 로컬 `python -m compileall aimaos tests`: 성공
- 로컬 Streamlit AppTest: 예외 0건, 오류 0건
- 로컬 `python -m pytest tests -q`: 6 passed
- GitHub Actions 자동 검증: 성공 (`CampaignPulse checks #17`, 32초)

## 로컬 테스트 실행

테스트 의존성 설치:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

테스트 실행:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 현재 반영 방식

원격 앱은 `samples/demo_data/campaignpulse_demo_ads.csv`를 기본 데모 데이터로 사용합니다.

사이드바에서 데모 데이터 사용 여부를 확인할 수 있고, 사용자가 실제 파일을 분석하면 업로드 데이터가 현재 세션의 우선 데이터가 됩니다. 기존 `data/raw/test_ads_full_visible.csv`는 이전 체험 흐름의 호환성을 위해 유지합니다.

## 현재 주의사항

원격 `aimaos/app/streamlit_app.py` 동기화와 Streamlit Cloud 재배포가 완료되었습니다.

온라인 화면에서 데모 안내 문구, 데모 토글, 데모 상태, 광고주 3개와 KPI가 표시되고 브라우저 오류가 없는 것을 확인했습니다.

## 자동 재발 방지

GitHub의 `main` 브랜치 push와 pull request에서는 다음 검사가 자동 실행됩니다.

```text
python -m compileall aimaos tests
python -m pytest tests -q
```

데모 CSV나 보고서 파일이 누락되거나 기존 분석 파이프라인이 데모 데이터를 처리하지 못하면 배포 준비 검사가 실패합니다.

현재 자동 검증은 GitHub에 포함된 가짜 데이터 `samples/demo_data/campaignpulse_demo_ads.csv`를 사용합니다. 실제 광고주 원본 파일이나 API 키는 사용하지 않습니다.
