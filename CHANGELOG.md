# Changelog

All notable changes to SimpleContext will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-01-03

**Initial production-ready release of SimpleContext** - Persistent memory tools for Claude Code via MCP.

### Core Features

**6 Memory Tools:**
- `remember(content, tags)` - Store memories with optional tags
- `recall(query, limit)` - Search memories with smart recency ranking
- `forget(query)` - Delete matching memories
- `store(name, content)` - Save large artifacts by name
- `retrieve(name)` - Get artifact content
- `status()` - View system status
- `get_context()` - Compiled context prompt for Claude

**Storage & Search:**
- SQLite database backend with FTS5 full-text search
- Temporal decay algorithm (recent memories ranked higher)
- Automatic schema creation and migration
- Write-Ahead Logging (WAL) for better concurrency
- Error tracking system with resolution marking
- Dual-mode context (coding/debugging)

### Security

**Production-Ready Security:**
- Database files created with `0o600` permissions (owner-only read/write)
- Input validation on all MCP tools (prevents empty/null/oversized inputs)
- Sensitive data detection (warns if passwords, API keys, tokens detected)
- Comprehensive error handling with try/except blocks
- SQL injection protection via parameterized queries
- Proper Python logging (no print statements in production)

**Validation Limits:**
- Content: 100 KB max per memory
- Artifacts: 1 MB max per artifact
- Query: 1 KB max search length
- Name: 255 characters max
- Recall limit: 1-100 results

### Code Quality

**Well-Tested & Documented:**
- 630 lines of Python code
- 7/7 comprehensive unit tests passing
- Type hints throughout
- Full docstrings with examples
- Context manager support (`__enter__`/`__exit__`)

### Packaging

**Modern Python Standards:**
- PEP 517/518 compliant (`pyproject.toml`)
- Pinned dependencies in `requirements.txt`
- Development dependencies in `requirements-dev.txt`
- pytest configuration included
- Coverage reporting support

### Technical Details

**Architecture:**
- FastMCP server for Model Context Protocol
- SQLite 3 with FTS5 extension
- Python 3.10+ required
- No external runtime dependencies (except FastMCP)

**File Structure:**
```
simplecontext/
├── src/
│   ├── simplecontext.py    # MCP server (main)
│   ├── memory.py           # Memory operations
│   ├── storage.py          # SQLite backend
│   ├── errors.py           # Error tracking
│   └── modes.py            # Mode detection
├── tests/
│   └── test_simple.py      # Test suite
├── examples/
│   └── demo.py             # Working demo
└── requirements.txt        # Dependencies
```

---

## Future Plans

**Potential v1.1.0 Features:**
- Performance benchmarks and optimization
- Enhanced context injection
- Additional search operators
- Extended configuration options

---

## Version History

- **v1.0.0** (2026-01-03) - Initial production release

---

## Credits

Built with Claude Code and focused on simplicity, reliability, and production-readiness.

**Technologies:**
- Python 3.10+
- SQLite with FTS5
- FastMCP (Model Context Protocol)
- pytest for testing
