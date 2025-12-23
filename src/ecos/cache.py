"""
ecos-reader 캐시 레이어

동일 요청에 대한 응답을 캐싱하여 API 호출을 최소화합니다.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

from .logging import log_cache_operation
from .metrics import record_cache_clear, record_cache_hit, record_cache_miss, record_cache_set


@dataclass
class CacheEntry:
    """캐시 항목"""

    value: Any
    created_at: float
    ttl: int

    def is_expired(self) -> bool:
        """캐시 만료 여부 확인"""
        return time.time() - self.created_at > self.ttl


class Cache:
    """
    인메모리 LRU 캐시

    TTL(Time-To-Live) 기반으로 캐시를 관리합니다.

    Parameters
    ----------
    ttl : int
        캐시 유효 시간 (초), 기본값 3600 (1시간)
    maxsize : int
        최대 캐시 항목 수, 기본값 100

    Examples
    --------
    >>> cache = Cache(ttl=3600, maxsize=100)
    >>> cache.set("key", {"data": "value"})
    >>> cache.get("key")
    {'data': 'value'}
    """

    def __init__(self, ttl: int = 3600, maxsize: int = 100):
        self.ttl = ttl
        self.maxsize = maxsize
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        """캐시 활성화 상태"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """캐시 활성화 설정"""
        self._enabled = value

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """
        요청 파라미터로부터 캐시 키를 생성합니다.

        Parameters
        ----------
        *args : Any
            위치 인자
        **kwargs : Any
            키워드 인자

        Returns
        -------
        str
            해시된 캐시 키 (SHA256 전체 해시 사용으로 충돌 방지)
        """
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """
        캐시에서 값을 조회합니다.

        Parameters
        ----------
        key : str
            캐시 키

        Returns
        -------
        Optional[Any]
            캐시된 값, 없거나 만료된 경우 None
        """
        if not self._enabled:
            return None

        entry = self._cache.get(key)
        if entry is None:
            record_cache_miss()
            log_cache_operation("get", key, hit=False)
            return None

        if entry.is_expired():
            self.invalidate(key)
            record_cache_miss()
            log_cache_operation("get", key, hit=False)
            return None

        # LRU: 접근된 항목을 최신으로 이동
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        record_cache_hit()
        log_cache_operation("get", key, hit=True)
        return entry.value

    def set(self, key: str, value: Any) -> None:
        """
        캐시에 값을 저장합니다.

        Parameters
        ----------
        key : str
            캐시 키
        value : Any
            저장할 값
        """
        if not self._enabled:
            return

        # 최대 크기 초과 시 가장 오래된 항목 제거
        while len(self._cache) >= self.maxsize and self._access_order:
            oldest_key = self._access_order.pop(0)
            self._cache.pop(oldest_key, None)

        self._cache[key] = CacheEntry(value=value, created_at=time.time(), ttl=self.ttl)

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        record_cache_set()
        log_cache_operation("set", key)

    def invalidate(self, key: str) -> None:
        """
        특정 캐시 항목을 무효화합니다.

        Parameters
        ----------
        key : str
            무효화할 캐시 키
        """
        self._cache.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        self._cache.clear()
        self._access_order.clear()
        record_cache_clear()
        log_cache_operation("clear", "")

    def __len__(self) -> int:
        """캐시된 항목 수"""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """캐시 키 존재 여부"""
        return key in self._cache and not self._cache[key].is_expired()


# 전역 캐시 인스턴스
_global_cache: Cache | None = None


def get_cache() -> Cache:
    """전역 캐시 인스턴스를 반환합니다."""
    global _global_cache
    if _global_cache is None:
        from .config import Settings

        _global_cache = Cache(ttl=Settings.CACHE_TTL, maxsize=Settings.CACHE_MAXSIZE)
    return _global_cache


def clear_cache() -> None:
    """전역 캐시를 초기화합니다."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()


def disable_cache() -> None:
    """캐시를 비활성화합니다."""
    get_cache().enabled = False


def enable_cache() -> None:
    """캐시를 활성화합니다."""
    get_cache().enabled = True
