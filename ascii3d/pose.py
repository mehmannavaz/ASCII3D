"""The box camera: docs-faithful 3D poses for any viewing angle.

HOW A TURN WORKS (docs/01-Theory/02-HowToTurn.md)
--------------------------------------------------
The theory docs draw a turned box with a *shear*, not a projection::

     the art              turned left, depth 3
      __________            _______
     |  __  __  |          /      /\\
     | |__||__| |         /______/    \\
     |__________|        \\  __  __ \\  . X  /
                          \\\\ \\\\_\\\\\\\\__\\\\ \\\\/

Every stroke stays ONE character on the grid: the front face rows
march sideways one column at a time, ``|`` walls become ``\\``
(or ``/``), a top face is added above and a side face closes the
silhouette.  Nothing is stretched or doubled to fake depth -- the
depth is *drawn*, as the marching strokes of the side face.

THE ONE GEOMETRY (why the corners always close)
--------------------------------------------------
Every face of the box is derived from **one depth vector**

    delta = (+k, -k)        (k = depth in cells, up-right 45deg)

so the faces share their corners *by construction*:

* the **top face** is the art's row 0 pushed up by delta (rise 1);
  its left/right edges are ``/`` chains marching one column per row,
  the back edge is the front edge drifted (T-1, -T), closed with one
  corner tile -- exactly the hand drawn docs example;
* the **side face**'s near edge is the art's right wall, the far
  edge is the near edge pushed back by delta, and the bottom
  closure marches ``/`` one column per row from the far corner down
  to the near corner -- landing exactly ON the face's bottom-right
  corner cell, never one short (the old renderer's gap bug);
* the **shading** fills the quad between the near line and the
  (far line | closure line) with the docs' dithered ramp
  ``. : X #`` (``docs/10-TODO/01-2Sides3dRendering.md``), light
  near the viewer, dark far away.

At ``Pose(lean=1, rise=1, side='right', reach=1)`` the construction
reduces cell-for-cell to :func:`ascii3d.engine.turn` -- the byte
exact docs renderer (pinned by ``test/test_pose.py``).

THE 360 DEGREE SPIN (:func:`turntable_pose`)
--------------------------------------------------
The camera stays ABOVE the box for the whole sweep (the pitch never
flips), so every frame is a *turned* view -- the top face is always
visible and the depth always marches DOWN ("only going down", never
looking up).  The flat, forward, "normal" view never appears: near
face-on the box keeps a gentle half lean and a visible top face.

The sweep walks the four honest quadrants of the turntable (the
visible face, the march direction and the visible side wall follow
the physical yaw)::

    theta in [0,  90)   the art,   rows march right, right wall
    theta in [90, 180)  the mirrored art, rows march left, left wall
    theta in [180,270)  the mirrored art, rows march right, right wall
    theta in [270,360)  the art,   rows march left, left wall

The face content mirrors exactly where the box passes edge-on (the
viewer starts seeing the back, which reads mirrored -- "mirror the
strokes and swap the faces", docs/01-Theory/03-LookAnywhere.md), and
the side wall switches where it is edge-on and thinnest.  Every
frame is a closed box silhouette: the front face's bottom edge is
never dropped, so no frame is ever a hollow funnel.
"""

from __future__ import annotations

import math

from .engine import mirror, normalize

__all__ = ['Pose', 'auto_depth', 'render_pose', 'turntable_pose']

# The docs' dithered side-face ramp (docs/10-TODO's "white-gray-black
# from 0 to 1" drawn like the hand examples: the ramp chars sit on
# every other column, the spaces between them are the lightest
# shade).  Light (near the viewer) to dark (far away).
SHADE_RAMP = '.:X#'

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
# canvas
# ----------------------------------------------------------------------
class _Canvas:
    """A sparse character grid (negative rows/cols are fine)."""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], str] = {}

    def put(self, row: int, col: int, ch: str) -> None:
        """Paint *ch* unconditionally (the front face strokes).

        Cells left of the grid are dropped, exactly like the
        engine's bounds check -- a left chain that would start at
        column -1 (an art whose row 0 starts at column 0) is simply
        not drawn, which keeps the mirrored frames free of stray
        orphan strokes.
        """
        if ch != ' ' and row >= 0 and col >= 0:
            self.cells[(row, col)] = ch

    def protect(self, row: int, col: int, ch: str) -> None:
        """Paint *ch* only over a blank or ``_`` (the box edges).

        The engine's rule: the silhouette edges may eat a trailing
        underscore but never the art's real strokes.
        """
        if (ch != ' ' and row >= 0 and col >= 0
                and self.cells.get((row, col), ' ') in (' ', '_')):
            self.cells[(row, col)] = ch

    def behind(self, row: int, col: int, ch: str) -> None:
        """Paint only into a blank cell (background strokes)."""
        if ch != ' ' and row >= 0 and col >= 0 \
                and (row, col) not in self.cells:
            self.cells[(row, col)] = ch

    def text(self) -> str:
        """The canvas as a block of text (trailing blanks trimmed)."""
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


