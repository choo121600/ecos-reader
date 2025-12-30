"""
E2E 테스트 - 실제 ECOS API를 호출하는 통합 테스트

이 테스트는 실제 ECOS API를 호출하므로 유효한 API 키가 필요합니다.
환경 변수 ECOS_API_KEY에 API 키를 설정해야 합니다.
"""

from __future__ import annotations

import os

import pytest

from ecos.client import EcosClient
from ecos.parser import parse_response


@pytest.fixture
def e2e_client():
    """E2E 테스트용 클라이언트 생성"""
    api_key = os.getenv("ECOS_API_KEY")
    if not api_key:
        pytest.skip("ECOS_API_KEY 환경 변수가 설정되지 않았습니다.")
    return EcosClient(api_key=api_key, use_cache=False)


class TestE2EStatisticSearch:
    """StatisticSearch API E2E 테스트"""

    def test_annual_data(self, e2e_client):
        """연간 데이터 조회 테스트"""
        result = e2e_client.get_statistic_search(
            stat_code="200Y101",
            period="A",
            start_date="2020",
            end_date="2023",
            item_code1="10101",
            start=1,
            end=10,
        )

        assert "StatisticSearch" in result
        assert "row" in result["StatisticSearch"]

        rows = result["StatisticSearch"]["row"]
        assert len(rows) > 0

        # DataFrame 변환 테스트
        df = parse_response(result)
        assert not df.empty
        assert "value" in df.columns
        assert "time" in df.columns

    def test_quarterly_data(self, e2e_client):
        """분기 데이터 조회 테스트 - GDP 성장률"""
        # 901Y009: GDP 및 GNI (분기 및 연간)
        result = e2e_client.get_statistic_search(
            stat_code="901Y009",
            period="Q",
            start_date="2020Q1",
            end_date="2023Q4",
            start=1,
            end=20,
        )

        assert "StatisticSearch" in result
        rows = result["StatisticSearch"]["row"]
        assert len(rows) > 0

    def test_monthly_data(self, e2e_client):
        """월간 데이터 조회 테스트 - 소비자물가지수"""
        # 901Y009: GDP 및 GNI, 월간 데이터 사용
        result = e2e_client.get_statistic_search(
            stat_code="901Y009",
            period="M",
            start_date="202301",
            end_date="202312",
            start=1,
            end=20,
        )

        assert "StatisticSearch" in result
        rows = result["StatisticSearch"]["row"]
        assert len(rows) > 0

        # 데이터 형식 확인
        first_row = rows[0]
        assert "TIME" in first_row
        assert "DATA_VALUE" in first_row
        assert "UNIT_NAME" in first_row


class TestE2EStatisticTableList:
    """StatisticTableList API E2E 테스트"""

    def test_get_table_list(self, e2e_client):
        """통계표 목록 조회 테스트"""
        result = e2e_client.get_statistic_table_list(
            start=1,
            end=10,
        )

        assert "StatisticTableList" in result
        assert "row" in result["StatisticTableList"]

        rows = result["StatisticTableList"]["row"]
        assert len(rows) > 0

        # DataFrame 변환 테스트
        df = parse_response(result)
        assert not df.empty
        assert "stat_code" in df.columns
        assert "stat_name" in df.columns

    def test_get_table_list_with_code(self, e2e_client):
        """특정 통계표코드로 필터링 테스트"""
        result = e2e_client.get_statistic_table_list(
            stat_code="200Y101",
            start=1,
            end=10,
        )

        assert "StatisticTableList" in result
        rows = result["StatisticTableList"]["row"]

        # 결과가 있으면 검증
        if len(rows) > 0:
            first_row = rows[0]
            assert "STAT_CODE" in first_row
            assert "STAT_NAME" in first_row


class TestE2EStatisticItemList:
    """StatisticItemList API E2E 테스트"""

    def test_get_item_list(self, e2e_client):
        """통계 세부항목 목록 조회 테스트"""
        result = e2e_client.get_statistic_item_list(
            stat_code="200Y101",
            start=1,
            end=10,
        )

        assert "StatisticItemList" in result
        assert "row" in result["StatisticItemList"]

        rows = result["StatisticItemList"]["row"]
        assert len(rows) > 0

        # DataFrame 변환 테스트
        df = parse_response(result)
        assert not df.empty

        # 필수 컬럼 확인
        first_row = rows[0]
        assert "STAT_CODE" in first_row
        assert "ITEM_CODE" in first_row
        assert "ITEM_NAME" in first_row


