"""
SimpleContext: Memory for Claude, in 800 lines.
"""

from .storage import SimpleStorage
from .memory import SimpleMemory
from .errors import ErrorMemory
from .modes import detect_mode, get_attention_budget, MODES

__version__ = "1.0.0"
__all__ = [
    "SimpleStorage",
    "SimpleMemory",
    "ErrorMemory",
    "detect_mode",
    "get_attention_budget",
    "MODES",
]
