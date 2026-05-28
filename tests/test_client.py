"""
client 모듈 테스트
"""

from __future__ import annotations

import logging
import re

import pytest
import responses

from ecos.client import EcosClient, get_client, reset_client
from ecos.config import Settings
from ecos.exceptions import (
    EcosAPIError,
    EcosConfigError,
    EcosNetworkError,
    EcosRateLimitError,
)


@pytest.mark.usefixtures("set_api_key")
class TestEcosClient:
    """EcosClient 클래스 테스트"""

    def test_init_with_api_key(self):
        """API 키로 초기화"""
        client = EcosClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_init_default_values(self):
        """기본값 확인"""
        client = EcosClient(api_key="test")
        assert client.timeout == Settings.DEFAULT_TIMEOUT
        assert client.max_retries == Settings.MAX_RETRIES
        assert client.use_cache is True

    def test_build_url(self, set_api_key):
        """URL 구성 테스트"""
        client = EcosClient()
        url = client._build_url("StatisticSearch", 1, 100, "722Y001", "M", "202401", "202412")

        assert "StatisticSearch" in url
        assert set_api_key in url
        assert "json" in url
        assert "kr" in url
        assert "722Y001" in url

    @responses.activate
    def test_get_statistic_search_success(self):
        """StatisticSearch 성공 테스트"""
        # Mock 응답 설정
        mock_response = {
            "StatisticSearch": {
                "row": [
                    {
                        "STAT_CODE": "722Y001",
                        "TIME": "202401",
                        "DATA_VALUE": "3.50",
                        "UNIT_NAME": "%",
                    }
                ]
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        client = EcosClient(use_cache=False)
        result = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
            item_code1="0101000",
        )

        assert "StatisticSearch" in result
        assert len(result["StatisticSearch"]["row"]) == 1

    @responses.activate
    def test_error_response_api_error(self):
        """API 에러 응답 테스트"""
        mock_response = {"RESULT": {"CODE": "ERROR-100", "MESSAGE": "필수 값이 누락되어 있습니다."}}

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        client = EcosClient(use_cache=False)

        with pytest.raises(EcosAPIError) as exc_info:
            client.get_statistic_search(
                stat_code="722Y001",
                period="M",
                start_date="202401",
                end_date="202412",
            )

        assert "100" in exc_info.value.code

    @responses.activate
    def test_error_response_config_error(self):
        """인증키 에러 응답 테스트"""
        mock_response = {"RESULT": {"CODE": "INFO-100", "MESSAGE": "인증키가 유효하지 않습니다."}}

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        client = EcosClient(use_cache=False)

        with pytest.raises(EcosConfigError):
            client.get_statistic_search(
                stat_code="722Y001",
                period="M",
                start_date="202401",
                end_date="202412",
            )

    @responses.activate
    def test_error_response_rate_limit(self):
        """Rate Limit 에러 테스트"""
        mock_response = {
            "RESULT": {
                "CODE": "ERROR-602",
                "MESSAGE": "과도한 OpenAPI 호출로 이용이 제한되었습니다.",
            }
        }

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        client = EcosClient(use_cache=False, max_retries=1)

        with pytest.raises(EcosRateLimitError):
            client.get_statistic_search(
                stat_code="722Y001",
                period="M",
                start_date="202401",
                end_date="202412",
            )

    @responses.activate
    def test_info_200_returns_empty(self):
        """INFO-200 (데이터 없음)은 에러가 아님"""
        mock_response = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}

        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json=mock_response,
            status=200,
        )

        client = EcosClient(use_cache=False)
        result = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
        )

        # 에러가 발생하지 않고 정상 응답
        assert "RESULT" in result

    @responses.activate
    def test_debug_log_masks_api_key(self, caplog, set_api_key):
        """DEBUG 로그에 raw API 키가 노출되지 않아야 한다 (#6)."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            json={"StatisticSearch": {"row": []}},
            status=200,
        )

        client = EcosClient(use_cache=False)
        with caplog.at_level(logging.DEBUG, logger="ecos"):
            client.get_statistic_search(
                stat_code="722Y001",
                period="M",
                start_date="202401",
                end_date="202412",
            )

        all_logs = "\n".join(record.getMessage() for record in caplog.records)
        # caplog가 실제로 잡았는지 먼저 확인 — 0건이면 마스킹 검사가 vacuously 통과
        assert any(
            "API 요청 전송" in r.getMessage() for r in caplog.records
        ), f"request log not captured by caplog (records={len(caplog.records)})"
        assert set_api_key not in all_logs, f"API key leaked into DEBUG logs:\n{all_logs}"
        assert (
            "/***/" in all_logs
        ), f"Expected masked API key marker '/***/' in request log:\n{all_logs}"

    @responses.activate
    def test_http_error_log_masks_api_key(self, caplog, set_api_key):
        """500 응답 경로(WARNING/ERROR 로그)에도 raw API 키가 노출되지 않아야 한다 (#6)."""
        responses.add(
            responses.GET,
            url=re.compile(r".*"),
            body="Internal Server Error",
            status=500,
        )

        client = EcosClient(use_cache=False, max_retries=1)
        with (
            caplog.at_level(logging.DEBUG, logger="ecos"),
            pytest.raises(EcosNetworkError),
        ):
            client.get_statistic_search(
                stat_code="722Y001",
                period="M",
                start_date="202401",
                end_date="202412",
            )

        all_logs = "\n".join(record.getMessage() for record in caplog.records)
        assert (
            set_api_key not in all_logs
        ), f"API key leaked into WARNING/ERROR logs via HTTPError str():\n{all_logs}"

    def test_mask_api_key_handles_trailing_segments(self):
        """mask_api_key는 후행 path 유무와 무관하게 키를 가린다 (#23 review)."""
        from ecos.logging import mask_api_key

        # 정상 ECOS URL — 후행 path 있음
        full = "https://x/api/StatisticSearch/MYKEY/json/kr/1/100"
        assert mask_api_key(full) == "https://x/api/StatisticSearch/***/json/kr/1/100"
        # 후행 path 없음 — 이전 정규식은 이 경우를 노-옵으로 남겼음
        bare = "https://x/api/StatisticSearch/MYKEY"
        assert mask_api_key(bare) == "https://x/api/StatisticSearch/***"
        # 패턴 불일치는 그대로
        assert mask_api_key("https://x/other") == "https://x/other"

    def test_caching(self):
        """캐싱 테스트 - Cache 클래스 직접 테스트"""
        from ecos.cache import Cache

        cache = Cache(ttl=3600, maxsize=100)

        # 캐시 키 생성
        cache_key = cache._make_key(
            "StatisticSearch",
            "722Y001",
            "M",
            "202401",
            "202412",
            "",
            "",
            "",
            "",
        )

        # 캐시에 데이터 저장
        test_data = {"StatisticSearch": {"row": [{"DATA_VALUE": "3.50"}]}}
        cache.set(cache_key, test_data)

        # 캐시에서 데이터 조회
        cached_result = cache.get(cache_key)

        assert cached_result == test_data
        assert len(cache) == 1

        # 동일 키로 다시 조회해도 같은 결과
        cached_result2 = cache.get(cache_key)
        assert cached_result2 == test_data


@pytest.mark.usefixtures("set_api_key")
class TestGlobalClient:
    """전역 클라이언트 테스트"""

    def test_get_client_singleton(self):
        """전역 클라이언트는 싱글톤"""
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2

    def test_reset_client(self):
        """클라이언트 리셋"""
        client1 = get_client()
        reset_client()
        client2 = get_client()
        assert client1 is not client2