def _mirror_canvas(canvas: _Canvas) -> _Canvas:
    """Mirror a canvas: flip the columns and the / and \\ strokes."""
    if not canvas.cells:
        return canvas
    max_col = max(c for _, c in canvas.cells)
    out = _Canvas()
    for (row, col), ch in canvas.cells.items():
        out.put(row, max_col - col, ch.translate(_MIRROR_CHARS))
    return out


# ----------------------------------------------------------------------
# the one corner-consistent box construction (right-turn geometry)
# ----------------------------------------------------------------------
def _draw_box(canvas: _Canvas, rows: list[str], lean: float,
              rise: int, k: int, draw_side: bool, shade: bool) -> None:
    """Draw the turned box: face, top/bottom face, side face.

    All faces derive from one depth per unit -- ``(+k, -k)`` seen
    from above (rise > 0) or ``(+k, +k)`` seen from below
    (rise < 0) -- so every corner is shared and the silhouette
    closes by construction:

    * the face rows march by ``_shear(lean, r)``;
    * the top face (rise > 0): ``/`` chains of T = k*rise cells,
      the back edge at (base-T, a+T-1 .. b+T) plus the closing
      corner tile;
    * the bottom face (rise < 0): the same construction mirrored
      below the face -- ``\\`` chains, the far floor edge at
      (base+L-1+T, ...), drifting the same way the face marches
      (exactly the hand drawn 'down' example of LookAnywhere);
    * the side face: near edge = the art's right wall, far edge =
      near + the depth vector, closures marching ``/`` (above) or
      shared with the floor's right chain (below);
    * the shading fills the side-face quad with the docs' dithered
      ramp, bounded by the near line and the far/closure lines.

    Args:
        canvas: The sparse grid to paint on.
        rows: The normalized art (the front face), >= 1 row.
        lean: The shear, 0..1 (1 = the docs' 45 degree turn).
        rise: Rows of face recede per depth unit; positive looks
            down on the box (the top face), negative looks up from
            below (the bottom face).
        k: The depth in cells (the side face's width and the
            recede per rise unit).
        draw_side: Draw the right side face and its closures.
        shade: Fill the side face with the depth gradient.
    """
    if rise < 0:
        _draw_box_below(canvas, rows, lean, -rise, k, draw_side, shade)
        return

    L, W = len(rows), len(rows[0])
    T = k * rise                       # top face height in rows
    base = T                           # the art's row 0 lands here
    row0 = rows[0]
    content = [c for c, ch in enumerate(row0) if ch != ' ']
    a = content[0] if content else 0   # first stroke col of row 0
    b = content[-1] if content else W - 1

    # -- front face: the art sheared, walls -> \ at the full lean ----
    for r, line in enumerate(rows):
        off = _shear(lean, r)
        for c, ch in enumerate(line):
            if ch != ' ':
                canvas.put(base + r, off + c, _wall_char(ch, lean))

    # -- top face: the art's row 0 extruded up by (T-1, -T) ----------
    # left chain: T '/' cells marching up-right from the front edge's
    # left closure (base, a-1) to the back edge's left end.
    for i in range(T):
        canvas.protect(base - i, a - 1 + i, '/')
    # right chain: T '/' cells from the front edge's right closure
    # (base, b+1) up to the back edge's right end; its top cell sits
    # directly above the back edge's corner tile.
    for i in range(T):
        canvas.protect(base - i, b + 1 + i, '/')
    # back edge: the art's row 0 pushed up T rows and drifted T-1
    # cols, plus one closing corner tile (the docs' extra floor
    # tile, `put(0, last + d, '_')` in the engine).
    for c, ch in enumerate(row0):
        if ch != ' ':
            canvas.behind(base - T, T - 1 + c, ch)
    if row0[b] == '_':
        canvas.behind(base - T, T - 1 + b + 1, '_')

    if not draw_side or L < 2:
        return

    # -- side face: the right wall of the box, seen from the right --
    def near(r: int) -> tuple[int, int]:
        """Near edge cell at art row r (the front wall)."""
        return (base + r, W - 1 + _shear(lean, r))

    def far(r: int) -> tuple[int, int]:
        """Far edge cell: the same wall pushed back (+k, -k)."""
        nr, nc = near(r)
        return (nr - k, nc + k)

    # near edge: parallel to the face's right wall (filled in so the
    # silhouette closes even when the art has no wall stroke there)
    for r in range(1, L):
        nr, nc = near(r)
        canvas.protect(nr, nc, '\\')
    # far edge: the near wall pushed back, marching parallel to it
    for r in range(1, L):
        fr, fc = far(r)
        canvas.protect(fr, fc, '\\')
    # bottom closure: k '/' cells from below the far edge's bottom
    # end marching down-left, ending exactly one col right of the
    # face's bottom-right corner (the docs' `\/` ending).
    fr, fc = far(L - 1)
    for m in range(k):
        canvas.put(fr + 1 + m, fc - m, '/')

    if not shade:
        return
    _shade_side(canvas, rows, lean, k, base)


