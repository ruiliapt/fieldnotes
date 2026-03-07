# Fieldnotes Lite Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor Fieldnotes Lite with test-first approach: build comprehensive pytest suite, then restructure gui.py into ui/ package, secure API keys with keyring, and optimize database performance.

**Architecture:** Test-first refactoring. Phase 1 builds pytest + pytest-qt test suite for all existing modules. Phase 2 restructures the 3400-line gui.py into a `ui/` package with dependency injection. Phase 3 optimizes database, secures API keys, and cleans up the project.

**Tech Stack:** Python 3.11+, PyQt6, pytest, pytest-qt, keyring, SQLite

---

## Phase 1: Test Suite Foundation

### Task 1: Setup pytest infrastructure

**Files:**
- Modify: `pyproject.toml:31-36`
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`
- Delete: `tests/test_basic.py` (replace with proper pytest tests)

**Step 1: Update pyproject.toml dev dependencies**

Add pytest-qt to dev dependencies:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-qt = "^4.4.0"
black = "^23.12.0"
flake8 = "^6.1.0"
pyinstaller = "^6.16.0"
```

**Step 2: Install dependencies**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry install --with dev`

**Step 3: Create tests/__init__.py**

```python
```

**Step 4: Create tests/conftest.py with shared fixtures**

```python
"""Shared test fixtures for Fieldnotes Lite."""
import os
import tempfile
import pytest
from database import CorpusDatabase


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = str(tmp_path / "test_corpus.db")
    db = CorpusDatabase(db_path)
    yield db
    db.close()


@pytest.fixture
def sample_entry():
    """A standard test entry dict."""
    return {
        "example_id": "TEST001",
        "source_text": "na\u02e7 te\u02e5 t\u0255\u02b0i\u02e5 fan\u02e8\u02e9",
        "gloss": "1SG CLF eat rice",
        "translation": "\u6211\u5403\u996d",
        "notes": "\u6d4b\u8bd5\u6570\u636e",
    }


@pytest.fixture
def sample_entries():
    """Multiple test entries for batch operations."""
    return [
        {
            "example_id": "TEST001",
            "source_text": "na\u02e7 te\u02e5 t\u0255\u02b0i\u02e5 fan\u02e8\u02e9",
            "gloss": "1SG CLF eat rice",
            "translation": "\u6211\u5403\u996d",
            "notes": "",
            "entry_type": "sentence",
        },
        {
            "example_id": "TEST002",
            "source_text": "ni\u02e7 k\u02b0\u0264\u02e5 na\u02e7 li\u02e5",
            "gloss": "2SG go where Q",
            "translation": "\u4f60\u53bb\u54ea\u91cc",
            "notes": "",
            "entry_type": "sentence",
        },
        {
            "example_id": "W001",
            "source_text": "fan\u02e8\u02e9",
            "gloss": "rice",
            "translation": "\u7c73\u996d",
            "notes": "",
            "entry_type": "word",
        },
    ]


@pytest.fixture
def populated_db(tmp_db, sample_entries):
    """A database pre-populated with sample entries."""
    for entry in sample_entries:
        tmp_db.insert_entry(**entry)
    return tmp_db
```

**Step 5: Verify pytest discovers the conftest**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest --collect-only tests/conftest.py`
Expected: No errors, fixtures listed

**Step 6: Commit**

```bash
git add pyproject.toml tests/__init__.py tests/conftest.py
git commit -m "test: setup pytest infrastructure with shared fixtures"
```

---

### Task 2: Database CRUD tests

**Files:**
- Create: `tests/test_database.py`

**Step 1: Write failing tests for database CRUD**

