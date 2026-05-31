"""
디스크 캐시 단위 테스트 (#102).

격리를 위해 각 테스트는 tmp_path 디렉터리를 사용한다(전역 캐시 미사용).
"""

from __future__ import annotations

import json
import re

import responses

from ecos.cache import DiskCache, make_key
from ecos.client import EcosClient


class TestDiskCacheBasics:
    def test_set_get_roundtrip(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.set("k1", {"a": 1, "b": [2, 3]})
        assert dc.get("k1") == {"a": 1, "b": [2, 3]}
        # 실제 파일로 저장됨
        assert (tmp_path / "k1.json").exists()

    def test_miss_returns_none(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        assert dc.get("absent") is None

    def test_persists_across_instances(self, tmp_path):
        DiskCache(cache_dir=tmp_path, ttl=100).set("k", {"v": 1})
        # 새 인스턴스(프로세스 재시작 모사)에서도 읽힘 — 영속성
        assert DiskCache(cache_dir=tmp_path, ttl=100).get("k") == {"v": 1}

    def test_expired_entry_removed(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.set("k", {"v": 1})
        # created_at을 과거로 조작해 만료 유도
        path = tmp_path / "k.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["created_at"] -= 1000
        path.write_text(json.dumps(payload), encoding="utf-8")

        assert dc.get("k") is None
        assert not path.exists()  # 만료 항목은 제거됨

    def test_corrupted_file_removed(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        assert dc.get("bad") is None
        assert not path.exists()

    def test_clear_removes_all(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.set("a", {"v": 1})
        dc.set("b", {"v": 2})
        assert len(dc) == 2
        dc.clear()
        assert len(dc) == 0
        assert dc.get("a") is None

    def test_invalidate_single(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.set("a", {"v": 1})
        dc.set("b", {"v": 2})
        dc.invalidate("a")
        assert dc.get("a") is None
        assert dc.get("b") == {"v": 2}

    def test_disabled_noop(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.enabled = False
        dc.set("k", {"v": 1})
        assert dc.get("k") is None
        assert not (tmp_path / "k.json").exists()

    def test_contains(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        dc.set("k", {"v": 1})
        assert "k" in dc
        assert "nope" not in dc

    def test_make_key_matches_module_function(self, tmp_path):
        dc = DiskCache(cache_dir=tmp_path, ttl=100)
        assert dc._make_key("a", b=1) == make_key("a", b=1)

    def test_creates_cache_dir(self, tmp_path):
        target = tmp_path / "nested" / "cache"
        DiskCache(cache_dir=target, ttl=100)
        assert target.is_dir()


class TestDiskCacheClientIntegration:
    @responses.activate
    def test_client_disk_cache_persists_across_instances(self, tmp_path):
        responses.add(
            responses.GET,
            re.compile(r".*"),
            json={"StatisticSearch": {"row": [{"TIME": "202401", "DATA_VALUE": "1"}]}},
            status=200,
        )
        # 첫 클라이언트: 네트워크 → 디스크 캐시에 저장
        c1 = EcosClient(api_key="k", disk_cache=True, disk_cache_dir=str(tmp_path))
        c1.get_statistic_search("722Y001", "M", "202401", "202401")

        # 둘째 클라이언트(같은 키/디렉터리): 디스크 캐시 히트로 네트워크 0회 추가
        c2 = EcosClient(api_key="k", disk_cache=True, disk_cache_dir=str(tmp_path))
        c2.get_statistic_search("722Y001", "M", "202401", "202401")

        assert len(responses.calls) == 1  # 두 번째는 캐시 히트
