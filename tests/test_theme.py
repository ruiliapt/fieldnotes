"""Tests for theme.py - theme management and stylesheet generation."""
import pytest
from theme import ThemeManager, ThemeColors, LIGHT_THEME, DARK_THEME


class TestThemeColors:
    """Test theme color definitions."""

    def test_light_theme_has_all_fields(self):
        fields = [f.name for f in ThemeColors.__dataclass_fields__.values()]
        for field in fields:
            assert hasattr(LIGHT_THEME, field)
            assert getattr(LIGHT_THEME, field) != ""

    def test_dark_theme_has_all_fields(self):
        fields = [f.name for f in ThemeColors.__dataclass_fields__.values()]
        for field in fields:
            assert hasattr(DARK_THEME, field)
            assert getattr(DARK_THEME, field) != ""

    def test_light_and_dark_differ(self):
        assert LIGHT_THEME.bg_primary != DARK_THEME.bg_primary
        assert LIGHT_THEME.text_primary != DARK_THEME.text_primary


class TestThemeManager:
    """Test ThemeManager behavior."""

    def test_default_is_light(self):
        tm = ThemeManager()
        assert tm.name == "light"

    def test_set_dark_theme(self):
        tm = ThemeManager("dark")
        assert tm.name == "dark"
        assert tm.colors == DARK_THEME

    def test_invalid_theme_falls_back_to_light(self):
        tm = ThemeManager("invalid")
        assert tm.name == "light"

    def test_set_theme(self):
        tm = ThemeManager("light")
        tm.set_theme("dark")
        assert tm.name == "dark"

    def test_set_invalid_theme_does_nothing(self):
        tm = ThemeManager("light")
        tm.set_theme("invalid")
        assert tm.name == "light"

    def test_generate_stylesheet_returns_string(self):
        tm = ThemeManager("light")
        css = tm.generate_stylesheet()
        assert isinstance(css, str)
        assert len(css) > 100

    def test_stylesheet_contains_theme_colors(self):
        tm = ThemeManager("dark")
        css = tm.generate_stylesheet()
        assert DARK_THEME.bg_primary in css
        assert DARK_THEME.text_primary in css

    def test_get_highlight_color(self, qapp):
        tm = ThemeManager("light")
        color = tm.get_highlight_color()
        assert color.isValid()
