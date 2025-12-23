"""
pytest 공통 fixtures

테스트 환경 설정 및 mock 데이터를 제공합니다.
"""

from __future__ import annotations

from typing import Any

import pytest
import responses

import ecos
from ecos.cache import get_cache
from ecos.client import reset_client
from ecos.config import clear_api_key


@pytest.fixture(autouse=True)
def reset_state():
    """각 테스트 전후로 상태를 초기화합니다."""
    # 테스트 전 초기화
    clear_api_key()
    reset_client()
    get_cache().clear()

    yield

    # 테스트 후 정리
    clear_api_key()
    reset_client()
    get_cache().clear()


@pytest.fixture
def api_key():
    """테스트용 API 키"""
    return "test_api_key_12345"


@pytest.fixture
def set_api_key(api_key: str):
    """API 키를 설정합니다."""
    ecos.set_api_key(api_key)
    return api_key


@pytest.fixture
def mock_responses():
    """HTTP 응답 모킹을 위한 fixture"""
    with responses.RequestsMock() as rsps:
        yield rsps


# ============================================================================
# Mock 응답 데이터
# ============================================================================


def make_statistic_search_response(
    stat_code: str = "722Y001",
    item_code1: str = "0101000",
    data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """StatisticSearch API 응답을 생성합니다."""
    if data is None:
        data = [
            {
                "STAT_CODE": stat_code,
                "STAT_NAME": "테스트 통계",
                "ITEM_CODE1": item_code1,
                "ITEM_NAME1": "테스트 항목",
                "TIME": "202401",
                "DATA_VALUE": "3.50",
                "UNIT_NAME": "%",
            },
            {
                "STAT_CODE": stat_code,
                "STAT_NAME": "테스트 통계",
                "ITEM_CODE1": item_code1,
                "ITEM_NAME1": "테스트 항목",
                "TIME": "202402",
                "DATA_VALUE": "3.50",
                "UNIT_NAME": "%",
            },
            {
                "STAT_CODE": stat_code,
                "STAT_NAME": "테스트 통계",
                "ITEM_CODE1": item_code1,
                "ITEM_NAME1": "테스트 항목",
                "TIME": "202403",
                "DATA_VALUE": "3.25",
                "UNIT_NAME": "%",
            },
        ]

    return {"StatisticSearch": {"row": data}}


def make_empty_response() -> dict[str, Any]:
    """빈 응답 (데이터 없음)"""
    return {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}


def make_error_response(code: str = "ERROR-100", message: str = "에러 발생") -> dict[str, Any]:
    """에러 응답"""
    return {"RESULT": {"CODE": code, "MESSAGE": message}}


@pytest.fixture
def mock_base_rate_response():
    """기준금리 응답 데이터"""
    return make_statistic_search_response(
        stat_code="722Y001",
        item_code1="0101000",
        data=[
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "한국은행 기준금리",
                "ITEM_CODE1": "0101000",
                "ITEM_NAME1": "기준금리",
                "TIME": "202401",
                "DATA_VALUE": "3.50",
                "UNIT_NAME": "%",
            },
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "한국은행 기준금리",
                "ITEM_CODE1": "0101000",
                "ITEM_NAME1": "기준금리",
                "TIME": "202402",
                "DATA_VALUE": "3.50",
                "UNIT_NAME": "%",
            },
        ],
    )


@pytest.fixture
def mock_cpi_response():
    """CPI 응답 데이터"""
    return make_statistic_search_response(
        stat_code="901Y009",
        item_code1="0",
        data=[
            {
                "STAT_CODE": "901Y009",
                "STAT_NAME": "소비자물가지수",
                "ITEM_CODE1": "0",
                "ITEM_NAME1": "총지수",
                "TIME": "202401",
                "DATA_VALUE": "3.20",
                "UNIT_NAME": "%",
            },
            {
                "STAT_CODE": "901Y009",
                "STAT_NAME": "소비자물가지수",
                "ITEM_CODE1": "0",
                "ITEM_NAME1": "총지수",
                "TIME": "202402",
                "DATA_VALUE": "3.10",
                "UNIT_NAME": "%",
            },
        ],
    )


@pytest.fixture
def mock_gdp_response():
    """GDP 응답 데이터"""
    return make_statistic_search_response(
        stat_code="200Y001",
        item_code1="10101",
        data=[
            {
                "STAT_CODE": "200Y001",
                "STAT_NAME": "국내총생산",
                "ITEM_CODE1": "10101",
                "ITEM_NAME1": "국내총생산",
                "TIME": "2024Q1",
                "DATA_VALUE": "560000",
                "UNIT_NAME": "십억원",
            },
            {
                "STAT_CODE": "200Y001",
                "STAT_NAME": "국내총생산",
                "ITEM_CODE1": "10101",
                "ITEM_NAME1": "국내총생산",
                "TIME": "2024Q2",
                "DATA_VALUE": "570000",
                "UNIT_NAME": "십억원",
            },
        ],
    )
