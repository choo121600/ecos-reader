# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2024-12-30

### Added
- **완전한 ECOS API 지원**: 누락되었던 3개의 API 엔드포인트 추가
  - `get_statistic_word()` - 통계용어사전 조회
  - `get_key_statistic_list()` - 100대 통계지표 조회
  - `get_statistic_meta()` - 통계메타DB 조회
- **확장된 주기 지원**: 반년(S), 반월(SM) 주기 타입 추가
- **향상된 날짜 파싱**: 모든 ECOS 날짜 형식 지원
  - 연간 (YYYY)
  - 반년 (YYYYSN)
  - 분기 (YYYYQN)
  - 월간 (YYYYMM)
  - 반월 (YYYYMMSMN)
  - 일간 (YYYYMMDD)
- **포괄적인 E2E 테스트**: 실제 API를 사용한 13개의 통합 테스트 추가
- **완전한 API 필드 매핑**: 모든 API 응답 필드에 대한 파서 지원

### Changed
- `EcosService` 타입에 `StatisticMeta` 추가
- `Period` 타입 확장: `D`, `M`, `Q`, `A`, `S`, `SM` 모두 지원
- 파서 컬럼 매핑 확장: StatisticWord, KeyStatisticList, StatisticMeta, StatisticTableList의 모든 필드 포함

### Fixed
- 공식 ECOS API 가이드와 완전히 일치하도록 코드 리팩토링
- URL 구성 및 파라미터 처리 개선

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

[0.1.2]: https://github.com/choo121600/ecos-reader/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/choo121600/ecos-reader/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/choo121600/ecos-reader/releases/tag/v0.1.0
