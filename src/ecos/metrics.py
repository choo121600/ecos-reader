"""
ecos-reader 성능 메트릭

API 호출 성능과 캐시 효율성을 모니터링합니다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class ApiMetrics:
    """API 호출 메트릭"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    last_request_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """성공률 (%))"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def average_response_time(self) -> float:
        """평균 응답 시간 (초)"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests

    def record_request(self, success: bool, response_time: float) -> None:
        """요청 기록"""
        self.total_requests += 1
        self.last_request_time = time.time()

        if success:
            self.successful_requests += 1
            self.total_response_time += response_time
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)
        else:
            self.failed_requests += 1


@dataclass
class CacheMetrics:
    """캐시 메트릭"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    clears: int = 0

    @property
    def total_requests(self) -> int:
        """총 캐시 요청 수"""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """캐시 적중률 (%)"""
        total = self.total_requests
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def record_hit(self) -> None:
        """캐시 적중 기록"""
        self.hits += 1

    def record_miss(self) -> None:
        """캐시 미스 기록"""
        self.misses += 1

    def record_set(self) -> None:
        """캐시 저장 기록"""
        self.sets += 1

    def record_invalidation(self) -> None:
        """캐시 무효화 기록"""
        self.invalidations += 1

    def record_clear(self) -> None:
        """캐시 전체 삭제 기록"""
        self.clears += 1


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self._lock = Lock()
        self.api_metrics: dict[str, ApiMetrics] = {}
        self.cache_metrics = CacheMetrics()
        self._start_time = time.time()

    def record_api_request(self, endpoint: str, success: bool, response_time: float) -> None:
        """API 요청 메트릭 기록"""
        with self._lock:
            if endpoint not in self.api_metrics:
                self.api_metrics[endpoint] = ApiMetrics()

            self.api_metrics[endpoint].record_request(success, response_time)

    def record_cache_hit(self) -> None:
        """캐시 적중 기록"""
        with self._lock:
            self.cache_metrics.record_hit()

    def record_cache_miss(self) -> None:
        """캐시 미스 기록"""
        with self._lock:
            self.cache_metrics.record_miss()

    def record_cache_set(self) -> None:
        """캐시 저장 기록"""
        with self._lock:
            self.cache_metrics.record_set()

    def record_cache_invalidation(self) -> None:
        """캐시 무효화 기록"""
        with self._lock:
            self.cache_metrics.record_invalidation()

    def record_cache_clear(self) -> None:
        """캐시 전체 삭제 기록"""
        with self._lock:
            self.cache_metrics.record_clear()

    def get_summary(self) -> dict[str, Any]:
        """메트릭 요약 반환"""
        with self._lock:
            uptime = time.time() - self._start_time

            # API 메트릭 집계
            total_api_requests = sum(m.total_requests for m in self.api_metrics.values())
            total_successful = sum(m.successful_requests for m in self.api_metrics.values())
            total_response_time = sum(m.total_response_time for m in self.api_metrics.values())

            overall_success_rate = 0.0
            overall_avg_response_time = 0.0

            if total_api_requests > 0:
                overall_success_rate = (total_successful / total_api_requests) * 100

            if total_successful > 0:
                overall_avg_response_time = total_response_time / total_successful

            return {
                "uptime_seconds": round(uptime, 2),
                "api": {
                    "total_requests": total_api_requests,
                    "success_rate_percent": round(overall_success_rate, 2),
                    "average_response_time_seconds": round(overall_avg_response_time, 3),
                    "by_endpoint": {
                        endpoint: {
                            "requests": metrics.total_requests,
                            "success_rate_percent": round(metrics.success_rate, 2),
                            "avg_response_time_seconds": round(metrics.average_response_time, 3),
                            "min_response_time_seconds": round(metrics.min_response_time, 3)
                            if metrics.min_response_time != float("inf")
                            else 0,
                            "max_response_time_seconds": round(metrics.max_response_time, 3),
                        }
                        for endpoint, metrics in self.api_metrics.items()
                    },
                },
                "cache": {
                    "total_requests": self.cache_metrics.total_requests,
                    "hit_rate_percent": round(self.cache_metrics.hit_rate, 2),
                    "hits": self.cache_metrics.hits,
                    "misses": self.cache_metrics.misses,
                    "sets": self.cache_metrics.sets,
                    "invalidations": self.cache_metrics.invalidations,
                    "clears": self.cache_metrics.clears,
                },
            }

    def reset(self) -> None:
        """메트릭 초기화"""
        with self._lock:
            self.api_metrics.clear()
            self.cache_metrics = CacheMetrics()
            self._start_time = time.time()


# 전역 메트릭 수집기
_global_metrics: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """전역 메트릭 수집기 반환"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics


def record_api_request(endpoint: str, success: bool, response_time: float) -> None:
    """API 요청 메트릭 기록"""
    get_metrics_collector().record_api_request(endpoint, success, response_time)


def record_cache_hit() -> None:
    """캐시 적중 기록"""
    get_metrics_collector().record_cache_hit()


def record_cache_miss() -> None:
    """캐시 미스 기록"""
    get_metrics_collector().record_cache_miss()


def record_cache_set() -> None:
    """캐시 저장 기록"""
    get_metrics_collector().record_cache_set()


def record_cache_invalidation() -> None:
    """캐시 무효화 기록"""
    get_metrics_collector().record_cache_invalidation()


def record_cache_clear() -> None:
    """캐시 전체 삭제 기록"""
    get_metrics_collector().record_cache_clear()


def get_metrics_summary() -> dict[str, Any]:
    """메트릭 요약 반환"""
    return get_metrics_collector().get_summary()


def reset_metrics() -> None:
    """메트릭 초기화"""
    get_metrics_collector().reset()
