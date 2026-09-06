"""Small helpers shared by the engine and the CLI."""

import os
import shutil

__all__ = ['getSize', 'fit_size']


def getSize() -> tuple[int, int]:
    """Get width and length of the terminal emulator.

    Falls back to ``shutil.get_terminal_size`` (which honours the
    ``COLUMNS``/``LINES`` environment variables and defaults to
    ``(80, 24)``) when the output stream is not a terminal, e.g. inside
    tests or when the output is piped.

    Returns:
        A tuple containing (columns, rows) of the terminal.

    Examples:
        >>> getSize()
        (177, 45)
    """
    try:
        size = os.get_terminal_size()
    except (OSError, ValueError):
        size = shutil.get_terminal_size()
    return (size.columns, size.lines)


def fit_size(width: int, height: int) -> bool:
    """Return True if a *width* x *height* block fits the terminal."""
    columns, lines = getSize()
    return width <= columns and height <= lines