def _draw_box_below(canvas: _Canvas, rows: list[str], lean: float,
                    rise: int, k: int, draw_side: bool,
                    shade: bool) -> None:
    r"""Draw the box seen from below: face, bottom face, side face.

    The vertical mirror of the classic construction, drawn directly
    (not by flipping the frame) so the face keeps marching the pose's
    way and the floor drifts the same way it marches -- exactly the
    hand drawn 'down' example of ``docs/01-Theory/03-LookAnywhere.md``:

        __________
       |          |
        |          |
         |__________|\
          \           \
          ...
              |__________|

    * the floor's ``\\`` chains march down-right from the face's
      bottom corners, T = k*rise cells each;
    * the far floor edge is the art's last row pushed down T rows
      and drifted T-1 cols, plus the closing corner tile;
    * the side face's far edge is the near wall pushed DOWN by the
      depth (below the camera), its bottom closing on the floor's
      right chain -- the shared corner.
    """
    L, W = len(rows), len(rows[0])
    T = k * rise                       # floor depth in rows
    base = 0                           # no top face: the art starts here
    row_n = rows[-1]
    bottom = base + L - 1              # the face's bottom row
    shear_n = _shear(lean, L - 1)      # the bottom row's shear
    content = [c for c, ch in enumerate(row_n) if ch != ' ']
    an = content[0] if content else 0  # first stroke col of last row
    bn = content[-1] if content else W - 1

    # -- front face: the art sheared, walls -> \ at the full lean ----
    for r, line in enumerate(rows):
        off = _shear(lean, r)
        for c, ch in enumerate(line):
            if ch != ' ':
                canvas.put(base + r, off + c, _wall_char(ch, lean))

    # -- bottom face (the floor): the art's last row extruded down --
    # left chain: '\' cells marching down-right from below the face's
    # bottom-left corner (the docs' down example starts the floor's
    # left edge one row under the bottom row), closing on the far
    # floor's left end.
    for i in range(1, T):
        canvas.protect(bottom + i, an + shear_n - 1 + i, '\\')
    # right chain: '\' cells from the face's bottom-right wall down
    # to the far floor's corner tile; the first k cells coincide
    # with the side face's far edge (the shared corner edge), the
    # last one lands exactly on the far floor's corner.
    for i in range(1, T + 1):
        canvas.protect(bottom + i, bn + shear_n + i, '\\')
    # far floor edge: the art's last row pushed down T rows and
    # drifted T-1 cols, plus the closing corner tile.
    for c, ch in enumerate(row_n):
        if ch != ' ':
            canvas.behind(bottom + T, shear_n + T - 1 + c, ch)
    if row_n[bn] == '_':
        canvas.behind(bottom + T, shear_n + T - 1 + bn + 1, '_')

    if not draw_side or L < 2:
        return

    # -- side face: the right wall of the box, seen from below -----
    def near(r: int) -> tuple[int, int]:
        return (base + r, W - 1 + _shear(lean, r))

    def far(r: int) -> tuple[int, int]:
        """Far edge cell: the same wall pushed down (+k, +k) --
        below the camera the depth recedes DOWN."""
        nr, nc = near(r)
        return (nr + k, nc + k)

    # near edge: the face's right wall (filled so the silhouette
    # closes even without a wall stroke there)
    for r in range(1, L):
        nr, nc = near(r)
        canvas.protect(nr, nc, '\\')
    # top closure: k '\' cells from the near edge's top end down to
    # the far edge's top end (the box's top-right edge seen from
    # below), each one col right per row.
    nr, nc = near(1)
    for i in range(k):
        canvas.protect(nr + i, nc + i, '\\')
    # far edge: the near wall pushed down, marching parallel to it
    for r in range(1, L):
        fr, fc = far(r)
        canvas.protect(fr, fc, '\\')
    # the far edge's bottom end lands exactly on the floor's right
    # chain (the shared corner) -- nothing else to close.

    if not shade:
        return
    _shade_side_below(canvas, rows, lean, k, base)