```python
"""Tests for database.py - CRUD operations, search, migrations."""
import pytest
from database import CorpusDatabase, SCHEMA_VERSION


class TestDatabaseCRUD:
    """Test basic Create, Read, Update, Delete operations."""

    def test_insert_entry_returns_id(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_get_entry_returns_inserted_data(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        entry = tmp_db.get_entry(entry_id)
        assert entry is not None
        assert entry["example_id"] == "TEST001"
        assert entry["source_text"] == sample_entry["source_text"]
        assert entry["gloss"] == "1SG CLF eat rice"
        assert entry["translation"] == sample_entry["translation"]

    def test_get_entry_nonexistent_returns_none(self, tmp_db):
        assert tmp_db.get_entry(9999) is None

    def test_update_entry_modifies_data(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        success = tmp_db.update_entry(
            entry_id=entry_id,
            example_id="TEST001",
            source_text="updated text",
            gloss="updated gloss",
            translation="updated translation",
        )
        assert success is True
        entry = tmp_db.get_entry(entry_id)
        assert entry["source_text"] == "updated text"

    def test_update_nonexistent_returns_false(self, tmp_db):
        success = tmp_db.update_entry(
            entry_id=9999,
            example_id="X",
            source_text="x",
            gloss="x",
            translation="x",
        )
        assert success is False

    def test_delete_entry_removes_record(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        assert tmp_db.delete_entry(entry_id) is True
        assert tmp_db.get_entry(entry_id) is None

    def test_delete_nonexistent_returns_false(self, tmp_db):
        assert tmp_db.delete_entry(9999) is False

    def test_get_all_entries(self, populated_db):
        entries = populated_db.get_all_entries()
        assert len(entries) == 3

    def test_get_count(self, populated_db):
        assert populated_db.get_count() == 3

    def test_insert_sets_timestamps(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        entry = tmp_db.get_entry(entry_id)
        assert entry["created_at"] is not None
        assert entry["updated_at"] is not None

    def test_update_changes_updated_at(self, tmp_db, sample_entry):
        entry_id = tmp_db.insert_entry(**sample_entry)
        entry_before = tmp_db.get_entry(entry_id)
        import time; time.sleep(0.01)
        tmp_db.update_entry(entry_id=entry_id, example_id="TEST001",
                           source_text="new", gloss="new", translation="new")
        entry_after = tmp_db.get_entry(entry_id)
        assert entry_after["updated_at"] >= entry_before["updated_at"]
```

**Step 2: Run tests to verify they pass**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_database.py -v`
Expected: All PASS (testing existing working code)

**Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test: add database CRUD tests"
```

---

### Task 3: Database search, tags, and type-filtering tests

**Files:**
- Modify: `tests/test_database.py` (append)

**Step 1: Add search and filter tests**

```python
class TestDatabaseSearch:
    """Test search and filtering functionality."""

    def test_search_by_source_text(self, populated_db):
        results = populated_db.search_entries("source_text", "fan")
        assert len(results) >= 1

    def test_search_by_gloss(self, populated_db):
        results = populated_db.search_entries("gloss", "eat")
        assert len(results) == 1

    def test_search_all_fields(self, populated_db):
        results = populated_db.search_entries("all", "rice")
        assert len(results) >= 1

    def test_search_no_results(self, populated_db):
        results = populated_db.search_entries("source_text", "zzzznotfound")
        assert len(results) == 0

    def test_search_invalid_field_returns_empty(self, populated_db):
        results = populated_db.search_entries("invalid_field", "test")
        assert results == []

    def test_search_by_entry_type(self, populated_db):
        results = populated_db.search_entries("all", "", entry_type="word")
        # All entries match empty string, filtered by type
        word_results = populated_db.get_entries_by_type("word")
        assert len(word_results) == 1
        assert word_results[0]["entry_type"] == "word"

    def test_get_entries_by_type(self, populated_db):
        sentences = populated_db.get_entries_by_type("sentence")
        assert len(sentences) == 2
        words = populated_db.get_entries_by_type("word")
        assert len(words) == 1


class TestDatabaseTags:
    """Test tag-related operations."""

    def test_insert_with_tags(self, tmp_db):
        entry_id = tmp_db.insert_entry(
            example_id="T1", source_text="x", gloss="x",
            translation="x", tags="\u5df2\u5ba1\u6838,\u6d4b\u8bd5"
        )
        entry = tmp_db.get_entry(entry_id)
        assert "\u5df2\u5ba1\u6838" in entry["tags"]

    def test_get_all_tags(self, tmp_db):
        tmp_db.insert_entry(example_id="T1", source_text="a", gloss="a",
                           translation="a", tags="\u6807\u7b7e1,\u6807\u7b7e2")
        tmp_db.insert_entry(example_id="T2", source_text="b", gloss="b",
                           translation="b", tags="\u6807\u7b7e2,\u6807\u7b7e3")
        tags = tmp_db.get_all_tags()
        assert "\u6807\u7b7e1" in tags
        assert "\u6807\u7b7e2" in tags
        assert "\u6807\u7b7e3" in tags

    def test_batch_update_tags_add(self, tmp_db):
        id1 = tmp_db.insert_entry(example_id="T1", source_text="a",
                                  gloss="a", translation="a", tags="")
        updated = tmp_db.batch_update_tags([id1], add_tags=["\u65b0\u6807\u7b7e"])
        assert updated == 1
        entry = tmp_db.get_entry(id1)
        assert "\u65b0\u6807\u7b7e" in entry["tags"]

    def test_batch_update_tags_remove(self, tmp_db):
        id1 = tmp_db.insert_entry(example_id="T1", source_text="a",
                                  gloss="a", translation="a", tags="\u5220\u6389,\u4fdd\u7559")
        tmp_db.batch_update_tags([id1], remove_tags=["\u5220\u6389"])
        entry = tmp_db.get_entry(id1)
        assert "\u5220\u6389" not in entry["tags"]
        assert "\u4fdd\u7559" in entry["tags"]

    def test_get_tag_distribution(self, tmp_db):
        tmp_db.insert_entry(example_id="T1", source_text="a", gloss="a",
                           translation="a", tags="A,B")
        tmp_db.insert_entry(example_id="T2", source_text="b", gloss="b",
                           translation="b", tags="A")
        dist = tmp_db.get_tag_distribution()
        tag_dict = dict(dist)
        assert tag_dict["A"] == 2
        assert tag_dict["B"] == 1

    def test_search_with_tag_filter(self, tmp_db):
        tmp_db.insert_entry(example_id="T1", source_text="hello", gloss="x",
                           translation="x", tags="\u6807\u8bb0")
        tmp_db.insert_entry(example_id="T2", source_text="hello", gloss="x",
                           translation="x", tags="\u5176\u4ed6")
        results = tmp_db.search_entries("source_text", "hello", tags=["\u6807\u8bb0"])
        assert len(results) == 1
```

