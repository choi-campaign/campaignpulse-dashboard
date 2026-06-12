# AIMAOS 다음 단계

현재 상태:

- Python 3.14.5 확인 완료
- AIMAOS 전용 가상환경 생성 완료
- pandas, openpyxl, streamlit 등 필수 패키지 설치 완료
- 샘플 광고 데이터 분석 실행 완료
- 샘플 보고서 생성 완료

## 바로 확인할 파일

- `data/reports/report.md`
- `data/reports/report.txt`
- `data/reports/analysis.xlsx`
- `data/raw/test_ads_full_visible.csv`
- `docs/TEST_DATA_GUIDE_KR.md`
- `docs/FORMAT_AND_PERIOD_GUIDE_KR.md`
- `docs/PHASE2_TEST_PREVIEW_GUIDE_KR.md`
- `HOW_TO_VIEW_TEST_RESULT_KR.md`

## 가장 쉬운 실행 방법

샘플 보고서를 다시 만들려면:

```text
run_sample_report.bat
```

분석 결과가 더 잘 보이는 확장 테스트 데이터를 실행하려면:

```text
run_full_test_report.bat
```

업로드 화면을 실행하려면:

```text
start_upload_app.bat
```

`data/raw` 폴더에 새 파일이 들어오면 자동 분석되게 하려면:

```text
watch_raw_folder.bat
```

## 실제 광고주 파일로 실행하는 방법

1. 광고센터에서 받은 엑셀 또는 CSV 파일을 `data/raw` 폴더에 넣습니다.
2. PowerShell을 이 폴더에서 엽니다.
3. 아래 명령을 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m aimaos.app.cli --input data/raw/파일명.xlsx --output data/reports --advertiser "광고주명"
```

CSV라면:

```powershell
.\.venv\Scripts\python.exe -m aimaos.app.cli --input data/raw/파일명.csv --output data/reports --advertiser "광고주명"
```

## 다음 개발 우선순위

1. 실제 네이버/카카오/구글 광고 엑셀 샘플 3개로 컬럼 매핑 사전 보강
2. 보고서 문구를 협회 표준 리포트 톤으로 정리
3. 업종, 광고주, 분석일 기준으로 보고서 저장 경로 자동 분리
4. 브라우저 자동 다운로드 수집기 설계
5. 전문가 승인 후 예산/입찰 변경 자동화 설계
