"""
Core memory operations for SimpleContext.
Simple, fast, no magic.
"""

import uuid
import time
import json
from typing import List, Dict, Optional
from functools import wraps

# Use absolute import for standalone execution
try:
    from .storage import SimpleStorage
except ImportError:
    from storage import SimpleStorage


def timed(func):
    """Log slow operations (>10ms)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 10:
            print(f"⚠️  {func.__name__} took {elapsed:.1f}ms")
        return result
    return wrapper


class SimpleMemory:
    """Core memory operations."""

    def __init__(self, db_path: str = ".simplecontext.db"):
        self.storage = SimpleStorage(db_path)
        self.db = self.storage.conn

    @timed
    def remember(self, content: str, tags: List[str] = None, importance: str = "medium") -> str:
        """
        Store a memory.

        Args:
            content: What to remember
            tags: Optional categorization tags
            importance: low/medium/high (default: medium)

        Returns:
            Memory ID

        Example:
            >>> mem.remember("Using PostgreSQL for database", tags=["database", "infra"])
        """
        memory_id = str(uuid.uuid4())
        tags_json = json.dumps(tags or [])

        self.db.execute(
            "INSERT INTO memories (id, content, tags, created_at, importance) VALUES (?, ?, ?, ?, ?)",
            (memory_id, content, tags_json, time.time(), importance)
        )
        self.db.commit()

        print(f"✓ Remembered: {content[:50]}{'...' if len(content) > 50 else ''}")
        return memory_id

    @timed
    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search memories with temporal decay.
        Recent memories rank higher than old ones.

        Args:
            query: Search term
            limit: Max results (default: 5)

        Returns:
            List of matching memories, sorted by relevance

        Example:
            >>> mem.recall("database")
            [{'content': 'Using PostgreSQL...', 'age_days': 2, 'tags': ['database']}]
        """
        cursor = self.db.execute("""
            SELECT
                m.*,
                (julianday('now') - julianday(m.created_at, 'unixepoch')) as age_days,
                1.0 / (1.0 + (julianday('now') - julianday(m.created_at, 'unixepoch')) * 0.1) as recency_score
            FROM memories m
            JOIN memories_fts ON m.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY recency_score DESC
            LIMIT ?
        """, (query, limit))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['tags'] = json.loads(result['tags']) if result['tags'] else []
            results.append(result)

        if results:
            print(f"✓ Found {len(results)} memories for '{query}'")
        return results

    @timed
    def forget(self, query: str) -> int:
        """
        Delete memories matching query.

        Args:
            query: Search term

        Returns:
            Number of memories deleted

        Example:
            >>> mem.forget("mysql")
            2  # Deleted 2 memories about mysql
        """
        cursor = self.db.execute(
            "DELETE FROM memories WHERE content LIKE ?",
            (f"%{query}%",)
        )
        self.db.commit()
        count = cursor.rowcount
        print(f"✓ Forgot {count} memories matching '{query}'")
        return count

    @timed
    def store(self, name: str, content: str) -> str:
        """
        Store large artifact by reference.

        Args:
            name: Artifact name (e.g., "config.py")
            content: Full content

        Returns:
            Artifact ID

        Example:
            >>> mem.store("database.sql", "CREATE TABLE users...")
        """
        artifact_id = str(uuid.uuid4())
        size = len(content)

        self.db.execute(
            "INSERT OR REPLACE INTO artifacts (id, name, content, size, created_at) VALUES (?, ?, ?, ?, ?)",
            (artifact_id, name, content, size, time.time())
        )
        self.db.commit()

        print(f"✓ Stored artifact: {name} ({size} bytes)")
        return artifact_id

    @timed
    def retrieve(self, name: str) -> Optional[str]:
        """
        Get artifact content.

        Args:
            name: Artifact name

        Returns:
            Content, or None if not found

        Example:
            >>> mem.retrieve("config.py")
            "DATABASE_URL = ..."
        """
        cursor = self.db.execute(
            "SELECT content FROM artifacts WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        if row:
            print(f"✓ Retrieved artifact: {name}")
            return row['content']
        else:
            print(f"✗ Artifact not found: {name}")
            return None

    def status(self) -> Dict:
        """
        Get system status.

        Returns:
            Dict with counts and current mode
        """
        cursor = self.db.execute("SELECT COUNT(*) as count FROM memories")
        memory_count = cursor.fetchone()['count']

        cursor = self.db.execute("SELECT COUNT(*) as count FROM artifacts")
        artifact_count = cursor.fetchone()['count']

        cursor = self.db.execute("SELECT COUNT(*) as count FROM errors WHERE resolved = 0")
        error_count = cursor.fetchone()['count']

        cursor = self.db.execute("SELECT value FROM config WHERE key = 'current_mode'")
        row = cursor.fetchone()
        current_mode = row['value'] if row else 'coding'

        return {
            'memories': memory_count,
            'artifacts': artifact_count,
            'unresolved_errors': error_count,
            'mode': current_mode,
            'db_path': self.storage.db_path
        }
