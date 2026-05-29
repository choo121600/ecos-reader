"""ECOS 에러 코드 단일 진실원천(SSOT) 테스트 (#12).

`ECOS_ERROR_CODES` 카탈로그가 코드별로 적절한 예외를 발생시키는지,
`RETRYABLE_ERROR_CODES`가 카탈로그에서 올바르게 파생되는지,
그리고 카테고리별(`EcosValidationError`/`EcosServerError`)로 catch가
가능한지 검증한다.
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.client import EcosClient
from ecos.exceptions import (
    ECOS_ERROR_CODES,
    RETRYABLE_ERROR_CODES,
    EcosAPIError,
    EcosConfigError,
    EcosRateLimitError,
    EcosServerError,
    EcosValidationError,
)


def _make_client() -> EcosClient:
    return EcosClient(api_key="test-key", use_cache=False, max_retries=1)


def _add_error_response(code: str, message: str = "msg") -> None:
    responses.add(
        responses.GET,
        url=re.compile(r".*"),
        json={"RESULT": {"CODE": code, "MESSAGE": message}},
        status=200,
    )


def _call(client: EcosClient):
    return client.get_statistic_search(
        stat_code="722Y001", period="M", start_date="202401", end_date="202412"
    )


class TestCatalog:
    def test_keys_use_hyphen_format(self):
        """모든 카탈로그 키가 하이픈 형식(ERROR-/INFO-)이다."""
        for code in ECOS_ERROR_CODES:
            assert "_" not in code
            assert code.startswith(("ERROR-", "INFO-"))

    def test_entries_are_triples(self):
        """각 항목은 (예외 클래스, 메시지, retryable) 3-튜플이다."""
        for code, entry in ECOS_ERROR_CODES.items():
            assert len(entry) == 3, code
            exc_class, message, retryable = entry
            assert isinstance(exc_class, type)
            assert isinstance(message, str) and message
            assert isinstance(retryable, bool)

    def test_retryable_set_derived_from_catalog(self):
        """RETRYABLE_ERROR_CODES는 카탈로그의 retryable 플래그에서 파생된다."""
        expected = {code for code, (_e, _m, retry) in ECOS_ERROR_CODES.items() if retry}
        assert set(RETRYABLE_ERROR_CODES) == expected
        # 서버측 일시 오류 + rate limit만 재시도, SQL 오류(601)는 비재시도
        assert set(RETRYABLE_ERROR_CODES) == {"ERROR-500", "ERROR-600", "ERROR-602"}
        assert "ERROR-601" not in RETRYABLE_ERROR_CODES
        assert "ERROR-100" not in RETRYABLE_ERROR_CODES


class TestErrorDispatch:
    @responses.activate
    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("ERROR-100", EcosValidationError),
            ("ERROR-101", EcosValidationError),
            ("ERROR-200", EcosValidationError),
            ("ERROR-300", EcosValidationError),
            ("ERROR-301", EcosValidationError),
            ("ERROR-500", EcosServerError),
            ("ERROR-600", EcosServerError),
            ("ERROR-601", EcosServerError),
            ("ERROR-602", EcosRateLimitError),
            ("INFO-100", EcosConfigError),
        ],
    )
    def test_code_raises_expected_exception(self, code, expected):
        _add_error_response(code)
        with pytest.raises(expected):
            _call(_make_client())

    @responses.activate
    def test_validation_error_catchable_by_category(self):
        """클라이언트 책임 에러는 EcosValidationError로 일괄 catch 가능하다."""
        _add_error_response("ERROR-301")
        with pytest.raises(EcosValidationError):
            _call(_make_client())

    @responses.activate
    def test_validation_error_is_api_error_subclass(self):
        """기존 `except EcosAPIError` 코드와의 하위호환을 유지한다."""
        _add_error_response("ERROR-100")
        with pytest.raises(EcosAPIError) as exc_info:
            _call(_make_client())
        assert exc_info.value.code == "100"

    @responses.activate
    def test_server_error_is_api_error_subclass(self):
        _add_error_response("ERROR-500")
        client = EcosClient(api_key="k", use_cache=False, max_retries=1)
        with pytest.raises(EcosAPIError) as exc_info:
            _call(client)
        assert exc_info.value.code == "500"

    @responses.activate
    def test_unknown_error_code_falls_back_to_api_error(self):
        """카탈로그에 없는 ERROR 코드는 일반 EcosAPIError로 처리된다."""
        _add_error_response("ERROR-999")
        with pytest.raises(EcosAPIError) as exc_info:
            _call(_make_client())
        assert exc_info.value.code == "999"

    @responses.activate
    def test_info_200_is_not_an_error(self):
        """INFO-200(데이터 없음)은 정상 응답이다."""
        _add_error_response("INFO-200")
        result = _call(_make_client())
        assert "RESULT" in result
