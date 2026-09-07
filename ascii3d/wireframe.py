"""A tiny 3D wireframe renderer that speaks ASCII.

This module is the geometric heart of the "look anywhere" features
(``docs/01-Theory/03-LookAnywhere.md``): instead of faking a turn with
the shear trick of :mod:`ascii3d.engine`, we

1. parse the art into 2D line segments (every ``_``, ``|``, ``/`` and
   ``\\`` stroke becomes a segment),
2. extrude the segments along the depth axis so the art becomes the
   front face of a real 3D box,
3. rotate the box around the Y (yaw) and X (pitch) axes by any angle,
   and
4. project and rasterize the segments back into ASCII characters with
   a painter's algorithm (near strokes overwrite far ones).

The same renderer also draws the theoretic meshes of
:mod:`ascii3d.theory` and powers the 360 degree rotation animation of
:mod:`ascii3d.rotation`.

Direction convention (matching the "look anywhere" theory): a *route*
is where the **viewer** stands.  ``route='left'`` means the camera is
to the left of the art, so the *left* side face becomes visible.  This
is the mirror of the engine's ``turn`` functions, where the *art*
turns (``turn_left`` reveals the right face); both conventions are
documented in ``docs/02-Usage/01-routes.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    'Segment',
    'art_segments',
    'merge_strokes',
    'extrude_segments',
    'rotate',
    'project',
    'rasterize',
    'render_segments',
    'render_art',
    'render_mesh',
    'mesh_segments',
]

# Characters a stroke can be parsed from.
STROKE_CHARS = '_|/\\'

# Aspect ratio of a character cell (height / width) in a terminal.
CELL_ASPECT = 0.5


# ----------------------------------------------------------------------
# geometry types
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Segment:
    """A 3D line segment from ``start`` to ``end`` (numpy arrays)."""

    start: np.ndarray
    end: np.ndarray

    @property
    def midpoint(self) -> np.ndarray:
        return (self.start + self.end) / 2.0


def art_segments(art: str) -> list[Segment]:
    """Parse an ASCII *art* into 3D segments.

    Every stroke character becomes one unit segment in screen cell
    coordinates (x growing right, y growing *down*, one unit per
    character cell):

    =========  =====================
    character  segment
    =========  =====================
    ``_``      bottom edge of the cell
    ``|``      vertical, middle of the cell
    ``/``      bottom-left to top-right
    ``\\``     top-left to bottom-right
    =========  =====================

    The cell coordinates are converted to world coordinates with
    ``y_world = -2 * y_cell``: the flip puts the first art row on top
    (world y points up) and the factor 2 compensates the character
    cell aspect, so that after :func:`project` (which compresses y
    by 0.5) every stroke lands back in its original cell.

    Args:
        art: The ASCII art as a plain string.

    Returns:
        A list of :class:`Segment` objects with ``z = 0``.
    """
    rows = art.split('\n')
    segments: list[Segment] = []
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == '_':
                segments.append(Segment(
                    np.array([c, -2.0 * (r + 1), 0.0]),
                    np.array([c + 1.0, -2.0 * (r + 1), 0.0])))
            elif ch == '|':
                segments.append(Segment(
                    np.array([c + 0.5, -2.0 * r, 0.0]),
                    np.array([c + 0.5, -2.0 * (r + 1), 0.0])))
            elif ch == '/':
                segments.append(Segment(
                    np.array([c, -2.0 * (r + 1), 0.0]),
                    np.array([c + 1.0, -2.0 * r, 0.0])))
            elif ch == '\\':
                segments.append(Segment(
                    np.array([c, -2.0 * r, 0.0]),
                    np.array([c + 1.0, -2.0 * (r + 1), 0.0])))
    return segments


def _point_key(p: np.ndarray) -> tuple[float, float, float]:
    """Hashable key for a 3D point (strokes live on exact grids)."""
    return (round(float(p[0]), 6), round(float(p[1]), 6),
            round(float(p[2]), 6))


def merge_strokes(segments: list[Segment]) -> list[Segment]:
    """Merge collinear consecutive unit strokes into long segments.

    A run of five ``_`` characters is parsed as five unit segments;
    this helper chains them back into a single segment, which makes
    the extruded box render with clean long edges instead of a noisy
    pile of overlapping unit cells.  Chaining only joins segments
    that share an endpoint and point in the same direction, so
    ``/`` diagonals chain with ``/`` and never with ``\\``.

    Args:
        segments: Unit segments, e.g. from :func:`art_segments`.

    Returns:
        The merged segment list (order is stable).
    """
    if not segments:
        return []

    def direction(s: Segment) -> np.ndarray:
        return s.end - s.start

    start_map: dict[tuple, list[int]] = {}
    end_map: dict[tuple, list[int]] = {}
    for i, s in enumerate(segments):
        start_map.setdefault(_point_key(s.start), []).append(i)
        end_map.setdefault(_point_key(s.end), []).append(i)

    used = [False] * len(segments)
    merged: list[Segment] = []
    for i, s in enumerate(segments):
        if used[i]:
            continue
        used[i] = True
        base_dir = s.end - s.start
        # Walk backwards to the head of the chain.
        head = s
        while True:
            prev = [j for j in end_map.get(_point_key(head.start), [])
                    if not used[j]
                    and np.array_equal(segments[j].end - segments[j].start,
                                       base_dir)]
            if not prev:
                break
            j = prev[0]
            used[j] = True
            head = Segment(segments[j].start, head.end)
        # Walk forwards to the tail of the chain.
        cur = head
        while True:
            nxt = [j for j in start_map.get(_point_key(cur.end), [])
                   if not used[j]
                   and np.array_equal(segments[j].end - segments[j].start,
                                      base_dir)]
            if not nxt:
                break
            j = nxt[0]
            used[j] = True
            cur = Segment(cur.start, segments[j].end)
        merged.append(cur)
    return merged


def _quantized_center(pts: np.ndarray) -> np.ndarray:
    """Centre *pts* on the origin, snapped to the stroke grid.

    Strokes parsed from art live on a half-cell grid: underscore
    endpoints sit on integer x, pipes on ``c + 0.5`` and the world y
    coordinates are even integers (``-2 * row``).  Centring with the
    exact mean would shift strokes onto fractional positions and blur
    the cell alignment (a one-cell stroke would straddle two cells),
    so the centre is snapped to a legal grid point first: integer x,
    even y, and z pinned to 0 so the front face keeps its exact size.
    """
    mid = pts.mean(axis=0)
    return np.array([
        float(round(float(mid[0]))),
        round(float(mid[1]) / 2) * 2.0,
        0.0,
    ])


def _convex_hull_2d(points: np.ndarray) -> list[int]:
    """Indices of the 2D convex hull of *points* (monotone chain).

    Args:
        points: Array of shape ``(n, 2)``.

    Returns:
        Hull vertex indices in counter-clockwise order (no collinear
        points on the edges).
    """
    pts = points[np.lexsort((points[:, 1], points[:, 0]))]
    if len(pts) < 3:
        return list(range(len(pts)))

    def cross(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])
                - (a[1] - o[1]) * (b[0] - o[0]))

    lower: list[int] = []
    for i in range(len(pts)):
        while len(lower) >= 2 and cross(pts[lower[-2]],
                                        pts[lower[-1]], pts[i]) <= 0:
            lower.pop()
        lower.append(i)
    upper: list[int] = []
    for i in range(len(pts) - 1, -1, -1):
        while len(upper) >= 2 and cross(pts[upper[-2]],
                                        pts[upper[-1]], pts[i]) <= 0:
            upper.pop()
        upper.append(i)
    hull = lower[:-1] + upper[:-1]
    # Map back to original indices (pts was re-sorted).
    order = np.lexsort((points[:, 1], points[:, 0]))
    return [int(order[i]) for i in hull]


def extrude_segments(segments: list[Segment], depth: float = 2.0,
                     center: bool = True, hull: bool = True
                     ) -> list[Segment]:
    """Extrude 2D *segments* into a 3D box of the given *depth*.

    The input segments become the front face (``z = 0``).  The box is
    closed behind by the **convex hull** of the front face: the back
    face is the hull pushed back by *depth* and the hull corners are
    connected front-to-back.  Using the hull instead of a full copy of
    the art is what gives the clean "one line to the top, one to the
    side" look of the hand drawn theory examples -- the interior
    detail of the hidden back face is simply not drawn.

    With ``center=True`` the art is moved so its geometric centre sits
    on the origin, which makes rotations behave nicely.

    Args:
        segments: 2D segments (``z`` ignored).
        depth: How deep the extruded box is.
        center: Recentre the geometry on the origin.
        hull: Close the box with the convex hull (recommended); with
            ``False`` the back face is a full copy of the art.

    Returns:
        The list of 3D segments (front face, back frame and hull
        connectors).
    """
    if not segments:
        return []
    if depth <= 0:  # flat art: no back face, no connectors
        return [Segment(s.start.astype(float), s.end.astype(float))
                for s in segments]
    if center:
        pts = np.array([p for s in segments for p in (s.start, s.end)])
        mid = _quantized_center(pts)
        front = [Segment(s.start.astype(float) - mid,
                         s.end.astype(float) - mid)
                 for s in segments]
    else:
        front = [Segment(s.start.astype(float).copy(),
                         s.end.astype(float).copy()) for s in segments]

    # The depth axis is z: the viewer sits at +z, the box goes behind.
    if not hull:
        back = [Segment(s.start - np.array([0.0, 0.0, depth]),
                        s.end - np.array([0.0, 0.0, depth]))
                for s in front]
        connectors: list[Segment] = []
        seen: set[tuple[float, float, float]] = set()
        for s in front:
            for p in (s.start, s.end):
                key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
                if key not in seen:
                    seen.add(key)
                    connectors.append(Segment(
                        p, p - np.array([0.0, 0.0, depth])))
        return front + back + connectors

    # Convex hull of the front face endpoints (in x/y, z is 0 here).
    endpoints = np.array([p for s in front for p in (s.start, s.end)])
    hull_idx = _convex_hull_2d(endpoints[:, :2])
    hull_pts = [endpoints[i] for i in hull_idx]
    back_frame = [Segment(p - np.array([0.0, 0.0, depth]),
                          q - np.array([0.0, 0.0, depth]))
                  for p, q in zip(hull_pts, hull_pts[1:] + hull_pts[:1])]
    connectors = [Segment(p, p - np.array([0.0, 0.0, depth]))
                  for p in hull_pts]
    return front + back_frame + connectors


def mesh_segments(vertices: np.ndarray, edges: list[tuple[int, int]],
                  scale: float = 10.0
                  ) -> list[Segment]:
    """Turn a theoretic mesh into drawable segments.

    Mesh vertices usually live in "math units" (a cube is ``±1``).
    This helper scales them to character-cell units; the projection
    then compresses y by 0.5, which is exactly what makes a math
    cube look square on the 2:1 character grid.

    Args:
        vertices: Array of shape ``(n, 3)`` with the vertex positions.
        edges: List of ``(i, j)`` index pairs into *vertices*.
        scale: Overall size in character cells.

    Returns:
        One :class:`Segment` per edge.
    """
    verts = np.asarray(vertices, dtype=float)
    if scale is not None:
        verts = verts * scale
    return [Segment(verts[i].copy(), verts[j].copy()) for i, j in edges]


# ----------------------------------------------------------------------
# transforms
# ----------------------------------------------------------------------
def _rotation_matrix(yaw: float = 0.0, pitch: float = 0.0,
                     roll: float = 0.0) -> np.ndarray:
    """Build the combined rotation matrix ``Ry @ Rx @ Rz`` (degrees)."""
    a = math.radians(yaw)
    b = math.radians(pitch)
    g = math.radians(roll)
    ry = np.array([
        [math.cos(a), 0.0, math.sin(a)],
        [0.0, 1.0, 0.0],
        [-math.sin(a), 0.0, math.cos(a)],
    ])
    rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, math.cos(b), -math.sin(b)],
        [0.0, math.sin(b), math.cos(b)],
    ])
    rz = np.array([
        [math.cos(g), -math.sin(g), 0.0],
        [math.sin(g), math.cos(g), 0.0],
        [0.0, 0.0, 1.0],
    ])
    return ry @ rx @ rz


def rotate(segments: list[Segment], yaw: float = 0.0, pitch: float = 0.0,
           roll: float = 0.0) -> list[Segment]:
    """Rotate *segments* by *yaw*, *pitch* and *roll* (degrees).

    The rotation order is roll, then pitch, then yaw (applied as
    ``Ry @ Rx @ Rz``), so the yaw happens around the screen's vertical
    axis which is what a turntable spin needs.

    Args:
        segments: The 3D segments to rotate.
        yaw: Rotation around the Y axis (turntable), degrees.
        pitch: Rotation around the X axis (nod), degrees.
        roll: Rotation around the Z axis (tilt), degrees.

    Returns:
        The rotated segments (new objects, inputs untouched).
    """
    matrix = _rotation_matrix(yaw, pitch, roll)
    return [Segment(matrix @ s.start, matrix @ s.end) for s in segments]


def _bounds(segments: list[Segment]) -> tuple[np.ndarray, np.ndarray]:
    """Return the (min, max) corner points of all segment endpoints."""
    pts = np.array([p for s in segments for p in (s.start, s.end)])
    return pts.min(axis=0), pts.max(axis=0)


class _Projection:
    """A shared perspective projection for one frame.

    All segments (and extra points, e.g. hull corners) passed through
    the same instance are guaranteed to land in one consistent screen
    coordinate system, which the composite renderer needs to overlay
    the front face on top of the hidden back frame.
    """

    def __init__(self, segments: list[Segment], zoom: float = 1.0,
                 perspective: float = 4.0):
        lo, hi = _bounds(segments)
        radius = max(
            float(np.linalg.norm(hi - lo)) / 2.0,
            float(np.linalg.norm(hi)),
            float(np.linalg.norm(lo)),
            1e-9,
        )
        self.radius = radius
        self.cam = radius * perspective
        self.zoom = zoom
        raw = [self._raw_pair(s) for s in segments]
        xs = [p[0] for pair in raw for p in pair]
        ys = [p[1] for pair in raw for p in pair]
        if xs:
            # Whole-cell shift: strokes live on a half-cell grid (pipes
            # at x = c + 0.5, underscores on integer boundaries) and a
            # fractional shift would blur that alignment.
            self.dx = -math.floor(min(xs))
            self.dy = -math.floor(min(ys))
        else:
            self.dx = self.dy = 0.0

    def _raw_pair(self, s: Segment) -> tuple[np.ndarray, np.ndarray]:
        pts = []
        for p in (s.start, s.end):
            depth = max(self.cam - p[2], 0.1 * self.radius)
            scale = self.cam / depth
            pts.append(np.array([p[0] * scale, -p[1] * scale * CELL_ASPECT]))
        return pts[0], pts[1]

    def _shift(self, u: np.ndarray) -> np.ndarray:
        return np.array([(u[0] + self.dx) * self.zoom,
                         (u[1] + self.dy) * self.zoom])

    def point(self, p: np.ndarray) -> np.ndarray:
        """Project a single 3D point to screen (cell) coordinates."""
        arr = np.asarray(p, dtype=float)
        pair = self._raw_pair(Segment(arr, arr))
        return self._shift(pair[0])

    def segments(self) -> list[tuple[np.ndarray, np.ndarray]]:
        """Project every segment; returns ``(start, end)`` pairs."""
        out = []
        for s in self._segments:
            u, v = self._raw_pair(s)
            out.append((self._shift(u), self._shift(v)))
        return out


def project(segments: list[Segment], zoom: float = 1.0,
            perspective: float = 4.0) -> list[tuple[np.ndarray, np.ndarray]]:
    """Project 3D *segments* onto the 2D character grid.

    A weak perspective camera sits on the +z axis looking at the
    origin; *perspective* is the camera distance as a multiple of the
    model radius (larger = more orthographic).  The y axis is
    compressed by :data:`CELL_ASPECT` so that squares look square on a
    character grid, and the coordinates are shifted so the projection
    lives in the first quadrant ("cell units", y growing down).

    Args:
        segments: Rotated 3D segments.
        zoom: Multiplies the natural size (1.0 = same number of
            cells as the unrotated art).
        perspective: Camera distance in model radii.

    Returns:
        List of ``(start, end)`` screen-space pairs (x right, y down,
        in character cells).
    """
    proj = _Projection(segments, zoom=zoom, perspective=perspective)
    proj._segments = segments
    return proj.segments()


# ----------------------------------------------------------------------
# rasterizer
# ----------------------------------------------------------------------
def _char_for(dx: float, dy: float) -> str:
    """Pick the stroke character for a segment of slope (dy, dx)."""
    if abs(dy) < 0.45 * abs(dx):
        return '_'
    if abs(dx) < 0.45 * abs(dy):
        return '|'
    return '\\' if dx * dy > 0 else '/'


def _segment_samples(u: np.ndarray, v: np.ndarray
                     ) -> list[tuple[str, int, int]]:
    """Sample one projected segment into (char, col, row) cells.

    Cell (c, r) covers the screen square ``[c, c+1] x [r, r+1]`` --
    the same geometry :func:`art_segments` parses.  Diagonals sample
    per cell (a staircase), but shallow lines follow ASCII
    conventions: a ``_`` segment stays on the single row of its
    midpoint (underscores live at the bottom of a cell) and a ``|``
    segment keeps the single column of its midpoint, which is what
    keeps rotated boxes looking hand-drawn instead of broken.
    """
    dx = v[0] - u[0]
    dy = v[1] - u[1]
    if dx == 0.0 and dy == 0.0:
        return []
    ch = _char_for(dx, dy)
    steps = max(2, int(math.ceil(max(abs(dx), abs(dy)) / 0.4)) + 1)
    # ASCII art keeps *shallow* lines flat: a '_' segment whose rows
    # drift by less than ~1.5 cells lives on the single row of its
    # midpoint (underscores sit at the bottom of a cell), and a '|'
    # segment keeps the single column of its midpoint.  Steeper lines
    # sample per cell, which draws proper staircases.
    if ch == '_' and abs(dy) < 1.5:
        flat_row = int(math.floor((u[1] + v[1]) / 2.0 - 0.5))
    else:
        flat_row = None
    if ch == '|' and abs(dx) < 1.5:
        flat_col = int(math.floor((u[0] + v[0]) / 2.0))
    else:
        flat_col = None
    samples = []
    for i in range(steps):
        t = (i + 0.5) / steps
        x = u[0] + dx * t
        y = u[1] + dy * t
        col = int(math.floor(x))
        if ch == '_':
            row = flat_row if flat_row is not None else int(
                math.floor(y - 0.5))
            samples.append((ch, col, row))
        elif ch == '|':
            row = int(math.floor(y))
            samples.append((ch, flat_col if flat_col is not None else col,
                            row))
        else:
            row = int(math.floor(y))
            samples.append((ch, col, row))
    return samples


def _painter_order(projected: list[tuple[np.ndarray, np.ndarray]],
                   rotated: list[Segment]) -> list[int]:
    """Segment indices sorted far-to-near (painter's algorithm)."""
    depth = [s.midpoint[2] for s in rotated]
    return sorted(range(len(projected)), key=lambda i: depth[i])


def rasterize(projected: list[tuple[np.ndarray, np.ndarray]],
              depth_rank: list[int] | None = None,
              margin: int = 0) -> list[list[str]]:
    """Draw projected segments onto a character grid.

    Segments are drawn far-to-near (painter's algorithm) so near
    strokes overwrite far ones.  Each segment is sampled along its
    length and every sample cell receives the character that matches
    the segment's screen slope, which reconstructs ``_``, ``|``, ``/``
    and ``\\`` strokes -- the same alphabet the parser understands, so
    rendering is idempotent for unrotated art.

    Args:
        projected: Output of :func:`project`.
        depth_rank: Draw order (indices, far first).  ``None`` means
            the call order is already far-to-near.
        margin: Blank cells to leave around the drawing.

    Returns:
        The character grid as a list of row lists.
    """
    if not projected:
        return []
    order = depth_rank if depth_rank is not None else list(
        range(len(projected)))
    all_samples: list[tuple[str, int, int]] = []
    for idx in order:
        u, v = projected[idx]
        all_samples.extend(_segment_samples(u, v))
    return _draw(all_samples, margin)


def _draw(all_samples: list[tuple[str, int, int]], margin: int,
          blocked: set[tuple[int, int]] | None = None,
          grid: list[list[str]] | None = None) -> list[list[str]]:
    """Allocate (or reuse) a grid and paint *all_samples* onto it.

    Args:
        all_samples: ``(char, col, row)`` cells in draw order.
        margin: Blank border in cells.
        blocked: Cells to leave untouched (hidden-line mask).
        grid: Existing grid to paint on (extended as needed).
    """
    if not all_samples:
        return grid if grid is not None else []
    min_col = min(c for _, c, _ in all_samples)
    min_row = min(r for _, _, r in all_samples)
    max_col = max(c for _, c, _ in all_samples)
    max_row = max(r for _, _, r in all_samples)
    width = max_col - min_col + 1 + 2 * margin
    height = max_row - min_row + 1 + 2 * margin
    off_col = min_col - margin
    off_row = min_row - margin
    if grid is None:
        grid = [[' '] * width for _ in range(height)]
    else:
        # Grow the existing grid to fit the new bounds (keep origin).
        need_w = off_col + width
        need_h = off_row + height
        for row in grid:
            if len(row) < need_w:
                row.extend([' '] * (need_w - len(row)))
        while len(grid) < need_h:
            grid.append([' '] * need_w)
    for ch, col, row in all_samples:
        col -= off_col
        row -= off_row
        if blocked is not None and (col, row) in blocked:
            continue
        if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
            grid[row][col] = ch
    return grid


def _blocked_cells(polygon: list[np.ndarray]) -> set[tuple[int, int]]:
    """Cells whose centre lies strictly inside *polygon* (scanline).

    The polygon is the projected silhouette of an opaque face; cells
    inside it are "blocked" so strokes behind the face are not drawn
    there -- a cheap hidden-line removal that gives the classic solid
    ASCII box look.
    """
    if len(polygon) < 3:
        return set()
    blocked: set[tuple[int, int]] = set()
    ys = [p[1] for p in polygon]
    xs = [p[0] for p in polygon]
    min_row = int(math.floor(min(ys)))
    max_row = int(math.ceil(max(ys)))
    min_col = int(math.floor(min(xs)))
    max_col = int(math.ceil(max(xs)))
    for row in range(min_row - 1, max_row + 2):
        y = row + 0.5
        crossings: list[float] = []
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i][0], polygon[i][1]
            x2, y2 = polygon[(i + 1) % n][0], polygon[(i + 1) % n][1]
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                crossings.append(x1 + t * (x2 - x1))
        crossings.sort()
        for x_left, x_right in zip(crossings[::2], crossings[1::2]):
            col_lo = int(math.floor(x_left - 0.5)) + 1
            col_hi = int(math.ceil(x_right - 0.5)) - 1
            for col in range(max(col_lo, min_col), min(col_hi, max_col) + 1):
                if x_left < col + 0.5 < x_right:
                    blocked.add((col, row))
    return blocked


