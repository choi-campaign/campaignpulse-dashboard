# 캠페인펄스 CampaignPulse

캠페인펄스는 광고 캠페인의 성과 신호를 읽고, 운영자가 지금 확인해야 할 일을 정리해 주는 광고 운영 대시보드입니다.

광고 엑셀/CSV 파일을 업로드하거나 수집 폴더에 넣으면 데이터를 공통 형식으로 정리하고, 성과 분석, 운영 점검 포인트, 실행 권고, 보고서 생성을 한 흐름으로 확인할 수 있습니다.

## 빠른 실행

이미 이 작업공간에는 `.venv` 가상환경이 준비되어 있습니다.

```powershell
.\.venv\Scripts\python.exe -m aimaos.app.cli --input data/raw/sample_ads.csv --output data/reports --advertiser "샘플 광고주"
```

Streamlit 화면 실행:

```powershell
.\.venv\Scripts\streamlit.exe run aimaos/app/streamlit_app.py
```

폴더 감시 실행:

```powershell
.\.venv\Scripts\python.exe -m aimaos.app.watch_folder --input-dir data/raw --output-dir data/reports --advertiser "광고주"
```

## 1차 서비스 범위

- 엑셀, CSV 파일 인식
- 폴더 감시
- 컬럼 자동 매핑
- 공통 광고 성과 형식 변환
- CTR, CPC, CVR, CPA, ROAS 계산
- 전기간 요약
- 기간 비교
- 사용자 지정 기간 선택
- 사용자 지정 두 기간 비교
- 운영 점검 포인트 탐지
- 실행 권고 생성
- 채널 통합 관제 구조
- DB 기반 채널 등록, 수정, 비활성화
- Markdown, TXT, XLSX 보고서 저장

## 운영 원칙

- 광고주가 매일 파일을 직접 다운로드하고 업로드하는 부담을 줄이는 구조를 우선합니다.
- 캡차 우회, 보안 우회, 정책 위반 자동화는 하지 않습니다.
- 반복 업무를 줄이고 전문가 판단을 보조하는 광고 운영 시스템으로 설계합니다.
- 분석 결과와 보고서는 장기적으로 운영 사례와 벤치마크 자산으로 축적될 수 있게 저장합니다.

## 폴더 구조

```text
aimaos/
  app/
  collectors/
  parsers/
  transformers/
  analyzers/
  recommenders/
  automations/
  validators/
  knowledge/
  benchmark/
  association/
  reports/
  configs/
data/
  raw/
  processed/
  reports/
  logs/
  channel_registry.sqlite
docs/
tests/
```

## 기본 입력 컬럼 예시

아래 이름은 자동으로 표준 컬럼에 매핑됩니다.

- 날짜, 일자, date
- 매체, 플랫폼, media, platform
- 계정명, 광고주, account
- 캠페인, campaign
- 광고그룹, ad group
- 키워드, keyword
- 노출, impressions
- 클릭, clicks
- 비용, 광고비, cost, spend
- 전환, conversions
- 매출, revenue
- 주문수, orders

## 보고서 산출물

기본적으로 `data/reports` 아래에 다음 파일이 생성됩니다.

- `report.md`
- `report.txt`
- `analysis.xlsx`
