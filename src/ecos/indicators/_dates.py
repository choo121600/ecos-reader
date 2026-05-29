"""
indicators 공용 날짜 헬퍼.

기본 조회 기간(시작/종료)을 빈도별로 계산하는 단일 진실원천 모듈입니다.
모든 함수는 ECOS API가 요구하는 문자열 형식을 반환합니다:

- ``default_daily``      → ``YYYYMMDD``
- ``default_monthly``    → ``YYYYMM``
- ``default_quarterly``  → ``YYYYQN``
- ``default_annual``     → ``YYYY``

각 함수는 ``today`` 인자로 기준일을 주입할 수 있어 테스트에서 결정적으로
동작합니다 (기본값은 ``datetime.now()``).
"""

from __future__ import annotations

from datetime import datetime, timedelta


def _reference(today: datetime | None) -> datetime:
    """기준일을 반환합니다. ``None``이면 현재 시각."""
    return today if today is not None else datetime.now()


def default_daily(days_back: int = 365, *, today: datetime | None = None) -> tuple[str, str]:
    """일별 기본 조회 기간을 ``YYYYMMDD`` 형식으로 반환합니다.

    ``timedelta`` 기반이므로 윤년 2/29 경계에서도
    ``ValueError: day is out of range`` 없이 안전합니다.
    """
    end = _reference(today)
    start = end - timedelta(days=days_back)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def default_monthly(months_back: int = 12, *, today: datetime | None = None) -> tuple[str, str]:
    """월별 기본 조회 기간을 ``YYYYMM`` 형식으로 반환합니다."""
    end = _reference(today)

    total_months = end.year * 12 + end.month
    start_total_months = total_months - months_back

    start_year = (start_total_months - 1) // 12
    start_month = (start_total_months - 1) % 12 + 1

    return f"{start_year}{start_month:02d}", f"{end.year}{end.month:02d}"


def default_quarterly(years_back: int = 5, *, today: datetime | None = None) -> tuple[str, str]:
    """분기별 기본 조회 기간을 ``YYYYQN`` 형식으로 반환합니다.

    시작은 ``years_back`` 년 전의 1분기, 종료는 기준일이 속한 분기입니다.
    """
    end = _reference(today)
    start_year = end.year - years_back
    current_quarter = (end.month - 1) // 3 + 1
    return f"{start_year}Q1", f"{end.year}Q{current_quarter}"


def default_annual(years_back: int = 10, *, today: datetime | None = None) -> tuple[str, str]:
    """연간 기본 조회 기간을 ``YYYY`` 형식으로 반환합니다."""
    end = _reference(today)
    return str(end.year - years_back), str(end.year)
