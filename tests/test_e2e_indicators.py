"""
E2E 테스트 - High-level Indicator 함수들

실제 ECOS API를 호출하여 모든 indicator 함수가 정상 작동하는지 테스트합니다.
"""

from __future__ import annotations

import os

import pytest

import ecos


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
