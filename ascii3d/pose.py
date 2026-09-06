"""The box camera: docs-faithful 3D poses for any viewing angle.

HOW A TURN WORKS (docs/01-Theory/02-HowToTurn.md)
--------------------------------------------------
The theory docs draw a turned box with a *shear*, not a projection::

     the art              turned left, depth 2
      __________           ___________
     |  __  __  |         /__________/  \\
     | |__||__| |         \\  __  __  \\   \\
     |__________|          \\ \\__\\\\__\\ \\  /
                            \\__________\\/

Every stroke stays ONE character on the grid: the front face rows
march sideways one column at a time, ``|`` walls become ``\\`` (or
``/``), a top face is added above and a side face closes the
silhouette.  Nothing is stretched or doubled to fake depth -- the
depth is *drawn*, as the marching ``\\`` column of the side face.

This module generalises that one drawing trick to any angle.  A
:class:`Pose` places the box on the character grid using three
numbers:

    lean   cols/row the front face rows march sideways.
           ``1`` = the docs' 45 degree turn, ``0.5`` = gentle,
           ``-1`` = turned the other way.  ``|`` walls flip to
           ``\\`` / ``/`` only at the full lean.
    rise   rows of recede per depth unit, sign = looking down (+)
           or up (-).  ``1`` = the docs' turn, ``2`` = the 'up'
           routes (a taller top face).
    side   which side face is visible ('right' / 'left' / 'none').

Every face is drawn between computed corner points with
:func:`_edge`, which rasterises a straight stroke as ONE character
per row (steep) or per column (shallow) -- the marching look of the
hand-drawn docs, with no character ever doubled or stretched.

The 360 degree spin (:mod:`ascii3d.rotation`) is a sequence of
poses around the compass.  The camera stays ABOVE the box for the
whole sweep (``rise > 0``), so every frame is a *turned* view with
the top face visible and the depth marching DOWN -- the flat,
forward, "normal" view never appears.
"""

from __future__ import annotations

import math

from .engine import mirror, normalize

__all__ = ['Pose', 'auto_depth', 'render_pose', 'turntable_pose']

# The side-face shading ramp: light (near the viewer) to dark (far
# away), docs/10-TODO's "white-gray-black from 0 to 1".  It is a
# DENSITY ramp (blank, dots, colons, X, #) so wide side faces shade
# smoothly, and it holds no / or \ so it can never pile up against
# the closure strokes.
SHADE_RAMP = ' ..::XX##'

# Characters that flip when a frame is mirrored horizontally.
_MIRROR_CHARS = str.maketrans({'/': '\\', '\\': '/'})


def auto_depth(art: str) -> int:
    """A depth that keeps the side face substantial.

    The docs are blunt: "we cant do that with 3x3 art! it should be
    at last 6x12" (02-HowToTurn) and the SimpleHead example uses
    depth 3 on a 4 row art.  A 1 deep box reads flat; the side face
    must be visible for the depth to land.
    """
    rows = normalize(art)
    return max(3, min(6, len(rows) // 2 + 1))


def _round(x: float) -> int:
    """Round half up (banker's rounding makes rows jump around)."""
    return int(math.floor(x + 0.5))


def _shear(lean: float, row: int) -> int:
    """Cols that art *row* marches sideways under *lean*.

    The docs keep the first row of the art in place and shift one
    column per row after that (their turned_width formula counts the
    shear from row 1); fractional leans halve the march.
    """
    if row <= 1:
        return 0
    return _round(lean * (row - 1))


def _wall_char(ch: str, lean: float) -> str:
    """Remap a wall stroke for a face leaning by *lean*.

    Only ``|`` changes, and only at a full 45 degree lean; a gentle
    lean marches the walls without tilting them, so every stroke
    stays a single character.
    """
    if ch == '|' and lean >= 0.99:
        return '\\'
    if ch == '|' and lean <= -0.99:
        return '/'
    return ch


# ----------------------------------------------------------------------
# canvas and strokes
# ----------------------------------------------------------------------
class _Canvas:
    """A sparse character grid (negative rows/cols are fine)."""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], str] = {}

    def put(self, row: int, col: int, ch: str) -> None:
        """Paint *ch*; later strokes win (painter's order)."""
        if ch != ' ':
            self.cells[(row, col)] = ch

    def behind(self, row: int, col: int, ch: str) -> None:
        """Paint only into a blank cell (background strokes)."""
        if ch != ' ' and (row, col) not in self.cells:
            self.cells[(row, col)] = ch

    def text(self) -> str:
        """The canvas as a block of text.

        Columns are shifted only when the drawing spills left of
        column 0 (mirrored frames); the art's own indentation is
        preserved, exactly like the engine's turned output.
        """
        if not self.cells:
            return ''
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        lo_c = min(min(cols), 0)
        grid = [[' '] * (max(cols) - lo_c + 1)
                for _ in range(max(rows) - min(rows) + 1)]
        for (r, c), ch in self.cells.items():
            grid[r - min(rows)][c - lo_c] = ch
        return '\n'.join(''.join(row).rstrip() for row in grid)