**Step 2: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_database.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test: add database search, tags, and type-filtering tests"
```

---

### Task 4: Database groups, stats, duplicates, and backup tests

**Files:**
- Modify: `tests/test_database.py` (append)

**Step 1: Add group, stats, and utility tests**

```python
class TestDatabaseGroups:
    """Test discourse/dialogue group operations."""

    def test_get_next_group_id_discourse(self, tmp_db):
        gid = tmp_db.get_next_group_id("discourse")
        assert gid == "DSC001"

    def test_get_next_group_id_dialogue(self, tmp_db):
        gid = tmp_db.get_next_group_id("dialogue")
        assert gid == "DLG001"

    def test_get_next_group_id_increments(self, tmp_db):
        tmp_db.insert_entry(example_id="D1", source_text="a", gloss="a",
                           translation="a", entry_type="discourse",
                           group_id="DSC001", group_name="Test")
        gid = tmp_db.get_next_group_id("discourse")
        assert gid == "DSC002"

    def test_get_groups_by_type(self, tmp_db):
        tmp_db.insert_entry(example_id="D1", source_text="a", gloss="a",
                           translation="a", entry_type="discourse",
                           group_id="DSC001", group_name="Story1")
        tmp_db.insert_entry(example_id="D2", source_text="b", gloss="b",
                           translation="b", entry_type="discourse",
                           group_id="DSC001", group_name="Story1")
        groups = tmp_db.get_groups_by_type("discourse")
        assert len(groups) == 1
        assert groups[0]["count"] == 2

    def test_get_entries_by_group(self, tmp_db):
        tmp_db.insert_entry(example_id="D1", source_text="a", gloss="a",
                           translation="a", entry_type="discourse",
                           group_id="DSC001", group_name="S1")
        tmp_db.insert_entry(example_id="D2", source_text="b", gloss="b",
                           translation="b", entry_type="discourse",
                           group_id="DSC001", group_name="S1")
        entries = tmp_db.get_entries_by_group("DSC001")
        assert len(entries) == 2

    def test_delete_group(self, tmp_db):
        tmp_db.insert_entry(example_id="D1", source_text="a", gloss="a",
                           translation="a", entry_type="discourse",
                           group_id="DSC001", group_name="S1")
        assert tmp_db.delete_group("DSC001") is True
        entries = tmp_db.get_entries_by_group("DSC001")
        assert len(entries) == 0

    def test_rename_group(self, tmp_db):
        tmp_db.insert_entry(example_id="D1", source_text="a", gloss="a",
                           translation="a", entry_type="discourse",
                           group_id="DSC001", group_name="Old")
        assert tmp_db.rename_group("DSC001", "New") is True
        entries = tmp_db.get_entries_by_group("DSC001")
        assert entries[0]["group_name"] == "New"


class TestDatabaseStats:
    """Test statistics and analytics."""

    def test_get_stats(self, populated_db):
        stats = populated_db.get_stats()
        assert stats["total"] == 3
        assert stats["by_type"]["sentence"] == 2
        assert stats["by_type"]["word"] == 1
        assert "today_count" in stats
        assert "week_count" in stats

    def test_get_word_frequencies(self, populated_db):
        freqs = populated_db.get_word_frequencies(limit=5)
        assert isinstance(freqs, list)
        # Each item is (word, count) tuple
        if freqs:
            assert len(freqs[0]) == 2

    def test_example_id_exists(self, populated_db):
        assert populated_db.example_id_exists("TEST001") is True
        assert populated_db.example_id_exists("NOTEXIST") is False

    def test_example_id_exists_with_exclude(self, populated_db):
        entry = populated_db.get_all_entries()[0]
        # Should return False when excluding the entry's own ID
        assert populated_db.example_id_exists(
            entry["example_id"], exclude_id=entry["id"]
        ) is False


