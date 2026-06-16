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
- `data/raw/test_ads_full_visible.csv`

## 절대 포함하면 안 되는 파일

- `.env`
- `.venv/`
- `.playwright-browsers/`
- 실제 광고주 CSV/XLSX 파일
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

## 배포 후 확인 순서

1. Streamlit Cloud 앱을 재부팅하거나 재배포합니다.
2. 첫 화면이 비어 있지 않은지 확인합니다.
3. 우선 처리 이슈와 성과 흐름이 표시되는지 확인합니다.
4. 광고 성과 분석 화면에서 체험 데이터 분석이 가능한지 확인합니다.
5. 실제 광고주 데이터나 `.env`가 GitHub에 올라가지 않았는지 확인합니다.

## 현재 반영 방식

현재 원격 앱 코드는 `data/raw/test_ads_full_visible.csv`를 체험 데이터로 읽습니다.
따라서 Streamlit Cloud에서 바로 예시 화면을 보여주기 위해 같은 경로에 안전한 가짜 데이터를 포함했습니다.

장기적으로는 `samples/demo_data/`를 기준으로 데모 모드를 사용하는 구조로 정리하는 것이 좋습니다.
