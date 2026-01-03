# SimpleContext

**Persistent memory for Claude Code via MCP** – Store and recall context across conversations.

Version: **1.0.0** | Status: **Production Ready** | License: MIT

---

## What is SimpleContext?

SimpleContext gives Claude Code the ability to remember information across conversations using 6 simple memory tools.

**The Problem:**
```
You: "We're using PostgreSQL with the user table in the auth schema"
(2 hours later)
You: "What database are we using?"
Claude: "I don't have that information..."
```

**The Solution:**
```
You: "Remember we're using PostgreSQL 14 on port 5432"
Claude: ✓ Remembered: Using PostgreSQL 14 on port 5432

(Later...)
You: "What database are we using?"
Claude: Found 1 memories: Using PostgreSQL 14 on port 5432
```

---

## Features

✅ **6 Core Memory Tools**
- `remember(content, tags)` - Store information
- `recall(query)` - Search with smart recency ranking
- `forget(query)` - Delete memories
- `store(name, content)` - Save large artifacts
- `retrieve(name)` - Get artifacts back
- `status()` - View system status

✅ **Smart Features**
- Full-text search with FTS5
- Temporal decay (recent memories ranked higher)
- Secure storage (owner-only permissions)
- Input validation and error handling
- Sensitive data detection warnings

✅ **Lightweight & Fast**
- 630 lines of Python code
- SQLite backend (no external dependencies)
- 7/7 tests passing

---

## Requirements

- **Python 3.10+** (required for FastMCP)
- Claude Code CLI installed

Check your Python version:
```bash
python3 --version  # Must be 3.10 or higher
```

---

## Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/jmartinmatias/simplecontext.git
cd simplecontext

# Run automated installer
./install.sh
# Checks Python version, installs dependencies, runs tests
```

### Manual Install

```bash
# Clone the repository
git clone https://github.com/jmartinmatias/simplecontext.git
cd simplecontext

# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
pytest tests/
# Expected: 7 passed in ~0.15s
```

### 2. Configure Claude Code

Add SimpleContext to your MCP configuration file at `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "simplecontext": {
      "command": "python3",
      "args": ["/absolute/path/to/simplecontext/src/simplecontext.py"],
      "cwd": "/your/working/directory"
    }
  }
}
```

**Important:** Replace `/absolute/path/to/simplecontext` with the actual path where you cloned the repo.

### 3. Restart Claude Code

```bash
# Restart Claude Code to load the MCP server
# The simplecontext tools will now be available
```

---

## Usage Examples

### Basic Memory Storage

```
You: "Remember we're using PostgreSQL 14 on port 5432"
Claude: ✓ Remembered: Using PostgreSQL 14 on port 5432 (ID: abc-123)

You: "Remember our API key is stored in AWS Secrets Manager"
Claude: ✓ Remembered: API key is stored in AWS Secrets Manager
⚠️  WARNING: Content may contain credentials or sensitive data!
```

### Searching Memories

```
You: "What database are we using?"
Claude: [Automatically calls recall("database")]
Found 1 memories:
- Using PostgreSQL 14 on port 5432 (0d ago)
```

### Storing Large Artifacts

```
You: "Store this config file as 'database.yml'"
Claude: ✓ Stored artifact: database.yml (2,048 bytes)

