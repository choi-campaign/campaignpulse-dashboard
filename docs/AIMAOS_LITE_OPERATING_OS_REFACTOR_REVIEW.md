# AIMAOS Lite 운영 OS 리팩토링 검토서

작성일: 2026년 6월 8일

## 1. 현재 코드 구조 분석

현재 AIMAOS MVP의 핵심 흐름은 다음 파일에 구현되어 있습니다.

| 영역 | 파일 | 역할 |
| --- | --- | --- |
| 앱 화면 | `aimaos/app/streamlit_app.py` | Streamlit UI, 대시보드, 광고 분석, 보고서 센터, 채널 관리 |
| CLI 실행 | `aimaos/app/cli.py` | 명령줄 분석 실행 |
| 폴더 감시 | `aimaos/app/watch_folder.py` | raw 폴더 파일 감시 후 분석 |
| 파이프라인 | `aimaos/pipeline.py` | 파일 검증, 로드, 표준화, 분석, 추천, 보고서 생성 연결 |
| 파일 로드 | `aimaos/parsers/excel_loader.py` | Excel/CSV 읽기 |
| 컬럼 매핑 | `aimaos/transformers/column_mapper.py` | 매체별 컬럼명을 표준 컬럼으로 매핑 |
| 데이터 표준화 | `aimaos/transformers/standardizer.py` | 숫자, 날짜, 텍스트 컬럼 정리 |
| 성과 분석 | `aimaos/analyzers/performance_analyzer.py` | KPI 계산, 기간 분석, 이상 탐지 |
| 기간 분석 | `aimaos/analyzers/custom_period_analyzer.py` | 사용자 지정 기간, 빠른 기간, 기간 비교 |
| 실행 권고 | `aimaos/recommenders/rule_engine.py` | 기존 이상 탐지 기반 추천안 생성 |
| 운영 액션 엔진 | `aimaos/recommenders/action_engine.py` | 오늘 해야 할 일, 광고주 설명 문구, 예상 효과 생성 |
| 보고서 생성 | `aimaos/reports/report_generator.py` | Markdown, TXT, Excel 결과 생성 |
| 표시 형식 | `aimaos/reports/formatting.py` | 한글 컬럼명, 숫자, 금액, 비율, ROAS 표시 |

## 2. 기존 기능 목록

현재 유지되는 기존 기능은 다음과 같습니다.

- CSV 업로드
- Excel 업로드
- 컬럼 자동 매핑
- 데이터 표준화
- 광고 성과 분석
- 운영 점검 포인트
- 기간 분석
- 사용자 지정 기간 분석
- 비교 분석
- Markdown 보고서 생성
- TXT 보고서 생성
- Excel 결과 파일 생성
- 채널 통합 관제 샘플
- 채널 DB 관리

## 3. 절대 보호 로직

이번 리팩토링에서 아래 파일의 계산 로직은 변경하지 않았습니다.

- `aimaos/pipeline.py`
- `aimaos/parsers/excel_loader.py`
- `aimaos/transformers/column_mapper.py`
- `aimaos/transformers/standardizer.py`
- `aimaos/analyzers/performance_analyzer.py`
- `aimaos/analyzers/custom_period_analyzer.py`
- `aimaos/reports/report_generator.py`

기존 분석 결과값이 달라지지 않도록, UI 표시와 운영 액션 생성 레이어만 개선했습니다.

추가 보호 기준:

- 기존 분석 계산 로직은 수정하지 않습니다.
- Rule Engine은 새로운 해석 레이어로만 추가합니다.
- 오늘 해야 할 일 카드는 기존 KPI 계산 결과를 참조만 합니다.
- AI/설명 문구는 Rule Engine 결과가 있을 때만 생성합니다.
- 원인 표현은 단정하지 않고 가능성, 의심, 검토 필요 수준으로 작성합니다.
- 데이터가 부족한 경우에는 판단 불가로 표시합니다.
- 대용량 데이터 대비 화면에서는 원본 전체 행을 직접 렌더링하지 않습니다.

## 4. 변경 가능한 UI 영역

안전하게 변경 가능한 영역은 다음입니다.

- 대시보드 표시 순서
- 오늘 해야 할 일 카드
- AI 운영 코치 표시 방식
- 데이터 최신성 상태 표시
- 보고서 센터의 대상별 안내 문구
- 설정 화면의 운영 원칙 안내
- Beta 영역의 준비중 기능 안내

## 5. 오늘 해야 할 일 엔진 설계

`오늘 해야 할 일`은 AIMAOS Lite의 핵심 화면입니다.

이번 작업에서 `aimaos/recommenders/action_engine.py`를 추가해 UI에서 직접 문장을 만들지 않고, Rule Engine 기반으로 운영 액션 이슈를 생성하도록 분리했습니다.

이슈 구조:

- 심각도
- 우선순위 점수
- 광고주명
- 매체
- 캠페인/광고그룹/상품명 또는 대상
- 발견된 문제
- 근거 데이터
- 원인 추정
- 추천 액션
- 예상 효과
- 광고주 설명 문구
- 보고서 반영 여부

## 6. Rule Engine 설계안

현재 MVP 기준 Rule Engine은 두 레이어입니다.

1. `performance_analyzer.py`
   - 숫자 기반 이상 탐지
   - 예: 광고비 소진 대비 전환 없음, 노출 대비 클릭률 저조, 확대 가능 구간

