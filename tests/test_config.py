"""
config 모듈 테스트
"""

from __future__ import annotations

import pytest

import ecos
from ecos.config import Settings, clear_api_key, get_api_key, set_api_key
from ecos.exceptions import EcosConfigError


class TestSetApiKey:
    """set_api_key 함수 테스트"""

    def test_set_api_key_success(self):
        """API 키 설정 성공"""
        set_api_key("test_key_123")
        assert get_api_key() == "test_key_123"

    def test_set_api_key_empty_string_raises(self):
        """빈 문자열 설정 시 에러"""
        with pytest.raises(EcosConfigError):
            set_api_key("")

    def test_set_api_key_none_raises(self):
        """None 설정 시 에러"""
        with pytest.raises(EcosConfigError):
            set_api_key(None)  # type: ignore


class TestGetApiKey:
    """get_api_key 함수 테스트"""

    def test_get_api_key_from_set(self):
        """set_api_key로 설정한 키 조회"""
        set_api_key("my_test_key")
        assert get_api_key() == "my_test_key"

    def test_get_api_key_from_env(self, monkeypatch):
        """환경 변수에서 키 조회"""
        monkeypatch.setenv("ECOS_API_KEY", "env_test_key")
        clear_api_key()
        assert get_api_key() == "env_test_key"

    def test_get_api_key_set_overrides_env(self, monkeypatch):
        """set_api_key가 환경 변수보다 우선"""
        monkeypatch.setenv("ECOS_API_KEY", "env_key")
        set_api_key("direct_key")
        assert get_api_key() == "direct_key"

    def test_get_api_key_not_set_raises(self, monkeypatch):
        """키가 없으면 에러"""
        monkeypatch.delenv("ECOS_API_KEY", raising=False)
        clear_api_key()
        with pytest.raises(EcosConfigError) as exc_info:
            get_api_key()
        assert "API Key가 설정되지 않았습니다" in str(exc_info.value)


class TestClearApiKey:
    """clear_api_key 함수 테스트"""

    def test_clear_api_key(self, monkeypatch):
        """API 키 초기화"""
        set_api_key("some_key")
        clear_api_key()
        monkeypatch.delenv("ECOS_API_KEY", raising=False)
        with pytest.raises(EcosConfigError):
            get_api_key()


class TestSettings:
    """Settings 클래스 테스트"""

    def test_default_values(self):
        """기본 설정값 확인"""
        assert Settings.BASE_URL == "https://ecos.bok.or.kr/api/"
        assert Settings.DEFAULT_FORMAT == "json"
        assert Settings.DEFAULT_LANG == "kr"
        assert Settings.DEFAULT_TIMEOUT == 30
        assert Settings.MAX_RETRIES == 3
        assert Settings.CACHE_TTL == 3600


class TestModuleLevelApi:
    """모듈 레벨 API 테스트"""

    def test_ecos_set_api_key(self):
        """ecos.set_api_key()"""
        ecos.set_api_key("module_test_key")
        assert ecos.get_api_key() == "module_test_key"
