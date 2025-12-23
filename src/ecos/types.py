"""
ecos-reader 타입 정의

타입 안전성을 위한 공통 타입들을 정의합니다.
"""

from __future__ import annotations

from typing import Any, Literal

# ============================================================================
# API 관련 타입
# ============================================================================

# ECOS 서비스명
EcosService = Literal[
    "StatisticSearch",  # 통계 조회
    "StatisticItemList",  # 통계 항목 목록
    "StatisticTableList",  # 통계표 목록
    "StatisticWord",  # 통계 용어 사전
    "KeyStatisticList",  # 주요 통계 지표
]

# 데이터 주기
Period = Literal["D", "M", "Q", "A"]  # Daily, Monthly, Quarterly, Annual

# 응답 포맷
ResponseFormat = Literal["json", "xml"]

# 언어 구분
Language = Literal["kr", "en"]

# ============================================================================
# 지표별 타입
# ============================================================================

# 금리 지표
TreasuryMaturity = Literal["1Y", "3Y", "5Y", "10Y", "20Y", "30Y"]

# 통화 지표
MoneySupplyIndicator = Literal["M1", "M2", "Lf"]
BankLendingSector = Literal["household", "corporate", "all"]

# 성장 지표
GdpFrequency = Literal["Q", "A"]  # Quarterly, Annual
GdpBasis = Literal["real", "nominal"]

# 환율 지표
Currency = Literal["USD", "JPY", "EUR", "CNY"]
EffectiveRateBasis = Literal["nominal", "real"]

# 심리 지표
BsiSector = Literal["manufacturing", "non_manufacturing", "all"]

# ============================================================================
# 날짜 관련 타입
# ============================================================================

# ECOS 시간 형식
EcosTimeFormat = Literal[
    "YYYY",  # 연간: 2024
    "YYYYQN",  # 분기: 2024Q1
    "YYYYMM",  # 월간: 202401
    "YYYYMMDD",  # 일간: 20240101
]

# 날짜 문자열 (유효성 검증은 별도 함수에서)
DateString = str

# ============================================================================
# 응답 관련 타입
# ============================================================================

# ECOS API 원시 응답 타입
EcosRawResponse = dict[str, Any]

# 통계 데이터 행
StatisticRow = dict[str, str | int | float]

# 통계 응답 데이터
StatisticData = list[StatisticRow]

# 에러 응답
ErrorResponse = dict[str, dict[str, str]]  # {"RESULT": {"CODE": "...", "MESSAGE": "..."}}