def _stroke_char(dr: float, dc: float) -> str:
    """The stroke char for a segment of slope (dr, dc)."""
    if abs(dc) < 0.45 * abs(dr):
        return '|'
    if abs(dr) < 0.45 * abs(dc):
        return '_'
    return '\\' if dr * dc > 0 else '/'


def _edge(canvas: _Canvas, start: tuple[int, int],
          end: tuple[int, int], behind: bool = True) -> None:
    """Draw a straight stroke between two grid points.

    The stroke marches ONE character per row when it is steep and
    one per column when it is shallow -- the single-stroke look of
    the docs, never a doubled run like ``\\\\\\\\``.  Shallow ``_``
    strokes sit at the bottom of a cell, so they are drawn one row
    above the geometric line.
    """
    (r0, c0), (r1, c1) = start, end
    dr, dc = r1 - r0, c1 - c0
    if dr == 0 and dc == 0:
        return
    paint = canvas.behind if behind else canvas.put
    ch = _stroke_char(dr, dc)
    if abs(dr) >= abs(dc):                        # steep: one per row
        lo, hi = (r0, r1) if r0 <= r1 else (r1, r0)
        for r in range(lo, hi + 1):
            t = (r - r0) / dr if dr else 0.0
            c = _round(c0 + dc * t)
            paint(r, c, ch)
    else:                                         # shallow: one per col
        lo, hi = (c0, c1) if c0 <= c1 else (c1, c0)
        for c in range(lo, hi + 1):
            t = (c - c0) / dc if dc else 0.0
            r = _round(r0 + dr * t)
            if ch == '_':
                r -= 1                             # underscore: bottom
            paint(r, c, ch)


# ----------------------------------------------------------------------
# faces
# ----------------------------------------------------------------------
def _face(canvas: _Canvas, rows: list[str], lean: float, base: int,
          behind: bool) -> None:
    """Draw the main face: the art sheared by *lean* at row *base*."""
    paint = canvas.behind if behind else canvas.put
    for r, line in enumerate(rows):
        off = _shear(lean, r)
        for c, ch in enumerate(line):
            if ch != ' ':
                paint(base + r, off + c, _wall_char(ch, lean))


