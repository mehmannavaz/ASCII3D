"""The nine routes: view an ASCII art from every direction.

A "route" is where you stand while looking at the art.  The 3x3 grid
of routes (this is the nine the ``docs/01-Theory/03-LookAnywhere.md``
sketch was reaching for)::

    leftup     up      rightup
    left     center    right
    leftdown  down     rightdown

Two rendering styles cooperate:

* **left / right** reuse the classic engine shear
  (:func:`ascii3d.engine.turn`) -- the exact look of the hand drawn
  theory docs.
* **up / down / the four diagonals and center** use the true 3D
  wireframe of :mod:`ascii3d.wireframe`: the art is extruded into a
  box and the camera moves to the requested compass position.

Direction convention (matching the engine): ``left`` means the *art
turns to the left*, so its right side face becomes visible -- exactly
like ``ascii3d.turn(art, 'left')``.  ``up`` means we look down on the
art and see its top face, ``down`` looks at it from below.

Example:
    >>> from ascii3d import route, nine_routes
    >>> print(route(' _\\n|_|', 'leftup'))
    ...
    >>> sheet = nine_routes(' _\\n|_|')   # dict of all nine views
"""

from __future__ import annotations

from .engine import turn as _engine_turn
from .wireframe import render_art as _render_art

__all__ = ['ROUTES', 'route', 'nine_routes', 'contact_sheet']

# (yaw, pitch) camera angles for the wireframe routes, degrees.
# yaw: turntable rotation (negative = art turns left, right face
# shows, like the engine's turn_left); pitch: positive looks down on
# the top face.
_WIRE_ANGLES = {
    'center': (0, 0),
    'up': (0, 65),
    'down': (0, -65),
    'leftup': (-45, 62),
    'leftdown': (-45, -45),
    'rightup': (45, 62),
    'rightdown': (45, -45),
}

ROUTES = ('leftup', 'up', 'rightup', 'left', 'center', 'right',
          'leftdown', 'down', 'rightdown')


def _auto_depth(art: str) -> int:
    """A depth that scales with the art (bigger art, deeper box)."""
    rows = [line for line in art.split('\n') if line.strip()]
    length = len(rows)
    return max(2, min(4, length // 2))


def route(art: str, direction: str = 'center', depth: int | None = None,
          zoom: float = 1.0, style: str = 'auto') -> str:
    """Render *art* viewed from one of the nine routes.

    Args:
        art: The ASCII art as a plain string.
        direction: One of :data:`ROUTES` -- ``left``, ``right``,
            ``up``, ``down``, ``leftup``, ``leftdown``, ``rightup``,
            ``rightdown`` or ``center``.
        depth: Depth of the 3D box.  ``None`` picks a depth that
            matches the art size.
        zoom: Scale factor for the wireframe routes.
        style: ``'auto'`` uses the engine shear for left/right and
            the 3D wireframe everywhere else; ``'engine'`` and
            ``'wire'`` force one style (``'engine'`` only supports
            left/right/center).

    Returns:
        The rendered ASCII art.

    Raises:
        ValueError: If *direction* or *style* is unknown.
    """
    if direction not in ROUTES:
        raise ValueError(
            f'direction must be one of {ROUTES}, not {direction!r}')
    if style not in ('auto', 'engine', 'wire'):
        raise ValueError(f"style must be 'auto', 'engine' or 'wire', "
                         f'not {style!r}')

    if depth is None:
        depth = _auto_depth(art)

    if style in ('auto', 'engine') and direction in ('left', 'right'):
        return _engine_turn(art, direction=direction, depth=depth)

    if direction == 'center':
        if style == 'engine':
            return '\n'.join(line.rstrip() for line in
                             art.strip('\n').split('\n'))
        # A little 3D frame around the plain art.
        return _render_art(art, yaw=0, pitch=0, depth=depth,
                           zoom=zoom)

    if style == 'engine':
        raise ValueError(
            "the 'engine' style only supports left/right/center; "
            'use style="wire" or "auto" for the other routes')

    yaw, pitch = _WIRE_ANGLES[direction]
    return _render_art(art, yaw=yaw, pitch=pitch, depth=depth, zoom=zoom)


def nine_routes(art: str, depth: int | None = None,
                zoom: float = 1.0, style: str = 'auto'
                ) -> dict[str, str]:
    """Render *art* from all nine routes at once.

    Args:
        art: The ASCII art as a plain string.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor for the wireframe routes.
        style: See :func:`route`.

    Returns:
        A dict mapping every route name to its rendered art, in the
        reading order of the 3x3 route grid (leftup, up, rightup,
        left, center, ...).
    """
    if depth is None:
        depth = _auto_depth(art)
    return {name: route(art, name, depth=depth, zoom=zoom, style=style)
            for name in ROUTES}


def contact_sheet(art: str, depth: int | None = None, zoom: float = 1.0,
                  style: str = 'auto', gap: int = 3) -> str:
    """Render all nine routes as one labelled 3x3 gallery.

    The sheet is laid out like the route grid::

        leftup | up | rightup
        left | center | right
        leftdown | down | rightdown

    Args:
        art: The ASCII art as a plain string.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor for the wireframe routes.
        style: See :func:`route`.
        gap: Blank columns between the gallery cells.

    Returns:
        The contact sheet as a single string.
    """
    routes = nine_routes(art, depth=depth, zoom=zoom, style=style)
    order = [('leftup', 'up', 'rightup'),
             ('left', 'center', 'right'),
             ('leftdown', 'down', 'rightdown')]
    lines: list[str] = []
    for row_routes in order:
        cells = []
        for name in row_routes:
            cell = routes[name].split('\n')
            label = f'-- {name} --'.ljust(
                max(len(line) for line in cell))
            cells.append([label] + cell)
        height = max(len(cell) for cell in cells)
        for cell in cells:
            width = max(len(line) for line in cell)
            cell.extend([' ' * width] * (height - len(cell)))
        for i in range(height):
            cell_width = max(len(line) for line in cell)
            lines.append((' ' * gap).join(
                cell[i].ljust(cell_width) for cell in cells))
        lines.append('')
    return '\n'.join(lines).rstrip('\n')
