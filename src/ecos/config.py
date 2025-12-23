"""
ecos-reader 설정 관리

API Key 및 기본 설정을 관리합니다.
"""

from __future__ import annotations

import os

from .exceptions import EcosConfigError

# dotenv 로드 상태(명시적으로만 로드)
_dotenv_loaded: bool = False

# 전역 API Key 저장소
_api_key: str | None = None


def load_env(*, dotenv_path: str | None = None, override: bool = False) -> bool:
    """
    .env 파일을 명시적으로 로드합니다.

    Notes
    -----
    라이브러리 import 시점에 자동으로 .env를 로드하지 않습니다.
    필요 시 사용자가 직접 호출하여 환경 변수를 로드할 수 있습니다.

    Parameters
    ----------
    dotenv_path : str, optional
        .env 파일 경로. 미지정 시 python-dotenv 기본 탐색 규칙을 따릅니다.
    override : bool, optional
        이미 설정된 환경 변수를 덮어쓸지 여부

    Returns
    -------
    bool
        .env 파일을 로드했으면 True, 아니면 False
    """
    global _dotenv_loaded
    try:
        from dotenv import load_dotenv
    except ImportError:
        # python-dotenv가 설치되어 있지 않은 경우
        _dotenv_loaded = False
        return False

    loaded = load_dotenv(dotenv_path=dotenv_path, override=override)
    _dotenv_loaded = bool(loaded)
    return _dotenv_loaded


def set_api_key(api_key: str) -> None:
    """
    API Key를 설정합니다.

    Parameters
    ----------
    api_key : str
        한국은행에서 발급받은 ECOS Open API 인증키

    Examples
    --------
    >>> import ecos
    >>> ecos.set_api_key("your_api_key")
    """
    global _api_key
    if not api_key or not isinstance(api_key, str):
        raise EcosConfigError("API Key는 빈 문자열이 아닌 문자열이어야 합니다.")
    _api_key = api_key


def get_api_key() -> str:
    """
    현재 설정된 API Key를 반환합니다.

    환경 변수 `ECOS_API_KEY`가 설정되어 있으면 해당 값을 사용합니다.
    `set_api_key()`로 직접 설정한 값이 있으면 해당 값을 우선합니다.
    `.env` 파일은 import 시점에 자동으로 로드되지 않습니다(필요 시 `load_env()` 호출).

    Returns
    -------
    str
        ECOS API 인증키

    Raises
    ------
    EcosConfigError
        API Key가 설정되지 않은 경우

    Examples
    --------
    >>> import ecos
    >>> ecos.set_api_key("your_api_key")
    >>> ecos.get_api_key()
    'your_api_key'
    """
    global _api_key

    # 직접 설정한 값 우선
    if _api_key is not None:
        return _api_key

    # 환경 변수에서 로드
    env_key = os.environ.get("ECOS_API_KEY")
    if env_key:
        return env_key

    raise EcosConfigError(
        "API Key가 설정되지 않았습니다. "
        "환경 변수 ECOS_API_KEY를 설정하거나, "
        "ecos.load_env()로 .env 파일을 로드하거나, "
        "ecos.set_api_key('your_api_key')를 호출하세요. "
        "API Key는 https://ecos.bok.or.kr/api/ 에서 신청할 수 있습니다."
    )


def clear_api_key() -> None:
    """
    설정된 API Key를 초기화합니다.

    주로 테스트 목적으로 사용됩니다.
    """
    global _api_key
    _api_key = None


# 기본 설정값
class Settings:
    """기본 설정값"""

    # API 기본값
    BASE_URL: str = "https://ecos.bok.or.kr/api/"
    DEFAULT_FORMAT: str = "json"
    DEFAULT_LANG: str = "kr"

    # 요청 설정
    DEFAULT_TIMEOUT: int = 30  # 초
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.0

    # 캐시 설정
    CACHE_TTL: int = 3600  # 1시간
    CACHE_MAXSIZE: int = 100

    # 페이지네이션
    DEFAULT_PAGE_SIZE: int = 10000
