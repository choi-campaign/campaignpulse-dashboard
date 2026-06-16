# 캠페인펄스 CampaignPulse

캠페인펄스는 광고 캠페인의 성과 신호를 읽고, 운영자가 지금 확인해야 할 일을 정리해 주는 광고 운영 대시보드입니다.

광고 엑셀/CSV 파일을 업로드하면 데이터를 공통 형식으로 정리하고, 성과 분석, 운영 점검 포인트, 실행 권고, 보고서 생성 흐름을 한 화면에서 확인할 수 있습니다.

## Streamlit Cloud 실행 정보

Streamlit Cloud 앱 실행 파일:

```text
aimaos/app/streamlit_app.py
```

필수 패키지:

```text
requirements.txt
```

## 온라인 데모 데이터

보안을 위해 실제 광고주 데이터, 실제 매출/광고비 데이터, API 키, 계정 정보는 GitHub에 올리지 않습니다.

온라인 데모에서 화면이 비어 보이지 않도록 안전한 가짜 데이터를 포함했습니다.

```text
samples/demo_data/campaignpulse_demo_ads.csv
data/raw/test_ads_full_visible.csv
```

포함된 데모 광고주:

- 샘플스토어 A
- 샘플브랜드 B
- 샘플몰 C

포함된 데모 매체:

- 네이버 검색광고
- G마켓
- 옥션
- 11번가

이 데이터는 기능 시연용 가짜 데이터이며 실제 광고주 데이터가 아닙니다.

## 로컬 실행

```powershell
.\.venv\Scripts\streamlit.exe run aimaos/app/streamlit_app.py
```

또는 Python 모듈 실행:

```powershell
.\.venv\Scripts\python.exe -m streamlit run aimaos/app/streamlit_app.py
```

## 보호해야 할 파일

다음 파일과 폴더는 GitHub에 올리지 않습니다.

- `.env`
- `.venv/`
- `.playwright-browsers/`
- `data/` 안의 실제 광고주 원본 파일
- 실제 CSV/XLSX 광고 리포트
- API Key, Secret Key, 광고주 계정 정보

## 현재 검증 상태

- 데모 CSV 로딩 가능
- 표준화 가능
- 분석 파이프라인 연결 가능
- 우선 처리 이슈 생성 가능
- Streamlit Cloud에서 예시 화면 표시 가능
