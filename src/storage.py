"""
SQLite storage for SimpleContext.
Single backend, no abstractions.
"""

import os
import sqlite3
from pathlib import Path


class SimpleStorage:
    """Dead-simple SQLite storage."""

    def __init__(self, db_path: str = ".simplecontext.db"):
        self.db_path = db_path

        # Create database with secure permissions (owner-only read/write)
        is_new_db = not Path(db_path).exists()

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Dict-like rows

        # Set secure file permissions (0o600 = rw-------)
        if is_new_db:
            try:
                os.chmod(db_path, 0o600)
            except (OSError, AttributeError):
                pass  # Windows doesn't support chmod, that's okay

        # Enable Write-Ahead Logging for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")

        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT,
                created_at REAL,
                importance TEXT DEFAULT 'medium'
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                size INTEGER,
                created_at REAL
            );

            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                error TEXT,
                context TEXT,
                created_at REAL,
                resolved INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp REAL
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            -- Full-text search on memories
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content, tags, content='memories', content_rowid='rowid'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, tags)
                VALUES (new.rowid, new.content, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                UPDATE memories_fts SET content = new.content, tags = new.tags
                WHERE rowid = new.rowid;
            END;

            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.rowid;
            END;
        """)
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.Error:
                pass  # Already closed

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
