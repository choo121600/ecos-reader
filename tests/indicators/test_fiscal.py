"""재정 지표 모듈 단위 테스트 (#13).

`get_fiscal_balance`를 mock 응답으로 검증한다 (ECOS_API_KEY 불필요).
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.indicators.fiscal import get_fiscal_balance


@pytest.mark.usefixtures("set_api_key")
class TestGetFiscalBalance:
    """get_fiscal_balance 함수 테스트"""

    @responses.activate
    def test_success(self):
        """통합재정수지 조회 성공"""
        mock = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "301Y013",
                        "TIME": "202401",
                        "DATA_VALUE": "-5.20",
                        "UNIT_NAME": "조원",
                    },
                    {
                        "STAT_CODE": "301Y013",
                        "TIME": "202402",
                        "DATA_VALUE": "-3.80",
                        "UNIT_NAME": "조원",
                    },
                ]
            }
        }
        responses.add(responses.GET, url=re.compile(r".*"), json=mock, status=200)

        df = get_fiscal_balance(start_date="202401", end_date="202402")

        assert not df.empty
        assert {"date", "value", "unit"} <= set(df.columns)
        assert df["value"].iloc[0] == -5.20
        assert len(df) == 2

    @responses.activate
    def test_empty_response_returns_empty_df(self):
        """데이터 없음(INFO-200)은 에러가 아니라 빈 DataFrame"""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}},
            status=200,
        )

        df = get_fiscal_balance(start_date="202401", end_date="202402")
        assert df.empty
