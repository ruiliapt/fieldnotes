"""Comprehensive tests for CorpusDatabase (CRUD, search, tags, groups, stats, duplicates, backup)."""
import os
import time
from datetime import datetime, timezone

import pytest

from database import CorpusDatabase, SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Task 2: CRUD tests
# ---------------------------------------------------------------------------
class TestDatabaseCRUD:
    """Basic create / read / update / delete operations."""

    def test_insert_returns_id(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_get_returns_data(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        entry = tmp_db.get_entry(row_id)
        assert entry is not None
        assert entry["example_id"] == sample_entry["example_id"]
        assert entry["source_text"] == sample_entry["source_text"]
        assert entry["gloss"] == sample_entry["gloss"]
        assert entry["translation"] == sample_entry["translation"]

    def test_get_nonexistent_returns_none(self, tmp_db):
        assert tmp_db.get_entry(99999) is None

    def test_update_modifies_data(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        result = tmp_db.update_entry(
            entry_id=row_id,
            example_id="TEST001",
            source_text="updated text",
            gloss="updated gloss",
            translation="updated translation",
        )
        assert result is True
        entry = tmp_db.get_entry(row_id)
        assert entry["source_text"] == "updated text"

    def test_update_nonexistent_returns_false(self, tmp_db):
        result = tmp_db.update_entry(
            entry_id=99999,
            example_id="X",
            source_text="x",
            gloss="x",
            translation="x",
        )
        assert result is False

    def test_delete_removes_record(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        assert tmp_db.delete_entry(row_id) is True
        assert tmp_db.get_entry(row_id) is None

    def test_delete_nonexistent_returns_false(self, tmp_db):
        assert tmp_db.delete_entry(99999) is False

    def test_get_all_entries(self, populated_db):
        entries = populated_db.get_all_entries()
        assert len(entries) == 3

    def test_get_count(self, populated_db):
        assert populated_db.get_count() == 3

    def test_insert_sets_timestamps(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        entry = tmp_db.get_entry(row_id)
        assert entry["created_at"] is not None
        assert entry["updated_at"] is not None
        # Should be valid ISO format containing today's UTC date
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert today_str in entry["created_at"]

    def test_update_changes_updated_at(self, tmp_db, sample_entry):
        row_id = tmp_db.insert_entry(**sample_entry)
        original = tmp_db.get_entry(row_id)
        original_updated = original["updated_at"]

        # Small delay to guarantee timestamp differs
        time.sleep(0.05)

        tmp_db.update_entry(
            entry_id=row_id,
            example_id="TEST001",
            source_text="changed",
            gloss="g",
            translation="t",
        )
        updated = tmp_db.get_entry(row_id)
        assert updated["updated_at"] >= original_updated


# ---------------------------------------------------------------------------
# Task 3: Search, tags, type-filtering tests
# ---------------------------------------------------------------------------
class TestDatabaseSearch:
    """Search and type-filtering."""

    def test_search_by_source_text(self, populated_db):
        results = populated_db.search_entries("source_text", "fan")
        assert len(results) >= 1
        assert any("fan" in r["source_text"] for r in results)

    def test_search_by_gloss(self, populated_db):
        results = populated_db.search_entries("gloss", "rice")
        assert len(results) >= 1

    def test_search_all_fields(self, populated_db):
        results = populated_db.search_entries("all", "rice")
        assert len(results) >= 1

    def test_search_no_results(self, populated_db):
        results = populated_db.search_entries("source_text", "xyznonexistent")
        assert results == []

    def test_search_invalid_field(self, populated_db):
        results = populated_db.search_entries("invalid_field", "test")
        assert results == []

    def test_get_entries_by_type(self, populated_db):
        words = populated_db.get_entries_by_type("word")
        assert len(words) == 1
        assert words[0]["example_id"] == "W001"

        sentences = populated_db.get_entries_by_type("sentence")
        assert len(sentences) == 2


class TestDatabaseTags:
    """Tag operations."""

    def test_insert_with_tags(self, tmp_db):
        row_id = tmp_db.insert_entry(
            example_id="T001",
            source_text="hello",
            gloss="greeting",
            translation="hi",
            tags="greetings,basic",
        )
        entry = tmp_db.get_entry(row_id)
        assert "greetings" in entry["tags"]
        assert "basic" in entry["tags"]

    def test_get_all_tags(self, tmp_db):
        tmp_db.insert_entry(
            example_id="T1", source_text="a", gloss="a", translation="a",
            tags="alpha,beta",
        )
        tmp_db.insert_entry(
            example_id="T2", source_text="b", gloss="b", translation="b",
            tags="beta,gamma",
        )
        tags = tmp_db.get_all_tags()
        assert "alpha" in tags
        assert "beta" in tags
        assert "gamma" in tags

    def test_batch_update_tags_add(self, tmp_db):
        id1 = tmp_db.insert_entry(
            example_id="T1", source_text="a", gloss="a", translation="a",
        )
        id2 = tmp_db.insert_entry(
            example_id="T2", source_text="b", gloss="b", translation="b",
        )
        updated = tmp_db.batch_update_tags([id1, id2], add_tags=["newtag"])
        assert updated == 2
        entry1 = tmp_db.get_entry(id1)
        assert "newtag" in entry1["tags"]

    def test_batch_update_tags_remove(self, tmp_db):
        id1 = tmp_db.insert_entry(
            example_id="T1", source_text="a", gloss="a", translation="a",
            tags="keep,remove_me",
        )
        updated = tmp_db.batch_update_tags([id1], remove_tags=["remove_me"])
        assert updated == 1
        entry = tmp_db.get_entry(id1)
        assert "remove_me" not in entry["tags"]
        assert "keep" in entry["tags"]

    def test_get_tag_distribution(self, tmp_db):
        tmp_db.insert_entry(
            example_id="T1", source_text="a", gloss="a", translation="a",
            tags="common,rare",
        )
        tmp_db.insert_entry(
            example_id="T2", source_text="b", gloss="b", translation="b",
            tags="common",
        )
        dist = tmp_db.get_tag_distribution()
        dist_dict = dict(dist)
        assert dist_dict["common"] == 2
        assert dist_dict["rare"] == 1

    def test_search_with_tag_filter(self, tmp_db):
        tmp_db.insert_entry(
            example_id="T1", source_text="hello world", gloss="g", translation="t",
            tags="tagged",
        )
        tmp_db.insert_entry(
            example_id="T2", source_text="hello earth", gloss="g", translation="t",
            tags="other",
        )
        results = tmp_db.search_entries("source_text", "hello", tags=["tagged"])
        assert len(results) == 1
        assert results[0]["example_id"] == "T1"


# ---------------------------------------------------------------------------
# Task 4: Groups, stats, duplicates, backup tests
# ---------------------------------------------------------------------------
class TestDatabaseGroups:
    """Group (discourse/dialogue) operations."""

    def test_get_next_group_id_discourse(self, tmp_db):
        gid = tmp_db.get_next_group_id("discourse")
        assert gid == "DSC001"

    def test_get_next_group_id_dialogue(self, tmp_db):
        gid = tmp_db.get_next_group_id("dialogue")
        assert gid == "DLG001"

    def test_get_next_group_id_increments(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="a", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        gid = tmp_db.get_next_group_id("discourse")
        assert gid == "DSC002"

    def test_get_groups_by_type(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="a", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        tmp_db.insert_entry(
            example_id="D2", source_text="b", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        groups = tmp_db.get_groups_by_type("discourse")
        assert len(groups) == 1
        assert groups[0]["group_id"] == "DSC001"
        assert groups[0]["count"] == 2

    def test_get_entries_by_group(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="a", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        tmp_db.insert_entry(
            example_id="D2", source_text="b", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        entries = tmp_db.get_entries_by_group("DSC001")
        assert len(entries) == 2

    def test_delete_group(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="a", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        tmp_db.insert_entry(
            example_id="D2", source_text="b", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="story1",
        )
        assert tmp_db.delete_group("DSC001") is True
        assert tmp_db.get_entries_by_group("DSC001") == []

    def test_rename_group(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="a", gloss="g", translation="t",
            entry_type="discourse", group_id="DSC001", group_name="old_name",
        )
        assert tmp_db.rename_group("DSC001", "new_name") is True
        entries = tmp_db.get_entries_by_group("DSC001")
        assert entries[0]["group_name"] == "new_name"


class TestDatabaseStats:
    """Statistics and word frequency."""

    def test_get_stats(self, populated_db):
        stats = populated_db.get_stats()
        assert stats["total"] == 3
        assert stats["by_type"]["word"] == 1
        assert stats["by_type"]["sentence"] == 2
        assert "today_count" in stats
        assert "week_count" in stats

    def test_get_word_frequencies(self, populated_db):
        freqs = populated_db.get_word_frequencies()
        # There should be word frequency pairs
        assert isinstance(freqs, list)
        assert len(freqs) > 0
        # Each item is a (word, count) tuple
        assert len(freqs[0]) == 2

    def test_example_id_exists(self, populated_db):
        assert populated_db.example_id_exists("TEST001") is True
        assert populated_db.example_id_exists("NONEXIST") is False

    def test_example_id_exists_with_exclude(self, populated_db):
        # Get the id of the TEST001 entry
        entries = populated_db.get_all_entries()
        test001 = next(e for e in entries if e["example_id"] == "TEST001")
        # Excluding itself, TEST001 should not exist
        assert populated_db.example_id_exists("TEST001", exclude_id=test001["id"]) is False


class TestDatabaseDuplicates:
    """Duplicate detection."""

    def test_find_exact_duplicates(self, tmp_db):
        tmp_db.insert_entry(
            example_id="D1", source_text="same text", gloss="g", translation="t",
        )
        tmp_db.insert_entry(
            example_id="D2", source_text="same text", gloss="g2", translation="t2",
        )
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert len(dupes) == 1
        assert len(dupes[0]) == 2

    def test_no_duplicates(self, tmp_db):
        tmp_db.insert_entry(
            example_id="U1", source_text="unique one", gloss="g", translation="t",
        )
        tmp_db.insert_entry(
            example_id="U2", source_text="totally different", gloss="g", translation="t",
        )
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert dupes == []

    def test_fuzzy_duplicates(self, tmp_db):
        tmp_db.insert_entry(
            example_id="F1", source_text="the quick brown fox", gloss="g", translation="t",
        )
        tmp_db.insert_entry(
            example_id="F2", source_text="the quick brown box", gloss="g", translation="t",
        )
        dupes = tmp_db.find_duplicates(threshold=0.8)
        assert len(dupes) >= 1


class TestDatabaseBackupAndIntegrity:
    """Backup and integrity check."""

    def test_create_backup(self, tmp_db, sample_entry):
        tmp_db.insert_entry(**sample_entry)
        backup_path = tmp_db.create_backup()
        assert os.path.exists(backup_path)
        # Backup should be a valid database
        backup_db = CorpusDatabase(backup_path)
        assert backup_db.get_count() == 1
        backup_db.close()

    def test_check_integrity(self, tmp_db):
        is_ok, message = tmp_db.check_integrity()
        assert is_ok is True
        assert "正常" in message or "通过" in message


class TestDatabaseMigration:
    """Schema migration and import."""

    def test_schema_version_is_current(self, tmp_db):
        version = tmp_db._get_schema_version()
        assert version == SCHEMA_VERSION

    def test_new_db_has_all_columns(self, tmp_db):
        tmp_db.cursor.execute("PRAGMA table_info(corpus)")
        columns = [row[1] for row in tmp_db.cursor.fetchall()]
        expected = [
            "id", "example_id", "source_text", "gloss", "translation", "notes",
            "source_text_cn", "gloss_cn", "translation_cn",
            "entry_type", "group_id", "group_name", "speaker", "turn_number",
            "created_at", "updated_at", "tags",
        ]
        for col in expected:
            assert col in columns, f"Missing column: {col}"

    def test_import_from_list(self, tmp_db, sample_entries):
        count = tmp_db.import_from_list(sample_entries)
        assert count == len(sample_entries)
        assert tmp_db.get_count() == len(sample_entries)


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

    def test_schema_version_is_4(self, tmp_db):
        assert tmp_db._get_schema_version() == 4

    def test_find_duplicates_exact_with_many_entries(self, tmp_db):
        # Insert 100 entries, 50 pairs of duplicates
        for i in range(100):
            tmp_db.insert_entry(
                example_id=f"E{i}", source_text=f"text{i % 50}",
                gloss="g", translation="t"
            )
        dupes = tmp_db.find_duplicates(threshold=1.0)
        assert len(dupes) == 50
