"""
parser 모듈 테스트
"""

from __future__ import annotations

import pandas as pd

from ecos.parser import (
    normalize_stat_result,
    parse_response,
    parse_time_column,
)


class TestParseResponse:
    """parse_response 함수 테스트"""

    def test_parse_statistic_search_response(self):
        """StatisticSearch 응답 파싱"""
        response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "722Y001",
                        "STAT_NAME": "기준금리",
                        "ITEM_CODE1": "0101000",
                        "ITEM_NAME1": "기준금리",
                        "TIME": "202401",
                        "DATA_VALUE": "3.50",
                        "UNIT_NAME": "%",
                    }
                ]
            }
        }

        df = parse_response(response)

        assert not df.empty
        assert "stat_code" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["value"].iloc[0] == 3.50

    def test_parse_empty_response(self):
        """빈 응답 파싱"""
        response = {"StatisticSearch": {"row": []}}
        df = parse_response(response)
        assert df.empty

    def test_parse_no_data_response(self):
        """데이터 없는 응답 파싱"""
        response = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
        df = parse_response(response)
        assert df.empty

    def test_column_mapping(self):
        """컬럼명 매핑 확인"""
        response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "test",
                        "DATA_VALUE": "100",
                        "UNIT_NAME": "원",
                    }
                ]
            }
        }

        df = parse_response(response)

        assert "stat_code" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert "STAT_CODE" not in df.columns

    def test_numeric_conversion(self):
        """수치 컬럼 변환"""
        response = {
            "StatisticSearch": {
                "row": [
                    {"DATA_VALUE": "123.45"},
                    {"DATA_VALUE": "-67.89"},
                    {"DATA_VALUE": "invalid"},
                ]
            }
        }

        df = parse_response(response)

        assert df["value"].iloc[0] == 123.45
        assert df["value"].iloc[1] == -67.89
        assert pd.isna(df["value"].iloc[2])


class TestParseTimeColumn:
    """parse_time_column 함수 테스트"""

    def test_annual_format(self):
        """연간 형식 (YYYY)"""
        df = pd.DataFrame({"time": ["2020", "2021", "2022"]})
        result = parse_time_column(df)

        assert "date" in result.columns
        assert result["date"].iloc[0] == pd.Timestamp("2020-01-01")

    def test_quarterly_format(self):
        """분기 형식 (YYYYQN)"""
        df = pd.DataFrame({"time": ["2024Q1", "2024Q2", "2024Q3", "2024Q4"]})
        result = parse_time_column(df)

        assert result["date"].iloc[0] == pd.Timestamp("2024-01-01")
        assert result["date"].iloc[1] == pd.Timestamp("2024-04-01")
        assert result["date"].iloc[2] == pd.Timestamp("2024-07-01")
        assert result["date"].iloc[3] == pd.Timestamp("2024-10-01")

    def test_monthly_format(self):
        """월간 형식 (YYYYMM)"""
        df = pd.DataFrame({"time": ["202401", "202406", "202412"]})
        result = parse_time_column(df)

        assert result["date"].iloc[0] == pd.Timestamp("2024-01-01")
        assert result["date"].iloc[1] == pd.Timestamp("2024-06-01")
        assert result["date"].iloc[2] == pd.Timestamp("2024-12-01")

    def test_daily_format(self):
        """일간 형식 (YYYYMMDD)"""
        df = pd.DataFrame({"time": ["20240115", "20240630"]})
        result = parse_time_column(df)

        assert result["date"].iloc[0] == pd.Timestamp("2024-01-15")
        assert result["date"].iloc[1] == pd.Timestamp("2024-06-30")

    def test_empty_dataframe(self):
        """빈 DataFrame"""
        df = pd.DataFrame()
        result = parse_time_column(df)
        assert result.empty


class TestNormalizeStatResult:
    """normalize_stat_result 함수 테스트"""

    def test_default_columns(self):
        """기본 컬럼 선택"""
        df = pd.DataFrame(
            {
                "time": ["202401", "202402"],
                "value": [1.0, 2.0],
                "unit": ["%", "%"],
                "stat_code": ["test", "test"],
            }
        )

        result = normalize_stat_result(df)

        assert list(result.columns) == ["date", "value", "unit"]

    def test_custom_columns(self):
        """커스텀 컬럼 선택"""
        df = pd.DataFrame(
            {
                "time": ["202401"],
                "value": [1.0],
                "stat_code": ["test"],
            }
        )

        result = normalize_stat_result(df, columns=["date", "value", "stat_code"])

        assert "date" in result.columns
        assert "value" in result.columns
        assert "stat_code" in result.columns

    def test_sort_by_date(self):
        """날짜 기준 정렬"""
        df = pd.DataFrame(
            {
                "time": ["202403", "202401", "202402"],
                "value": [3.0, 1.0, 2.0],
                "unit": ["%", "%", "%"],
            }
        )

        result = normalize_stat_result(df)

        assert result["value"].tolist() == [1.0, 2.0, 3.0]
