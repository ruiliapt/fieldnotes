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
        "source_text": "ŋa˧ tə˥ tɕʰi˥ fan˨˩",
        "gloss": "1SG CLF eat rice",
        "translation": "我吃饭",
        "notes": "测试数据",
    }


@pytest.fixture
def sample_entries():
    """Multiple test entries for batch operations."""
    return [
        {
            "example_id": "TEST001",
            "source_text": "ŋa˧ tə˥ tɕʰi˥ fan˨˩",
            "gloss": "1SG CLF eat rice",
            "translation": "我吃饭",
            "notes": "",
            "entry_type": "sentence",
        },
        {
            "example_id": "TEST002",
            "source_text": "ni˧ kʰɤ˥ na˧ li˥",
            "gloss": "2SG go where Q",
            "translation": "你去哪里",
            "notes": "",
            "entry_type": "sentence",
        },
        {
            "example_id": "W001",
            "source_text": "fan˨˩",
            "gloss": "rice",
            "translation": "米饭",
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