def _top_face(canvas: _Canvas, rows: list[str], lean: float, rise: int,
              depth: int, base: int, reach: float = 1.0) -> None:
    """The top face: the art's row 0 extruded up by ``rise x depth``.

    Corners (right-leaning turn, depth 3 -- the docs' drawing)::

        row 0:  ____________      back edge (row 0 of the art, on top)
        row 1: /           /\\     left edge /, corner /\\
        row 2: /           /  \\
        row 3: /___________/    \\   front edge = the art's row 0

    The back edge sits ``rise * depth`` rows above the art's row 0
    and drifts ``round(lean * (depth - 1))`` columns aside (a depth 1
    box recedes straight up, deeper boxes drift with the lean -- the
    docs' formula).  The side edges march one column per row: single
    ``/`` strokes, exactly like the hand-drawn examples.
    """
    row0 = rows[0]
    content = [c for c, ch in enumerate(row0) if ch != ' ']
    if not content:
        return
    first, last = content[0], content[-1]
    top = base - rise * depth                     # rows of recede
    span = rise * depth                           # strokes per edge
    # The back edge drifts sideways as the depth axis leans: for the
    # classic turn (rise 1) the docs' formula (a depth 1 box recedes
    # straight up); for the tall 'up' faces the drift grows with the
    # span so the 45-degree side march lands exactly on the front
    # corners and the silhouette always closes.
    if rise == 1:
        drift = _round(lean * reach * (depth - 1))
    else:
        drift = span if lean >= 0 else -span

    # back edge: the art's row 0 pushed up and aside (+ corner tile)
    for c, ch in enumerate(row0):
        if ch != ' ':
            canvas.behind(top, drift + c, ch)
    if row0[last] == '_':
        canvas.behind(top, drift + last + 1, '_')

    # front edge: the art's row 0 again, at the top of the main face
    # (the boundary between top face and front face -- visible even
    # when the main face itself is edge-on hidden)
    for c, ch in enumerate(row0):
        if ch != ' ':
            canvas.behind(base, c, ch)

    # side edges: '/' strokes marching one column per row -- the
    # docs' exact 45-degree march, from the back corners down to the
    # front corners (single characters, never doubled).
    for k in range(1, span + 1):
        canvas.behind(top + k, drift + first - k, '/')
        canvas.behind(top + k, drift + last + 1 - (k - 1), '/')


def _bottom_face(canvas: _Canvas, rows: list[str], lean: float,
                 depth: int, base: int, span: int = 1) -> None:
    """The bottom face: the art's last row extruded down (seen from
    below).  Vertical mirror of :func:`_top_face`: the floor is
    pushed down ``span * depth`` rows (2x for the 'down' routes,
    where the bottom face dominates the frame), drifted aside by the
    same amount and connected with '\\' strokes marching one column
    per row.
    """
    row_n = rows[-1]
    content = [c for c, ch in enumerate(row_n) if ch != ' ']
    if not content:
        return
    first, last = content[0], content[-1]
    length = len(rows)
    steps = span * depth
    floor = base + length - 1 + steps
    drift = steps if lean >= 0 else -steps

    for c, ch in enumerate(row_n):
        if ch != ' ':
            canvas.behind(floor, drift + c, ch)
    if row_n[last] == '_':
        canvas.behind(floor, drift + last + 1, '_')
    # side edges: clean strokes from the (sheared) front floor
    # corners down to the pushed floor corners ('\': one per row)
    front_row = base + length - 1
    shear = _shear(lean, length - 1)
    _edge(canvas, (front_row, shear + first), (floor, drift + first))
    _edge(canvas, (front_row, shear + last + 1),
          (floor, drift + last + 1))


