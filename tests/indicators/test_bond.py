"""채권시장 지표 모듈 단위 테스트 (#13).

`get_bond_yield`를 mock 응답으로 검증한다 (ECOS_API_KEY 불필요).
종류별/시장별 모두 EcosPartialCoverageWarning을 발생시키므로 함께 검증한다.
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators._deprecations import EcosPartialCoverageWarning
from ecos.indicators.bond import get_bond_yield


def _mock(value: str = "45.20", stat_code: str = "901Y015") -> dict:
    return {
        "StatisticSearch": {
            "row": [
                {
                    "STAT_CODE": stat_code,
                    "TIME": "202401",
                    "DATA_VALUE": value,
                    "UNIT_NAME": "조원",
                }
            ]
        }
    }


@pytest.mark.usefixtures("set_api_key")
class TestGetBondYield:
    """get_bond_yield 함수 테스트"""

    @responses.activate
    def test_by_type_success(self):
        """종류별 채권 거래 조회 성공 (+ 부분커버리지 경고)"""
        responses.add(responses.GET, url=re.compile(r".*"), json=_mock(), status=200)

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_bond_yield(bond_type="종류별", start_date="202401", end_date="202401")

        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)
        assert df["value"].iloc[0] == 45.20

    @responses.activate
    def test_by_market_success(self):
        """시장별 채권 거래 조회 성공 (+ 부분커버리지 경고)"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=_mock(value="38.70", stat_code="901Y120"),
            status=200,
        )

        with pytest.warns(EcosPartialCoverageWarning):
            df = get_bond_yield(bond_type="시장별", start_date="202401", end_date="202401")

        assert not df.empty
        assert df["value"].iloc[0] == 38.70

    def test_invalid_bond_type_raises(self):
        """허용되지 않은 bond_type은 ValueError"""
        with pytest.raises(ValueError, match="bond_type"):
            get_bond_yield(bond_type="invalid")