class TestDatabaseDuplicates:
    """Test duplicate detection."""

    def test_find_exact_duplicates(self, tmp_db):
        tmp_db.insert_entry(example_id="A", source_text="hello world",
                           gloss="x", translation="x")
        tmp_db.insert_entry(example_id="B", source_text="hello world",
                           gloss="y", translation="y")
        tmp_db.insert_entry(example_id="C", source_text="different",
                           gloss="z", translation="z")
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert len(dupes) == 1
        assert len(dupes[0]) == 2

    def test_find_no_duplicates(self, tmp_db):
        tmp_db.insert_entry(example_id="A", source_text="unique1",
                           gloss="x", translation="x")
        tmp_db.insert_entry(example_id="B", source_text="unique2",
                           gloss="y", translation="y")
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert len(dupes) == 0

    def test_find_fuzzy_duplicates(self, tmp_db):
        tmp_db.insert_entry(example_id="A", source_text="hello world",
                           gloss="x", translation="x")
        tmp_db.insert_entry(example_id="B", source_text="hello worlds",
                           gloss="y", translation="y")
        dupes = tmp_db.find_duplicates(threshold=0.8)
        assert len(dupes) == 1


class TestDatabaseBackupAndIntegrity:
    """Test backup and integrity check."""

    def test_create_backup(self, tmp_db, sample_entry):
        tmp_db.insert_entry(**sample_entry)
        backup_path = tmp_db.create_backup()
        assert os.path.exists(backup_path)
        # Clean up
        os.remove(backup_path)

    def test_check_integrity(self, tmp_db):
        is_ok, msg = tmp_db.check_integrity()
        assert is_ok is True
        assert "\u901a\u8fc7" in msg


class TestDatabaseMigration:
    """Test schema versioning and migration."""

    def test_schema_version_is_current(self, tmp_db):
        version = tmp_db._get_schema_version()
        assert version == SCHEMA_VERSION

    def test_new_db_has_all_columns(self, tmp_db):
        tmp_db.cursor.execute("PRAGMA table_info(corpus)")
        columns = [row[1] for row in tmp_db.cursor.fetchall()]
        expected = [
            "id", "example_id", "source_text", "gloss", "translation",
            "notes", "source_text_cn", "gloss_cn", "translation_cn",
            "entry_type", "group_id", "group_name", "speaker",
            "turn_number", "created_at", "updated_at", "tags",
        ]
        for col in expected:
            assert col in columns, f"Missing column: {col}"

    def test_import_from_list(self, tmp_db, sample_entries):
        count = tmp_db.import_from_list(sample_entries)
        assert count == len(sample_entries)
        assert tmp_db.get_count() == len(sample_entries)
```

**Step 2: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_database.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test: add database groups, stats, duplicates, backup, and migration tests"
```

---

### Task 5: Exporter tests (TextFormatter + WordExporter)

**Files:**
- Create: `tests/test_exporter.py`

**Step 1: Write exporter tests**

```python
"""Tests for exporter.py - TextFormatter and WordExporter."""
import os
import pytest
from exporter import TextFormatter, WordExporter


class TestCalculateDisplayWidth:
    """Test character width calculation for alignment."""

    def test_ascii_characters(self):
        assert TextFormatter.calculate_display_width("hello") == 5

    def test_chinese_characters(self):
        assert TextFormatter.calculate_display_width("\u4f60\u597d") == 4  # 2 chars * 2 width

    def test_mixed_ascii_and_chinese(self):
        width = TextFormatter.calculate_display_width("hi\u4f60")
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
            "source_text": "hello",
            "gloss": "1SG",
            "translation": "I",
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
            "source_text_cn": "\u6d4b\u8bd5",
            "gloss_cn": "",
            "translation_cn": "",
        }
        text = TextFormatter.format_entry(entry, include_chinese=True)
        assert "\u6d4b\u8bd5" in text


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
                "translation": "\u4f60\u597d",
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
                "source_text_cn": "\u6d4b\u8bd5 \u6587\u672c",
                "gloss_cn": "\u6ce8\u91ca1 \u6ce8\u91ca2",
                "translation_cn": "\u6211\u53bb",
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
```

