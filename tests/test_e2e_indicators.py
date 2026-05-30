"""
E2E 테스트 - High-level Indicator 함수들

실제 ECOS API를 호출하여 모든 indicator 함수가 정상 작동하는지 테스트합니다.
"""

from __future__ import annotations

import os
from typing import ClassVar

import pytest

import ecos
from ecos.constants import CPI_CATEGORY_CODES

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module", autouse=True)
def setup_api_key():
    """API 키 설정"""
    api_key = os.getenv("ECOS_API_KEY")
    if not api_key:
        pytest.skip("ECOS_API_KEY 환경 변수가 설정되지 않았습니다.")
    ecos.set_api_key(api_key)
    ecos.disable_cache()  # 실제 API 호출 확인을 위해 캐시 비활성화
    yield
    ecos.clear_api_key()


class TestE2EInterestRateIndicators:
    """금리 지표 E2E 테스트"""

    def test_get_base_rate(self):
        """한국은행 기준금리 조회"""
        df = ecos.get_base_rate(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["unit"].iloc[0] == "연%"  # 연% (annual percentage)
        assert len(df) > 0

    def test_get_treasury_yield_3y(self):
        """국고채 3년물 수익률 조회"""
        df = ecos.get_treasury_yield(maturity="3Y", start_date="20230101", end_date="20231231")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_treasury_yield_10y(self):
        """국고채 10년물 수익률 조회"""
        df = ecos.get_treasury_yield(maturity="10Y", start_date="20230101", end_date="20231231")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_yield_spread(self):
        """장단기 금리차 조회"""
        df = ecos.get_yield_spread(start_date="20230101", end_date="20231231")

        assert not df.empty
        assert "date" in df.columns
        assert "long_yield" in df.columns
        assert "short_yield" in df.columns
        assert "spread" in df.columns
        assert len(df) > 0


class TestE2EPriceIndicators:
    """물가 지표 E2E 테스트"""

    def test_get_cpi(self):
        """소비자물가지수 조회"""
        df = ecos.get_cpi(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_core_cpi(self):
        """근원 CPI 조회"""
        df = ecos.get_core_cpi(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_ppi(self):
        """생산자물가지수 조회"""
        df = ecos.get_ppi(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EGrowthIndicators:
    """성장 지표 E2E 테스트"""

    def test_get_gdp_quarterly_real(self):
        """실질 GDP (분기) 조회"""
        df = ecos.get_gdp(frequency="Q", basis="real", start_date="2020Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_gdp_annual_real(self):
        """실질 GDP (연간) 조회"""
        df = ecos.get_gdp(frequency="A", basis="real", start_date="2020", end_date="2023")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_quarterly_nominal(self):
        """명목 GDP (분기) 조회"""
        df = ecos.get_gdp(frequency="Q", basis="nominal", start_date="2020Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_deflator(self):
        """GDP 디플레이터 조회"""
        df = ecos.get_gdp_deflator(start_date="2020Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EMoneyIndicators:
    """통화 지표 E2E 테스트"""

    def test_get_money_supply_m1(self):
        """M1 통화량 조회"""
        df = ecos.get_money_supply(indicator="M1", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_money_supply_m2(self):
        """M2 통화량 조회"""
        df = ecos.get_money_supply(indicator="M2", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_money_supply_lf(self):
        """Lf 통화량 조회"""
        df = ecos.get_money_supply(indicator="Lf", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_bank_lending_all(self):
        """은행 전체 대출 조회"""
        df = ecos.get_bank_lending(sector="all", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_bank_lending_household(self):
        """은행 가계 대출 조회"""
        df = ecos.get_bank_lending(sector="household", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EFiscalIndicators:
    """재정 지표 E2E 테스트"""

    def test_get_fiscal_balance(self):
        """통합재정수지 조회"""
        df = ecos.get_fiscal_balance(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0


class TestE2EStockIndicators:
    """주식시장 지표 E2E 테스트"""

    def test_get_stock_index_daily(self):
        """주가지수 조회 (일별)"""
        df = ecos.get_stock_index(frequency="daily", start_date="20230101", end_date="20230131")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_stock_index_monthly(self):
        """주가지수 조회 (월별)"""
        df = ecos.get_stock_index(frequency="monthly", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_investor_trading(self):
        """투자자별 주식거래 조회"""
        df = ecos.get_investor_trading(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0


class TestE2EBondIndicators:
    """채권시장 지표 E2E 테스트"""

    def test_get_bond_yield_type(self):
        """채권 수익률 조회 (종류별)"""
        df = ecos.get_bond_yield(bond_type="종류별", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_bond_yield_market(self):
        """채권 수익률 조회 (시장별)"""
        df = ecos.get_bond_yield(bond_type="시장별", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EBankRateIndicators:
    """예금·대출 금리 지표 E2E 테스트"""

    def test_get_bank_deposit_rate_new(self):
        """예금은행 수신금리 (신규취급액)"""
        df = ecos.get_bank_deposit_rate(basis="신규취급액", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_bank_deposit_rate_balance(self):
        """예금은행 수신금리 (잔액)"""
        df = ecos.get_bank_deposit_rate(basis="잔액", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_bank_lending_rate_new(self):
        """예금은행 대출금리 (신규취급액)"""
        df = ecos.get_bank_lending_rate(basis="신규취급액", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_bank_lending_rate_balance(self):
        """예금은행 대출금리 (잔액)"""
        df = ecos.get_bank_lending_rate(basis="잔액", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EMoneyVariantsIndicators:
    """통화 세부 지표 E2E 테스트"""

    def test_get_m1_variants_avg_seasonal(self):
        """M1 세부 데이터 조회 (평잔_계절조정)"""
        df = ecos.get_m1_variants(variant="평잔_계절조정", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_m1_variants_avg_raw(self):
        """M1 세부 데이터 조회 (평잔_원계열)"""
        df = ecos.get_m1_variants(variant="평잔_원계열", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_m1_variants_end_seasonal(self):
        """M1 세부 데이터 조회 (말잔_계절조정)"""
        df = ecos.get_m1_variants(variant="말잔_계절조정", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_m2_variants_avg_seasonal(self):
        """M2 세부 데이터 조회 (평잔_계절조정)"""
        df = ecos.get_m2_variants(variant="평잔_계절조정", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_m2_variants_avg_raw(self):
        """M2 세부 데이터 조회 (평잔_원계열)"""
        df = ecos.get_m2_variants(variant="평잔_원계열", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_m2_variants_end_seasonal(self):
        """M2 세부 데이터 조회 (말잔_계절조정)"""
        df = ecos.get_m2_variants(variant="말잔_계절조정", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_m2_by_holder_avg_seasonal(self):
        """M2 경제주체별 조회 (평잔_계절조정)"""
        df = ecos.get_m2_by_holder(variant="평잔_계절조정", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_m2_by_holder_avg_raw(self):
        """M2 경제주체별 조회 (평잔_원계열)"""
        df = ecos.get_m2_by_holder(variant="평잔_원계열", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EHouseholdFinanceIndicators:
    """가계금융 지표 E2E 테스트"""

    def test_get_household_credit_sector(self):
        """가계신용 조회 (업권별)"""
        df = ecos.get_household_credit(category="업권별", start_date="2023Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_household_credit_purpose(self):
        """가계신용 조회 (용도별)"""
        df = ecos.get_household_credit(category="용도별", start_date="2023Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_household_lending_detail(self):
        """예금취급기관 가계대출 용도별"""
        df = ecos.get_household_lending_detail(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_borrower_loan_new(self):
        """차주별 가계대출 (신규)"""
        df = ecos.get_borrower_loan(loan_type="신규", start_date="2023Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_borrower_loan_balance(self):
        """차주별 가계대출 (잔액)"""
        df = ecos.get_borrower_loan(loan_type="잔액", start_date="2023Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EGrowthDetailIndicators:
    """성장 세부 지표 E2E 테스트"""

    def test_get_gdp_growth_rate_quarterly(self):
        """실질 GDP 성장률 (분기)"""
        df = ecos.get_gdp_growth_rate(frequency="Q", start_date="2023Q1", end_date="2023Q4")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    @pytest.mark.skip(reason="stat_code 200Y104는 분기 데이터만 제공 (연간 미지원)")
    def test_get_gdp_growth_rate_annual(self):
        """실질 GDP 성장률 (연간) - 미지원"""
        df = ecos.get_gdp_growth_rate(frequency="A", start_date="2020", end_date="2023")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_by_industry_real_seasonal(self):
        """산업별 GDP (실질, 계절조정)"""
        df = ecos.get_gdp_by_industry(
            basis="real", seasonal_adj=True, frequency="Q", start_date="2023Q1", end_date="2023Q4"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_gdp_by_industry_nominal_seasonal(self):
        """산업별 GDP (명목, 계절조정)"""
        df = ecos.get_gdp_by_industry(
            basis="nominal",
            seasonal_adj=True,
            frequency="Q",
            start_date="2023Q1",
            end_date="2023Q4",
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_by_industry_real_raw(self):
        """산업별 GDP (실질, 원계열)"""
        df = ecos.get_gdp_by_industry(
            basis="real", seasonal_adj=False, frequency="Q", start_date="2023Q1", end_date="2023Q4"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_by_expenditure_real(self):
        """지출항목별 GDP (실질)"""
        df = ecos.get_gdp_by_expenditure(
            basis="real", frequency="Q", start_date="2023Q1", end_date="2023Q4"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_gdp_by_expenditure_nominal(self):
        """지출항목별 GDP (명목)"""
        df = ecos.get_gdp_by_expenditure(
            basis="nominal", frequency="Q", start_date="2023Q1", end_date="2023Q4"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_get_gdp_deflator_by_industry_quarterly(self):
        """산업별 GDP 디플레이터 (분기)"""
        df = ecos.get_gdp_deflator_by_industry(
            frequency="Q", start_date="2023Q1", end_date="2023Q4"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) > 0

    def test_get_gdp_deflator_by_industry_annual(self):
        """산업별 GDP 디플레이터 (연간)"""
        df = ecos.get_gdp_deflator_by_industry(frequency="A", start_date="2020", end_date="2023")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EPriceDetailIndicators:
    """물가 세부 지표 E2E 테스트"""

    def test_get_cpi_monthly(self):
        """CPI 월별 원지수 (901Y009 총지수)"""
        df = ecos.get_cpi_monthly(start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    @pytest.mark.skip(reason="stat_code 901Y002가 ECOS API에 존재하지 않음")
    def test_get_cpi_by_category_goods(self):
        """CPI 세부 항목 - 상품 (존재하지 않는 통계)"""
        df = ecos.get_cpi_by_category(category="상품", start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0


class TestE2EIntegrationWorkflow:
    """통합 워크플로우 테스트"""

    def test_complete_macro_dashboard(self):
        """거시경제 대시보드 데이터 수집"""

        # 금리
        base_rate = ecos.get_base_rate(start_date="202301", end_date="202312")
        assert not base_rate.empty

        # 물가
        cpi = ecos.get_cpi(start_date="202301", end_date="202312")
        assert not cpi.empty

        # 성장
        gdp = ecos.get_gdp(frequency="Q", basis="real", start_date="2023Q1", end_date="2023Q4")
        assert not gdp.empty

        # 통화
        m2 = ecos.get_money_supply(indicator="M2", start_date="202301", end_date="202312")
        assert not m2.empty

        # 모든 데이터가 정상적으로 조회됨
        assert len(base_rate) > 0
        assert len(cpi) > 0
        assert len(gdp) > 0
        assert len(m2) > 0

    def test_financial_market_dashboard(self):
        """금융시장 대시보드 데이터 수집"""

        # 재정
        fiscal = ecos.get_fiscal_balance(start_date="202301", end_date="202312")
        assert not fiscal.empty

        # 주식
        stock = ecos.get_stock_index(frequency="monthly", start_date="202301", end_date="202312")
        assert not stock.empty

        # 채권
        bond = ecos.get_bond_yield(bond_type="종류별", start_date="202301", end_date="202312")
        assert not bond.empty

        # 모든 데이터가 정상적으로 조회됨
        assert len(fiscal) > 0
        assert len(stock) > 0
        assert len(bond) > 0

    def test_household_finance_dashboard(self):
        """가계금융 대시보드 데이터 수집"""

        # 가계신용
        credit = ecos.get_household_credit(
            category="업권별", start_date="2023Q1", end_date="2023Q4"
        )
        assert not credit.empty

        # 가계대출
        lending = ecos.get_household_lending_detail(start_date="202301", end_date="202312")
        assert not lending.empty

        # 차주별 대출
        borrower = ecos.get_borrower_loan(loan_type="잔액", start_date="2023Q1", end_date="2023Q4")
        assert not borrower.empty

        # 모든 데이터가 정상적으로 조회됨
        assert len(credit) > 0
        assert len(lending) > 0
        assert len(borrower) > 0

    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        # 캐시 활성화
        ecos.enable_cache()

        # 첫 번째 호출 (API 호출)
        df1 = ecos.get_base_rate(start_date="202301", end_date="202303")

        # 두 번째 호출 (캐시에서 가져옴)
        df2 = ecos.get_base_rate(start_date="202301", end_date="202303")

        # 결과가 동일해야 함
        assert len(df1) == len(df2)
        assert df1.equals(df2)

        # 캐시 클리어
        ecos.clear_cache()

        # 비활성화
        ecos.disable_cache()


class TestE2EIntegrationNewIndicators:
    """신규 지표 통합 워크플로우 테스트"""

    def test_financial_market_dashboard(self):
        """금융시장 대시보드 데이터 수집"""

        # 재정
        fiscal = ecos.get_fiscal_balance(start_date="202301", end_date="202312")
        assert not fiscal.empty

        # 주식
        stock = ecos.get_stock_index(frequency="monthly", start_date="202301", end_date="202312")
        assert not stock.empty

        # 채권
        bond = ecos.get_bond_yield(bond_type="종류별", start_date="202301", end_date="202312")
        assert not bond.empty

        # 모든 데이터가 정상적으로 조회됨
        assert len(fiscal) > 0
        assert len(stock) > 0
        assert len(bond) > 0

    def test_household_finance_dashboard(self):
        """가계금융 대시보드 데이터 수집"""

        # 가계신용
        credit = ecos.get_household_credit(
            category="업권별", start_date="2023Q1", end_date="2023Q4"
        )
        assert not credit.empty

        # 가계대출
        lending = ecos.get_household_lending_detail(start_date="202301", end_date="202312")
        assert not lending.empty

        # 차주별 대출
        borrower = ecos.get_borrower_loan(loan_type="잔액", start_date="2023Q1", end_date="2023Q4")
        assert not borrower.empty

        # 모든 데이터가 정상적으로 조회됨
        assert len(credit) > 0
        assert len(lending) > 0
        assert len(borrower) > 0


class TestE2ERegressionV016:
    """v0.1.6(#27, #28)에서 수정한 stat_code/item_code 매핑 회귀 가드 (#30).

    빈 응답·잘못된 데이터를 돌려주던 변종들이 다시 깨지면 즉시 감지하기 위한
    회귀 케이스 모음. 각 케이스는 수정 당시의 의도(연간 fallback, 측정 기준,
    지원되지 않는 조합 차단 등)를 명시적으로 검증한다.
    """

    # ---- GDP 연간 fallback (#28) ----

    def test_gdp_growth_rate_annual_fallback(self):
        """frequency='A'는 계절조정(분기 전용) 대신 원계열 200Y106으로 fallback해야 함."""
        df = ecos.get_gdp_growth_rate(frequency="A", start_date="2020", end_date="2023")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    @pytest.mark.parametrize("basis", ["real", "nominal"])
    def test_gdp_by_expenditure_annual_fallback(self, basis):
        """frequency='A'는 원계열(real→200Y110 / nominal→200Y109)로 fallback해야 함."""
        df = ecos.get_gdp_by_expenditure(
            basis=basis, frequency="A", start_date="2020", end_date="2023"
        )

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    def test_gdp_by_industry_seasonal_annual_raises(self):
        """계절조정 시리즈는 ECOS에서 분기만 제공 → seasonal_adj=True+연간은 차단."""
        with pytest.raises(ValueError, match="seasonal_adj"):
            ecos.get_gdp_by_industry(
                seasonal_adj=True, frequency="A", start_date="2020", end_date="2023"
            )

    # ---- M2 보유주체별 말잔 (#28) ----

    @pytest.mark.parametrize("variant", ["말잔_계절조정", "말잔_원계열"])
    def test_m2_by_holder_eop_variants(self, variant):
        """말잔_계절조정(BBGS00)/말잔_원계열(BBGA00) 모두 데이터를 반환해야 함."""
        df = ecos.get_m2_by_holder(variant=variant, start_date="202301", end_date="202312")

        assert not df.empty
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    # ---- CPI 세부 카테고리 (#27) ----

    @pytest.mark.parametrize("category", list(CPI_CATEGORY_CODES.keys()))
    def test_cpi_by_category_all(self, category):
        """8개 CPI 카테고리 전부 (stat_code, item_code) 매핑이 살아있어야 함."""
        df = ecos.get_cpi_by_category(category=category, start_date="202301", end_date="202312")

        assert not df.empty, f"category='{category}' returned empty"
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) > 0

    # ---- 채권 수익률 월별 1행 (#28) ----

    @pytest.mark.parametrize("bond_type", ["종류별", "시장별"])
    def test_bond_yield_one_row_per_month(self, bond_type):
        """혼합 measure 버그 회귀: 결과는 월별 1행이어야 함 (한 달에 여러 행 금지)."""
        df = ecos.get_bond_yield(bond_type=bond_type, start_date="202301", end_date="202312")

        assert not df.empty
        # 같은 달에 여러 row가 섞이면 nunique(month) < len(df)
        months = df["date"].dt.to_period("M")
        assert months.nunique() == len(df), (
            f"bond_type='{bond_type}': 월별 1행이 아님 "
            f"(rows={len(df)}, unique_months={months.nunique()})"
        )

    # ---- 차주별 가계대출: v0.1.6 차단 조합이 #29 재설계로 정상화 ----

    # v0.1.6에서 stat_code 매핑이 ECOS와 일치하지 않아 ValueError로 차단했던 7개 조합.
    # #29 재설계(181Y001/181Y002 + item_code prefix 필터)로 이제 정상 데이터를 반환한다.
    _PREVIOUSLY_BROKEN_BORROWER_COMBINATIONS: ClassVar = [
        ("신규", "연령별"),
        ("신규", "지역별"),
        ("신규", "담보유형별"),
        ("신규", "업권별"),
        ("잔액", "연령별"),
        ("잔액", "지역별"),
        ("잔액", "업권별"),
    ]

    @pytest.mark.parametrize(("loan_type", "category"), _PREVIOUSLY_BROKEN_BORROWER_COMBINATIONS)
    def test_borrower_loan_previously_broken_now_return_data(self, loan_type, category):
        """v0.1.6 차단 7개 조합은 #29 재설계 후 long-format 실데이터를 반환해야 함."""
        df = ecos.get_borrower_loan(
            loan_type=loan_type,
            category=category,
            start_date="2023Q1",
            end_date="2023Q4",
        )

        assert not df.empty, f"({loan_type}, {category}) returned empty"
        assert "category_value" in df.columns
        assert "value" in df.columns
        # 분류축이므로 세부 항목이 2개 이상 존재해야 함
        assert df["category_value"].nunique() >= 2
