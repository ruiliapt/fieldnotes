"""Tests for GUI widgets - IPAToolbarWidget, TagSelectorWidget."""
import os
import sys
import pytest

from ui.widgets import IPAToolbarWidget, TagSelectorWidget


class TestIPAToolbarWidget:
    """Test IPA symbol toolbar."""

    def test_creates_without_error(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        assert widget is not None

    def test_starts_collapsed(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        assert widget.content_widget.isVisible() is False

    def test_toggle_expands(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        widget._toggle()
        assert widget._expanded is True
        assert "\u25bc" in widget.toggle_btn.text()

    def test_toggle_collapses(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        widget._toggle()  # expand
        widget._toggle()  # collapse
        assert widget._expanded is False

    def test_symbol_signal_emitted(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        with qtbot.waitSignal(widget.symbol_clicked, timeout=1000) as blocker:
            widget.symbol_clicked.emit("\u014b")
        assert blocker.args == ["\u014b"]

    def test_has_all_categories(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        assert len(widget.IPA_CATEGORIES) >= 5


class TestTagSelectorWidget:
    """Test tag selector widget."""

    def test_creates_without_error(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        assert widget is not None

    def test_get_tags_empty_by_default(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        assert widget.get_tags() == []

    def test_set_and_get_predefined_tags(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_tags(["\u5df2\u5ba1\u6838"])
        tags = widget.get_tags()
        assert "\u5df2\u5ba1\u6838" in tags

    def test_set_custom_tags(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_tags(["\u81ea\u5b9a\u4e49\u6807\u7b7e"])
        tags = widget.get_tags()
        assert "\u81ea\u5b9a\u4e49\u6807\u7b7e" in tags

    def test_clear_tags(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_tags(["\u5df2\u5ba1\u6838", "\u81ea\u5b9a\u4e49"])
        widget.clear()
        assert widget.get_tags() == []

    def test_mixed_predefined_and_custom(self, qtbot):
        widget = TagSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_tags(["\u5df2\u5ba1\u6838", "\u6211\u7684\u6807\u7b7e"])
        tags = widget.get_tags()
        assert "\u5df2\u5ba1\u6838" in tags
        assert "\u6211\u7684\u6807\u7b7e" in tags
