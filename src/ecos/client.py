"""
ecos-reader API 클라이언트

ECOS API와 HTTP 통신을 담당하는 핵심 클라이언트입니다.
"""

from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .cache import Cache, DiskCache, get_cache, get_disk_cache
from .config import Settings, get_api_key
from .exceptions import (
    ECOS_ERROR_CODES,
    RETRYABLE_ERROR_CODES,
    EcosAPIError,
    EcosNetworkError,
    EcosRateLimitError,
)
from .logging import log_api_request, log_error_response, log_retry_attempt, logger, mask_api_key
from .ratelimit import RateLimiter, get_rate_limiter

if TYPE_CHECKING:
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
        disk_cache: bool = False,
        disk_cache_dir: str | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache
        self.use_disk_cache = disk_cache
        self.session = self._build_session()
        # 캐시 백엔드 선택: opt-in 디스크 캐시(영속) 또는 인메모리 LRU(기본).
        self._cache: Cache | DiskCache | None
        if not use_cache:
            self._cache = None
        elif disk_cache:
            self._cache = get_disk_cache(disk_cache_dir)
        else:
            self._cache = get_cache()
        # 선제 rate limiter: 생략 시 전역 limiter(같은 계정 한도 공유).
        self._rate_limiter = rate_limiter if rate_limiter is not None else get_rate_limiter()

    def _build_session(self) -> requests.Session:
        """재시도 정책과 커넥션 풀이 구성된 Session을 생성합니다.

        전송 계층(urllib3.Retry)에서 처리하는 것:
        - 5xx/429/408 및 연결/읽기 오류 재시도 (``status_forcelist``)
        - 4xx(408/429 제외)는 ``status_forcelist`` 밖이므로 재시도하지 않음
        - 429/503의 ``Retry-After`` 헤더 존중 (``respect_retry_after_header``)

        ECOS 비즈니스 에러(HTTP 200 + ``RESULT.CODE``)는 이 계층에서 보이지
        않으므로 ``_make_request``의 애플리케이션 루프에서 별도로 재시도한다.
        """
        session = requests.Session()
        retry = Retry(
            total=self.max_retries,
            backoff_factor=Settings.RETRY_BACKOFF_FACTOR,
            status_forcelist=Settings.RETRY_STATUS_FORCELIST,
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
            # 재시도 소진 후에도 마지막 응답을 그대로 반환받아 raise_for_status로
            # 일관되게 변환한다 (urllib3가 MaxRetryError를 던지지 않도록).
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=Settings.POOL_CONNECTIONS,
            pool_maxsize=Settings.POOL_MAXSIZE,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get_api_key(self) -> str:
        """
        요청 시점의 API Key를 반환합니다.

        주의: 캐시 키 구성에는 이 메서드를 직접 쓰지 말고
        ``_resolve_cache_key_api_key``를 사용하세요. 이 메서드는 매 호출마다
        전역 키를 재조회하므로, 같은 클라이언트라도 도중에 ``set_api_key()``가
        바뀌면 캐시 키도 함께 바뀌어 이전에 저장한 응답을 찾지 못합니다 (#24).
        """
        if self.api_key:
            return self.api_key
        return get_api_key()

    def _resolve_cache_key_api_key(self) -> str:
        """
        캐시 키 구성용 API Key를 안정적으로 반환합니다 (#24).

        ``self.api_key``가 명시되어 있으면 그 값, 아니면 처음 호출된 시점의
        전역 키를 인스턴스에 한 번만 고정해 이후 전역 키 로테이션과
        무관하게 동일 키를 반환합니다. 이를 통해 멀티 테넌트 환경에서
        한 클라이언트가 자기 응답만 캐시에서 가져오도록 보장합니다.
        """
        if self.api_key:
            return self.api_key
        cached = getattr(self, "_resolved_cache_api_key", None)
        if cached is None:
            cached = get_api_key()
            self._resolved_cache_api_key = cached
        return cached

    def _assemble_url(
        self,
        api_key: str,
        service: EcosService,
        start: int,
        end: int,
        *path_params: str,
    ) -> str:
        """주어진 ``api_key`` 로 ECOS 요청 URL을 조립합니다.

        URL 형식: {BASE_URL}/{service}/{api_key}/{format}/{lang}/{start}/{end}/{params...}/

        로깅용으로는 ``api_key="***"`` 를 넘겨 키가 **처음부터 포함되지 않은**
        URL을 만든다(#125). 사후 마스킹(``mask_api_key``)과 달리 평문 키가 로그
        경로의 데이터 흐름에 전혀 등장하지 않아, 정적 분석(CodeQL)의 clear-text
        logging 오탐을 원천 차단한다.
        """
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

    def _build_url(
        self,
        service: EcosService,
        start: int,
        end: int,
        *path_params: str,
    ) -> str:
        """실제 요청용 URL(인증키 포함)을 구성합니다."""
        return self._assemble_url(self._get_api_key(), service, start, end, *path_params)

    def _build_log_url(
        self,
        service: EcosService,
        start: int,
        end: int,
        *path_params: str,
    ) -> str:
        """로깅/에러 메시지용 URL을 구성합니다(인증키 자리는 ``***``). (#125)"""
        return self._assemble_url("***", service, start, end, *path_params)

    @log_api_request
    def _make_request(self, url: str, log_url: str) -> dict[str, Any]:
        """
        HTTP GET 요청을 수행합니다.

        Parameters
        ----------
        url : str
            실제 요청 URL (인증키 포함).
        log_url : str
            로깅/에러 메시지용 URL (인증키 자리는 ``***``). 평문 키가 로그
            데이터 흐름에 등장하지 않도록 호출부에서 키 없이 구성한다(#125).

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
        # 전송 계층(urllib3.Retry)이 5xx/429/408·연결/읽기 오류를 이미 재시도한다.
        # 이 루프는 HTTP 200으로 내려오는 ECOS 비즈니스 에러(ERROR-500/600/602 등
        # RETRYABLE_ERROR_CODES)만 추가로 재시도한다.
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                # 선제 throttle: 캐시 미스로 실제 네트워크를 칠 때만 한도를 소모한다.
                # 재시도(백오프)도 각 시도마다 throttle을 거친다.
                if self._rate_limiter is not None:
                    self._rate_limiter.acquire()

                # log_url은 키가 없는 URL이므로 추가 마스킹 없이 그대로 로깅한다.
                logger.debug(f"API 요청 전송: {log_url}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = cast("dict[str, Any]", response.json())

                # 에러 응답 확인 (로그용 키 없는 URL 전달)
                self._check_error_response(data, log_url)

                logger.debug(f"API 응답 성공: {len(data)} 바이트 수신")
                return data

            except requests.exceptions.Timeout as e:
                # 읽기 타임아웃: urllib3 재시도까지 소진된 상태이므로 즉시 변환
                raise EcosNetworkError(f"요청 타임아웃 ({self.timeout}초)") from e

            except requests.exceptions.ConnectionError as e:
                # 연결 오류: urllib3 재시도 소진 후 도달. raw URL(api_key)이 섞일 수
                # 있어 마스킹.
                raise EcosNetworkError(f"네트워크 연결 오류: {mask_api_key(str(e))}") from e

            except requests.exceptions.HTTPError as e:
                # 4xx(408/429 제외)는 status_forcelist 밖이라 재시도 없이 즉시 도달하고,
                # 5xx/429는 어댑터가 재시도를 소진한 최종 응답이다. 어느 쪽이든 즉시 raise.
                # requests HTTPError str()에 full URL(key 포함)이 들어가므로 마스킹 필수.
                raise EcosNetworkError(f"HTTP 오류: {mask_api_key(str(e))}") from e

            except (EcosAPIError, EcosRateLimitError) as e:
                # 비즈니스 에러: 재시도 대상이 아니면 즉시 raise
                error_key = f"ERROR-{e.code}" if hasattr(e, "code") else ""
                if error_key not in RETRYABLE_ERROR_CODES:
                    raise

                last_exception = e
                if attempt < self.max_retries - 1:
                    log_retry_attempt(attempt + 1, self.max_retries, e)
                    # 비즈니스 에러는 HTTP 200이라 Retry-After 헤더가 없으므로
                    # exponential backoff 적용
                    wait_time = Settings.RETRY_BACKOFF_FACTOR * (2**attempt)
                    logger.debug(f"재시도 전 대기: {wait_time:.2f}초")
                    time.sleep(wait_time)

        # 모든 재시도 실패
        if last_exception:
            raise last_exception

        raise EcosNetworkError("알 수 없는 네트워크 오류")

    def _check_error_response(self, data: dict[str, Any], log_url: str = "") -> None:
        """
        API 응답에서 에러를 확인합니다.

        Parameters
        ----------
        data : dict
            API 응답 데이터
        log_url : str, optional
            로깅용 URL (인증키 자리는 ``***``, 호출부에서 키 없이 구성). (#125)
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

        # 카탈로그(ECOS_ERROR_CODES) 단일 조회로 코드별 예외 결정
        mapping = ECOS_ERROR_CODES.get(code)
        if mapping is None:
            # 카탈로그 미등록 코드: ERROR 접두는 일반 API 에러로, 그 외는 정상 처리
            if code.startswith("ERROR"):
                log_error_response(code, message, log_url)
                raise EcosAPIError(self._error_num(code), message)
            return

        exc_class, default_message, _retryable = mapping
        log_error_response(code, message, log_url)
        msg = message or default_message

        # EcosAPIError 계열은 (code, message) 시그니처, 그 외(Config/RateLimit)는 (message)
        if issubclass(exc_class, EcosAPIError):
            raise exc_class(self._error_num(code), msg)
        raise exc_class(msg)

    @staticmethod
    def _error_num(code: str) -> str:
        """``ERROR-100`` → ``100``처럼 코드에서 숫자 부분을 추출합니다."""
        if "-" in code:
            return code.split("-", 1)[-1]
        return code.replace("ERROR", "")

    def _cached_request(
        self,
        service: EcosService,
        start: int,
        end: int,
        *path_params: str,
    ) -> dict[str, Any]:
        """
        캐시를 적용한 공통 요청 헬퍼 (#31).

        6개 client 엔드포인트가 동일한 캐시 키 규칙을 공유하도록 한다.
        키 구성에 페이지 범위(start/end), API 키(인스턴스 단위로 고정된 값,
        ``_resolve_cache_key_api_key``), 언어, format, 그리고 서비스별
        path 파라미터를 포함해 페이지·키·언어·서비스·인자가 다른 요청이
        서로 충돌하지 않도록 한다.

        참고: ``path_params``는 ``_build_url``과 캐시 키에 동일하게 전달된다.
        ``_build_url``은 빈 문자열 인자를 URL에서 제외하지만 캐시 키에는
        그대로 포함해, 서비스별 인자 개수가 달라도 키가 안정적으로 구분된다.

        ``Settings.DEFAULT_LANG`` / ``DEFAULT_FORMAT``은 현재 정적이지만 키에
        포함하는 이유는 두 가지다. (1) 향후 client 단위 옵션으로 승격되면
        자동으로 캐시 격리가 동작하도록 차원을 미리 확보한다. (2) 사용자가
        monkey-patch하면 _build_url과 캐시 키가 동시에 새 값을 사용하도록 한다.
        """
        cache_key: str | None = None
        if self._cache is not None and self.use_cache:
            cache_key = self._cache._make_key(
                service,
                self._resolve_cache_key_api_key(),
                Settings.DEFAULT_LANG,
                Settings.DEFAULT_FORMAT,
                int(start),
                int(end),
                *path_params,
            )
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cast("dict[str, Any]", cached)

        url = self._build_url(service, start, end, *path_params)
        log_url = self._build_log_url(service, start, end, *path_params)
        result = self._make_request(url, log_url)

        if cache_key is not None and self._cache is not None:
            self._cache.set(cache_key, result)

        return result

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
        return self._cached_request(
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
        return self._cached_request("StatisticItemList", start, end, stat_code)

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
        return self._cached_request("StatisticTableList", start, end, stat_code)

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
        return self._cached_request("StatisticWord", start, end, word)

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
        return self._cached_request("KeyStatisticList", start, end)

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
        return self._cached_request("StatisticMeta", start, end, data_name)


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
