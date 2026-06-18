# CampaignPulse Streamlit Cloud 현재 상태

상태 갱신: 2026-06-19

## 온라인 주소

https://campaignpulse-dashboard-q58duahzapzaw423gqyrub.streamlit.app/

## 현재 정상 확인

- 데모 데이터 자동 표시
- 실제 광고주 데이터가 아니라는 안내 표시
- 광고주 3개
- 광고비 7,451,000원
- 매출 36,810,000원
- ROAS 494.03%
- 네이버, G마켓, 옥션, 11번가 데모 상태 표시
- 실제 파일 업로드 시 데모보다 업로드 결과 우선
- 업로드 후 데모 안내 제거와 데모 토글 비활성화
- 라이트·다크 모드 사이드바와 본문 버튼 대비 보강
- 온라인 콘솔 오류 0건

## 안전 데모 데이터

- `samples/demo_data/campaignpulse_demo_ads.csv`
- `data/raw/test_ads_full_visible.csv`
- `data/phase2_samples/commerce_sample.csv`
- `data/phase2_samples/search_sample.csv`
- `data/phase2_samples/ai_visibility_sample.csv`
- `data/reports/demo/analysis.xlsx`
- `data/reports/demo/report.md`
- `data/reports/demo/report.txt`

모든 데모 값은 가짜 데이터다.

## 실제 데이터 보호

GitHub에 올리지 않는 항목:

- 실제 광고주 CSV, XLS, XLSX
- 실제 광고비·매출·전환 데이터
- `.env`
- API Key와 Secret Key
- 광고주 로그인 정보와 세션 파일

## 자동 검증

```text
Python compile: 성공
pytest: 18개 통과
Streamlit AppTest: 성공
GitHub Actions: 성공
```

자동 검증 범위:

- 데모 CSV 필수 컬럼과 광고주·매체 수
- 데모 보고서 Excel, Markdown, TXT
- 기존 분석 파이프라인 연결
- 데모 안내 문구
- 실제 업로드 우선순위
- 라이트·다크 버튼 대비 CSS
- 네이버 날짜 범위·stats 파싱·표준 CSV
- G마켓·옥션 다운로드 파일 판정 경계
- `collection_log` 성공·실패 기록

## 현재 남은 병목

1. G마켓·옥션 실제 광고 리포트 다운로드 파일 생성 검증
2. 실제 파일 감지 후 분석 파이프라인 연결
3. 네이버 실제 양수 성과 행 날짜 범위 검증
4. 네이버 운영 스케줄·재시도·암호화 비밀값 관리
5. 11번가 실제 계정과 원본 리포트 확보

## 로컬 검증 명령

```powershell
.\.venv\Scripts\python.exe -m compileall aimaos tests
.\.venv\Scripts\python.exe -m pytest tests -q
```
