"""
ecos-reader API 클라이언트

ECOS API와 HTTP 통신을 담당하는 핵심 클라이언트입니다.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any, cast
from urllib.parse import quote

import requests

from .cache import Cache, get_cache
from .config import Settings, get_api_key
from .exceptions import (
    RETRYABLE_ERROR_CODES,
    EcosAPIError,
    EcosConfigError,
    EcosNetworkError,
    EcosRateLimitError,
)
from .logging import log_api_request, log_error_response, log_retry_attempt, logger
from .types import EcosService


class EcosClient:
    """
    ECOS API 클라이언트

    한국은행 ECOS Open API와 HTTP 통신을 담당합니다.

    Parameters
    ----------
    api_key : str, optional
        ECOS API 인증키. 미제공 시 환경 변수에서 로드
    timeout : int, optional
        요청 타임아웃(초), 기본값 30
    max_retries : int, optional
        최대 재시도 횟수, 기본값 3
    use_cache : bool, optional
        캐시 사용 여부, 기본값 True

    Examples
    --------
    >>> client = EcosClient()
    >>> result = client.get_statistic_search(
    ...     stat_code="722Y001",
    ...     period="M",
    ...     start_date="202301",
    ...     end_date="202312",
    ...     item_code1="0101000"
    ... )
    """

    BASE_URL = Settings.BASE_URL

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = Settings.DEFAULT_TIMEOUT,
        max_retries: int = Settings.MAX_RETRIES,
        use_cache: bool = True,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache
        self.session = requests.Session()
        self._cache: Cache | None = get_cache() if use_cache else None

    def _get_api_key(self) -> str:
        """API Key를 반환합니다."""
        if self.api_key:
            return self.api_key
        return get_api_key()

    def _build_url(
        self,
        service: EcosService,
        start: int,
        end: int,
        *path_params: str,
    ) -> str:
        """
        ECOS API 요청 URL을 구성합니다.

        URL 형식: {BASE_URL}/{service}/{api_key}/{format}/{lang}/{start}/{end}/{params...}/
        """
        api_key = self._get_api_key()
        parts = [
            self.BASE_URL.rstrip("/"),
            service,
            api_key,
            Settings.DEFAULT_FORMAT,
            Settings.DEFAULT_LANG,
            str(start),
            str(end),
        ]

        # 추가 파라미터 (통계코드, 주기, 날짜 등)
        for param in path_params:
            if param:  # 빈 문자열은 제외
                parts.append(quote(str(param), safe=""))

        return "/".join(parts)

    @log_api_request
    def _make_request(self, url: str) -> dict[str, Any]:
        """
        HTTP GET 요청을 수행합니다.

        Parameters
        ----------
        url : str
            요청 URL

        Returns
        -------
        dict
            JSON 응답

        Raises
        ------
        EcosNetworkError
            네트워크 에러 발생 시
        EcosAPIError
            API 에러 응답 시
        EcosRateLimitError
            Rate Limit 초과 시
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"API 요청 전송: {url}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = cast(dict[str, Any], response.json())

                # 에러 응답 확인
                self._check_error_response(data, url)

                logger.debug(f"API 응답 성공: {len(data)} 바이트 수신")
                return data

            except requests.exceptions.Timeout:
                last_exception = EcosNetworkError(f"요청 타임아웃 ({self.timeout}초)")
                if attempt < self.max_retries - 1:
                    log_retry_attempt(attempt + 1, self.max_retries, last_exception)

            except requests.exceptions.ConnectionError as e:
                last_exception = EcosNetworkError(f"네트워크 연결 오류: {e}")
                if attempt < self.max_retries - 1:
                    log_retry_attempt(attempt + 1, self.max_retries, last_exception)

            except requests.exceptions.HTTPError as e:
                last_exception = EcosNetworkError(f"HTTP 오류: {e}")
                if attempt < self.max_retries - 1:
                    log_retry_attempt(attempt + 1, self.max_retries, last_exception)

            except (EcosAPIError, EcosRateLimitError) as e:
                # 재시도 가능한 에러인지 확인
                error_key = f"ERROR-{e.code}" if hasattr(e, "code") else ""
                if error_key in RETRYABLE_ERROR_CODES:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        log_retry_attempt(attempt + 1, self.max_retries, last_exception)
                else:
                    raise

            # 재시도 전 대기 (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = Settings.RETRY_BACKOFF_FACTOR * (2**attempt)
                logger.debug(f"재시도 전 대기: {wait_time:.2f}초")
                time.sleep(wait_time)

        # 모든 재시도 실패
        if last_exception:
            raise last_exception

        raise EcosNetworkError("알 수 없는 네트워크 오류")

    def _check_error_response(self, data: dict[str, Any], url: str = "") -> None:
        """
        API 응답에서 에러를 확인합니다.

        Parameters
        ----------
        data : dict
            API 응답 데이터
        url : str, optional
            요청 URL (로깅용)
        """
        # RESULT 키 확인
        result = data.get("RESULT")
        if not result:
            return

        code = result.get("CODE", "")
        message = result.get("MESSAGE", "")

        # 정보 코드 200: 데이터 없음 - 정상 처리 (빈 결과)
        if code == "INFO-200":
            return

        # 정보 코드 100: 인증키 오류
        if code == "INFO-100":
            log_error_response(code, message, url)
            raise EcosConfigError(message)

        # 에러 코드
        if code.startswith("ERROR"):
            error_num = code.split("-")[-1] if "-" in code else code.replace("ERROR", "")
            log_error_response(code, message, url)

            if error_num == "602":
                raise EcosRateLimitError(message)

            raise EcosAPIError(error_num, message)

    def get_statistic_search(
        self,
        stat_code: str,
        period: str,
        start_date: str,
        end_date: str,
        item_code1: str = "",
        item_code2: str = "",
        item_code3: str = "",
        item_code4: str = "",
        start: int = 1,
        end: int = 100000,
    ) -> dict[str, Any]:
        """
        통계 조회 (StatisticSearch)

        Parameters
        ----------
        stat_code : str
            통계표코드
        period : str
            주기 (D: 일, M: 월, Q: 분기, A: 연)
        start_date : str
            조회 시작일
        end_date : str
            조회 종료일
        item_code1 : str, optional
            통계항목코드1
        item_code2 : str, optional
            통계항목코드2
        item_code3 : str, optional
            통계항목코드3
        item_code4 : str, optional
            통계항목코드4
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 100000

        Returns
        -------
        dict
            API 응답 데이터
        """
        # 캐시 확인
        if self._cache and self.use_cache:
            cache_key = self._cache._make_key(
                "StatisticSearch",
                stat_code,
                period,
                start_date,
                end_date,
                item_code1,
                item_code2,
                item_code3,
                item_code4,
            )
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cast(dict[str, Any], cached)

        url = self._build_url(
            "StatisticSearch",
            start,
            end,
            stat_code,
            period,
            start_date,
            end_date,
            item_code1,
            item_code2,
            item_code3,
            item_code4,
        )

        result = self._make_request(url)

        # 캐시 저장
        if self._cache and self.use_cache:
            self._cache.set(cache_key, result)

        return result

    def get_statistic_item_list(
        self,
        stat_code: str,
        start: int = 1,
        end: int = 10000,
    ) -> dict[str, Any]:
        """
        통계 항목 목록 조회 (StatisticItemList)

        Parameters
        ----------
        stat_code : str
            통계표코드
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 10000

        Returns
        -------
        dict
            API 응답 데이터
        """
        url = self._build_url("StatisticItemList", start, end, stat_code)
        return self._make_request(url)

    def get_statistic_table_list(
        self,
        stat_code: str = "",
        start: int = 1,
        end: int = 10000,
    ) -> dict[str, Any]:
        """
        통계표 목록 조회 (StatisticTableList)

        Parameters
        ----------
        stat_code : str, optional
            통계표코드 (검색어로 활용)
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 10000

        Returns
        -------
        dict
            API 응답 데이터
        """
        url = self._build_url("StatisticTableList", start, end, stat_code)
        return self._make_request(url)

    def get_statistic_word(
        self,
        word: str,
        start: int = 1,
        end: int = 10,
    ) -> dict[str, Any]:
        """
        통계용어사전 조회 (StatisticWord)

        Parameters
        ----------
        word : str
            검색할 통계 용어
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 10

        Returns
        -------
        dict
            API 응답 데이터
        """
        url = self._build_url("StatisticWord", start, end, word)
        return self._make_request(url)

    def get_key_statistic_list(
        self,
        start: int = 1,
        end: int = 100,
    ) -> dict[str, Any]:
        """
        100대 통계지표 조회 (KeyStatisticList)

        Parameters
        ----------
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 100

        Returns
        -------
        dict
            API 응답 데이터
        """
        url = self._build_url("KeyStatisticList", start, end)
        return self._make_request(url)

    def get_statistic_meta(
        self,
        data_name: str,
        start: int = 1,
        end: int = 10,
    ) -> dict[str, Any]:
        """
        통계메타DB 조회 (StatisticMeta)

        Parameters
        ----------
        data_name : str
            조회할 데이터명
        start : int, optional
            시작 건수, 기본값 1
        end : int, optional
            종료 건수, 기본값 10

        Returns
        -------
        dict
            API 응답 데이터
        """
        url = self._build_url("StatisticMeta", start, end, data_name)
        return self._make_request(url)


# 전역 클라이언트 인스턴스
_global_client: EcosClient | None = None


def get_client() -> EcosClient:
    """전역 클라이언트 인스턴스를 반환합니다."""
    global _global_client
    if _global_client is None:
        _global_client = EcosClient()
    return _global_client


def set_client(client: EcosClient | None) -> None:
    """
    전역 기본 클라이언트를 설정합니다.

    Notes
    -----
    - indicator 함수들은 기본적으로 이 전역 클라이언트를 사용합니다.
    - 기존 전역 클라이언트가 존재하면 세션을 close()한 뒤 교체합니다.
    """
    global _global_client
    if _global_client is not None and _global_client is not client:
        with contextlib.suppress(Exception):
            _global_client.session.close()
    _global_client = client


def reset_client() -> None:
    """전역 클라이언트를 초기화합니다."""
    global _global_client
    if _global_client is not None:
        with contextlib.suppress(Exception):
            _global_client.session.close()
    _global_client = None
