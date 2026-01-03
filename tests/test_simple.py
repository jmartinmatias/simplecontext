"""
Core tests for SimpleContext.
100% coverage on critical paths.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add parent to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory import SimpleMemory
from src.errors import ErrorMemory
from src.modes import detect_mode
from src.storage import SimpleStorage


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


def test_remember_recall(temp_db):
    """Test basic remember/recall."""
    mem = SimpleMemory(temp_db)

    # Remember
    mem_id = mem.remember("Using PostgreSQL", tags=["database"])
    assert mem_id

    # Recall
    results = mem.recall("PostgreSQL")
    assert len(results) == 1
    assert results[0]['content'] == "Using PostgreSQL"
    assert "database" in results[0]['tags']


def test_temporal_decay(temp_db):
    """Recent memories rank higher."""
    mem = SimpleMemory(temp_db)

    mem.remember("Old fact", tags=["test"])
    import time
    time.sleep(0.1)
    mem.remember("Recent fact", tags=["test"])

    results = mem.recall("fact")
    assert len(results) == 2
    assert results[0]['content'] == "Recent fact"  # More recent ranks first


def test_forget(temp_db):
    """Test forgetting memories."""
    mem = SimpleMemory(temp_db)

    mem.remember("Use MySQL")
    mem.remember("Use PostgreSQL")

    count = mem.forget("MySQL")
    assert count == 1

    results = mem.recall("MySQL")
    assert len(results) == 0


def test_store_retrieve(temp_db):
    """Test artifact storage."""
    mem = SimpleMemory(temp_db)

    code = "def hello():\n    print('world')"
    mem.store("test.py", code)

    retrieved = mem.retrieve("test.py")
    assert retrieved == code


def test_error_tracking(temp_db):
    """Test error logging."""
    storage = SimpleStorage(temp_db)
    err = ErrorMemory(storage)

    err_id = err.log_error("npm install", "EACCES permission denied")
    assert err_id

    error_list = err.get_recent_errors(limit=10)
    assert len(error_list) == 1
    assert error_list[0]['action'] == "npm install"

    err.resolve_error(err_id)
    error_list = err.get_recent_errors(unresolved_only=True)
    assert len(error_list) == 0


def test_mode_detection():
    """Test automatic mode switching."""
    assert detect_mode("The tests are failing") == "debugging"
    assert detect_mode("Add a login feature") == "coding"
    assert detect_mode("Fix the bug in auth.py") == "debugging"
    assert detect_mode("Refactor the user service") == "coding"


def test_status(temp_db):
    """Test status reporting."""
    mem = SimpleMemory(temp_db)

    mem.remember("Test memory")
    mem.store("test.txt", "content")

    status = mem.status()
    assert status['memories'] == 1
    assert status['artifacts'] == 1
    assert status['mode'] == 'coding'