def grid_to_text(grid: list[list[str]]) -> str:
    """Join a character grid into a trimmed string."""
    return '\n'.join(''.join(row).rstrip() for row in grid).rstrip('\n')


def render_segments(segments: list[Segment], yaw: float = 0.0,
                    pitch: float = 0.0, roll: float = 0.0,
                    zoom: float = 1.0, margin: int = 0) -> str:
    """Rotate, project and rasterize *segments* in one call.

    Args:
        segments: 3D segments (e.g. from :func:`extrude_segments`).
        yaw: Rotation around the vertical axis, degrees.
        pitch: Nod rotation, degrees.
        roll: Tilt rotation, degrees.
        zoom: Scale of the drawing (1.0 = natural size).
        margin: Blank border, in cells.

    Returns:
        The rendered ASCII frame.
    """
    if not segments:
        return ''
    rotated = rotate(segments, yaw, pitch, roll)
    projected = project(rotated, zoom=zoom)
    order = _painter_order(projected, rotated)
    grid = rasterize(projected, depth_rank=order, margin=margin)
    return grid_to_text(grid)


def render_art(art: str, yaw: float = 0.0, pitch: float = 0.0,
               roll: float = 0.0, depth: float = 2.0,
               zoom: float = 1.0, margin: int = 0, hull: bool = True
               ) -> str:
    """Render an ASCII *art* as an extruded 3D box.

    The strokes of the art become the front face of a box whose depth
    is *depth* cells.  The box is closed behind by the convex hull of
    the front face; strokes of the back frame that would fall behind
    the opaque front face are masked out (hidden-line removal), which
    is what gives the solid, hand-drawn look of the theory docs.

    Args:
        art: The ASCII art (the future front face of the box).
        yaw: Rotation around the vertical axis, degrees.  Negative
            yaw turns the art to the left (the right face shows).
        pitch: Nod rotation, degrees; positive looks down on the top
            face.
        roll: Tilt rotation, degrees.
        depth: Depth of the extruded box.
        zoom: Scale of the drawing.
        margin: Blank border, in cells.
        hull: Close the silhouette with the convex hull (classic
            look); ``False`` keeps the full back face wireframe.

    Returns:
        The rendered ASCII frame.

    Examples:
        >>> print(render_art(' _\\n|_|', depth=0))
         _
        |_|
    """
    front = merge_strokes(art_segments(art))
    if not front:
        return ''
    # Centre the art on the origin so rotations pivot around it
    # (snapped to the stroke grid to keep the cell alignment).
    pts = np.array([p for s in front for p in (s.start, s.end)])
    mid = _quantized_center(pts)
    front = [Segment(s.start - mid, s.end - mid) for s in front]

    if depth <= 0:
        return render_segments(front, yaw, pitch, roll, zoom, margin)

    # The convex hull closes the box behind the front face.  Only the
    # two *visible* faces of the box are drawn -- the top (or bottom)
    # face and the one side face the viewer can see -- exactly like
    # the hand drawn theory examples; the rest is hidden behind the
    # opaque front face anyway.
    endpoints = np.array([p for s in front for p in (s.start, s.end)])
    deep = np.array([0.0, 0.0, depth])
    if hull and len(endpoints) >= 3:
        hull_idx = _convex_hull_2d(endpoints[:, :2])
        hull_pts = [endpoints[i] for i in hull_idx]
        matrix_pre = _rotation_matrix(yaw, pitch, roll)
        center2 = endpoints[:, :2].mean(axis=0)
        normals = []
        for i in range(len(hull_pts)):
            p, q = hull_pts[i], hull_pts[(i + 1) % len(hull_pts)]
            e2 = q[:2] - p[:2]
            n2 = np.array([e2[1], -e2[0], 0.0])
            if np.dot(n2[:2], (p[:2] + q[:2]) / 2 - center2) < 0:
                n2 = -n2
            normals.append(matrix_pre @ n2)
        # Top or bottom edge, depending on whether we look down on
        # the box or up at it.
        up_z = float((matrix_pre @ np.array([0.0, 1.0, 0.0]))[2])
        ys = [n[1] for n in normals]
        vertical_idx = (int(np.argmax(ys)) if up_z > 0
                        else int(np.argmin(ys)))
        # The side edge facing the viewer most.
        side_idx = max((i for i in range(len(hull_pts))
                        if i != vertical_idx),
                       key=lambda i: normals[i][2])
        chosen = []
        for i in {vertical_idx, side_idx}:
            chosen.append((hull_pts[i],
                           hull_pts[(i + 1) % len(hull_pts)]))
        back = [Segment(p - deep, q - deep) for p, q in chosen]
        seen: set[tuple] = set()
        corners = []
        for p, q in chosen:
            for c in (p, q):
                key = (round(c[0], 6), round(c[1], 6))
                if key not in seen:
                    seen.add(key)
                    corners.append(c)
        connectors = [Segment(c, c - deep) for c in corners]
    else:
        hull_pts = []
        back = []
        connectors = []

    matrix = _rotation_matrix(yaw, pitch, roll)
    everything = front + back + connectors
    rotated = [Segment(matrix @ s.start, matrix @ s.end)
               for s in everything]
    proj = _Projection(rotated, zoom=zoom)
    proj._segments = rotated
    projected = proj.segments()
    n_front = len(front)

    nz = float((matrix @ np.array([0.0, 0.0, 1.0]))[2])
    if nz > 0.15 and hull and len(hull_pts) >= 3:
        # The front face looks at the viewer: it is opaque, so mask
        # out everything that projects behind its silhouette.
        rot_hull = [matrix @ p for p in hull_pts]
        polygon = [proj.point(p) for p in rot_hull]
        blocked = _blocked_cells(polygon)
    else:
        blocked = None

    order = _painter_order(projected, rotated)
    far = [i for i in order if i >= n_front]
    near = [i for i in order if i < n_front]
    far_samples: list[tuple[str, int, int]] = []
    for idx in far:
        u, v = projected[idx]
        far_samples.extend(_segment_samples(u, v))
    near_samples: list[tuple[str, int, int]] = []
    for idx in near:
        u, v = projected[idx]
        near_samples.extend(_segment_samples(u, v))

    all_samples = far_samples + near_samples
    if not all_samples:
        return ''
    # One shared canvas origin for both layers, otherwise the far
    # and near strokes land in different coordinate systems.
    min_col = min(c for _, c, _ in all_samples)
    min_row = min(r for _, _, r in all_samples)
    max_col = max(c for _, c, _ in all_samples)
    max_row = max(r for _, _, r in all_samples)
    off_col = min_col - margin
    off_row = min_row - margin
    width = max_col - min_col + 1 + 2 * margin
    height = max_row - min_row + 1 + 2 * margin
    grid = [[' '] * width for _ in range(height)]

    def paint(samples: list[tuple[str, int, int]],
              blocked: set[tuple[int, int]] | None) -> None:
        for ch, col, row in samples:
            col -= off_col
            row -= off_row
            if blocked is not None and (col, row) in blocked:
                continue
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = ch

    # Hidden lines first (masked by the opaque front face), then the
    # front face strokes on top.
    paint(far_samples, blocked)
    paint(near_samples, None)
    return grid_to_text(grid)


def render_mesh(vertices: np.ndarray, edges: list[tuple[int, int]],
                yaw: float = 0.0, pitch: float = 0.0, roll: float = 0.0,
                scale: float = 10.0, zoom: float = 1.0,
                margin: int = 0) -> str:
    """Render a theoretic mesh (vertices + edges) as ASCII.

    Args:
        vertices: ``(n, 3)`` array of vertex positions (math units).
        edges: ``(i, j)`` index pairs.
        yaw: Rotation around the vertical axis, degrees.
        pitch: Nod rotation, degrees.
        roll: Tilt rotation, degrees.
        scale: Size of the mesh in character cells.
        zoom: Extra scale factor.
        margin: Blank border, in cells.

    Returns:
        The rendered ASCII frame.
    """
    segments = mesh_segments(vertices, edges, scale=scale)
    return render_segments(segments, yaw=yaw, pitch=pitch, roll=roll,
                           zoom=zoom, margin=margin)
