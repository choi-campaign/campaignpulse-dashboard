# CampaignPulse Continuous Hardening Status

기록일: 2026-06-20

## 실제 변경 파일

- `aimaos/storage/collection_log.py`
  - 최근 시도가 실패하거나 데이터 없음이어도 마지막 성공 시각과 최근 실패 시각을 각각 보존한다.
- `aimaos/app/streamlit_app.py`
  - 수집 시도 시각과 성공 수집 시각을 구분한다.
  - 데모 상태를 데이터 확인 필요 건수에서 제외한다.
  - 매체·채널 칩의 글자가 라이트·다크 테마 공통 본문 색상을 따르도록 보강한다.
- `aimaos/collectors/marketplace/base_collector.py`
- `aimaos/collectors/marketplace/marketplace_collection_poc.py`
  - 성공 로그에 실제 진단 행 수와 감지 파일 용량을 기록한다.
- `aimaos/collectors/marketplace/download_watcher.py`
  - CSV/Excel 확장자를 대소문자와 관계없이 감지한다.
  - 0바이트 파일과 다운로드 중인 임시 파일은 수집 성공으로 인정하지 않는다.
- `aimaos/collectors/marketplace/gmarket_computer_use_download_poc.py`
  - 감시 전용 실행에서 오래된 다운로드 파일을 새 수집 성공으로 재사용하지 않도록 최근 파일 감지 범위를 제한한다.
- `tests/test_marketplace_collection.py`
- `tests/test_demo_deploy_readiness.py`
- `docs/COLLECTION_LOG_SCHEMA.md`
- `docs/DATA_STATUS_CENTER_REFACTOR.md`
- `docs/MARKETPLACE_DOWNLOAD_SUCCESS_GUARD.md`

## 검증 결과

- Python compile: 성공
- pytest: `30 passed`
- GitHub Actions `CampaignPulse checks`: 성공
- 마켓플레이스 파일 감지 회귀 테스트: 성공
- 온라인 데모 안내: 정상
- 온라인 데이터 확인 필요: 1개 채널
- 온라인 주요 메뉴 8개: 모두 정상
- 온라인 콘솔 오류: 0건
- 라이트·다크 모드: 제목, 본문, 카드, 버튼, 매체 칩 대비 보강
- 실제 업로드 데이터 우선 적용: AppTest 통과

Streamlit Cloud에서 이전 화면이 유지된 원인은 비활성 앱 절전 상태였다. 앱을 다시 시작한 뒤 최신 GitHub 커밋, `마지막 수집 시도` 문구, 데모 상태 집계 1건이 온라인에 반영된 것을 확인했다.

## 보호한 영역

- 광고 성과와 KPI 계산
- Rule Engine
- 보고서 계산과 산출물 구조
- 데이터 표준화와 컬럼 매핑
- 업로드와 파싱 로직

## 남은 가장 큰 병목

최근 광고 집행 이력이 있는 G마켓·옥션 계정에서 실제 리포트 파일 다운로드와 CampaignPulse 파일 감지를 검증해야 한다. 광고센터 진입만으로는 성공으로 기록하지 않는다. 파일 생성, 원본 진단, 분석 파이프라인 연결까지 완료되어야 실제 수집 성공이다.
