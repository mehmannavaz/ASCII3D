"""The nine routes: view an ASCII art from every direction.

A "route" is where you stand while looking at the art.  The 3x3 grid
of routes (the idea sketched in ``docs/01-Theory/03-LookAnywhere.md``)::

    leftup     up      rightup
    left     center    right
    leftdown  down     rightdown

Two renderers cooperate:

* **left / right** reuse the classic engine shear
  (:func:`ascii3d.engine.turn`) -- byte-exact against the hand drawn
  theory docs.
* **the other seven** use the box camera (:mod:`ascii3d.pose`): the
  art is the front face of a box and the camera sits at the
  requested compass position -- every face drawn with single
  marching strokes, the side face shaded with the depth gradient.

Direction convention (matching the engine): ``left`` means the *art
turns to the left*, so its right side face becomes visible -- exactly
like ``ascii3d.turn(art, 'left')``.  ``up`` looks down on the art from
above (the top face dominating the frame), ``down`` looks up from
below (the bottom face visible underneath).

Example:
    >>> from ascii3d import route, nine_routes
    >>> sheet = nine_routes(' _\\n|_|')   # dict of all nine views
    >>> print(route(' _\\n|_|', 'leftup'))
    ...
"""

from __future__ import annotations

from .engine import turn as _engine_turn
from .pose import Pose, auto_depth as _auto_depth, render_pose

__all__ = ['ROUTES', 'route', 'nine_routes', 'contact_sheet']

#: The nine routes in reading order of the 3x3 grid.
ROUTES = ('leftup', 'up', 'rightup', 'left', 'center', 'right',
          'leftdown', 'down', 'rightdown')

#: The box-camera pose for each route (left/right use the engine's
#: byte-exact shear instead).  'center' is the straight-on view with
#: the top face receding down -- every cell of the 3x3 gallery is a
#: 3D view, none is the flat 2D art.
ROUTE_POSES = {
    'center': Pose(lean=0.5, rise=1, side='none', reach=0.5),
    'up': Pose(lean=0.5, rise=2, side='none', reach=1.0),
    'down': Pose(lean=0.5, rise=-2, side='none', reach=1.0),
    'leftup': Pose(lean=1.0, rise=2, side='right', reach=1.0),
    'rightup': Pose(lean=1.0, rise=2, side='left', reach=1.0),
    'leftdown': Pose(lean=1.0, rise=-2, side='right', reach=1.0),
    'rightdown': Pose(lean=1.0, rise=-2, side='left', reach=1.0),
}


def route(art: str, direction: str = 'center', depth: int | None = None,
          style: str = 'auto') -> str:
    """Render *art* viewed from one of the nine routes.

    Args:
        art: The ASCII art as a plain string.
        direction: One of :data:`ROUTES`.
        depth: Depth of the 3D box.  ``None`` picks a depth that
            scales with the art (substantial, as the docs demand).
        style: ``'auto'`` uses the engine shear for left/right and
            the box camera everywhere else; ``'engine'`` and
            ``'pose'`` force one renderer (``'engine'`` only
            supports left/right/center).  ``'wire'`` is an alias
            for ``'pose'`` (the old wireframe name).

    Returns:
        The rendered ASCII art.

    Raises:
        ValueError: If *direction* or *style* is unknown.
    """
    if direction not in ROUTES:
        raise ValueError(
            f'direction must be one of {ROUTES}, not {direction!r}')
    if style not in ('auto', 'engine', 'pose', 'wire'):
        raise ValueError(f"style must be 'auto', 'engine' or 'pose', "
                         f'not {style!r}')

    if direction in ('left', 'right'):
        if style == 'pose':
            # the mirrored turn as a pose (same look, pose pipeline)
            lean = 1.0 if direction == 'left' else -1.0
            side = 'right' if direction == 'left' else 'left'
            return render_pose(art, Pose(lean=lean, rise=1, side=side,
                                         reach=1.0), depth=depth)
        return _engine_turn(art, direction=direction, depth=depth or
                            _auto_depth(art))

    if direction == 'center':
        if style == 'engine':
            return '\n'.join(line.rstrip() for line in
                             art.strip('\n').split('\n'))
        # the straight-on view with the top face going down
        return render_pose(art, ROUTE_POSES['center'], depth=depth)

    if style == 'engine':
        raise ValueError(
            "the 'engine' style only supports left/right/center; "
            'use style="pose" or "auto" for the other routes')

    return render_pose(art, ROUTE_POSES[direction], depth=depth)


def nine_routes(art: str, depth: int | None = None,
                style: str = 'auto') -> dict[str, str]:
    """Render *art* from all nine routes at once.

    Args:
        art: The ASCII art as a plain string.
        depth: Depth of the 3D box (``None`` = auto).
        style: See :func:`route`.

    Returns:
        A dict mapping every route name to its rendered art, in the
        reading order of the 3x3 route grid (leftup, up, rightup,
        left, center, ...).
    """
    return {name: route(art, name, depth=depth, style=style)
            for name in ROUTES}


def contact_sheet(art: str, depth: int | None = None,
                  style: str = 'auto', gap: int = 3) -> str:
    """Render all nine routes as one labelled 3x3 gallery.

    The sheet is laid out like the route grid::

        leftup | up | rightup
        left | center | right
        leftdown | down | rightdown

    Args:
        art: The ASCII art as a plain string.
        depth: Depth of the 3D box (``None`` = auto).
        style: See :func:`route`.
        gap: Blank columns between the gallery cells.

    Returns:
        The contact sheet as a single string.
    """
    routes = nine_routes(art, depth=depth, style=style)
    order = [('leftup', 'up', 'rightup'),
             ('left', 'center', 'right'),
             ('leftdown', 'down', 'rightdown')]
    # One width per gallery column (the widest cell of that column),
    # so every line of the sheet has the same length.
    col_width = [0, 0, 0]
    cells_by_row = []
    for row_routes in order:
        cells = []
        for i, name in enumerate(row_routes):
            cell = routes[name].split('\n')
            label = f'-- {name} --'
            cell = [label] + cell
            cells.append(cell)
            col_width[i] = max(col_width[i],
                               max(len(line) for line in cell))
        height = max(len(cell) for cell in cells)
        for i, cell in enumerate(cells):
            cell.extend([' ' * col_width[i]] * (height - len(cell)))
        cells_by_row.append(cells)
    lines: list[str] = []
    for cells in cells_by_row:
        for i in range(len(cells[0])):
            lines.append((' ' * gap).join(
                cell[i].ljust(width)
                for cell, width in zip(cells, col_width)))
        lines.append('')
    return '\n'.join(lines).rstrip('\n')