2. `action_engine.py`
   - 이상 탐지 결과를 운영 액션으로 변환
   - 광고주 설명 문구 생성
   - 보고서 반영 후보 표시

향후 확장 구조:

```text
aimaos/recommenders/
  rule_engine.py
  action_engine.py
  rules/
    common_rules.py
    industry_rules.py
    advertiser_rules.py
```

## 7. AI 설명 원칙

AI 설명은 Rule Engine 결과 기반이어야 합니다.

금지:

- 숫자 근거 없는 평가
- 원인 단정
- 광고 문제로만 단정
- 상품, 가격, 상세페이지, 후기, 시장 경쟁 가능성 배제

현재 적용:

- 광고주 설명 문구에는 "가능성", "함께 확인", "단정하지 않음" 표현을 포함했습니다.
- 광고 외 원인 가능성을 문구에 포함했습니다.
- 데이터가 부족하면 "판단 불가"로 표시하고 설명 문구 생성을 제한합니다.

## 8. 데이터 수집 UX 개선안

현재 MVP는 파일 업로드 중심입니다.

하지만 장기적으로는 다음 우선순위가 필요합니다.

1. API 수집
2. 자동 다운로드 에이전트
3. 파일 업로드

현재 UI에 반영한 상태:

- API 연동 가능 매체 표시
- 자동 수집 예정 매체 표시
- 현재 수집 방식 표시
- 마지막 데이터 기준일 표시
- 데이터 최신성 상태 표시
- 누락 데이터 행 수 표시

## 9. 대용량 데이터 처리 개선안

상품 수가 많아지면 원본 전체 행을 매번 화면에서 직접 분석하면 느려질 수 있습니다.

권장 구조:

```text
원본 파일 저장
↓
정규화 테이블 생성
↓
일별/매체별/광고주별/상품별 집계 테이블 생성
↓
분석용 요약 테이블 생성
↓
화면에서는 요약 테이블 우선 조회
↓
필요할 때만 상세 drill-down
```

현재 단계에서는 구조 원칙을 설정 화면에 반영했습니다. 실제 DuckDB/SQLite 집계 테이블 구현은 다음 단계입니다.

UI 원칙:

- 원본 전체 행은 화면에 직접 렌더링하지 않습니다.
- 샘플 원본 미리보기는 상위 50행으로 제한합니다.
- 대시보드와 오늘 해야 할 일 화면은 요약/룰 결과를 우선 사용합니다.

## 10. 보고서와 오늘 해야 할 일 연결

보고서 센터의 맞춤 요약에 `오늘 해야 할 일 반영 후보`를 추가했습니다.

보고서 유형:

- 대표 보고서
- 광고주 보고서
- 실무자 보고서
- 대행사 보고서
- 요약 보고서

각 보고서에는 Rule Engine 기반 이슈, 추천 액션, 광고주 설명 문구를 포함할 수 있도록 설계했습니다.

## 11. 이번 작업에서 새로 추가한 기능

- `action_engine.py` 추가
- 오늘 해야 할 일 Rule Engine 분리
- 광고주 설명 문구 생성
- 데이터 최신성 상태 표시
- 데이터 수집 구조 안내
- 대용량 데이터 처리 원칙 안내
- 보고서 센터의 오늘 해야 할 일 반영 후보

## 12. 아직 미구현인 기능

- 실제 API 수집
- 자동 다운로드 에이전트
- DuckDB/SQLite 집계 테이블 생성
- 광고주별 개별 룰 저장
- 업종별 룰 저장
- 품절 상품 자동 확인
- 광고 ON/OFF 이상 감지
- 월간 보고서에 실제 처리 이슈 자동 누적
- PDF 보고서 생성

## 13. 다음 작업 우선순위

1. 실제 지마켓/옥션/네이버 광고 파일을 워크스페이스로 복사해 컬럼 구조 학습
2. `action_engine.py`의 이슈를 Excel 보고서 시트로 추가
3. 광고주별 목표 ROAS/CPA/CPC 설정 파일 추가
4. 데이터 최신성 기준을 매체별로 다르게 설정
5. 대용량 대비 DuckDB 요약 테이블 PoC
6. 지마켓/옥션 legacy 리포트 파서 설계
7. 신규 지마켓/옥션 광고센터 next 리포트 대응 구조 분리

## 14. 테스트 방법

기본 테스트:

```powershell
.\.venv\Scripts\python.exe -m compileall aimaos
```

샘플 분석 테스트:

```powershell
.\.venv\Scripts\python.exe -m aimaos.app.cli --input data/raw/sample_ads.csv --output data/reports --advertiser "테스트 광고주"
```

화면 테스트:

```powershell
.\.venv\Scripts\streamlit.exe run aimaos/app/streamlit_app.py
```

접속 주소:

```text
http://localhost:8502/
```

## 15. 최종 판단

이번 리팩토링은 기존 분석 MVP를 유지하면서 AIMAOS Lite를 "오늘 해야 할 일" 중심 운영 OS에 더 가깝게 만든 작업입니다.

핵심 기준은 다음입니다.

> 이 화면을 보면 오늘 어떤 광고주를 먼저 봐야 하고, 무엇을 조치해야 하며, 광고주에게 뭐라고 설명해야 하는지 바로 알 수 있는가?

현재 단계에서는 그 기준에 맞춰 UI와 Rule Engine 구조를 최소 단위로 정리했습니다.
