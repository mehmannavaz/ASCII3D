"""The ASCII3D rendering engine.

This module implements the core idea documented in ``docs/01-Theory``:

* The 2D art is treated as the **front face** of a box.
* "Turning" the art shears the front face (every row steps one column
  sideways) and swaps the vertical ``|`` strokes for diagonals, which
  makes the face look tilted in 3D.
* A **top face** (drawn with ``/`` diagonals above the front face) and a
  **side face** (drawn on the right for a left turn) are added to close
  the silhouette of the box, exactly like the hand drawn examples in
  ``docs/01-Theory/01-SImpleHead.md``.

Formulas (see ``docs/01-Theory/02-HowToTurn.md``)::

    turned_length = length + depth       (the docs use depth = 1)
    turned_width  = width  + length - 1   (plus depth when the side face is on)

Direction convention (see ``docs/01-Theory/00-SimpleGaze.md``):

* ``turn_left``  -- the art turns to the left, ``|`` becomes ``\\`` and the
  visible side face is the right one.
* ``turn_right`` -- the mirror image: ``|`` becomes ``/`` and the visible
  side face is the left one.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    'ascii',
    'Ascii3D',
    'turn',
    'turn_left',
    'turn_right',
    'mirror',
]

# Characters used to shade the side face from "white" (near) to "black"
# (far), see docs/10-TODO/01-2Sides3dRendering.md
SHADE_RAMP = '.:/X#'

# Characters that are swapped when an art is mirrored horizontally.
_MIRROR_MAP = str.maketrans({
    '/': '\\', '\\': '/',
    '(': ')', ')': '(',
    '[': ']', ']': '[',
    '{': '}', '}': '{',
    '<': '>', '>': '<',
})


def normalize(art: str) -> list[str]:
    """Split *art* into equal width rows.

    Leading and trailing blank lines (an artefact of triple quoted
    strings) are removed, while blank lines *inside* the art are kept
    because they are part of the drawing.  Every row is padded with
    spaces to the width of the widest row so the art becomes a perfect
    rectangle, which the turning algorithm requires.

    Args:
        art: The ASCII art as a plain string.

    Returns:
        A list of equally wide rows.

    Raises:
        TypeError: If *art* is not a string.
        ValueError: If *art* contains no visible character.
    """
    if not isinstance(art, str):
        raise TypeError(f'art must be a string, not {type(art).__name__}')
    rows = art.split('\n')
    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    if not rows:
        raise ValueError('art is empty (no visible characters)')
    width = max(len(row) for row in rows)
    return [row.ljust(width) for row in rows]


def mirror(art: str) -> str:
    """Mirror *art* horizontally.

    Every row is reversed and mirror-symmetric characters are swapped
    (``/`` with ``\\``, brackets with each other, ...).  This is what
    allows :func:`turn_right` to be implemented as the mirror image of
    :func:`turn_left`.

    Args:
        art: The ASCII art to mirror.

    Returns:
        The horizontally mirrored art.
    """
    rows = normalize(art)
    rows = [row[::-1].translate(_MIRROR_MAP).rstrip() for row in rows]
    return '\n'.join(_dedent(rows))


def _dedent(rows: list[str]) -> list[str]:
    """Remove the common leading spaces so the art hugs the left edge."""
    indents = [len(row) - len(row.lstrip(' ')) for row in rows
               if row.strip()]
    if not indents:
        return rows
    shift = min(indents)
    return [row[shift:] if row.strip() else '' for row in rows]


class ascii:  # noqa: N801 - kept for backwards compatibility with 0.0.1
    """A 2D ASCII art that can be turned to look 3D.

    Attributes:
        art (str): The original art as given by the user.
        length (int): Number of rows of the normalized art.
        width (int): Width (columns) of the normalized art.
        matrix (numpy.ndarray): The art as a 2D char matrix of shape
            ``(length, width)``.
        turned_length (int): Height of the turned art for ``depth=1``
            (``length + 1``, the formula from the theory docs).
        turned_width (int): Width of the turned art for ``depth=1``
            (``width + length - 1``, the formula from the theory docs).

    Examples:
        >>> from ascii3d import ascii
        >>> cube = ascii(' _ \\n|_|')
        >>> cube.length, cube.width
        (2, 3)
        >>> print(cube.turn_left())
         __
        /_/\\
        \\_\\/
    """

    def __init__(self, art: str):
        self.art = art
        self.lines = normalize(art)
        self.length = len(self.lines)
        self.width = len(self.lines[0])
        self.matrix = np.array(
            [list(line) for line in self.lines], dtype='<U1')
        # Formulas from docs/01-Theory/02-HowToTurn.md (for depth = 1).
        self.turned_length = self.length + 1
        self.turned_width = self.width + self.length - 1

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def turn_left(self, depth: int = 1, side: bool = True,
                  shade: bool = False, fill: str | None = None) -> str:
        """Turn the art to the left and reveal its right side.

        The front face is sheared to the right (``|`` strokes become
        ``\\``), a top face is drawn above it and, by default, the right
        side face is drawn too.

        Args:
            depth: How deep the box is.  Bigger values make a bigger top
                and side face (1 keeps the art compact, 2-3 look very
                "boxy").
            side: Draw the visible (right) side face.
            shade: Fill the side face with a depth gradient
                (``.:/X#``), light near the viewer and dark far away.
            fill: Fill the side face uniformly with this character
                instead of the gradient.

        Returns:
            The turned art as a string.

        Examples:
            >>> cube = ascii(' _ \\n|_|')
            >>> print(cube.turn_left())
             __
            /_/\\
            \\_\\/
        """
        lines = _turn_left(self.lines, depth, side, shade, fill)
        return '\n'.join(''.join(line).rstrip() for line in lines)

    def turn_right(self, depth: int = 1, side: bool = True,
                   shade: bool = False, fill: str | None = None) -> str:
        """Turn the art to the right and reveal its left side.

        This is the mirror image of :meth:`turn_left`: the front face is
        sheared to the left (``|`` strokes become ``/``) and the visible
        side face is the left one.

        Args:
            depth: How deep the box is.
            side: Draw the visible (left) side face.
            shade: Fill the side face with a depth gradient.
            fill: Fill the side face uniformly with this character.

        Returns:
            The turned art as a string.
        """
        mirrored = normalize(mirror('\n'.join(self.lines)))
        lines = _turn_left(mirrored, depth, side, shade, fill)
        rows = [''.join(line)[::-1].translate(_MIRROR_MAP).rstrip()
                for line in lines]
        return '\n'.join(_dedent(rows))

    def turn(self, direction: str = 'left', depth: int = 1, side: bool = True,
             shade: bool = False, fill: str | None = None) -> str:
        """Turn the art in the given *direction* (``'left'`` or ``'right'``).

        Args:
            direction: ``'left'`` or ``'right'``.
            depth: How deep the box is.
            side: Draw the visible side face.
            shade: Fill the side face with a depth gradient.
            fill: Fill the side face uniformly with this character.

        Returns:
            The turned art as a string.

        Raises:
            ValueError: If *direction* is neither ``'left'`` nor
                ``'right'``.
        """
        if direction == 'left':
            return self.turn_left(depth, side, shade, fill)
        if direction == 'right':
            return self.turn_right(depth, side, shade, fill)
        raise ValueError(
            f"direction must be 'left' or 'right', "
            f'not {direction!r}')

    # Convenient alias.
    render = turn

    def __str__(self) -> str:
        return '\n'.join(line.rstrip() for line in self.lines)

    def __repr__(self) -> str:
        return f'<ascii {self.length}x{self.width}>'


# Backwards/API friendly alias.
Ascii3D = ascii


# ----------------------------------------------------------------------
# module level helpers
# ----------------------------------------------------------------------
def turn(art: str, direction: str = 'left', depth: int = 1, side: bool = True,
         shade: bool = False, fill: str | None = None) -> str:
    """Turn an ASCII *art* to make it look 3D.

    Args:
        art: The ASCII art as a plain string.
        direction: ``'left'`` or ``'right'``.
        depth: How deep the box is.
        side: Draw the visible side face.
        shade: Fill the side face with a depth gradient.
        fill: Fill the side face uniformly with this character.

    Returns:
        The turned art as a string.

    Examples:
        >>> print(turn(' _ \\n|_|'))
         __
        /_/\\
        \\_\\/
    """
    return ascii(art).turn(direction, depth, side, shade, fill)


def turn_left(art: str, depth: int = 1, side: bool = True,
              shade: bool = False, fill: str | None = None) -> str:
    """Shortcut for :meth:`ascii.turn_left`."""
    return turn(art, 'left', depth, side, shade, fill)


def turn_right(art: str, depth: int = 1, side: bool = True,
               shade: bool = False, fill: str | None = None) -> str:
    """Shortcut for :meth:`ascii.turn_right`."""
    return turn(art, 'right', depth, side, shade, fill)


# ----------------------------------------------------------------------
# the renderer
# ----------------------------------------------------------------------
def _turn_left(lines: list[str], depth: int, side: bool,
               shade: bool, fill: str | None) -> list[str]:
    """Render the *lines* turned to the left; returns raw padded rows.

    This is the algorithm described in the theory docs:

    1. the front face rows are shifted right one column at a time,
    2. ``|`` strokes become ``\\`` diagonals,
    3. a top face is built from the first row of the art,
    4. a right side face closes the box silhouette.
    """
    if not isinstance(depth, int) or isinstance(depth, bool):
        raise TypeError(f'depth must be an int, not {type(depth).__name__}')
    if depth < 0:
        raise ValueError('depth must be >= 0')
    if depth == 0:
        return list(lines)

    length, width = len(lines), len(lines[0])
    d = depth

    # Content extent of the first row (the future top edge).
    row0 = lines[0]
    content_cols = [c for c, ch in enumerate(row0) if ch != ' ']
    first = content_cols[0] if content_cols else 0
    last = content_cols[-1] if content_cols else -1
    corner = last + 1  # column of the top-right corner

    out_h = length + d
    out_w = width + length + d + 2
    grid = [[' '] * out_w for _ in range(out_h)]

    def put(row: int, col: int, ch: str, protect: bool = False) -> None:
        if 0 <= row < out_h and 0 <= col < out_w:
            if not protect or grid[row][col] in (' ', '_'):
                grid[row][col] = ch

    # -- front face ----------------------------------------------------
    for r, line in enumerate(lines):
        row = r + d
        offset = 0 if r <= 1 else r - 1
        for c, ch in enumerate(line):
            if ch == '|':
                ch = '\\'
            put(row, offset + c, ch)

    # -- top face ------------------------------------------------------
    # Back edge: the first row of the art, pushed up and aside.
    for c, ch in enumerate(row0):
        put(0, d - 1 + c, ch)
    # Close the back-right corner with one extra floor tile.
    if last >= 0 and row0[last] == '_':
        put(0, last + d, '_')
    # Left edge and right edge of the top face.
    for k in range(1, d + 1):
        put(k, first + d - 1 - k, '/', protect=True)
        put(k, corner + d - k, '/', protect=True)

    # -- side face (the right one) --------------------------------------
    if side and length >= 2:
        # Near edge: parallel to the front face right edge.
        for r in range(1, length):
            put(d + r, width - 2 + r, '\\', protect=True)
        # Far edge: the near edge pushed back by the depth.
        for r in range(1, length):
            put(r, width + r + d - 2, '\\')
        # Bottom edge closing the silhouette.
        for j in range(length, length + d):
            put(j, width + 2 * length + d - 3 - j, '/')
        # Optional shading of the side face interior.
        if fill or shade:
            fill_char = fill if fill else None
            for rho in range(1, length + d - 1):
                # Left boundary: top-right edge, then near edge.
                if rho <= d:
                    left = corner + d - rho
                else:
                    left = rho + width - d - 2
                # Right boundary: far edge, then bottom edge.
                if rho < length:
                    right = rho + width + d - 2
                else:
                    right = width + 2 * length + d - 3 - rho
                for gamma in range(left + 1, right):
                    if fill_char:
                        ch = fill_char
                    else:
                        z = ((gamma - rho) - (width - d - 2)) / 2
                        z = max(1, int(z + 0.5))
                        ramp = max(1, d - 1) * (len(SHADE_RAMP) - 1)
                        idx = round((z - 1) / ramp) if ramp else 0
                        ch = SHADE_RAMP[min(len(SHADE_RAMP) - 1, max(0, idx))]
                    put(rho, gamma, ch, protect=True)

    return grid