def _side_face(canvas: _Canvas, rows: list[str], lean: float,
               depth: int, base: int, sign: int, shade: bool,
               reach: float = 1.0) -> None:
    """The visible side face, closing the silhouette.

    Corners (right side, depth 2 -- the docs' drawing)::

        row 1:                  /\\    far edge starts at the corner
        row 2:  \\  __  __  \\   \\     near edge = the art's wall
        row 3:   \\ \\  \\\\ \\ \\   \\    far edge = near + (d, -d)
        row 4:    \\ \\__\\\\__\\ \\  /    bottom closure = '/' strokes
        row 5:     \\__________\\/

    Both edges march one column per row -- single ``\\`` characters,
    never a stretched run.  With *shade* the interior gets the depth
    gradient of docs/10-TODO/01-2Sides3dRendering.md (light near,
    dark far).
    """
    length, width = len(rows), len(rows[0])
    if length < 2:
        return
    # The near edge shadows the art's bounding wall on the visible
    # side; the far edge is that wall pushed back (dx, -d) where dx
    # grows with the reach -- the exact (d, -d) offset of the docs'
    # 45 degree turn, widening as the box rotates towards edge-on.
    wall = width - 1 if sign > 0 else 0
    back = _round(depth * reach) if reach > 0 else 0

    def near(r: int) -> tuple[int, int]:
        """Near edge point at art row r (the front wall)."""
        return (base + r, _shear(lean, r) + wall)

    def far(r: int) -> tuple[int, int]:
        """Far edge point: the same wall, back cells away."""
        nr, nc = near(r)
        return (nr - depth, nc + sign * back)

    # far edge: the back wall, marching parallel to the front wall
    # (a 2 row art gives a single point -- still one stroke)
    far_start, far_end = far(1), far(length - 1)
    if far_start == far_end:
        canvas.behind(far_start[0], far_start[1], '\\')
    else:
        _edge(canvas, far_start, far_end)
    # near edge: the art's own wall (redrawn so the silhouette always
    # closes, even when the art has no wall stroke there)
    near_start, near_end = near(1), near(length - 1)
    if near_start == near_end:
        canvas.behind(near_start[0], near_start[1], '\\')
    else:
        _edge(canvas, near_start, near_end)
    # bottom closure: '/' strokes one row below the far edge's end,
    # marching one column per row up to the front face's bottom
    # corner -- always a single character per row (the docs' closure)
    (fr, fc) = far(length - 1)
    for k in range(depth):
        canvas.behind(fr + 1 + k, fc - sign * k, '/')

    if shade and depth >= 1:
        _shade_side(canvas, rows, lean, depth, base, sign, reach)


def _shade_side(canvas: _Canvas, rows: list[str], lean: float,
                depth: int, base: int, sign: int,
                reach: float = 1.0) -> None:
    """Fill the side face with the depth gradient (light to dark).

    The side face is the quad between the near wall (the art's
    bounding wall) and the far wall.  At each row of the front face
    the interior runs from the near line towards the far line,
    switching to the bottom edge line below the far edge's end.
    The SHADE_RAMP steps from light (near the viewer) to dark (far
    away) -- docs/10-TODO's "white-gray-black from 0 to 1" -- painted
    on every other column so the texture stays airy, never a solid
    noisy block.
    """
    length, width = len(rows), len(rows[0])
    wall = width - 1 if sign > 0 else 0
    back = _round(depth * reach) if reach > 0 else 0
    bottom_row = base + length - 1
    far_end_row = bottom_row - depth          # last row of the far edge
    far_end_col = wall + back + _shear(lean, length - 1)
    for row in range(base + 1, bottom_row):
        near_col = wall + _shear(lean, row - base)
        if row <= far_end_row:
            # above the far edge's end: the far line is the boundary
            bound = wall + back + _shear(lean, row - base + depth)
        else:
            # below it: the '/' closure line marches up to the corner
            steps = row - far_end_row - 1
            bound = far_end_col - sign * steps
        span = abs(bound - near_col)
        for k in range(1, span):
            if k % 2 == 0:                     # airy: every other col
                continue
            t = k / span
            idx = min(len(SHADE_RAMP) - 1,
                      int(t * (len(SHADE_RAMP) - 1) + 0.5))
            canvas.behind(row, near_col + sign * k, SHADE_RAMP[idx])


