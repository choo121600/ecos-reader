"""
ecos-reader 로깅 설정

구조화된 로깅을 위한 설정과 유틸리티를 제공합니다.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from .metrics import record_api_request

# 타입 변수 정의
P = ParamSpec("P")
R = TypeVar("R")

# ecos-reader 전용 로거 설정
logger = logging.getLogger("ecos")

# 기본 로그 레벨 설정 (환경 변수로 오버라이드 가능)
DEFAULT_LOG_LEVEL = logging.INFO

# 라이브러리는 import 시점에 핸들러를 구성하지 않습니다.
# 대신 NullHandler를 등록해 "No handler could be found" 류의 경고를 피합니다.
logger.addHandler(logging.NullHandler())
_logging_configured: bool = False


def setup_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    """
    ecos-reader 로깅을 설정합니다.

    Parameters
    ----------
    level : int
        로그 레벨 (logging.DEBUG, INFO, WARNING, ERROR)

    Examples
    --------
    >>> from ecos.logging import setup_logging
    >>> import logging
    >>> setup_logging(logging.DEBUG)  # 디버그 로그 활성화
    """
    global _logging_configured
    if _logging_configured:
        return

    logger.setLevel(level)

    # 기본 NullHandler 제거 (setup_logging 호출 시 실제 핸들러로 교체)
    for handler in list(logger.handlers):
        if isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 포맷터 설정 - 구조화된 로그 형식
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # 부모 로거로의 전파 방지 (중복 로그 방지)
    logger.propagate = False


def log_api_request(func: Callable[P, R]) -> Callable[P, R]:
    """
    API 요청을 로깅하는 데코레이터

    Parameters
    ----------
    func : Callable
        로깅할 함수

    Returns
    -------
    Callable
        로깅이 추가된 함수
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()

        # 함수명과 주요 파라미터 로깅
        func_name = func.__name__
        logger.debug(f"API 요청 시작: {func_name}")

        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # 성능 메트릭 기록
            record_api_request(func_name, success=True, response_time=elapsed_time)

            logger.info(f"API 요청 성공: {func_name} " f"(응답시간: {elapsed_time:.2f}초)")

            return result

        except Exception as e:
            elapsed_time = time.time() - start_time

            # 성능 메트릭 기록
            record_api_request(func_name, success=False, response_time=elapsed_time)

            logger.error(
                f"API 요청 실패: {func_name} "
                f"(응답시간: {elapsed_time:.2f}초, 에러: {type(e).__name__}: {e})"
            )

            raise

    return wrapper


def log_cache_operation(operation: str, key: str, hit: bool = False) -> None:
    """
    캐시 작업을 로깅합니다.

    Parameters
    ----------
    operation : str
        캐시 작업 종류 ('get', 'set', 'clear', 'invalidate')
    key : str
        캐시 키
    hit : bool, optional
        캐시 히트 여부 (get 작업 시만 사용)
    """
    if operation == "get":
        status = "HIT" if hit else "MISS"
        logger.debug(f"캐시 조회: {key} - {status}")
    elif operation == "set":
        logger.debug(f"캐시 저장: {key}")
    elif operation == "clear":
        logger.info("캐시 전체 삭제")
    elif operation == "invalidate":
        logger.debug(f"캐시 무효화: {key}")


def log_error_response(error_code: str, error_message: str, url: str) -> None:
    """
    ECOS API 에러 응답을 로깅합니다.

    Parameters
    ----------
    error_code : str
        ECOS 에러 코드
    error_message : str
        에러 메시지
    url : str
        요청 URL (민감 정보는 마스킹됨)
    """
    # URL에서 API 키 마스킹
    masked_url = mask_api_key(url)

    logger.warning(f"ECOS API 에러: [{error_code}] {error_message} " f"(URL: {masked_url})")


def log_retry_attempt(attempt: int, max_retries: int, error: Exception) -> None:
    """
    재시도 시도를 로깅합니다.

    Parameters
    ----------
    attempt : int
        현재 시도 횟수
    max_retries : int
        최대 재시도 횟수
    error : Exception
        발생한 에러
    """
    logger.warning(f"API 요청 재시도 {attempt}/{max_retries}: " f"{type(error).__name__}: {error}")


def mask_api_key(url: str) -> str:
    """
    URL에서 API 키를 마스킹합니다.

    Parameters
    ----------
    url : str
        원본 URL

    Returns
    -------
    str
        API 키가 마스킹된 URL
    """
    import re

    # ECOS URL 패턴에서 API 키 부분을 ***으로 대체
    # 예: /api/StatisticSearch/ABC123DEF/json/kr/... -> /api/StatisticSearch/***/json/kr/...
    pattern = r"(/api/[^/]+/)([^/]+)(/.*)"
    replacement = r"\1***\3"

    return re.sub(pattern, replacement, url)