**Step 2: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_exporter.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_exporter.py
git commit -m "test: add TextFormatter and WordExporter tests"
```

---

### Task 6: AI backend tests

**Files:**
- Create: `tests/test_ai_backend.py`

**Step 1: Write AI backend tests (mocking external APIs)**

```python
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
        assert "\u6ca1\u6709\u53ef\u7528" in resp.error

    def test_reload_config(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        manager = AIManager()
        # Should not raise
        manager.reload_config()
```

**Step 2: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_ai_backend.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_ai_backend.py
git commit -m "test: add AI backend tests with mocked providers"
```

---

### Task 7: AI prompts tests

**Files:**
- Create: `tests/test_ai_prompts.py`

**Step 1: Write prompt construction tests**

```python
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
        assert "\u4f8b1:" in result
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
            "source_text_cn": "\u6d4b\u8bd5",
        }]
        result = _format_context_entries(entries)
        assert "\u6d4b\u8bd5" in result


class TestBuildGlossPrompt:
    """Test gloss prompt construction."""

    def test_returns_system_and_user_prompts(self):
        sys_p, usr_p = build_gloss_prompt("hello world", [])
        assert isinstance(sys_p, str)
        assert isinstance(usr_p, str)

    def test_system_prompt_contains_rules(self):
        sys_p, _ = build_gloss_prompt("test", [])
        assert "Leipzig" in sys_p or "\u83b1\u6bd4\u9521" in sys_p
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
        _, usr_p = build_gloss_prompt("test", [], source_text_cn="\u6d4b\u8bd5")
        assert "\u6d4b\u8bd5" in usr_p


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
        assert "\u7ffb\u8bd1" in sys_p


class TestLeipzigAbbreviations:
    """Test abbreviation reference."""

    def test_contains_common_abbreviations(self):
        for abbr in ["1", "SG", "PL", "NOM", "ACC", "PST", "NEG"]:
            assert abbr in LEIPZIG_ABBREVIATIONS
```

**Step 2: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_ai_prompts.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_ai_prompts.py
git commit -m "test: add AI prompts tests"
```

---

### Task 8: Theme and Logger tests

**Files:**
- Create: `tests/test_theme.py`
- Create: `tests/test_logger.py`

**Step 1: Write theme tests**

```python
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

    def test_get_highlight_color(self):
        tm = ThemeManager("light")
        color = tm.get_highlight_color()
        assert color.isValid()
```

**Step 2: Write logger tests**

```python
"""Tests for logger.py - logging configuration."""
import os
import glob as glob_mod
import pytest
from logger import setup_logger, _cleanup_old_logs


class TestSetupLogger:
    """Test logger initialization."""

    def test_setup_returns_logger(self):
        logger = setup_logger()
        assert logger is not None
        assert logger.name == "fieldnote"

    def test_logger_has_handlers(self):
        logger = setup_logger()
        assert len(logger.handlers) >= 1

    def test_logger_level_is_debug(self):
        import logging
        logger = setup_logger()
        assert logger.level == logging.DEBUG


class TestCleanupOldLogs:
    """Test log cleanup."""

    def test_cleanup_removes_old_files(self, tmp_path):
        import time
        # Create a fake old log file
        old_log = tmp_path / "fieldnote_2020-01-01.log"
        old_log.write_text("old log content")
        # Set modification time to 60 days ago
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(str(old_log), (old_time, old_time))

        _cleanup_old_logs(str(tmp_path), max_days=30)
        assert not old_log.exists()

    def test_cleanup_keeps_recent_files(self, tmp_path):
        recent_log = tmp_path / "fieldnote_2026-03-07.log"
        recent_log.write_text("recent log content")

        _cleanup_old_logs(str(tmp_path), max_days=30)
        assert recent_log.exists()
```

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_theme.py tests/test_logger.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/test_theme.py tests/test_logger.py
git commit -m "test: add theme and logger tests"
```

---

### Task 9: GUI widget tests with pytest-qt

**Files:**
- Create: `tests/test_gui/__init__.py`
- Create: `tests/test_gui/conftest.py`
- Create: `tests/test_gui/test_widgets.py`

**Step 1: Create GUI test infrastructure**

```python
# tests/test_gui/__init__.py
```

```python
# tests/test_gui/conftest.py
"""GUI test fixtures using pytest-qt."""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
```

**Step 2: Write widget tests**

```python
# tests/test_gui/test_widgets.py
"""Tests for GUI widgets - IPAToolbarWidget, TagSelectorWidget, EntryTabWidget."""
import pytest
from PyQt6.QtCore import Qt

# Skip all tests if no display is available (CI)
pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY") and sys.platform != "darwin" and sys.platform != "win32",
    reason="No display available"
)

import os
import sys
from gui import IPAToolbarWidget, TagSelectorWidget


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
        assert widget.content_widget.isVisible() is True
        assert "\u25bc" in widget.toggle_btn.text()

    def test_toggle_collapses(self, qtbot):
        widget = IPAToolbarWidget()
        qtbot.addWidget(widget)
        widget._toggle()  # expand
        widget._toggle()  # collapse
        assert widget.content_widget.isVisible() is False

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
```

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_gui/ -v`
Expected: All PASS (or skipped if no display)

**Step 4: Commit**

```bash
git add tests/test_gui/
git commit -m "test: add GUI widget tests with pytest-qt"
```

---

### Task 10: Run full test suite and measure coverage

**Step 1: Run all tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v --tb=short`
Expected: All PASS

**Step 2: Remove old test scripts**

Delete the old non-pytest test files:

```bash
rm tests/test_basic.py
# Keep test_formatter.py, test_word_export.py etc. as reference but rename
# Actually just remove them - they are demonstration scripts
rm -f tests/test_formatter.py tests/test_word_export.py tests/test_long_sentence.py tests/test_long_multiline.py 2>/dev/null
```

**Step 3: Commit**

```bash
git add -A tests/
git commit -m "test: remove legacy test scripts, full pytest suite complete"
```

---

## Phase 2: GUI Refactoring

### Task 11: Create ui/ package skeleton

**Files:**
- Create: `ui/__init__.py`
- Create: `ui/main_window.py`
- Create: `ui/tab_manager.py`
- Create: `ui/entry_tab_widget.py`
- Create: `ui/data_operations.py`
- Create: `ui/search_manager.py`
- Create: `ui/export_manager.py`
- Create: `ui/ai_coordinator.py`
- Create: `ui/dialogs.py`
- Create: `ui/widgets.py`

**Step 1: Create the ui/ package with empty modules**

Create each file with a module docstring only. This step is purely structural.

```python
# ui/__init__.py
"""UI package - refactored from monolithic gui.py"""
```

Each other file:
```python
# ui/<module>.py
"""<Module description>"""
```

**Step 2: Commit**

```bash
git add ui/
git commit -m "refactor: create ui/ package skeleton"
```

---

### Task 12: Extract widgets (IPAToolbarWidget, TagSelectorWidget)

**Files:**
- Modify: `ui/widgets.py`
- Modify: `gui.py` (remove widget classes, import from ui.widgets)
- Modify: `tests/test_gui/test_widgets.py` (update imports)

**Step 1: Move IPAToolbarWidget and TagSelectorWidget to ui/widgets.py**

Copy the `IPAToolbarWidget` (lines 58-116) and `TagSelectorWidget` (lines 119-200) classes from gui.py into ui/widgets.py, along with the `_get_monospace_font` helper and necessary imports.

**Step 2: Update gui.py to import from ui.widgets**

Replace the class definitions in gui.py with:
```python
from ui.widgets import IPAToolbarWidget, TagSelectorWidget, _get_monospace_font
```

**Step 3: Update test imports**

```python
# tests/test_gui/test_widgets.py
from ui.widgets import IPAToolbarWidget, TagSelectorWidget
```

**Step 4: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add ui/widgets.py gui.py tests/test_gui/test_widgets.py
git commit -m "refactor: extract IPAToolbarWidget and TagSelectorWidget to ui/widgets"
```

---

### Task 13: Extract EntryTabWidget

**Files:**
- Modify: `ui/entry_tab_widget.py`
- Modify: `gui.py` (remove EntryTabWidget, import from ui)

**Step 1: Move EntryTabWidget to ui/entry_tab_widget.py**

Copy EntryTabWidget class (gui.py lines 203-481) to ui/entry_tab_widget.py. Import widgets from ui.widgets.

**Step 2: Update gui.py imports**

```python
from ui.entry_tab_widget import EntryTabWidget
```

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/entry_tab_widget.py gui.py
git commit -m "refactor: extract EntryTabWidget to ui/entry_tab_widget"
```

---

### Task 14: Extract DataOperations (CRUD logic)

**Files:**
- Modify: `ui/data_operations.py`
- Modify: `gui.py` (delegate CRUD methods)

**Step 1: Create DataOperations class**

Extract add_entry, update_entry, delete_entry, clear_inputs, import_data, load_entry_to_form from MainWindow into ui/data_operations.py. This class takes a reference to the database and the current tab widget.

**Step 2: Update MainWindow to delegate to DataOperations**

MainWindow methods become thin wrappers that call self.data_ops.method().

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/data_operations.py gui.py
git commit -m "refactor: extract DataOperations from MainWindow"
```

---

### Task 15: Extract SearchManager

**Files:**
- Modify: `ui/search_manager.py`
- Modify: `gui.py`

**Step 1: Create SearchManager class**

Extract create_search_tab, perform_search, and related methods from MainWindow.

**Step 2: Update MainWindow to use SearchManager**

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/search_manager.py gui.py
git commit -m "refactor: extract SearchManager from MainWindow"
```

---

### Task 16: Extract ExportManager

**Files:**
- Modify: `ui/export_manager.py`
- Modify: `gui.py`

**Step 1: Create ExportManager class**

Extract all export methods: export_to_word, quick_export_word, quick_export_all_word, quick_export_text, quick_export_all_text, export_to_csv, export_to_json, create_export_tab.

**Step 2: Update MainWindow**

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/export_manager.py gui.py
git commit -m "refactor: extract ExportManager from MainWindow"
```

---

### Task 17: Extract AICoordinator

**Files:**
- Modify: `ui/ai_coordinator.py`
- Modify: `gui.py`

**Step 1: Create AICoordinator class**

Extract ai_auto_gloss, ai_auto_translate, _on_ai_gloss_result, _on_ai_translate_result, and AI-related methods.

**Step 2: Update MainWindow**

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/ai_coordinator.py gui.py
git commit -m "refactor: extract AICoordinator from MainWindow"
```

---

### Task 18: Extract Dialogs

**Files:**
- Modify: `ui/dialogs.py`
- Modify: `gui.py`

**Step 1: Create dialog classes**

Extract about dialog, help dialog, backup dialog, font config dialog, and other popup dialogs from MainWindow.

**Step 2: Update MainWindow**

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add ui/dialogs.py gui.py
git commit -m "refactor: extract dialog classes to ui/dialogs"
```

---

### Task 19: Finalize MainWindow with dependency injection

**Files:**
- Modify: `ui/main_window.py`
- Modify: `ui/__init__.py`
- Modify: `main.py`
- Delete: `gui.py` (or keep as thin re-export for backwards compat)

**Step 1: Move the slim MainWindow to ui/main_window.py**

The MainWindow should now only handle:
- Window setup (title, geometry)
- Menu bar creation
- Tab container assembly
- Dependency wiring

Constructor accepts injected dependencies:
```python
class MainWindow(QMainWindow):
    def __init__(self, db: CorpusDatabase, exporter: WordExporter,
                 ai_manager: AIManager, theme: ThemeManager):
```

**Step 2: Update ui/__init__.py**

```python
from ui.main_window import MainWindow
```

**Step 3: Update main.py**

```python
from ui import MainWindow
```

Keep gui.py as a re-export for any external references:
```python
# gui.py - backwards compatibility
from ui import MainWindow
```

**Step 4: Run full test suite**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add ui/ gui.py main.py
git commit -m "refactor: finalize ui/ package with dependency injection in MainWindow"
```

---

## Phase 3: Module Optimizations

### Task 20: Secure API keys with keyring

**Files:**
- Modify: `pyproject.toml` (add keyring dependency)
- Modify: `ai_backend.py`
- Create: `tests/test_ai_keyring.py`

**Step 1: Add keyring to dependencies**

```toml
[tool.poetry.dependencies]
keyring = "^25.0.0"
```

Run: `poetry install`

**Step 2: Write failing test**

```python
# tests/test_ai_keyring.py
"""Tests for API key secure storage with keyring."""
import pytest
from unittest.mock import patch, MagicMock


class TestSecureKeyStorage:
    """Test keyring-based API key storage."""

    @patch("ai_backend.keyring")
    def test_save_stores_key_in_keyring(self, mock_keyring, tmp_path, monkeypatch):
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        from ai_backend import AIConfig
        config = AIConfig(claude_api_key="sk-test-key")
        config.save()
        mock_keyring.set_password.assert_called()

    @patch("ai_backend.keyring")
    def test_save_does_not_write_key_to_json(self, mock_keyring, tmp_path, monkeypatch):
        import json
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        from ai_backend import AIConfig
        config = AIConfig(claude_api_key="sk-secret")
        config.save()
        with open(config_path) as f:
            saved = json.load(f)
        assert "sk-secret" not in json.dumps(saved)

    @patch("ai_backend.keyring")
    def test_load_reads_key_from_keyring(self, mock_keyring, tmp_path, monkeypatch):
        import json
        config_path = str(tmp_path / "ai_config.json")
        monkeypatch.setattr("ai_backend.AI_CONFIG_PATH", config_path)
        with open(config_path, "w") as f:
            json.dump({"provider": "claude"}, f)
        mock_keyring.get_password.return_value = "sk-from-keyring"
        from ai_backend import AIConfig
        config = AIConfig.load()
        assert config.claude_api_key == "sk-from-keyring"
```

**Step 3: Implement keyring storage in AIConfig**

Modify `AIConfig.save()` and `AIConfig.load()`:
- `save()`: Store API keys via `keyring.set_password("fieldnote", "claude_api_key", value)`, write non-sensitive fields to JSON, set placeholder in JSON for key fields
- `load()`: Read JSON, then retrieve API keys from keyring via `keyring.get_password()`, fall back to JSON values for migration

**Step 4: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_ai_keyring.py tests/test_ai_backend.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add pyproject.toml ai_backend.py tests/test_ai_keyring.py
git commit -m "feat: secure API keys with keyring, auto-migrate from plaintext"
```

---

### Task 21: Database performance optimization

**Files:**
- Modify: `database.py`
- Modify: `tests/test_database.py` (add new tests)

**Step 1: Write tests for new index and optimized duplicates**

```python
class TestDatabasePerformance:
    """Test database performance optimizations."""

    def test_indexes_exist_after_migration(self, tmp_db):
        tmp_db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row[0] for row in tmp_db.cursor.fetchall()]
        assert "idx_corpus_source_text" in indexes
        assert "idx_corpus_entry_type" in indexes
        assert "idx_corpus_tags" in indexes

    def test_find_duplicates_exact_uses_sql(self, tmp_db):
        # Insert 100 entries, 50 pairs of duplicates
        for i in range(100):
            tmp_db.insert_entry(
                example_id=f"E{i}", source_text=f"text{i % 50}",
                gloss="g", translation="t"
            )
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert len(dupes) == 50

    def test_transaction_rollback_on_error(self, tmp_db):
        count_before = tmp_db.get_count()
        # batch_update_tags with non-existent IDs should not corrupt
        tmp_db.batch_update_tags([9999], add_tags=["test"])
        count_after = tmp_db.get_count()
        assert count_before == count_after