class TestE2EStatisticWord:
    """StatisticWord API E2E 테스트"""

    def test_search_word(self, e2e_client):
        """통계용어 검색 테스트"""
        result = e2e_client.get_statistic_word(
            word="소비자물가지수",
            start=1,
            end=10,
        )

        assert "StatisticWord" in result

        # 데이터가 있는 경우 검증
        if "row" in result["StatisticWord"]:
            rows = result["StatisticWord"]["row"]
            if len(rows) > 0:
                df = parse_response(result)
                assert not df.empty
                assert "word" in df.columns
                assert "content" in df.columns

    def test_search_gdp(self, e2e_client):
        """GDP 용어 검색 테스트"""
        result = e2e_client.get_statistic_word(
            word="GDP",
            start=1,
            end=10,
        )

        assert "StatisticWord" in result


class TestE2EKeyStatisticList:
    """KeyStatisticList API E2E 테스트"""

    def test_get_key_statistics(self, e2e_client):
        """100대 통계지표 조회 테스트"""
        result = e2e_client.get_key_statistic_list(
            start=1,
            end=10,
        )

        assert "KeyStatisticList" in result
        assert "row" in result["KeyStatisticList"]

        rows = result["KeyStatisticList"]["row"]
        assert len(rows) > 0

        # DataFrame 변환 테스트
        df = parse_response(result)
        assert not df.empty

        # 필수 컬럼 확인
        first_row = rows[0]
        assert "CLASS_NAME" in first_row
        assert "KEYSTAT_NAME" in first_row
        assert "DATA_VALUE" in first_row
        assert "CYCLE" in first_row
        assert "UNIT_NAME" in first_row

    def test_get_all_key_statistics(self, e2e_client):
        """전체 100대 통계지표 조회 테스트"""
        result = e2e_client.get_key_statistic_list(
            start=1,
            end=100,
        )

        assert "KeyStatisticList" in result
        rows = result["KeyStatisticList"]["row"]
        assert len(rows) > 0


class TestE2EStatisticMeta:
    """StatisticMeta API E2E 테스트"""

    def test_get_meta_data(self, e2e_client):
        """통계메타데이터 조회 테스트"""
        result = e2e_client.get_statistic_meta(
            data_name="경제심리지수",
            start=1,
            end=10,
        )

        assert "StatisticMeta" in result

        # 데이터가 있는 경우 검증
        if "row" in result["StatisticMeta"]:
            rows = result["StatisticMeta"]["row"]
            if len(rows) > 0:
                df = parse_response(result)
                assert not df.empty

                first_row = rows[0]
                assert "LVL" in first_row
                assert "CONT_NAME" in first_row
                assert "META_DATA" in first_row


class TestE2EIntegration:
    """통합 워크플로우 테스트"""

    def test_complete_workflow(self, e2e_client):
        """전체 워크플로우 테스트: 통계표 검색 -> 항목 조회"""

        # 1. 통계표 목록 조회
        table_result = e2e_client.get_statistic_table_list(start=1, end=10)
        assert "StatisticTableList" in table_result

        tables = table_result["StatisticTableList"]["row"]
        assert len(tables) > 0

        # 2. 알려진 통계표의 세부항목 조회
        # 200Y101: 주요지표(연간지표) - 항목이 많은 통계표
        item_result = e2e_client.get_statistic_item_list(
            stat_code="200Y101",
            start=1,
            end=5,
        )
        assert "StatisticItemList" in item_result
        items = item_result["StatisticItemList"]["row"]
        assert len(items) > 0

        # 3. 실제 데이터 조회는 주기와 항목코드가 필요하므로 생략
        # (각 통계표마다 주기가 다르므로 일반화된 테스트 어려움)

    def test_key_statistics_workflow(self, e2e_client):
        """100대 통계지표 워크플로우 테스트"""

        # 1. 100대 통계지표 조회
        result = e2e_client.get_key_statistic_list(start=1, end=10)
        assert "KeyStatisticList" in result

        rows = result["KeyStatisticList"]["row"]
        assert len(rows) > 0

        # 2. DataFrame으로 변환하여 분석
        df = parse_response(result)
        assert not df.empty

        # 3. 그룹별 통계 확인
        if "class_name" in df.columns:
            groups = df["class_name"].unique()
            assert len(groups) > 0
