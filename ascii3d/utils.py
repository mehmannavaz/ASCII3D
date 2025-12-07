import os

def getSize() -> tuple[int, int]:
    """Get width and lenth of terminal emulator.

    Returns:
        A tuple containing (columns, rows) of the terminal

    Examples:
        >>> getSize()
        (177, 45)
    """
    size = os.get_terminal_size()
    return (size.columns, size.lines)
