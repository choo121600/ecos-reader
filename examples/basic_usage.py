"""
ecos-reader 기본 사용 예제

이 예제는 ecos-reader의 기본적인 사용법을 보여줍니다.
실행 전 ECOS API 키를 설정해야 합니다.

API 키 발급: https://ecos.bok.or.kr/api/
"""

import ecos

# ============================================================================
# 1. API 키 설정
# ============================================================================

# 방법 1: 환경 변수 사용 (권장)
# export ECOS_API_KEY="your_api_key"

# 방법 2: 직접 설정
# ecos.set_api_key("your_api_key")

# ============================================================================
# 2. 금리 지표 조회
# ============================================================================

print("=" * 60)
print("1. 한국은행 기준금리")
print("=" * 60)

# 기준금리 조회 (최근 1년)
df_base_rate = ecos.get_base_rate()
print(df_base_rate)
print()

# 특정 기간 조회
df_base_rate_period = ecos.get_base_rate(start_date="202001", end_date="202312")
print(f"조회 건수: {len(df_base_rate_period)}개")
print()

print("=" * 60)
print("2. 국고채 수익률")
print("=" * 60)

# 국고채 3년물
df_treasury_3y = ecos.get_treasury_yield(maturity="3Y")
print("국고채 3년물:")
print(df_treasury_3y.tail())
print()

# 국고채 10년물
df_treasury_10y = ecos.get_treasury_yield(maturity="10Y")
print("국고채 10년물:")
print(df_treasury_10y.tail())
print()

print("=" * 60)
print("3. 장단기 금리차 (10Y - 3Y)")
print("=" * 60)

# 장단기 금리차 계산
df_spread = ecos.get_yield_spread()
print(df_spread.tail())
print()

# ============================================================================
# 3. 물가 지표 조회
# ============================================================================

print("=" * 60)
print("4. 소비자물가지수 (CPI)")
print("=" * 60)

# CPI 조회
df_cpi = ecos.get_cpi()
print(df_cpi.tail())
print()

# 근원 CPI
df_core_cpi = ecos.get_core_cpi()
print("근원 CPI:")
print(df_core_cpi.tail())
print()

print("=" * 60)
print("5. 생산자물가지수 (PPI)")
print("=" * 60)

df_ppi = ecos.get_ppi()
print(df_ppi.tail())
print()

# ============================================================================
# 4. 성장 지표 조회
# ============================================================================

print("=" * 60)
print("6. GDP")
print("=" * 60)

# 분기별 실질 GDP
df_gdp_q = ecos.get_gdp(frequency="Q", basis="real")
print("분기별 실질 GDP:")
print(df_gdp_q.tail())
print()

# 연간 명목 GDP
df_gdp_a = ecos.get_gdp(frequency="A", basis="nominal")
print("연간 명목 GDP:")
print(df_gdp_a.tail())
print()

# ============================================================================
# 5. 통화 지표 조회
# ============================================================================

print("=" * 60)
print("7. 통화량 (M2)")
print("=" * 60)

df_m2 = ecos.get_money_supply(indicator="M2")
print(df_m2.tail())
print()

print("=" * 60)
print("8. 은행 대출")
print("=" * 60)

# 가계대출
df_household = ecos.get_bank_lending(sector="household")
print("가계대출:")
print(df_household.tail())
print()

# 기업대출
df_corporate = ecos.get_bank_lending(sector="corporate")
print("기업대출:")
print(df_corporate.tail())
print()

print("=" * 60)
print("예제 완료!")
print("=" * 60)