# ----------------------------------------------------------------------
# the pose
# ----------------------------------------------------------------------
class Pose:
    """A camera position, expressed on the character grid.

    Attributes:
        lean: Cols per row the front face rows march sideways.  +1
            turns left (rows march right, ``|`` becomes ``\\``),
            -1 turns right, 0 faces the viewer head on.
        rise: Rows of recede per depth unit; +1 is the docs' turn,
            +2 looks down harder, -1 looks up from below.
        side: The visible side face: ``'right'``, ``'left'`` or
            ``'none'``.
        face: The main face content: ``'front'`` draws the art,
            ``'back'`` draws the hull outline, ``'hidden'`` draws
            neither (the box is edge on).
        shade: Fill the side face with the depth gradient.
        reach: How far the depth axis reaches sideways, 0..1.4.
            1.0 is the docs' 45 degree turn; smaller = nearly face
            on, larger = nearly edge on.  The spin grows it as the
            box rotates so the side face visibly widens.
    """

    __slots__ = ('lean', 'rise', 'side', 'face', 'shade', 'reach')

    def __init__(self, lean: float = 1.0, rise: int = 1,
                 side: str = 'right', face: str = 'front',
                 shade: bool = True, reach: float = 1.0):
        self.lean = lean
        self.rise = rise
        self.side = side
        self.face = face
        self.shade = shade
        self.reach = reach

    def __repr__(self) -> str:
        return (f'Pose(lean={self.lean:+g}, rise={self.rise:+d}, '
                f'side={self.side!r}, face={self.face!r}, '
                f'reach={self.reach:g})')


def render_pose(art: str, pose: Pose, depth: int | None = None,
                shade: bool | None = None) -> str:
    """Render *art* as a 3D box seen from *pose*.

    Faces are painted back to front: top/bottom face and side face
    first (background strokes), the main face last, so the art's own
    strokes always win.  A *left* turn is rendered as a mirrored
    right turn -- the same trick the engine uses for
    ``turn_right`` -- so all the geometry is proven in one
    direction only.

    Args:
        art: The ASCII art (the front face of the box).
        pose: The camera position (see :class:`Pose`).
        depth: Box depth in cells (``None`` = :func:`auto_depth`).
        shade: Override the pose's side-face shading choice.

    Returns:
        The rendered frame as a string.
    """
    if shade is not None and shade != pose.shade:
        pose = Pose(lean=pose.lean, rise=pose.rise, side=pose.side,
                    face=pose.face, shade=shade, reach=pose.reach)
    if pose.side == 'left' or (pose.side == 'none' and pose.lean < 0):
        # A left turn is the mirror image of a right turn: mirror
        # the art, render in the proven right-turn geometry, then
        # mirror the frame back -- cell by cell, so every stroke
        # stays exactly on the character grid.
        flipped = Pose(lean=abs(pose.lean), rise=pose.rise,
                       side='right' if pose.side == 'left' else 'none',
                       face=pose.face, shade=pose.shade,
                       reach=pose.reach)
        canvas = _render_canvas(mirror(art), flipped, depth)
        return _mirror_canvas(canvas).text()
    return _render_canvas(art, pose, depth).text()


def _render_canvas(art: str, pose: Pose,
                   depth: int | None = None) -> _Canvas:
    """Render *art* at *pose* into a canvas (right-turn geometry).

    The pose must lean right / show the right side; the mirrored
    half is handled by :func:`render_pose`.
    """
    rows = normalize(art)
    depth = auto_depth(art) if depth is None else depth
    depth = max(depth, 1)
    length = len(rows)
    top_span = depth * pose.rise if pose.rise > 0 else 0
    base = top_span                              # main face top row

    main = (rows if pose.face == 'front'
            else normalize(mirror(art)) if pose.face == 'back'
            else [])
    # The back face shows the art's own strokes, mirrored -- "the
    # engine would need to mirror the strokes and swap the faces"
    # (docs/01-Theory/03-LookAnywhere.md, Behind) -- so the spin
    # keeps readable content through the whole 360 degrees.

    canvas = _Canvas()
    if pose.rise > 0:
        _top_face(canvas, main or rows, pose.lean, pose.rise, depth,
                  base, pose.reach)
    if pose.rise < 0:
        _bottom_face(canvas, main or rows, pose.lean, depth, base,
                     span=abs(pose.rise))
    if pose.side != 'none' and length >= 2:
        _side_face(canvas, main or rows, pose.lean, depth, base,
                   1, pose.shade, pose.reach)
    if main:
        _face(canvas, main, pose.lean, base, behind=False)
    return canvas


