"""
Automatic mode detection.
Two modes: coding (default) and debugging.
"""

from typing import Dict


# Hardcoded attention budgets
MODES = {
    "coding": {
        "memories": 0.30,
        "artifacts": 0.30,
        "session": 0.25,
        "errors": 0.10,
        "goal": 0.05
    },
    "debugging": {
        "errors": 0.50,
        "session": 0.25,
        "memories": 0.15,
        "artifacts": 0.10,
        "goal": 0.00
    }
}

DEBUG_KEYWORDS = [
    "error", "bug", "fail", "failing", "broken", "crash", "crashes",
    "exception", "traceback", "stack trace", "fix", "debug", "debugging",
    "not working", "doesn't work", "won't work"
]


def detect_mode(message: str) -> str:
    """
    Detect mode from user message.

    Args:
        message: User's message

    Returns:
        "debugging" if error-related, else "coding"

    Example:
        >>> detect_mode("The tests are failing")
        'debugging'
        >>> detect_mode("Add a login feature")
        'coding'
    """
    message_lower = message.lower()

    for keyword in DEBUG_KEYWORDS:
        if keyword in message_lower:
            return "debugging"

    return "coding"


def get_attention_budget(mode: str) -> Dict[str, float]:
    """
    Get attention budget for mode.

    Args:
        mode: "coding" or "debugging"

    Returns:
        Budget allocation dict
    """
    return MODES.get(mode, MODES["coding"])
