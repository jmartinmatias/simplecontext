"""
SimpleContext MCP server.
Connects to Claude via Model Context Protocol.
"""

import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional
from mcp.server import FastMCP

# Add src directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory import SimpleMemory
from errors import ErrorMemory
from modes import detect_mode, get_attention_budget
from storage import SimpleStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize storage (auto-creates DB on first use)
storage = SimpleStorage(".simplecontext.db")
memory = SimpleMemory(".simplecontext.db")
errors = ErrorMemory(storage)

# Create MCP server
app = FastMCP("simplecontext")

# Input validation constants
MAX_CONTENT_LENGTH = 100_000  # 100KB max per memory
MAX_QUERY_LENGTH = 1_000

# Sensitive data patterns
SENSITIVE_PATTERNS = [
    r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"]?[\w@#$%^&*()_+=\-[\]{};:,.<>?/]+',
    r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'"]?[\w\-]+',
    r'(?i)(secret|token|bearer)\s*[:=]\s*[\'"]?[\w\-]+',
    r'(?i)(credentials?|auth)\s*[:=]\s*[\'"]?[\w@#$%^&*()_+=\-[\]{};:,.<>?/]+',
]


def validate_input(content: str, field_name: str = "content", max_length: int = MAX_CONTENT_LENGTH) -> None:
    """
    Validate input parameters.

    Args:
        content: Content to validate
        field_name: Name of field for error messages
        max_length: Maximum allowed length

    Raises:
        ValueError: If validation fails
    """
    if content is None:
        raise ValueError(f"{field_name} cannot be None")

    if not isinstance(content, str):
        raise ValueError(f"{field_name} must be a string, got {type(content).__name__}")

    if not content.strip():
        raise ValueError(f"{field_name} cannot be empty")

    if len(content) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")