You: "Retrieve the database config"
Claude: [Returns full config file content]
```

### Checking Status

```
You: "What's in memory?"
Claude: [Calls status()]
SimpleContext Status:
- Memories: 12
- Artifacts: 3
- Unresolved Errors: 0
- Current Mode: coding
- Database: .simplecontext.db
```

---

## Architecture

```
simplecontext/
├── src/
│   ├── simplecontext.py    # MCP server (main entry point)
│   ├── memory.py           # Core memory operations
│   ├── storage.py          # SQLite backend + FTS5
│   ├── errors.py           # Error tracking
│   └── modes.py            # Context mode detection
├── tests/
│   └── test_simple.py      # 7 comprehensive tests
├── examples/
│   └── demo.py             # Working demo
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Package configuration
```

**Total:** ~630 lines of code

---

## Security Features

🔒 **Built-in Security**
- Database files created with `0o600` permissions (owner-only)
- Input validation on all tools (max 100KB per memory)
- Sensitive data detection (warns if passwords/API keys detected)
- Comprehensive error handling (prevents crashes)
- SQL injection protection (parameterized queries)

---

## How It Works

### 1. Storage
- All memories stored in SQLite database (`.simplecontext.db`)
- Full-text search using SQLite FTS5 extension
- Automatic schema creation on first use

### 2. Temporal Decay
- Recent memories ranked higher in search results
- Recency score calculated based on age
- Helps surface relevant, recent information first

### 3. Mode Detection
- **Coding mode**: Focus on memories and artifacts
- **Debugging mode**: Include recent errors in context

---

## Configuration

SimpleContext works out of the box with sensible defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| Database path | `.simplecontext.db` | SQLite database location |
| Max content | 100 KB | Maximum memory size |
| Max query | 1 KB | Maximum search query length |
| Max artifact | 1 MB | Maximum artifact size |
| Recall limit | 5-100 | Results per search |

---

## Troubleshooting

### "No module named 'mcp'" or "No module named 'fastmcp'"

**Solution:**
```bash
# Make sure you have Python 3.10+
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### "Tests failing"

**Solution:**
```bash
# Run tests with verbose output
pytest tests/ -v

# All 7 tests should pass
# If any fail, please file an issue on GitHub
```

### "Claude doesn't see my memories"

**Solution:**
- Verify MCP configuration in `~/.claude/.mcp.json`
- Check that paths are absolute (not relative)
- Restart Claude Code after configuration changes
- Claude must explicitly call `recall()` to search memories

### "Permission denied" when accessing database

**Solution:**
```bash
# Check database file permissions
ls -la .simplecontext.db

# Should show: -rw------- (600)
# If not, fix permissions:
chmod 600 .simplecontext.db
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_simple.py::test_remember_recall -v
```

### Project Structure

- **src/** - Main source code
- **tests/** - Test suite (pytest)
- **examples/** - Usage examples
- **docs/** - Additional documentation

### Contributing

We welcome contributions! Please:
- Keep changes focused and simple
- Add tests for new features
- Follow existing code style
- Update documentation

**Not accepting** (to maintain simplicity):
- Alternative storage backends
- UI/dashboard features
- Complex integrations

---

## FAQ

**Q: Does this work with other AI tools besides Claude Code?**
A: SimpleContext is designed specifically for Claude Code's MCP (Model Context Protocol). It may work with other MCP-compatible tools but is not officially supported.

**Q: Where is data stored?**
A: All data is stored locally in `.simplecontext.db` in your working directory. Nothing is sent to external servers.

**Q: Can I use this in production?**
A: Yes! Version 1.0.0 is production-ready with comprehensive security features and error handling.

**Q: How much data can I store?**
A: Individual memories are limited to 100KB, artifacts to 1MB. Total database size is limited only by available disk space.

**Q: Is my data encrypted?**
A: The database file has secure permissions (owner-only access), but data is not encrypted at rest. For sensitive data, consider using OS-level encryption.

**Q: Can I migrate data between projects?**
A: Yes, the `.simplecontext.db` file is portable. Copy it to your new project directory.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and detailed changes.

### Version 1.0.0 (Latest)
- Production-ready release
- Comprehensive security hardening
- Input validation and error handling
- Sensitive data detection
- Database permission fixes (0o600)
- Python logging integration
- Full packaging support (pyproject.toml)

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/jmartinmatias/simplecontext/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jmartinmatias/simplecontext/discussions)

---

## Acknowledgments

Built with Claude Code and focused on simplicity, reliability, and production-readiness.

**Core Technologies:**
- Python 3.10+
- SQLite with FTS5
- FastMCP (Model Context Protocol)
- pytest

---

*SimpleContext v1.0.0 - Persistent memory for Claude Code*
