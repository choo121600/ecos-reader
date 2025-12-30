# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-12-30

### Added
- 완전한 MkDocs 문서 사이트
  - 설치 가이드 및 빠른 시작
  - 사용자 가이드 (기본 사용법, 금리/물가/성장/통화 지표, 고급 기능)
  - API 레퍼런스 (클라이언트, 지표 함수, 예외 처리)
  - 실전 예제 (기본 사용법, 거시경제 대시보드)
  - 기여 가이드
- GitHub Actions 워크플로우를 통한 문서 자동 배포
- `docs` optional dependency 추가 (mkdocs, mkdocs-material)

### Changed
- README에 문서 링크 추가
- pyproject.toml의 Documentation URL을 GitHub Pages로 업데이트

## [0.1.0] - 2024-12-30

### Added
- 초기 릴리스
- 한국은행 ECOS Open API 클라이언트 구현
- 금리 지표 조회
  - 한국은행 기준금리 (`get_base_rate`)
  - 국고채 수익률 (`get_treasury_yield`)
  - 장단기 금리차 (`get_yield_spread`)
- 물가 지표 조회
  - 소비자물가지수 (`get_cpi`)
  - 근원 CPI (`get_core_cpi`)
  - 생산자물가지수 (`get_ppi`)
- 성장 지표 조회
  - GDP (`get_gdp`)
  - GDP 디플레이터 (`get_gdp_deflator`)
- 통화 지표 조회
  - 통화량 (`get_money_supply`)
  - 은행 대출 (`get_bank_lending`)
- API 키 설정 기능
  - 환경 변수 지원
  - `.env` 파일 지원
  - 코드에서 직접 설정
- 자동 캐싱 기능
- 에러 처리
  - `EcosConfigError` - 설정 오류
  - `EcosNetworkError` - 네트워크 오류
  - `EcosAPIError` - API 응답 오류
- 로깅 지원
- 타입 힌팅
- 단위 테스트 및 커버리지
- 예제 코드
  - 기본 사용법 (`examples/basic_usage.py`)
  - 거시경제 대시보드 (`examples/macro_dashboard.py`)

[0.1.1]: https://github.com/choo121600/ecos-reader/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/choo121600/ecos-reader/releases/tag/v0.1.0
