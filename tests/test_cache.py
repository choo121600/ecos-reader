"""
cache 모듈 테스트
"""

from __future__ import annotations

import threading
import time

from ecos.cache import (
    Cache,
    clear_cache,
    disable_cache,
    enable_cache,
    get_cache,
)


class TestCache:
    """Cache 클래스 테스트"""

    def test_set_and_get(self):
        """캐시 저장 및 조회"""
        cache = Cache(ttl=3600)
        cache.set("key1", {"data": "value1"})
        assert cache.get("key1") == {"data": "value1"}

    def test_get_nonexistent_key(self):
        """존재하지 않는 키 조회"""
        cache = Cache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """TTL 만료 테스트"""
        cache = Cache(ttl=1)  # 1초 TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(1.1)  # 만료 대기
        assert cache.get("key1") is None

    def test_maxsize_eviction(self):
        """최대 크기 초과 시 LRU 제거"""
        cache = Cache(ttl=3600, maxsize=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # key1 접근하여 최신으로
        cache.get("key1")

        # 새 항목 추가 - key2 제거됨 (LRU)
        cache.set("key4", "value4")

        assert "key1" in cache
        assert "key2" not in cache
        assert "key3" in cache
        assert "key4" in cache

    def test_invalidate(self):
        """캐시 무효화"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        """캐시 전체 삭제"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert len(cache) == 0

    def test_contains(self):
        """캐시 키 존재 확인"""
        cache = Cache()
        cache.set("key1", "value1")
        assert "key1" in cache
        assert "key2" not in cache

    def test_len(self):
        """캐시 항목 수"""
        cache = Cache()
        assert len(cache) == 0
        cache.set("key1", "value1")
        assert len(cache) == 1
        cache.set("key2", "value2")
        assert len(cache) == 2

    def test_disable_cache(self):
        """캐시 비활성화"""
        cache = Cache()
        cache.set("key1", "value1")

        cache.enabled = False
        assert cache.get("key1") is None

        cache.set("key2", "value2")
        cache.enabled = True
        assert cache.get("key2") is None  # 비활성화 중 저장 안 됨

    def test_make_key(self):
        """캐시 키 생성"""
        cache = Cache()
        key1 = cache._make_key("arg1", "arg2", kwarg1="val1")
        key2 = cache._make_key("arg1", "arg2", kwarg1="val1")
        key3 = cache._make_key("arg1", "arg3", kwarg1="val1")

        assert key1 == key2
        assert key1 != key3


class TestGlobalCache:
    """전역 캐시 함수 테스트"""

    def test_get_cache_singleton(self):
        """전역 캐시는 싱글톤"""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_clear_cache(self):
        """전역 캐시 초기화"""
        cache = get_cache()
        cache.set("test", "value")
        clear_cache()
        assert cache.get("test") is None

    def test_disable_enable_cache(self):
        """캐시 비활성화/활성화"""
        cache = get_cache()
        cache.set("test", "value")

        disable_cache()
        assert cache.get("test") is None

        enable_cache()
        cache.set("test2", "value2")
        assert cache.get("test2") == "value2"


class TestCacheConcurrency:
    """스레드 안전성 테스트 (#10)"""

    def test_concurrent_set_get_no_corruption(self):
        """10개 스레드가 동시에 set/get 해도 예외/데이터 손상이 없다."""
        cache = Cache(ttl=3600, maxsize=50)
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def worker(tid: int) -> None:
            barrier.wait()  # 모든 스레드가 동시에 출발
            try:
                for i in range(500):
                    key = f"t{tid}-k{i % 20}"
                    cache.set(key, {"tid": tid, "i": i})
                    cache.get(key)
                    cache.get(f"t{(tid + 1) % 10}-k{i % 20}")
                    if i % 50 == 0:
                        cache.invalidate(key)
                    len(cache)
                    _ = key in cache
            except Exception as exc:  # pragma: no cover - 실패 시 진단용
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for thr in threads:
            thr.start()
        for thr in threads:
            thr.join()

        assert not errors, f"동시성 예외 발생: {errors[:3]}"
        # maxsize 불변식: 동시 부하 후에도 항목 수가 maxsize를 넘지 않는다.
        assert len(cache) <= cache.maxsize

    def test_lru_eviction_keeps_maxsize_invariant(self):
        """대량 set 후 항목 수가 정확히 maxsize 이하로 유지된다 (O(1) 퇴출)."""
        cache = Cache(ttl=3600, maxsize=100)
        for i in range(1000):
            cache.set(f"key{i}", i)
        assert len(cache) == 100
        # 가장 최근 100개만 남아야 한다.
        assert "key999" in cache
        assert "key899" not in cache
