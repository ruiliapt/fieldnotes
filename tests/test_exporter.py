"""Tests for exporter.py - TextFormatter and WordExporter."""
import os
import pytest
from exporter import TextFormatter, WordExporter


class TestCalculateDisplayWidth:
    """Test character width calculation for alignment."""

    def test_ascii_characters(self):
        assert TextFormatter.calculate_display_width("hello") == 5

    def test_chinese_characters(self):
        assert TextFormatter.calculate_display_width("你好") == 4  # 2 chars * 2 width

    def test_mixed_ascii_and_chinese(self):
        width = TextFormatter.calculate_display_width("hi你")
        assert width == 4  # 2 + 2

    def test_empty_string(self):
        assert TextFormatter.calculate_display_width("") == 0

    def test_combining_diacritics_zero_width(self):
        # Combining tilde should be zero width
        width = TextFormatter.calculate_display_width("n\u0303")  # n with combining tilde
        assert width == 1  # only the base character counts

    def test_superscript_digits(self):
        # Superscript digits should have reduced width
        width = TextFormatter.calculate_display_width("\u00b2\u00b3")  # superscript 2, 3
        assert width >= 1


class TestAlignWords:
    """Test word alignment for linguistic glossing."""

    def test_equal_length_lists(self):
        src, gls = TextFormatter.align_words(["hello", "world"], ["1SG", "go"])
        assert len(src) == len(gls)

    def test_unequal_length_pads_shorter(self):
        src, gls = TextFormatter.align_words(["a", "b", "c"], ["x", "y"])
        # Should pad gloss with empty string
        assert len(src) == len(gls)

    def test_alignment_preserves_content(self):
        src, gls = TextFormatter.align_words(["eat"], ["1SG"])
        assert "eat" in src
        assert "1SG" in gls


class TestFormatEntry:
    """Test single entry formatting."""

    def test_basic_format(self):
        entry = {
            "id": 1,
            "example_id": "EX1",
            "source_text": "hello world",
            "gloss": "1SG go",
            "translation": "I go",
            "notes": "",
        }
        text = TextFormatter.format_entry(entry)
        assert "(EX1)" in text
        assert "hello" in text
        assert "1SG" in text
        assert "'I go'" in text

    def test_format_without_numbering(self):
        entry = {
            "id": 1,
            "example_id": "EX1",
            "source_text": "hello",
            "gloss": "1SG",
            "translation": "I",
            "notes": "",
        }
        text = TextFormatter.format_entry(entry, show_numbering=False)
        assert "(EX1)" not in text

    def test_format_with_notes(self):
        entry = {
            "id": 1,
            "example_id": "EX1",
            "source_text": "hello world",
            "gloss": "1SG go",
            "translation": "I go",
            "notes": "test note",
        }
        text = TextFormatter.format_entry(entry)
        assert "test note" in text

    def test_format_with_chinese(self):
        entry = {
            "id": 1,
            "example_id": "EX1",
            "source_text": "hello world",
            "gloss": "1SG go",
            "translation": "I go",
            "notes": "",
            "source_text_cn": "测试",
            "gloss_cn": "",
            "translation_cn": "",
        }
        text = TextFormatter.format_entry(entry, include_chinese=True)
        assert "测试" in text


class TestFormatEntries:
    """Test multiple entries formatting."""

    def test_format_multiple(self):
        entries = [
            {"id": 1, "example_id": "1", "source_text": "a b",
             "gloss": "x y", "translation": "t1", "notes": ""},
            {"id": 2, "example_id": "2", "source_text": "c d",
             "gloss": "z w", "translation": "t2", "notes": ""},
        ]
        text = TextFormatter.format_entries(entries)
        assert "(1)" in text
        assert "(2)" in text


class TestWordExporter:
    """Test Word document export."""

    def test_export_creates_file(self, tmp_path):
        entries = [
            {
                "example_id": "EX1",
                "source_text": "hello world",
                "gloss": "1SG go",
                "translation": "I go",
                "notes": "",
            }
        ]
        output = str(tmp_path / "test.docx")
        exporter = WordExporter()
        result = exporter.export(entries, output)
        assert result is True
        assert os.path.exists(output)

    def test_export_empty_entries(self, tmp_path):
        output = str(tmp_path / "empty.docx")
        exporter = WordExporter()
        result = exporter.export([], output)
        assert result is True

    def test_export_single_word_entry(self, tmp_path):
        entries = [
            {
                "example_id": "W1",
                "source_text": "hello",
                "gloss": "greeting",
                "translation": "你好",
                "notes": "",
            }
        ]
        output = str(tmp_path / "word.docx")
        exporter = WordExporter()
        result = exporter.export(entries, output)
        assert result is True

    def test_export_with_chinese_fields(self, tmp_path):
        entries = [
            {
                "example_id": "EX1",
                "source_text": "hello world",
                "gloss": "1SG go",
                "translation": "I go",
                "notes": "",
                "source_text_cn": "测试 文本",
                "gloss_cn": "注释1 注释2",
                "translation_cn": "我去",
            }
        ]
        output = str(tmp_path / "chinese.docx")
        exporter = WordExporter()
        result = exporter.export(entries, output, include_chinese=True)
        assert result is True

    def test_export_with_font_config(self, tmp_path):
        entries = [
            {
                "example_id": "EX1",
                "source_text": "a b c",
                "gloss": "x y z",
                "translation": "test",
                "notes": "",
            }
        ]
        output = str(tmp_path / "fonts.docx")
        exporter = WordExporter()
        font_config = {
            "source_text": "Arial",
            "source_text_size": 14,
            "gloss": "Arial",
            "gloss_size": 12,
        }
        result = exporter.export(entries, output, font_config=font_config)
        assert result is True

    def test_export_long_sentence_auto_linebreak(self, tmp_path):
        # Test that long sentences with many words don't crash
        words = " ".join([f"word{i}" for i in range(20)])
        glosses = " ".join([f"GLOSS{i}" for i in range(20)])
        entries = [
            {
                "example_id": "LONG",
                "source_text": words,
                "gloss": glosses,
                "translation": "long sentence test",
                "notes": "",
            }
        ]
        output = str(tmp_path / "long.docx")
        exporter = WordExporter()
        result = exporter.export(entries, output)
        assert result is True
