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
        assert any("API 요청 전송" in r.getMessage() for r in caplog.records), (
            f"request log not captured by caplog (records={len(caplog.records)})"
        )
        assert set_api_key not in all_logs, f"API key leaked into DEBUG logs:\n{all_logs}"
        assert "/***/" in all_logs, (
            f"Expected masked API key marker '/***/' in request log:\n{all_logs}"
        )

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
        assert set_api_key not in all_logs, (
            f"API key leaked into WARNING/ERROR logs via HTTPError str():\n{all_logs}"
        )

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

    @responses.activate
    def test_cache_key_isolates_page_range(self):
        """서로 다른 start/end는 별도 캐시 엔트리를 가져야 한다 (#7)."""
        page1 = {"StatisticSearch": {"row": [{"TIME": "202401", "DATA_VALUE": "1"}]}}
        page2 = {"StatisticSearch": {"row": [{"TIME": "202501", "DATA_VALUE": "2"}]}}
        responses.add(responses.GET, url=re.compile(r".*/1/100/.*"), json=page1, status=200)
        responses.add(responses.GET, url=re.compile(r".*/101/200/.*"), json=page2, status=200)

        client = EcosClient(api_key="key-A", use_cache=True)
        r1 = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
            start=1,
            end=100,
        )
        r2 = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
            start=101,
            end=200,
        )

        assert r1 == page1
        assert r2 == page2, "second page must not be served from page1 cache entry"

    @responses.activate
    def test_cache_key_isolates_api_key(self):
        """서로 다른 API 키는 캐시를 공유하지 않아야 한다 (#7)."""
        resp_a = {"StatisticSearch": {"row": [{"DATA_VALUE": "from-A"}]}}
        resp_b = {"StatisticSearch": {"row": [{"DATA_VALUE": "from-B"}]}}
        responses.add(responses.GET, url=re.compile(r".*/key-A/.*"), json=resp_a, status=200)
        responses.add(responses.GET, url=re.compile(r".*/key-B/.*"), json=resp_b, status=200)

        client_a = EcosClient(api_key="key-A", use_cache=True)
        client_b = EcosClient(api_key="key-B", use_cache=True)

        r_a = client_a.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
        )
        r_b = client_b.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
        )

        assert r_a == resp_a
        assert r_b == resp_b, "key-B request must not return cached key-A response"

    @responses.activate
    def test_cache_key_pinned_against_global_key_rotation(self):
        """클라이언트가 api_key 없이 만들어진 뒤 전역 키가 바뀌어도
        같은 응답을 캐시에서 가져와야 한다 (#24 review).

        과거 _get_api_key()는 매 호출마다 전역 키를 재조회했기 때문에,
        같은 클라이언트로 두 번 호출하는 사이에 set_api_key()가 다른
        값으로 바뀌면 캐시 키가 달라져 적중 실패했다.
        """
        import ecos

        resp = {"StatisticSearch": {"row": [{"DATA_VALUE": "pinned"}]}}
        responses.add(responses.GET, url=re.compile(r".*"), json=resp, status=200)

        # 전역 키 A로 시작 — 클라이언트 인스턴스는 키를 받지 않음
        ecos.set_api_key("global-key-A")
        client = EcosClient(use_cache=True)
        first = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
        )

        # 전역 키가 B로 바뀌어도, 캐시 키는 첫 호출 시점의 키(A)에 고정되어야 함
        ecos.set_api_key("global-key-B")
        second = client.get_statistic_search(
            stat_code="722Y001",
            period="M",
            start_date="202401",
            end_date="202412",
        )

        assert first == resp
        assert second == resp
        # 전역 키 회전 후에도 캐시 적중 → 네트워크 호출은 한 번만
        assert len(responses.calls) == 1, (
            f"expected single network call due to cache hit, got {len(responses.calls)}"
        )


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
