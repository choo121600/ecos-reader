"""공용 날짜 헬퍼(`ecos.indicators._dates`) 회귀 테스트 (#9).

기준일을 주입해 결정적으로 검증하며, 특히 윤년(2/29)·월말·연말 경계를
다룹니다. 윤년 케이스는 기존 `datetime(year-1, month, day)` 구현에서
`ValueError`를 일으키던 회귀를 방지합니다.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from ecos.indicators._dates import (
    default_annual,
    default_daily,
    default_monthly,
    default_quarterly,
)


class TestDefaultDaily:
    def test_leap_day_does_not_raise(self):
        """윤년 2/29 기준일에서도 예외 없이 365일 전을 계산한다."""
        start, end = default_daily(365, today=datetime(2024, 2, 29))
        assert end == "20240229"
        assert start == "20230301"  # 2024-02-29 - 365d

    def test_basic_window(self):
        start, end = default_daily(365, today=datetime(2023, 6, 15))
        assert end == "20230615"
        assert start == "20220615"

    def test_year_end(self):
        start, end = default_daily(30, today=datetime(2024, 12, 31))
        assert end == "20241231"
        assert start == "20241201"


class TestDefaultMonthly:
    def test_basic(self):
        start, end = default_monthly(12, today=datetime(2024, 6, 1))
        assert end == "202406"
        assert start == "202306"

    def test_month_end_boundary(self):
        """월말 기준일이어도 월 단위 계산은 일자에 영향받지 않는다."""
        start, end = default_monthly(1, today=datetime(2024, 1, 31))
        assert end == "202401"
        assert start == "202312"

    def test_year_end_wraps(self):
        start, end = default_monthly(12, today=datetime(2024, 12, 31))
        assert end == "202412"
        assert start == "202312"

    def test_cross_year_underflow(self):
        start, end = default_monthly(6, today=datetime(2024, 3, 1))
        assert end == "202403"
        assert start == "202309"


class TestDefaultQuarterly:
    def test_q1(self):
        start, end = default_quarterly(5, today=datetime(2024, 2, 15))
        assert start == "2019Q1"
        assert end == "2024Q1"

    def test_q4_year_end(self):
        start, end = default_quarterly(5, today=datetime(2024, 12, 31))
        assert start == "2019Q1"
        assert end == "2024Q4"

    @pytest.mark.parametrize(
        "month,quarter",
        [(1, 1), (3, 1), (4, 2), (6, 2), (7, 3), (9, 3), (10, 4), (12, 4)],
    )
    def test_quarter_mapping(self, month, quarter):
        _, end = default_quarterly(5, today=datetime(2024, month, 1))
        assert end == f"2024Q{quarter}"


class TestDefaultAnnual:
    def test_basic(self):
        start, end = default_annual(10, today=datetime(2024, 6, 1))
        assert start == "2014"
        assert end == "2024"

    def test_year_end(self):
        start, end = default_annual(10, today=datetime(2024, 12, 31))
        assert start == "2014"
        assert end == "2024"


def test_defaults_use_now_when_today_omitted():
    """today 미지정 시 datetime.now() 기준으로 현재 연도를 반영한다."""
    current_year = datetime.now().year
    _, end = default_annual(10)
    assert end == str(current_year)
