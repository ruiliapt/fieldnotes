"""Tests for ai_backend.py - AI provider abstraction layer."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from ai_backend import (
    AIConfig, AIManager, AIProvider, AIResponse,
    ClaudeProvider, OllamaProvider, OpenAICompatibleProvider,
    OPENAI_PRESETS,
)


class TestAIConfig:
    """Test AIConfig dataclass and persistence."""

    def test_default_values(self):
        config = AIConfig()
        assert config.provider == "auto"
        assert config.temperature == 0.3
        assert config.max_context_entries == 5

    def test_save_and_load(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)

        config = AIConfig(provider="claude", claude_api_key="test-key")
        config.save()

        loaded = AIConfig.load()
        assert loaded.provider == "claude"
        assert loaded.claude_api_key == "test-key"

    def test_load_nonexistent_returns_defaults(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        config = AIConfig.load()
        assert config.provider == "auto"

    def test_load_merges_new_defaults(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        # Save config with only some fields
        with open(config_path, "w") as f:
            json.dump({"provider": "ollama"}, f)
        config = AIConfig.load()
        assert config.provider == "ollama"
        assert config.temperature == 0.3  # default filled in


class TestAIResponse:
    """Test AIResponse dataclass."""

    def test_default_values(self):
        resp = AIResponse()
        assert resp.success is False
        assert resp.text == ""
        assert resp.error == ""

    def test_success_response(self):
        resp = AIResponse(text="result", success=True, provider_used="Claude")
        assert resp.success is True
        assert resp.text == "result"


class TestClaudeProvider:
    """Test Claude provider (mocked)."""

    def test_not_available_without_key(self):
        provider = ClaudeProvider(api_key="", model="claude-sonnet-4-20250514")
        assert provider.is_available() is False

    def test_complete_without_availability(self):
        provider = ClaudeProvider(api_key="", model="claude-sonnet-4-20250514")
        resp = provider.complete("system", "user")
        assert resp.success is False
        assert "Claude" in resp.error


class TestOllamaProvider:
    """Test Ollama provider (mocked)."""

    def test_not_available_when_server_down(self):
        provider = OllamaProvider(host="http://localhost:99999", model="test")
        assert provider.is_available() is False

    @patch("ai_backend.urlopen")
    def test_available_when_server_up(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        provider = OllamaProvider(host="http://localhost:11434", model="test")
        assert provider.is_available() is True

    @patch("ai_backend.urlopen")
    def test_complete_success(self, mock_urlopen):
        response_data = json.dumps({
            "response": "test output",
            "prompt_eval_count": 10,
            "eval_count": 5,
        }).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        provider = OllamaProvider(host="http://localhost:11434", model="test")
        resp = provider.complete("system", "user")
        assert resp.success is True
        assert resp.text == "test output"
        assert resp.provider_used == "Ollama"


class TestOpenAICompatibleProvider:
    """Test OpenAI compatible provider (mocked)."""

    def test_not_available_without_key(self):
        provider = OpenAICompatibleProvider(
            base_url="https://api.openai.com/v1", api_key="", model="gpt-4o"
        )
        assert provider.is_available() is False

    def test_not_available_without_url(self):
        provider = OpenAICompatibleProvider(
            base_url="", api_key="test-key", model="gpt-4o"
        )
        assert provider.is_available() is False

    def test_available_with_key_and_url(self):
        provider = OpenAICompatibleProvider(
            base_url="https://api.openai.com/v1", api_key="test-key", model="gpt-4o"
        )
        assert provider.is_available() is True

    @patch("ai_backend.urlopen")
    def test_complete_success(self, mock_urlopen):
        response_data = json.dumps({
            "choices": [{"message": {"content": "translated text"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        provider = OpenAICompatibleProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key", model="gpt-4o", preset_name="OpenAI",
        )
        resp = provider.complete("system", "user")
        assert resp.success is True
        assert resp.text == "translated text"


class TestOpenAIPresets:
    """Test OpenAI preset configurations."""

    def test_presets_have_required_keys(self):
        for name, preset in OPENAI_PRESETS.items():
            assert "base_url" in preset
            assert "default_model" in preset

    def test_known_presets_exist(self):
        assert "OpenAI" in OPENAI_PRESETS
        assert "DeepSeek" in OPENAI_PRESETS


class TestAIManager:
    """Test AIManager orchestration."""

    def test_get_status(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        manager = AIManager()
        status = manager.get_status()
        assert "claude_available" in status
        assert "ollama_available" in status
        assert "openai_available" in status
        assert "active_provider" in status

    def test_complete_no_provider(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        manager = AIManager()
        resp = manager.complete("sys", "user")
        assert resp.success is False
        assert "没有可用" in resp.error

    def test_reload_config(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        manager = AIManager()
        # Should not raise
        manager.reload_config()
