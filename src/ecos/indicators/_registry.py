"""선언적 지표 레지스트리 (#16).

새 지표 1개를 추가할 때 변경해야 하는 지점을 다섯 군데에서 한 군데로 줄이기
위한 단일 진실원천입니다. ``IndicatorSpec`` 한 줄을 :data:`INDICATORS` 에 등록하면
:func:`get_indicator` 로 즉시 조회할 수 있고, ``__all__`` 자동 생성 및
``IMPLEMENTATION_STATUS.md`` 자동 생성의 근거가 됩니다.

이 레지스트리는 "1 통계표 = 1 항목 = 1 함수" 의 단순 패턴(날짜 외 선택 인자가 없는
지표)을 대상으로 합니다. ``maturity`` / ``basis`` / ``variant`` 등 추가 선택 인자나
계산이 필요한 지표(예: ``get_yield_spread``)는 각 카테고리 모듈의 전용 함수로
유지하되, 단순 지표는 얇은 alias 로 이 레지스트리에 위임합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from ..client import get_client
from ..constants import (
    ITEM_BASE_RATE,
    ITEM_CORE_CPI,
    ITEM_CPI_TOTAL,
    ITEM_FISCAL_BALANCE,
    ITEM_PPI_TOTAL,
    PERIOD_ANNUAL,
    PERIOD_DAILY,
    PERIOD_MONTHLY,
    PERIOD_QUARTERLY,
    STAT_BASE_RATE,
    STAT_CORE_CPI,
    STAT_CPI,
    STAT_CPI_MONTHLY,
    STAT_FISCAL_BALANCE,
    STAT_PPI,
)
from ..parser import normalize_stat_result, parse_response
from ._dates import default_annual, default_daily, default_monthly, default_quarterly

if TYPE_CHECKING:
    import pandas as pd

# 날짜 포맷별 (기본 기간 계산 함수, 기본 lookback) 매핑.
DateFormat = Literal["D", "M", "Q", "A"]

_DATE_FORMAT_PERIOD: dict[DateFormat, str] = {
    "D": PERIOD_DAILY,
    "M": PERIOD_MONTHLY,
    "Q": PERIOD_QUARTERLY,
    "A": PERIOD_ANNUAL,
}

_DEFAULT_DATE_FUNC = {
    "D": default_daily,
    "M": default_monthly,
    "Q": default_quarterly,
    "A": default_annual,
}

# date_format별 기본 lookback (개수). spec에서 default_lookback 으로 재정의 가능.
_DEFAULT_LOOKBACK: dict[DateFormat, int] = {"D": 365, "M": 12, "Q": 5, "A": 10}


@dataclass(frozen=True)
class IndicatorSpec:
    """단일 지표의 선언적 정의.

    Parameters
    ----------
    name : str
        레지스트리 키이자 :func:`get_indicator` 의 식별자.
    stat_code : str
        ECOS 통계표코드.
    item_code1 : str
        항목코드1. 단일 항목 지표의 항목 선택자.
    date_format : {"D", "M", "Q", "A"}
        조회 주기. period 코드와 기본 날짜 형식을 함께 결정합니다.
    default_lookback : int, optional
        기본 조회 기간 길이. ``None`` 이면 date_format별 기본값을 사용합니다
        (D=365일, M=12개월, Q=5년, A=10년).
    unit : str, optional
        값의 단위(문서·메타용, 조회 동작에는 영향 없음).
    category : str
        지표 분류(문서 그룹핑용).
    description : str
        한 줄 설명(문서용).
    """

    name: str
    stat_code: str
    item_code1: str = ""
    date_format: DateFormat = "M"
    default_lookback: int | None = None
    unit: str | None = None
    category: str = ""
    description: str = ""

    @property
    def period(self) -> str:
        """ECOS API period 코드 (date_format에서 파생)."""
        return _DATE_FORMAT_PERIOD[self.date_format]

    def default_dates(self) -> tuple[str, str]:
        """이 지표의 기본 (시작, 종료) 날짜를 주기에 맞춘 형식으로 반환합니다."""
        lookback = (
            self.default_lookback
            if self.default_lookback is not None
            else _DEFAULT_LOOKBACK[self.date_format]
        )
        return _DEFAULT_DATE_FUNC[self.date_format](lookback)


# ============================================================================
# 레지스트리 — 새 단순 지표는 아래에 한 줄만 추가하면 동작합니다.
# ============================================================================

INDICATORS: dict[str, IndicatorSpec] = {
    "base_rate": IndicatorSpec(
        name="base_rate",
        stat_code=STAT_BASE_RATE,
        item_code1=ITEM_BASE_RATE,
        date_format="M",
        default_lookback=12,
        unit="%",
        category="금리",
        description="한국은행 기준금리",
    ),
    "fiscal_balance": IndicatorSpec(
        name="fiscal_balance",
        stat_code=STAT_FISCAL_BALANCE,
        item_code1=ITEM_FISCAL_BALANCE,
        date_format="M",
        default_lookback=24,
        unit="조원",
        category="재정",
        description="통합재정수지",
    ),
    "cpi": IndicatorSpec(
        name="cpi",
        stat_code=STAT_CPI,
        item_code1=ITEM_CPI_TOTAL,
        date_format="M",
        default_lookback=24,
        unit="2020=100",
        category="물가",
        description="소비자물가지수(CPI) 총지수(지수, 2020=100)",
    ),
    "core_cpi": IndicatorSpec(
        name="core_cpi",
        stat_code=STAT_CORE_CPI,
        item_code1=ITEM_CORE_CPI,
        date_format="M",
        default_lookback=24,
        unit="2020=100",
        category="물가",
        description="근원 소비자물가지수(Core CPI) 지수(2020=100)",
    ),
    "ppi": IndicatorSpec(
        name="ppi",
        stat_code=STAT_PPI,
        item_code1=ITEM_PPI_TOTAL,
        date_format="M",
        default_lookback=24,
        unit="2020=100",
        category="물가",
        description="생산자물가지수(PPI) 총지수(지수, 2020=100)",
    ),
    "cpi_monthly": IndicatorSpec(
        name="cpi_monthly",
        stat_code=STAT_CPI_MONTHLY,
        item_code1=ITEM_CPI_TOTAL,
        date_format="M",
        default_lookback=24,
        unit=None,
        category="물가",
        description="소비자물가지수 월별 원지수(총지수)",
    ),
}


def list_indicators() -> list[IndicatorSpec]:
    """등록된 모든 지표 spec을 이름순으로 반환합니다."""
    return [INDICATORS[name] for name in sorted(INDICATORS)]


def get_indicator(
    name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """레지스트리에 등록된 단일 지표를 이름으로 조회합니다.

    Parameters
    ----------
    name : str
        :data:`INDICATORS` 의 키 (예: ``"cpi"``, ``"fiscal_balance"``).
    start_date : str, optional
        조회 시작일. 주기에 맞춘 형식(M=YYYYMM 등). 기본값은 spec의 lookback.
    end_date : str, optional
        조회 종료일. 기본값은 현재.

    Returns
    -------
    pd.DataFrame
        컬럼: date, value, unit.

    Raises
    ------
    ValueError
        ``name`` 이 레지스트리에 없을 때. 사용 가능한 이름 목록을 함께 안내합니다.

    Examples
    --------
    >>> import ecos
    >>> df = ecos.get_indicator("cpi", start_date="202301", end_date="202312")
    """
    spec = INDICATORS.get(name)
    if spec is None:
        available = ", ".join(sorted(INDICATORS))
        raise ValueError(f"알 수 없는 지표 '{name}'. 사용 가능: {available}")

    if start_date is None or end_date is None:
        default_start, default_end = spec.default_dates()
        start_date = start_date or default_start
        end_date = end_date or default_end

    client = get_client()
    response = client.get_statistic_search(
        stat_code=spec.stat_code,
        period=spec.period,
        start_date=start_date,
        end_date=end_date,
        item_code1=spec.item_code1,
    )

    df = parse_response(response)
    return normalize_stat_result(df)
