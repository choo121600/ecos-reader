"""
ecos-reader 캐시 레이어

동일 요청에 대한 응답을 캐싱하여 API 호출을 최소화합니다.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .logging import log_cache_operation
from .metrics import record_cache_clear, record_cache_hit, record_cache_miss, record_cache_set


def make_key(*args: Any, **kwargs: Any) -> str:
    """요청 파라미터로부터 캐시 키(SHA256 전체 해시)를 생성합니다.

    인메모리/디스크 캐시가 동일한 키 규칙을 공유하도록 모듈 수준에 둔다.
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.sha256(key_data.encode()).hexdigest()


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
        # OrderedDict가 LRU 순서를 직접 보유하므로 O(1) move_to_end/popitem 사용.
        # 별도 _access_order 리스트(O(n) remove)와의 비일관성을 제거한다.
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        # 재진입 가능 락: get()이 만료 시 invalidate()를 호출하므로 RLock 필요.
        self._lock = threading.RLock()
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
        return make_key(*args, **kwargs)

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

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                record_cache_miss()
                log_cache_operation("get", key, hit=False)
                return None

            if entry.is_expired():
                # 만료 항목 능동 제거 (maxsize 미만이어도 메모리 점유 방지)
                self._cache.pop(key, None)
                record_cache_miss()
                log_cache_operation("get", key, hit=False)
                return None

            # LRU: 접근된 항목을 최신으로 이동 (O(1))
            self._cache.move_to_end(key)

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

        with self._lock:
            if key in self._cache:
                # 기존 키 갱신: 값 교체 후 최신으로 이동, 퇴출 불필요
                self._cache[key] = CacheEntry(value=value, created_at=time.time(), ttl=self.ttl)
                self._cache.move_to_end(key)
            else:
                # 최대 크기 초과 시 가장 오래된 항목(맨 앞) 제거 (O(1))
                while self._cache and len(self._cache) >= self.maxsize:
                    self._cache.popitem(last=False)
                self._cache[key] = CacheEntry(value=value, created_at=time.time(), ttl=self.ttl)

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
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        with self._lock:
            self._cache.clear()
            record_cache_clear()
            log_cache_operation("clear", "")

    def __len__(self) -> int:
        """캐시된 항목 수"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """캐시 키 존재 여부 (만료 항목은 미포함으로 간주)"""
        with self._lock:
            entry = self._cache.get(key)
            return entry is not None and not entry.is_expired()


def _default_disk_cache_dir() -> Path:
    """디스크 캐시 기본 경로. ``XDG_CACHE_HOME`` 또는 ``~/.cache`` 하위."""
    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base) if base else Path.home() / ".cache"
    return root / "ecos-reader"


class DiskCache:
    """파일 기반 영속 캐시 (#102, opt-in).

    인메모리 :class:`Cache` 와 동일한 인터페이스(``_make_key``/``get``/``set``/
    ``clear``/``invalidate``/``enabled``)를 제공하여 클라이언트에서 드롭인
    교체된다. 응답을 캐시 디렉터리에 해시 키의 JSON 파일로 저장하며,
    프로세스/세션을 넘어 유지된다. 인메모리 캐시의 100엔트리 한계가 없다.

    Parameters
    ----------
    cache_dir : str or Path, optional
        캐시 디렉터리. 생략 시 ``~/.cache/ecos-reader``.
    ttl : int, default 86400
        캐시 유효 시간(초). 기본 1일.
    """

    def __init__(self, cache_dir: str | Path | None = None, ttl: int = 86400) -> None:
        self.ttl = ttl
        self._enabled = True
        self._lock = threading.RLock()
        self.cache_dir = Path(cache_dir) if cache_dir else _default_disk_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        return make_key(*args, **kwargs)

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        if not self._enabled:
            return None
        path = self._path(key)
        with self._lock:
            try:
                raw = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                record_cache_miss()
                log_cache_operation("get", key, hit=False)
                return None

            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, KeyError):
                # 손상된 파일은 제거하고 미스 처리.
                path.unlink(missing_ok=True)
                record_cache_miss()
                log_cache_operation("get", key, hit=False)
                return None

            if time.time() - payload["created_at"] > payload["ttl"]:
                path.unlink(missing_ok=True)
                record_cache_miss()
                log_cache_operation("get", key, hit=False)
                return None

            record_cache_hit()
            log_cache_operation("get", key, hit=True)
            return payload["value"]

    def set(self, key: str, value: Any) -> None:
        if not self._enabled:
            return
        with self._lock:
            payload = {"created_at": time.time(), "ttl": self.ttl, "value": value}
            # 원자적 쓰기: 임시 파일에 쓰고 rename(같은 FS에서 원자적).
            tmp = self.cache_dir / f"{key}.{os.getpid()}.tmp"
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            os.replace(tmp, self._path(key))
            record_cache_set()
            log_cache_operation("set", key)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._path(key).unlink(missing_ok=True)

    def clear(self) -> None:
        with self._lock:
            for p in self.cache_dir.glob("*.json"):
                p.unlink(missing_ok=True)
            record_cache_clear()
            log_cache_operation("clear", "")

    def __len__(self) -> int:
        with self._lock:
            return sum(1 for _ in self.cache_dir.glob("*.json"))

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None


# 전역 캐시 인스턴스
_global_cache: Cache | None = None
_global_disk_cache: DiskCache | None = None


def get_cache() -> Cache:
    """전역 캐시 인스턴스를 반환합니다."""
    global _global_cache
    if _global_cache is None:
        from .config import Settings

        _global_cache = Cache(ttl=Settings.CACHE_TTL, maxsize=Settings.CACHE_MAXSIZE)
    return _global_cache


def get_disk_cache(cache_dir: str | Path | None = None) -> DiskCache:
    """전역 디스크 캐시 인스턴스를 반환합니다(opt-in, 없으면 생성)."""
    global _global_disk_cache
    if _global_disk_cache is None:
        from .config import Settings

        _global_disk_cache = DiskCache(
            cache_dir=cache_dir or Settings.DISK_CACHE_DIR,
            ttl=Settings.DISK_CACHE_TTL,
        )
    return _global_disk_cache


def reset_disk_cache() -> None:
    """전역 디스크 캐시 핸들을 초기화합니다(다음 접근 시 재생성)."""
    global _global_disk_cache
    _global_disk_cache = None


def clear_cache() -> None:
    """전역 캐시를 초기화합니다(인메모리 + 디스크)."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
    if _global_disk_cache is not None:
        _global_disk_cache.clear()


def disable_cache() -> None:
    """캐시를 비활성화합니다."""
    get_cache().enabled = False


def enable_cache() -> None:
    """캐시를 활성화합니다."""
    get_cache().enabled = True
