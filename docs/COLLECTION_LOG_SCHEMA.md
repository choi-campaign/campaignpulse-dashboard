# AIMAOS Collection Log Schema

## 목적

AIMAOS의 데이터 수집은 광고주가 파일을 직접 다운로드/업로드하지 않도록 만드는 핵심 기능이다.

따라서 각 수집 시도는 성공/실패 여부와 원인을 반드시 남겨야 한다. 이 로그는 다음 목적에 사용한다.

- 데이터 최신성 판단
- 수집 실패 원인 안내
- 고객지원 비용 감소
- 매체별 수집 성공률 계산
- 광고주 100명/1000명 확장 시 운영 상태 추적

## 저장 위치

- 기본 DB: `data/storage/collection_log.sqlite3`
- 준비 명령: `python -m aimaos.storage.collection_log`

## 테이블

테이블명: `collection_log`

| 컬럼 | 설명 | 예시 |
|---|---|---|
| collection_id | 수집 시도 고유 ID | `naver_20260611_031200` |
| advertiser_id | 광고주 또는 계정 식별자 | `client_001` |
| media | 매체명 | `naver`, `gmarket`, `auction` |
| started_at | 수집 시작 시각 | `2026-06-11 03:12:00` |
| finished_at | 수집 종료 시각 | `2026-06-11 03:14:00` |
| status | 결과 상태 | `success`, `failed`, `partial`, `no_data` |
| rows_collected | 수집 행 수 | `1520` |
| file_count | 생성/감지 파일 수 | `3` |
| storage_used_mb | 이번 수집으로 사용한 용량 | `12.4` |
| error_code | 실패 코드 | `LOGIN_REQUIRED` |
| error_message | 사용자에게 설명 가능한 실패 사유 | `로그인 인증이 필요합니다.` |

## 상태값 기준

| 상태 | 의미 | 사용자 안내 |
|---|---|---|
| success | 데이터 수집 성공 | 수집 완료 |
| partial | 일부 데이터만 수집 | 일부 매체 확인 필요 |
| no_data | 응답은 성공했으나 데이터 없음 | 최신 성과 확인 필요 |
| failed | 수집 실패 | 실패 원인 확인 필요 |

## 운영 원칙

비밀번호 저장, 캡차 우회, 2차 인증 우회는 하지 않는다.

수집 실패 시 개발자용 표현 대신 아래처럼 안내한다.

- 연결 필요
- 인증 필요
- 최신화 필요
- 데이터 없음
- 리포트 확인 필요

## 확장 계획

1. 수집 모듈 완료 시마다 `collection_log`에 기록
2. Data Status Center에서 매체별 최신성/성공률 계산
3. 광고주별 30일 수집 성공률 표시
4. 실패 원인별 고객지원 FAQ 연결

