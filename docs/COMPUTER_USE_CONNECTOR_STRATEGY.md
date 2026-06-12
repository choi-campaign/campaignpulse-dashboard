# Computer Use Connector Strategy

## 원칙

AIMAOS 데이터 수집 우선순위는 다음과 같다.

1. 공식 API 수집
2. 공식 리포트 다운로드 자동화
3. Computer Use 기반 반자동 다운로드
4. 수동 업로드

## 이번 POC 범위

이번 작업은 G마켓 파워클릭 G 일별 리포트 다운로드 검증 1개로 제한한다.

## 적용하지 않는 것

- 자동 로그인
- 비밀번호 저장
- 2차 인증 우회
- 캡차 우회
- 광고비/입찰/예산 변경
- 광고 생성 또는 수정

## 상태 기준

- success: 파일 감지, 진단, 분석, 오늘 해야 할 일, 보고서 생성까지 통과
- partial: 파일 생성 또는 진단 일부만 통과
- no_data: 조회는 됐지만 결과 0건
- failed: 화면 인식, 다운로드, 파일 진단, 파이프라인 중 실패
- blocked_by_environment: 현재 실행 환경에서 광고센터 접속 제한
- needs_user_authentication: 사용자 로그인 또는 인증 필요
