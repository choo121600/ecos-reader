"""
선제 rate limiter (#102).

ECOS Open API는 **300 calls / 3분(180초)** 한도를 둔다(코드에 명문화되지
않았던 제약). 대량 조회/크롤 시 이를 초과하면 차단되므로, 클라이언트가
서버를 때리기 **전에** 스스로 throttle 한다.

알고리즘은 **sliding window log**: 최근 호출 시각을 deque에 보관하고, 임의의
``period`` 초 창에 ``max_calls`` 건을 넘지 않도록 가장 오래된 호출이 창을
벗어날 때까지 대기한다. "300/3분" 의미를 근사 없이 정확히 반영한다.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class RateLimiter:
    """Sliding window log 방식의 선제 rate limiter (스레드 안전).

    Parameters
    ----------
    max_calls : int, default 300
        ``period`` 초 창에서 허용하는 최대 호출 수. 0 이하면 무제한(throttle 없음).
    period : float, default 180.0
        윈도우 길이(초). 기본 ECOS 한도는 300 calls / 180초.
    enabled : bool, default True
        ``False`` 면 :meth:`acquire` 가 즉시 통과한다.
    clock : callable, optional
        현재 시각(단조 증가, 초)을 반환하는 함수. 테스트 주입용.
        기본값 :func:`time.monotonic`.
    sleep : callable, optional
        대기 함수. 테스트 주입용. 기본값 :func:`time.sleep`.
    """

    def __init__(
        self,
        max_calls: int = 300,
        period: float = 180.0,
        *,
        enabled: bool = True,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.max_calls = max_calls
        self.period = float(period)
        self.enabled = enabled
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep

    def acquire(self) -> None:
        """호출 1건의 권한을 얻는다. 창이 가득 차 있으면 가장 오래된 호출이
        만료될 때까지 대기한 뒤 진행한다."""
        if not self.enabled or self.max_calls <= 0:
            return

        with self._lock:
            now = self._clock()
            self._evict(now)

            if len(self._calls) >= self.max_calls:
                # 가장 오래된 호출이 창을 벗어날 때까지 대기.
                wait = self.period - (now - self._calls[0])
                if wait > 0:
                    self._sleep(wait)
                    now = self._clock()
                    self._evict(now)

            self._calls.append(now)

    def _evict(self, now: float) -> None:
        """``period`` 창을 벗어난(만료된) 호출 기록을 제거한다."""
        cutoff = now - self.period
        while self._calls and self._calls[0] <= cutoff:
            self._calls.popleft()

    def reset(self) -> None:
        """기록된 호출 이력을 모두 비운다."""
        with self._lock:
            self._calls.clear()

    def __len__(self) -> int:
        """현재 윈도우에 기록된 호출 수(만료 미반영 단순 길이)."""
        with self._lock:
            return len(self._calls)


# 전역 rate limiter (같은 계정/키의 여러 클라이언트가 한도를 공유하도록 기본 사용).
_global_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """전역 rate limiter 인스턴스를 반환한다(없으면 Settings 기본값으로 생성)."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        from .config import Settings

        _global_rate_limiter = RateLimiter(
            Settings.RATE_LIMIT_CALLS,
            Settings.RATE_LIMIT_PERIOD,
            enabled=Settings.RATE_LIMIT_ENABLED,
        )
    return _global_rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """전역 rate limiter를 교체한다."""
    global _global_rate_limiter
    _global_rate_limiter = limiter


def reset_rate_limiter() -> None:
    """전역 rate limiter를 초기화한다(다음 접근 시 재생성)."""
    global _global_rate_limiter
    _global_rate_limiter = None
