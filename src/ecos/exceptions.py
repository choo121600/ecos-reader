"""
ecos-reader 예외 클래스 정의

ECOS API 에러 및 라이브러리 예외를 처리합니다.
"""

from __future__ import annotations


class EcosError(Exception):
    """ecos-reader 기본 예외"""

    pass


class EcosAPIError(EcosError):
    """ECOS API 호출 에러

    Attributes
    ----------
    code : str
        ECOS API 에러 코드
    message : str
        에러 메시지
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class EcosConfigError(EcosError):
    """설정 관련 에러 (API Key 등)"""

    pass


class EcosNetworkError(EcosError):
    """네트워크 연결 에러"""

    pass


class EcosRateLimitError(EcosError):
    """Rate Limit 초과"""

    def __init__(self, message: str, code: str = "602"):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ECOS 에러 코드 매핑
ECOS_ERROR_CODES: dict[str, tuple[type[EcosError], str]] = {
    # 정보 코드
    "INFO_100": (EcosConfigError, "인증키가 유효하지 않습니다."),
    "INFO_200": (EcosAPIError, "해당하는 데이터가 없습니다."),  # 빈 DataFrame 반환으로 처리
    # 에러 코드
    "ERROR_100": (EcosAPIError, "필수 값이 누락되어 있습니다."),
    "ERROR_101": (EcosAPIError, "주기와 다른 형식의 날짜 형식입니다."),
    "ERROR_200": (EcosAPIError, "파일타입 값이 누락 혹은 유효하지 않습니다."),
    "ERROR_300": (EcosAPIError, "조회건수 값이 누락되어 있습니다."),
    "ERROR_301": (EcosAPIError, "조회건수 값의 타입이 유효하지 않습니다."),
    "ERROR_400": (EcosAPIError, "검색범위가 적정범위를 초과하여 TIMEOUT이 발생하였습니다."),
    "ERROR_500": (EcosAPIError, "서버 오류입니다."),  # 재시도 대상
    "ERROR_600": (EcosAPIError, "DB Connection 오류입니다."),  # 재시도 대상
    "ERROR_601": (EcosAPIError, "SQL 오류입니다."),
    "ERROR_602": (EcosRateLimitError, "과도한 OpenAPI 호출로 이용이 제한되었습니다."),
}

# 재시도 가능한 에러 코드 (ECOS API는 하이픈 형식 사용: ERROR-500)
RETRYABLE_ERROR_CODES = {"ERROR-500", "ERROR-600", "ERROR-602"}
