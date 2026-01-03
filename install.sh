#!/bin/bash
# SimpleContext v1.0.0 Installation Script
# Usage: ./install.sh

set -e  # Exit on error

echo ""
echo "🚀 SimpleContext v1.0.0 Installation"
echo "===================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found"
    echo "   Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"
    echo "   Please upgrade Python: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION (compatible)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if pip3 install -r requirements.txt; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Run tests
echo "🧪 Running tests..."
if python3 -m pytest tests/ -q; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed (but installation may still work)"
fi
echo ""

# Get installation path
INSTALL_PATH=$(pwd)

echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "   1. Add to ~/.claude/.mcp.json:"
echo ""
echo '   {
     "mcpServers": {
       "simplecontext": {
         "command": "python3",
         "args": ["'$INSTALL_PATH'/src/simplecontext.py"],
         "cwd": "'$INSTALL_PATH'"
       }
     }
   }'
echo ""
echo "   2. Restart Claude Code"
echo ""
echo "📚 Documentation: $INSTALL_PATH/README.md"
echo "🐛 Issues: https://github.com/jmartinmatias/simplecontext/issues"
echo ""
