"""
rate limiter 단위 테스트 (#102).

실제 시간을 쓰지 않도록 clock/sleep을 주입해 결정적으로 검증한다.
"""

from __future__ import annotations

import re

import pytest
import responses

from ecos.client import EcosClient
from ecos.ratelimit import (
    RateLimiter,
    get_rate_limiter,
    reset_rate_limiter,
    set_rate_limiter,
)


class FakeTime:
    """주입용 가짜 단조 시계 + sleep(누적 기록)."""

    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds  # 잠든 만큼 시간 경과


def _limiter(max_calls, period, ft):
    return RateLimiter(max_calls, period, clock=ft.clock, sleep=ft.sleep)


class TestRateLimiterThrottle:
    def test_under_limit_does_not_sleep(self):
        ft = FakeTime()
        rl = _limiter(3, 10, ft)
        for _ in range(3):
            rl.acquire()
        assert ft.sleeps == []
        assert len(rl) == 3

    def test_blocks_when_window_full(self):
        ft = FakeTime()
        rl = _limiter(2, 10, ft)
        rl.acquire()  # t=0
        rl.acquire()  # t=0
        rl.acquire()  # 윈도우 가득 → 가장 오래된(t=0) 만료까지 10초 대기
        assert ft.sleeps == [10.0]
        # 대기 후 t=10에서 t=0 두 건은 만료 제거, 새 호출만 남음
        assert len(rl) == 1

    def test_window_slides_no_sleep_after_expiry(self):
        ft = FakeTime()
        rl = _limiter(2, 10, ft)
        rl.acquire()  # t=0
        rl.acquire()  # t=0
        ft.t = 11.0  # 윈도우(10초)를 지나 경과
        rl.acquire()  # 이전 두 건 만료 → 대기 없음
        assert ft.sleeps == []
        assert len(rl) == 1

    def test_exact_300_per_180s_semantics(self):
        # 임의 180초 창에 300건 이하 보장: 300건 후 1건은 대기
        ft = FakeTime()
        rl = _limiter(300, 180, ft)
        for _ in range(300):
            rl.acquire()
        assert ft.sleeps == []
        rl.acquire()  # 301번째 → 대기
        assert ft.sleeps == [180.0]


class TestRateLimiterConfig:
    def test_disabled_never_sleeps(self):
        ft = FakeTime()
        rl = RateLimiter(1, 10, enabled=False, clock=ft.clock, sleep=ft.sleep)
        for _ in range(5):
            rl.acquire()
        assert ft.sleeps == []

    def test_max_calls_zero_is_unlimited(self):
        ft = FakeTime()
        rl = _limiter(0, 10, ft)
        for _ in range(5):
            rl.acquire()
        assert ft.sleeps == []

    def test_reset_clears_history(self):
        ft = FakeTime()
        rl = _limiter(2, 10, ft)
        rl.acquire()
        rl.acquire()
        rl.reset()
        assert len(rl) == 0
        rl.acquire()  # 리셋 후라 대기 없음
        assert ft.sleeps == []


class TestGlobalRateLimiter:
    def test_singleton_and_reset(self):
        a = get_rate_limiter()
        b = get_rate_limiter()
        assert a is b
        reset_rate_limiter()
        c = get_rate_limiter()
        assert c is not a

    def test_set_rate_limiter(self):
        custom = RateLimiter(5, 5)
        set_rate_limiter(custom)
        assert get_rate_limiter() is custom


class _CountingLimiter(RateLimiter):
    """acquire 호출 횟수를 세는 limiter."""

    def __init__(self) -> None:
        super().__init__(max_calls=0)  # 무제한(대기 없음)
        self.acquired = 0

    def acquire(self) -> None:
        self.acquired += 1


@pytest.mark.usefixtures("set_api_key")
class TestRateLimiterClientIntegration:
    @responses.activate
    def test_acquire_called_on_network_request(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json={"StatisticSearch": {"row": [{"TIME": "202401", "DATA_VALUE": "1"}]}},
            status=200,
        )
        limiter = _CountingLimiter()
        client = EcosClient(api_key="k", use_cache=False, rate_limiter=limiter)
        client.get_statistic_search("722Y001", "M", "202401", "202401")
        assert limiter.acquired == 1

    @responses.activate
    def test_acquire_not_called_on_cache_hit(self):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json={"StatisticSearch": {"row": [{"TIME": "202401", "DATA_VALUE": "1"}]}},
            status=200,
        )
        limiter = _CountingLimiter()
        client = EcosClient(api_key="k", use_cache=True, rate_limiter=limiter)
        # 첫 호출: 네트워크 → acquire 1회
        client.get_statistic_search("722Y001", "M", "202401", "202401")
        # 둘째 호출: 캐시 히트 → acquire 추가 없음
        client.get_statistic_search("722Y001", "M", "202401", "202401")
        assert limiter.acquired == 1