def _mirror_canvas(canvas: _Canvas) -> _Canvas:
    """Mirror a canvas: flip the columns and the / and \\ strokes.

    Mirroring at the cell level (instead of on the text) keeps every
    frame exactly on the grid -- no padding or dedent surprises.
    The shading ramp (``. : X #``) is mirror-neutral by design.
    """
    if not canvas.cells:
        return canvas
    max_col = max(c for _, c in canvas.cells)
    out = _Canvas()
    for (row, col), ch in canvas.cells.items():
        out.put(row, max_col - col, ch.translate(_MIRROR_CHARS))
    return out


# ----------------------------------------------------------------------
# the turntable
# ----------------------------------------------------------------------
def turntable_pose(theta: float, pitch: float = 30.0) -> Pose:
    """The pose of a box yawed *theta* degrees on a turntable.

    The camera stays ABOVE the box for the whole sweep (the pitch
    never flips), so every frame is a *turned* view -- the top face
    is always visible, the depth always marches down.  The flat
    forward view never appears: near face-on the box keeps a gentle
    half lean and a visible top face.

    The sweep is continuous by construction: the visible side wall
    is the right one for theta < 180 and the left one after (the
    switch happens exactly where the side face is edge-on and
    invisible), and the lean keeps its sign inside each half turn.

    Args:
        theta: Yaw in degrees (0 = the art faces the viewer, 90 =
            edge on, 180 = the back hull faces the viewer).
        pitch: Constant downward look in degrees; above 40 the top
            face grows (rise 2).  Sign is forced positive.

    Returns:
        The snapped :class:`Pose` for that angle.
    """
    theta %= 360.0
    rise = 2 if abs(pitch) > 40 else 1

    # Main face: the art for the front half turn, the hull for the
    # back half.  Exactly edge on (within 15 degrees) the face is
    # hidden: only the top face and the shaded side face remain.
    edge_on = min(abs(theta - 90.0), abs(theta - 270.0)) < 15.0
    back_half = 90.0 < theta < 270.0
    face = 'hidden' if edge_on else ('back' if back_half else 'front')

    # The lean: tan of the angle to the nearest face-on direction
    # (0 or 180), clamped to the docs' 45 degree look and snapped to
    # half steps so the strokes stay on the grid.  The sign is
    # stable inside each half turn: the rows keep marching the same
    # way as the box rotates towards edge on.
    rel = (180.0 - theta) if back_half else (
        theta - 360.0 if theta > 180.0 else theta)
    tan = math.tan(math.radians(rel))
    lean = max(-1.0, min(1.0, tan))
    lean = _round(lean * 2) / 2.0

    # The reach of the depth axis grows with |sin theta|: face on it
    # is 0 (no side face visible), at the docs' 45 degree turn it is
    # 1, and edge on it maxes out at 1.4 so the side face keeps
    # widening as the box rotates.  Snapped to tenths to keep the
    # grid stable across frames.
    reach = min(1.4, abs(math.sin(math.radians(theta))) / 0.7071)
    reach = round(max(reach, 0.0) * 10) / 10.0
    if 0.05 < reach < 0.5:
        reach = 0.5   # near face on: keep a thin side sliver visible

    # The visible side wall: the right one while theta sweeps the
    # front half (0..180), the left one after -- the switch lands
    # where the side face is edge on and invisible.
    side = 'right' if theta < 180.0 else 'left'
    if reach < 0.05:
        side = 'none'          # exactly face on: no side face at all

    if face == 'hidden':
        # Edge on: the rows march at the full 45 degree lean.
        lean = 1.0 if lean >= 0 else -1.0
        return Pose(lean=lean, rise=rise, side=side, face='hidden',
                    reach=max(reach, 1.0))

    # Around face-on the lean is gentle, but never fully flat: a
    # spin frame always shows SOME turn plus the top face receding
    # down -- the docs' turned look, never the flat forward art.
    if abs(lean) < 0.5:
        lean = 0.5 if lean >= 0 else -0.5
    return Pose(lean=lean, rise=rise, side=side, face=face, reach=reach)