```

**Step 2: Implement optimizations**

In `database.py`:

1. Bump `SCHEMA_VERSION` to 4
2. In `_run_migrations()`, add Migration 4:
```python
# Migration 4: Add indexes for performance
if current < 4:
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_source_text ON corpus(source_text)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_entry_type ON corpus(entry_type)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_tags ON corpus(tags)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_gloss ON corpus(gloss)")
    self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_created_at ON corpus(created_at)")
```

3. Optimize `find_duplicates()` for exact match:
```python
if threshold >= 1.0:
    self.cursor.execute("""
        SELECT source_text FROM corpus
        WHERE source_text IS NOT NULL AND source_text != ''
        GROUP BY LOWER(TRIM(source_text))
        HAVING COUNT(*) > 1
    """)
    duplicate_texts = [row[0] for row in self.cursor.fetchall()]
    result = []
    for text in duplicate_texts:
        self.cursor.execute(
            "SELECT * FROM corpus WHERE LOWER(TRIM(source_text)) = ?",
            (text.strip().lower(),)
        )
        group = [dict(r) for r in self.cursor.fetchall()]
        if len(group) > 1:
            result.append(group)
    return result
```

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_database.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "perf: add database indexes and optimize find_duplicates with SQL GROUP BY"
```

---

### Task 22: Exporter refactoring - extract constants and split methods