def _shade_side(canvas: _Canvas, rows: list[str], lean: float,
                k: int, base: int) -> None:
    """Fill the side face with the docs' dithered depth gradient.

    The region is the side-face quad: bounded left by the top face's
    right chain (above the face) and the near wall (beside the
    face), bounded right by the far edge (above its end) and the
    bottom closure (below it) -- the same boundary lines the engine
    uses, so the ramp never escapes the drawn strokes.

    The ramp is the docs' hand drawn ``. : X #``: the shade chars
    sit on every other column starting right at the near wall, the
    spaces between them are the lightest level, light near the
    viewer and dark far away.
    """
    L, W = len(rows), len(rows[0])
    row0 = rows[0]
    content = [c for c, ch in enumerate(row0) if ch != ' ']
    b = content[-1] if content else W - 1
    top_chain_col = lambda row: b + 1 + (base - row)   # right chain
    near_col = lambda row: W - 1 + _shear(lean, row - base)
    far_row_end = base + L - 1 - k                      # far edge end
    far_col = lambda row: W - 1 + _shear(lean, row - base + k) + k
    # the closure line: '/' cells at (base+L-k+m, wf-m)
    wf = W - 1 + _shear(lean, L - 1) + k
    close_col = lambda row: wf - (row - (base + L - k))

    for row in range(base + 1 - k, base + L):
        if row <= base:
            left = top_chain_col(row)
        else:
            left = near_col(row)
        if row <= far_row_end:
            right = far_col(row)
        else:
            right = close_col(row)
        span = right - left
        # The dark end of the ramp (X, #) only appears on wide
        # strips -- the docs' roomy-scale -- so a narrow strip
        # never shows a lone dark char pinned against its edge.
        ramp = SHADE_RAMP[:max(2, min(4, span - 4))]
        for j in range(1, span):
            # j odd carries the ramp char (the docs' dither), its
            # index stretched proportionally across the strip so
            # a span-8 strip reproduces the hand drawn '. : X #'.
            idx = (j - 1) * len(ramp) // max(span - 1, 1)
            ch = ' ' if j % 2 == 0 else ramp[idx]
            canvas.behind(row, left + j, ch)


def _shade_side_below(canvas: _Canvas, rows: list[str], lean: float,
                      k: int, base: int) -> None:
    """Fill the below-view side face with the dithered gradient.

    The quad is bounded left by the near wall (beside the face) and
    the floor's right chain (below it), bounded right by the top
    closure (above the far edge) and the far edge -- the vertical
    mirror of :func:`_shade_side`'s boundaries.
    """
    L, W = len(rows), len(rows[0])
    near_col = lambda row: W - 1 + _shear(lean, row - base)
    near_top = base + 1
    far_top_row = near_top + k
    top_edge_col = lambda row: near_col(near_top) + (row - near_top)
    far_col = lambda row: W - 1 + _shear(lean, row - base - k) + k
    # the floor's right chain line: '\' at (bottom+i, bn+shear_n+i)
    row_n = rows[-1]
    content = [c for c, ch in enumerate(row_n) if ch != ' ']
    bn = content[-1] if content else W - 1
    shear_n = _shear(lean, L - 1)
    floor_col = lambda row: bn + shear_n + (row - (base + L - 1))

    for row in range(near_top, base + L - 1 + k):
        if row <= base + L - 1:
            left = near_col(row)
        else:
            left = floor_col(row)
        if row < far_top_row:
            right = top_edge_col(row)
        else:
            right = far_col(row)
        span = right - left
        ramp = SHADE_RAMP[:max(2, min(4, span - 4))]
        for j in range(1, span):
            idx = (j - 1) * len(ramp) // max(span - 1, 1)
            ch = ' ' if j % 2 == 0 else ramp[idx]
            canvas.behind(row, left + j, ch)


