"""
Automatic error tracking.
Claude learns from mistakes.
"""

import time
from typing import List, Dict

# Use absolute import for standalone execution
try:
    from .storage import SimpleStorage
except ImportError:
    from storage import SimpleStorage


class ErrorMemory:
    """Track and learn from errors."""

    def __init__(self, storage: SimpleStorage):
        self.db = storage.conn

    def log_error(self, action: str, error: str, context: str = "") -> int:
        """
        Automatically log an error.

        Args:
            action: What was being attempted
            error: The error message
            context: Additional context

        Returns:
            Error ID
        """
        cursor = self.db.execute(
            "INSERT INTO errors (action, error, context, created_at) VALUES (?, ?, ?, ?)",
            (action, error, context, time.time())
        )
        self.db.commit()

        error_id = cursor.lastrowid
        print(f"⚠️  Error logged: {action} → {error[:50]}")
        return error_id

    def resolve_error(self, error_id: int, resolution: str = "") -> bool:
        """
        Mark error as resolved.

        Args:
            error_id: Error to resolve
            resolution: How it was fixed

        Returns:
            True if resolved, False if not found
        """
        cursor = self.db.execute(
            "UPDATE errors SET resolved = 1 WHERE id = ?",
            (error_id,)
        )
        self.db.commit()

        if cursor.rowcount > 0:
            print(f"✓ Error {error_id} resolved: {resolution}")
            return True
        return False

    def get_recent_errors(self, limit: int = 5, unresolved_only: bool = True) -> List[Dict]:
        """
        Get recent errors for context.

        Args:
            limit: Max errors to return
            unresolved_only: Only show unresolved errors

        Returns:
            List of error dicts
        """
        query = """
            SELECT * FROM errors
            WHERE resolved = 0
            ORDER BY created_at DESC
            LIMIT ?
        """ if unresolved_only else """
            SELECT * FROM errors
            ORDER BY created_at DESC
            LIMIT ?
        """

        cursor = self.db.execute(query, (limit,))
        return [dict(row) for row in cursor.fetchall()]