**Files:**
- Modify: `exporter.py`
- Run: `tests/test_exporter.py` (existing tests protect the refactor)

**Step 1: Extract constants to class level**

At the top of `WordExporter`:
```python
class WordExporter:
    # Export constants
    DEFAULT_SOURCE_FONT = "Doulos SIL Compact"
    DEFAULT_SOURCE_SIZE = 12
    DEFAULT_GLOSS_FONT = "Charis SIL Compact"
    DEFAULT_GLOSS_SIZE = 11
    DEFAULT_TRANSLATION_SIZE = 11
    DEFAULT_CHINESE_SIZE = 10
    CELL_MARGIN_DXA = 108  # 0.19cm
    TABLE_WIDTH_PCT = 5000  # 100%
    DEFAULT_ROW_HEIGHT = 300  # twips
```

**Step 2: Split export() into private methods**

Extract from the 400-line export():
- `_init_font_config(font_config)` - parse font configuration
- `_build_table_entry(entry, ...)` - handle table-based multi-word entries
- `_build_paragraph_entry(entry, ...)` - handle paragraph-based single-word entries
- `_setup_table_properties(table)` - set borders, layout, spacing

**Step 3: Run tests**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/test_exporter.py -v`
Expected: All PASS (behavior unchanged)

**Step 4: Commit**

```bash
git add exporter.py
git commit -m "refactor: extract constants and split export() into focused methods"
```

---

### Task 23: Project cleanup

**Files:**
- Delete: stale scripts and test artifacts
- Create: `.editorconfig`

**Step 1: Remove stale files**

```bash
rm -f test_transparent_table_export.docx
rm -f scripts/build_executable_fixed.sh
rm -f scripts/run.bat scripts/run.sh
rm -f scripts/stop.bat scripts/stop.sh
```

**Step 2: Create .editorconfig**

```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

**Step 3: Run full test suite**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: project cleanup - remove stale files, add .editorconfig"
```

---

### Task 24: Final verification

**Step 1: Run complete test suite with verbose output**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run pytest tests/ -v --tb=short`
Expected: All PASS

**Step 2: Verify application launches**

Run: `cd /Users/ruil/Documents/GitHub/fieldnote && poetry run python main.py`
Expected: Application window opens without errors

**Step 3: Verify git status is clean**

Run: `git status`
Expected: Clean working tree

**Step 4: Tag release**

```bash
git tag -a v0.7.0 -m "v0.7.0 - Major refactoring: test suite, ui/ package, keyring security, DB optimization"
```
