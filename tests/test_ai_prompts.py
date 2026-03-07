"""Tests for ai_prompts.py - prompt building and formatting."""
import pytest
from ai_prompts import (
    build_gloss_prompt, build_translation_prompt,
    _format_context_entries, LEIPZIG_ABBREVIATIONS,
)


class TestFormatContextEntries:
    """Test few-shot example formatting."""

    def test_empty_entries(self):
        assert _format_context_entries([]) == ""

    def test_single_entry(self):
        entries = [{
            "source_text": "hello",
            "gloss": "greeting",
            "translation": "hi",
            "source_text_cn": "",
        }]
        result = _format_context_entries(entries)
        assert "例1:" in result
        assert "hello" in result
        assert "greeting" in result

    def test_skips_entries_without_gloss(self):
        entries = [
            {"source_text": "hello", "gloss": "", "translation": "hi"},
        ]
        result = _format_context_entries(entries)
        assert result == ""

    def test_includes_chinese_source(self):
        entries = [{
            "source_text": "hello",
            "gloss": "greeting",
            "translation": "",
            "source_text_cn": "测试",
        }]
        result = _format_context_entries(entries)
        assert "测试" in result


class TestBuildGlossPrompt:
    """Test gloss prompt construction."""

    def test_returns_system_and_user_prompts(self):
        sys_p, usr_p = build_gloss_prompt("hello world", [])
        assert isinstance(sys_p, str)
        assert isinstance(usr_p, str)

    def test_system_prompt_contains_rules(self):
        sys_p, _ = build_gloss_prompt("test", [])
        assert "Leipzig" in sys_p or "莱比锡" in sys_p
        assert "gloss" in sys_p.lower()

    def test_user_prompt_contains_source_text(self):
        _, usr_p = build_gloss_prompt("hello world", [])
        assert "hello world" in usr_p

    def test_user_prompt_with_context(self):
        context = [{
            "source_text": "prev", "gloss": "PREV",
            "translation": "previous", "source_text_cn": "",
        }]
        _, usr_p = build_gloss_prompt("test", context)
        assert "prev" in usr_p

    def test_user_prompt_with_chinese(self):
        _, usr_p = build_gloss_prompt("test", [], source_text_cn="测试")
        assert "测试" in usr_p


class TestBuildTranslationPrompt:
    """Test translation prompt construction."""

    def test_returns_system_and_user_prompts(self):
        sys_p, usr_p = build_translation_prompt("hello", "greeting", [])
        assert isinstance(sys_p, str)
        assert isinstance(usr_p, str)

    def test_user_prompt_contains_source_and_gloss(self):
        _, usr_p = build_translation_prompt("hello", "greeting", [])
        assert "hello" in usr_p
        assert "greeting" in usr_p

    def test_system_prompt_contains_translation_rules(self):
        sys_p, _ = build_translation_prompt("test", "test", [])
        assert "翻译" in sys_p


class TestLeipzigAbbreviations:
    """Test abbreviation reference."""

    def test_contains_common_abbreviations(self):
        for abbr in ["1", "SG", "PL", "NOM", "ACC", "PST", "NEG"]:
            assert abbr in LEIPZIG_ABBREVIATIONS
