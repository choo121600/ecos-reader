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


class EcosValidationError(EcosAPIError):
    """클라이언트 책임 요청 오류 (4xx 성격)

    필수값 누락·형식/타입 오류 등 요청 자체가 잘못된 경우. 동일 요청을
    재시도해도 동일하게 실패하므로 재시도 대상이 아닙니다.
    """

    pass


class EcosServerError(EcosAPIError):
    """ECOS 서버측 오류 (5xx 성격)

    서버 오류·DB Connection·SQL 오류 등. 일시적 오류(서버/DB)는 재시도
    대상일 수 있습니다 (`ECOS_ERROR_CODES`의 retryable 플래그 참조).
    """

    pass


class EcosRateLimitError(EcosError):
    """Rate Limit 초과"""

    def __init__(self, message: str, code: str = "602"):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ECOS 에러 코드 단일 진실원천 (Single Source of Truth)
#
# 키는 ECOS API가 실제로 반환하는 하이픈 형식("ERROR-602")으로 통일한다.
# 값은 (예외 클래스, 기본 메시지, 재시도 가능 여부) 3-튜플이다.
# 클라이언트는 이 매핑을 조회해 코드별 예외를 일관되게 발생시키고,
# RETRYABLE_ERROR_CODES도 여기서 파생한다.
ECOS_ERROR_CODES: dict[str, tuple[type[EcosError], str, bool]] = {
    # 정보 코드
    "INFO-100": (EcosConfigError, "인증키가 유효하지 않습니다.", False),
    "INFO-200": (EcosAPIError, "해당하는 데이터가 없습니다.", False),  # 빈 결과로 처리
    # 클라이언트 책임(요청 검증) 에러 — 재시도해도 동일 실패
    "ERROR-100": (EcosValidationError, "필수 값이 누락되어 있습니다.", False),
    "ERROR-101": (EcosValidationError, "주기와 다른 형식의 날짜 형식입니다.", False),
    "ERROR-200": (EcosValidationError, "파일타입 값이 누락 혹은 유효하지 않습니다.", False),
    "ERROR-300": (EcosValidationError, "조회건수 값이 누락되어 있습니다.", False),
    "ERROR-301": (EcosValidationError, "조회건수 값의 타입이 유효하지 않습니다.", False),
    "ERROR-400": (EcosAPIError, "검색범위가 적정범위를 초과하여 TIMEOUT이 발생하였습니다.", False),
    # 서버측 에러 — 서버/DB는 일시적일 수 있어 재시도, SQL 오류는 비재시도
    "ERROR-500": (EcosServerError, "서버 오류입니다.", True),
    "ERROR-600": (EcosServerError, "DB Connection 오류입니다.", True),
    "ERROR-601": (EcosServerError, "SQL 오류입니다.", False),
    # Rate limit
    "ERROR-602": (EcosRateLimitError, "과도한 OpenAPI 호출로 이용이 제한되었습니다.", True),
}

# 재시도 가능한 에러 코드 — ECOS_ERROR_CODES의 retryable 플래그에서 파생
RETRYABLE_ERROR_CODES: frozenset[str] = frozenset(
    code for code, (_exc, _msg, retryable) in ECOS_ERROR_CODES.items() if retryable
)