# ----------------------------------------------------------------------
# the pose
# ----------------------------------------------------------------------
class Pose:
    """A camera position, expressed on the character grid.

    Attributes:
        lean: Cols per row the front face rows march sideways.  +1
            turns left (rows march right, ``|`` becomes ``\\``),
            -1 turns right, 0 faces the viewer head on.  The sign
            also picks the construction: a negative lean renders as
            the mirror image of the positive one.
        rise: Rows of top-face recede per depth unit; +1 is the
            docs' turn, +2 looks down harder ('up' routes), -1/-2
            look up from below ('down' routes, the bottom face).
        side: The visible side face: ``'right'``, ``'left'`` or
            ``'none'``.  Must agree with the lean's sign (right
            wall with a right march).
        face: The main face content: ``'front'`` draws the art,
            ``'back'`` draws its mirror (the back of the box).
        shade: Fill the side face with the depth gradient.
        reach: How far the depth axis reaches, as a fraction of the
            docs' 45 degree turn (1.0 = the classic turn; the spin
            grows it towards edge-on and shrinks it near face-on).
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

    The box is drawn with the single-geometry construction of
    :func:`_draw_box` (every corner shared, the silhouette closed).
    A *left* turn is rendered as the mirrored right turn (the
    engine's proven trick); a *below* camera (``rise < 0``) is drawn
    directly with the bottom-face construction -- the art always
    reads right-side up and the floor drifts the way the rows
    march, like the hand drawn 'down' example.

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
    halves are handled by :func:`render_pose`.
    """
    rows = normalize(art)
    depth = auto_depth(art) if depth is None else depth
    depth = max(depth, 1)
    # The side face's width and the top face's height scale with the
    # reach: 1.0 is the docs' classic turn, larger widens the side
    # face towards edge-on, smaller keeps a sliver near face-on.
    # The floor of 2 (capped by the depth) keeps even the face-on
    # frames a visible box -- the docs' "never the flat view".
    k = max(min(2, depth), _round(depth * max(pose.reach, 0.0)))

    main = (rows if pose.face == 'front'
            else normalize(mirror(art)))
    # The back face shows the art's own strokes, mirrored -- "the
    # engine would need to mirror the strokes and swap the faces"
    # (docs/01-Theory/03-LookAnywhere.md, Behind) -- so the spin
    # keeps readable content through the whole 360 degrees.

    canvas = _Canvas()
    _draw_box(canvas, main, abs(pose.lean), pose.rise, k,
              draw_side=pose.side == 'right' and len(main) >= 2,
              shade=pose.shade)
    return canvas


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

    The sweep walks the four honest quadrants of the turntable --
    which face is visible, which way its rows march and which side
    wall shows all follow the physical yaw::

        [0, 90)    the art,        march right, right wall
        [90, 180)  mirrored art,   march left,  left wall
        [180,270)  mirrored art,   march right, right wall
        [270,360)  the art,        march left,  left wall

    The content mirrors exactly where the box passes edge-on (the
    back view reads mirrored) and the side wall switches where it is
    thinnest, so the sweep is as continuous as the shear style
    allows -- and every frame is a closed box.

    Args:
        theta: Yaw in degrees (0 = the art faces the viewer, 90 =
            edge on, 180 = the back faces the viewer).
        pitch: Constant downward look in degrees; above 40 the top
            face grows (rise 2).  Sign is forced positive.

    Returns:
        The snapped :class:`Pose` for that angle.
    """
    theta %= 360.0
    rise = 2 if abs(pitch) > 40 else 1

    # Which face the viewer sees, and which way its rows march:
    # the front for the first and last quarter, the (mirrored) back
    # in between; the march flips at each edge-on crossing (90 and
    # 270) exactly where the visible face swaps -- the honest
    # behaviour of a rotating box seen through a shear camera.
    quadrant = int(theta // 90) % 4
    face = 'back' if quadrant in (1, 2) else 'front'
    march_right = quadrant in (0, 2)
    side = 'right' if march_right else 'left'

    # The lean: tan of the angle to the nearest face-on direction
    # (0 or 180 degrees), clamped to the docs' 45 degree look and
    # snapped to half steps so the strokes stay on the grid.
    tilt = theta % 180.0
    tilt = min(tilt, 180.0 - tilt)
    tan = math.tan(math.radians(tilt))
    lean = max(0.5, min(1.0, tan))
    lean = _round(lean * 2) / 2.0

    # The reach of the depth axis: the projected width of the side
    # face, D*sqrt(2)*|sin theta| -- 0 at face-on, the docs' full
    # turn at 45 degrees, widest at edge-on.  Snapped to tenths.
    reach = math.sqrt(2.0) * abs(math.sin(math.radians(theta)))
    reach = round(reach * 10) / 10.0

    return Pose(lean=lean if march_right else -lean, rise=rise,
                side=side, face=face, reach=reach)