def check_sensitive_data(content: str) -> Optional[str]:
    """
    Check if content contains sensitive data patterns.

    Args:
        content: Content to check

    Returns:
        Warning message if sensitive data detected, None otherwise
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, content):
            return "⚠️  WARNING: Content may contain credentials or sensitive data!"
    return None


def get_context_for_claude() -> str:
    """
    Compile context for Claude based on current mode.
    This is called automatically by Claude.
    """
    # Get current mode
    cursor = storage.conn.execute("SELECT value FROM config WHERE key = 'current_mode'")
    row = cursor.fetchone()
    mode = row['value'] if row else 'coding'

    budget = get_attention_budget(mode)

    # Build context sections
    sections = []

    # Recent session (last 10 exchanges)
    cursor = storage.conn.execute(
        "SELECT role, content FROM session ORDER BY timestamp DESC LIMIT 10"
    )
    session_items = [f"{row['role']}: {row['content']}" for row in cursor.fetchall()]
    if session_items:
        sections.append(f"## Recent Session\n" + "\n".join(reversed(session_items)))

    # Memories (top 5 by recency)
    cursor = storage.conn.execute(
        "SELECT content FROM memories ORDER BY created_at DESC LIMIT 5"
    )
    memory_items = [row['content'] for row in cursor.fetchall()]
    if memory_items:
        sections.append(f"## Memories\n" + "\n".join(f"- {m}" for m in memory_items))

    # Unresolved errors (if in debugging mode)
    if mode == "debugging":
        recent_errors = errors.get_recent_errors(limit=5)
        if recent_errors:
            error_lines = [f"- {e['action']}: {e['error']}" for e in recent_errors]
            sections.append(f"## Recent Errors\n" + "\n".join(error_lines))

    # Artifacts (list only, lazy load content)
    cursor = storage.conn.execute("SELECT name FROM artifacts")
    artifact_names = [row['name'] for row in cursor.fetchall()]
    if artifact_names:
        sections.append(f"## Available Artifacts\n" + "\n".join(f"- {name}" for name in artifact_names))

    return "\n\n".join(sections)


# MCP Prompts (for automatic context injection)

@app.prompt()
def get_context() -> str:
    """
    Get current context compiled for Claude.
    Claude can call this to see memories, artifacts, and errors.
    """
    return get_context_for_claude()


# MCP Tools

@app.tool()
def remember(content: str, tags: list[str] = None) -> str:
    """
    Store a memory for later recall.

    Args:
        content: What to remember
        tags: Optional tags for categorization
    """
    try:
        # Validate input
        validate_input(content, "content")

        # Check for sensitive data
        warning = check_sensitive_data(content)
        if warning:
            logger.warning(f"Sensitive data detected in remember(): {content[:50]}...")

        # Store memory
        memory_id = memory.remember(content, tags or [])
        logger.info(f"Stored memory {memory_id}")

        result = f"✓ Remembered: {content[:100]}{'...' if len(content) > 100 else ''} (ID: {memory_id})"
        if warning:
            result += f"\n{warning}"
        return result

    except ValueError as e:
        logger.error(f"Validation error in remember(): {e}")
        return f"❌ Error: {str(e)}"
    except sqlite3.Error as e:
        logger.error(f"Database error in remember(): {e}", exc_info=True)
        return f"❌ Database error: Unable to store memory"
    except Exception as e:
        logger.exception(f"Unexpected error in remember(): {e}")
        return f"❌ Unexpected error: {str(e)}"


@app.tool()
def recall(query: str, limit: int = 5) -> str:
    """
    Search memories.

    Args:
        query: Search term
        limit: Max results (default 5)
    """
    try:
        # Validate input
        validate_input(query, "query", MAX_QUERY_LENGTH)

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        # Search memories
        results = memory.recall(query, limit)
        logger.info(f"Recalled {len(results)} memories for query: {query}")

        if not results:
            return f"No memories found for '{query}'"

        lines = [f"Found {len(results)} memories:"]
        for r in results:
            age_days = int(r['age_days'])
            age_str = f"{age_days}d ago" if age_days > 0 else "today"
            tags_str = f" [{', '.join(r['tags'])}]" if r['tags'] else ""
            lines.append(f"- {r['content']} ({age_str}){tags_str}")

        return "\n".join(lines)

    except ValueError as e:
        logger.error(f"Validation error in recall(): {e}")
        return f"❌ Error: {str(e)}"
    except sqlite3.Error as e:
        logger.error(f"Database error in recall(): {e}", exc_info=True)
        return f"❌ Database error: Unable to search memories"
    except Exception as e:
        logger.exception(f"Unexpected error in recall(): {e}")
        return f"❌ Unexpected error: {str(e)}"


@app.tool()
def forget(query: str) -> str:
    """
    Delete memories matching query.

    Args:
        query: Search term
    """
    try:
        # Validate input
        validate_input(query, "query", MAX_QUERY_LENGTH)

        # Delete memories
        count = memory.forget(query)
        logger.info(f"Deleted {count} memories matching: {query}")

        return f"✓ Deleted {count} memories matching '{query}'"

    except ValueError as e:
        logger.error(f"Validation error in forget(): {e}")
        return f"❌ Error: {str(e)}"
    except sqlite3.Error as e:
        logger.error(f"Database error in forget(): {e}", exc_info=True)
        return f"❌ Database error: Unable to delete memories"
    except Exception as e:
        logger.exception(f"Unexpected error in forget(): {e}")
        return f"❌ Unexpected error: {str(e)}"


@app.tool()
def store(name: str, content: str) -> str:
    """
    Store large artifact by reference.

    Args:
        name: Artifact name (e.g., "config.py")
        content: Full content
    """
    try:
        # Validate inputs
        validate_input(name, "name", 255)  # Reasonable file name limit
        validate_input(content, "content", MAX_CONTENT_LENGTH * 10)  # Larger limit for artifacts

        # Check for sensitive data
        warning = check_sensitive_data(content)
        if warning:
            logger.warning(f"Sensitive data detected in store(): {name}")

        # Store artifact
        memory.store(name, content)
        logger.info(f"Stored artifact: {name} ({len(content)} bytes)")

        result = f"✓ Stored artifact: {name} ({len(content)} bytes)"
        if warning:
            result += f"\n{warning}"
        return result

    except ValueError as e:
        logger.error(f"Validation error in store(): {e}")
        return f"❌ Error: {str(e)}"
    except sqlite3.Error as e:
        logger.error(f"Database error in store(): {e}", exc_info=True)
        return f"❌ Database error: Unable to store artifact"
    except Exception as e:
        logger.exception(f"Unexpected error in store(): {e}")
        return f"❌ Unexpected error: {str(e)}"


@app.tool()
def retrieve(name: str) -> str:
    """
    Get artifact content.

    Args:
        name: Artifact name
    """
    try:
        # Validate input
        validate_input(name, "name", 255)

        # Retrieve artifact
        content = memory.retrieve(name)
        logger.info(f"Retrieved artifact: {name}")

        if content:
            return content
        else:
            return f"❌ Artifact '{name}' not found"

    except ValueError as e:
        logger.error(f"Validation error in retrieve(): {e}")
        return f"❌ Error: {str(e)}"
    except sqlite3.Error as e:
        logger.error(f"Database error in retrieve(): {e}", exc_info=True)
        return f"❌ Database error: Unable to retrieve artifact"
    except Exception as e:
        logger.exception(f"Unexpected error in retrieve(): {e}")
        return f"❌ Unexpected error: {str(e)}"


@app.tool()
def status() -> str:
    """Get system status."""
    try:
        s = memory.status()
        logger.info("Status check performed")

        return f"""SimpleContext Status:
- Memories: {s['memories']}
- Artifacts: {s['artifacts']}
- Unresolved Errors: {s['unresolved_errors']}
- Current Mode: {s['mode']}
- Database: {s['db_path']}
"""
    except sqlite3.Error as e:
        logger.error(f"Database error in status(): {e}", exc_info=True)
        return f"❌ Database error: Unable to get status"
    except Exception as e:
        logger.exception(f"Unexpected error in status(): {e}")
        return f"❌ Unexpected error: {str(e)}"


# Server entry point
if __name__ == "__main__":
    app.run(transport="stdio")
