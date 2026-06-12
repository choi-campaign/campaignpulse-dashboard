# AIMAOS Data Retention and Storage Policy

## 목적

AIMAOS가 광고주 100명, 1000명 규모로 확장되면 데이터 수집보다 저장 비용과 정리 비용이 더 큰 문제가 될 수 있다.

이 문서는 원본 데이터, 가공 데이터, 보고서, 로그, 스크린샷의 보관 기준을 정의한다.

## 보관 기간

| 데이터 종류 | 보관 기간 | 이유 |
|---|---:|---|
| 원본 데이터 | 90일 | 재수집/재분석 검증용 |
| 가공 데이터 | 365일 | 기간 분석, 벤치마크, 운영 비교용 |
| 보고서 | 365일 | 광고주 보고 이력 보존 |
| 로그 | 180일 | 장애 원인 및 고객지원 대응 |
| 스크린샷 | 30일 | POC와 장애 증거 확인 |

## 현재 구현 명령

정리 대상만 확인:

```powershell
python -m aimaos.storage.retention_cleanup --dry-run
```

정책에 따라 실제 정리:

```powershell
python -m aimaos.storage.retention_cleanup --apply
```

현재 단계에서는 `--dry-run`으로 정리 대상을 먼저 확인하는 것을 기본으로 한다.

## 정리 결과 파일

- dry-run 결과: `data/storage/retention_cleanup_last_dry_run.json`
- apply 결과: `data/storage/retention_cleanup_last_apply.json`

## Data Status Center 연결

Data Status Center에는 다음 운영 지표를 표시한다.

- 전체 저장 용량
- 삭제 예정 파일 수
- 삭제 예정 용량
- 다음 정리 상태

## 운영 원칙

삭제는 항상 프로젝트 폴더 내부 파일만 대상으로 한다.

분석 결과와 보고서의 장기 보관은 협회 데이터 자산화와 연결되므로, 원본보다 긴 기간을 둔다.

## 남은 과제

1. 광고주별 저장 용량 집계
2. 매체별 저장 용량 집계
3. 월별 스토리지 증가량 예측
4. 대용량 보고서 압축 보관
5. 관리자 화면에서 정리 예정 파일 확인

