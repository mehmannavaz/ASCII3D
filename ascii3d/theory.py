"""Theoretic ASCII arts: mathematical meshes drawn as ASCII.

These are the "theoretic" arts -- shapes that do not come from a
drawing but from *mathematics*: the Platonic solids, a wireframe
sphere, a torus, a helix, a Moebius strip, a sine field...  Every
generator returns a :class:`Mesh` (vertices + edges) that
:func:`ascii3d.wireframe.render_mesh` projects onto the character
grid, and :mod:`ascii3d.rotation` can spin around a full 360.

The vertices live in "math units" (a cube spans ``-1 .. +1``); the
renderer scales them to character cells.

Example:
    >>> from ascii3d.theory import MESHES
    >>> from ascii3d.wireframe import render_mesh
    >>> cube = MESHES['cube']
    >>> print(render_mesh(cube.vertices, cube.edges))
    ...
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = ['Mesh', 'MESHES', 'mesh', 'render', 'cube', 'box', 'tetrahedron',
           'octahedron', 'icosahedron', 'dodecahedron', 'sphere', 'torus',
           'helix', 'double_helix', 'mobius', 'wave', 'spiral']

GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass(frozen=True)
class Mesh:
    """A theoretic wireframe mesh.

    Attributes:
        vertices: ``(n, 3)`` float array of vertex positions.
        edges: List of ``(i, j)`` index pairs into *vertices*.
        name: Human friendly name (for labels and the CLI).
    """

    vertices: np.ndarray
    edges: list[tuple[int, int]]
    name: str = 'mesh'

    def __post_init__(self) -> None:
        object.__setattr__(self, 'vertices',
                           np.asarray(self.vertices, dtype=float))

    @property
    def n_vertices(self) -> int:
        return len(self.vertices)

    @property
    def n_edges(self) -> int:
        return len(self.edges)


def mesh(name: str, vertices, edges) -> Mesh:
    """Build a :class:`Mesh` (thin convenience wrapper)."""
    return Mesh(np.asarray(vertices, dtype=float),
                [(int(i), int(j)) for i, j in edges], name=name)


def _edges_from_grid(rows: int, cols: int) -> list[tuple[int, int]]:
    """Edges of a ``rows x cols`` lattice (row-major vertex order)."""
    edges = []
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if c + 1 < cols:
                edges.append((i, i + 1))
            if r + 1 < rows:
                edges.append((i, i + cols))
    return edges


# ----------------------------------------------------------------------
# the Platonic solids
# ----------------------------------------------------------------------
def cube() -> Mesh:
    """The cube: 8 vertices, 12 edges."""
    verts = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    return mesh('cube', verts, edges)


def box(width: float = 1.6, height: float = 1.0, depth: float = 1.0
        ) -> Mesh:
    """A rectangular box (cuboid) with the given half extents."""
    verts = [
        (-width, -height, -depth), (width, -height, -depth),
        (width, height, -depth), (-width, height, -depth),
        (-width, -height, depth), (width, -height, depth),
        (width, height, depth), (-width, height, depth),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    return mesh('box', verts, edges)


def tetrahedron() -> Mesh:
    """The tetrahedron: 4 vertices, 6 edges."""
    verts = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    return mesh('tetrahedron', verts, edges)


def octahedron() -> Mesh:
    """The octahedron: 6 vertices, 12 edges."""
    verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
             (0, 0, 1), (0, 0, -1)]
    edges = [(0, 2), (0, 3), (0, 4), (0, 5),
             (1, 2), (1, 3), (1, 4), (1, 5),
             (2, 4), (4, 3), (3, 5), (5, 2)]
    return mesh('octahedron', verts, edges)


def icosahedron() -> Mesh:
    """The icosahedron: 12 vertices on three golden rectangles."""
    g = GOLDEN
    verts = ([(0, -1, -g), (0, -1, g), (0, 1, -g), (0, 1, g)]
             + [(-1, -g, 0), (-1, g, 0), (1, -g, 0), (1, g, 0)]
             + [(-g, 0, -1), (g, 0, -1), (-g, 0, 1), (g, 0, 1)])
    # The 30 edges: pairs of vertices at the minimal distance 2.
    verts_arr = np.asarray(verts, dtype=float)
    edges = []
    for i in range(len(verts_arr)):
        for j in range(i + 1, len(verts_arr)):
            if np.linalg.norm(verts_arr[i] - verts_arr[j]) < 2.01:
                edges.append((i, j))
    return mesh('icosahedron', verts, edges)


def dodecahedron() -> Mesh:
    """The dodecahedron: 20 vertices, 30 edges."""
    g = GOLDEN
    verts = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                verts.append((x, y, z))
    for a in (-1 / g, 1 / g):
        for b in (-g, g):
            verts.append((0, a, b))
            verts.append((a, b, 0))
            verts.append((b, 0, a))
    verts_arr = np.asarray(verts, dtype=float)
    edges = []
    for i in range(len(verts_arr)):
        for j in range(i + 1, len(verts_arr)):
            if np.linalg.norm(verts_arr[i] - verts_arr[j]) < 1.3:
                edges.append((i, j))
    return mesh('dodecahedron', verts, edges)


# ----------------------------------------------------------------------
# curved theoretic shapes
# ----------------------------------------------------------------------
def sphere(lats: int = 4, lons: int = 8) -> Mesh:
    """A wireframe sphere: *lats* latitude rings and *lons* meridians."""
    verts = [(0.0, 1.0, 0.0)]  # north pole
    for i in range(1, lats):
        phi = math.pi * i / lats
        for j in range(lons):
            theta = 2 * math.pi * j / lons
            verts.append((math.sin(phi) * math.cos(theta),
                          math.cos(phi),
                          math.sin(phi) * math.sin(theta)))
    verts.append((0.0, -1.0, 0.0))  # south pole
    edges = []
    # latitude rings
    for i in range(1, lats):
        base = 1 + (i - 1) * lons
        for j in range(lons):
            edges.append((base + j, base + (j + 1) % lons))
    # meridians between consecutive rings
    for i in range(1, lats - 1):
        base = 1 + (i - 1) * lons
        for j in range(lons):
            edges.append((base + j, base + lons + j))
    # pole fans
    south = len(verts) - 1
    last_ring = 1 + (lats - 2) * lons
    for j in range(lons):
        edges.append((0, 1 + j))
        edges.append((south, last_ring + j))
    return mesh('sphere', verts, edges)


def torus(major: int = 8, minor: int = 5) -> Mesh:
    """A torus: a *major* x *minor* wireframe grid."""
    verts = []
    for i in range(major):
        u = 2 * math.pi * i / major
        for j in range(minor):
            v = 2 * math.pi * j / minor
            r = 2.0 + 0.7 * math.cos(v)
            verts.append((r * math.cos(u), 0.7 * math.sin(v),
                          r * math.sin(u)))
    edges = []
    for i in range(major):
        for j in range(minor):
            idx = i * minor + j
            edges.append((idx, ((i + 1) % major) * minor + j))
            edges.append((idx, i * minor + (j + 1) % minor))
    return mesh('torus', verts, edges)


def helix(turns: float = 2.5, steps: int = 40, radius: float = 1.0,
          height: float = 3.0) -> Mesh:
    """A single helix (a spring)."""
    verts = []
    for k in range(steps):
        t = k / (steps - 1)
        a = 2 * math.pi * turns * t
        verts.append((radius * math.cos(a),
                      height * (t - 0.5),
                      radius * math.sin(a)))
    edges = [(i, i + 1) for i in range(steps - 1)]
    return mesh('helix', verts, edges)


def double_helix(turns: float = 2.5, steps: int = 40, radius: float = 1.0,
                 height: float = 3.0) -> Mesh:
    """The DNA double helix: two strands with rungs."""
    strand_a, strand_b = [], []
    for k in range(steps):
        t = k / (steps - 1)
        a = 2 * math.pi * turns * t
        strand_a.append((radius * math.cos(a), height * (t - 0.5),
                         radius * math.sin(a)))
        strand_b.append((radius * math.cos(a + math.pi),
                         height * (t - 0.5),
                         radius * math.sin(a + math.pi)))
    n = steps
    edges = [(i, i + 1) for i in range(n - 1)]
    edges += [(n + i, n + i + 1) for i in range(n - 1)]
    for k in range(0, steps, max(1, steps // (int(turns * 4) + 1))):
        edges.append((k, n + k))
    verts = strand_a + strand_b
    return mesh('double_helix', verts, edges)


def mobius(steps: int = 16, width: float = 0.5) -> Mesh:
    """A Moebius strip: one side, one edge."""
    verts = []
    rows = 3
    for i in range(steps):
        u = 2 * math.pi * i / steps
        for w in range(rows):
            v = width * (w / (rows - 1) - 0.5) * 2
            x = (2 + v * math.cos(u / 2)) * math.cos(u)
            z = (2 + v * math.cos(u / 2)) * math.sin(u)
            y = v * math.sin(u / 2)
            verts.append((x, y, z))
    edges = []
    # straight band edges across the width...
    for i in range(steps):
        for w in range(rows - 1):
            idx = i * rows + w
            edges.append((idx, idx + 1))
    # ...and ring edges along the length (the strip closes with a
    # half twist: the last step connects width-reversed).
    for i in range(steps - 1):
        for w in range(rows):
            edges.append((i * rows + w, (i + 1) * rows + w))
    for w in range(rows):
        edges.append(((steps - 1) * rows + w, w))
    return mesh('mobius', verts, edges)


def wave(nx: int = 7, ny: int = 5) -> Mesh:
    """A sine field: y = sin(x) * cos(z), as a wireframe."""
    verts = []
    for i in range(nx):
        x = 2.0 * i / (nx - 1) * math.pi - math.pi
        for j in range(ny):
            z = 2.0 * j / (ny - 1) * math.pi - math.pi
            verts.append((x / math.pi, math.sin(x) * math.cos(z),
                          z / math.pi))
    # vertices are laid out row-major with nx rows of ny columns
    edges = _edges_from_grid(nx, ny)
    return mesh('wave', verts, edges)


def spiral(turns: float = 3.0, steps: int = 48) -> Mesh:
    """A flat Archimedean spiral in the x/z plane, lifted slightly."""
    verts = []
    for k in range(steps):
        t = k / (steps - 1)
        a = 2 * math.pi * turns * t
        r = 0.15 + 1.8 * t
        verts.append((r * math.cos(a), 0.0, r * math.sin(a)))
    edges = [(i, i + 1) for i in range(steps - 1)]
    return mesh('spiral', verts, edges)


MESHES: dict[str, Mesh] = {
    'cube': cube(),
    'box': box(),
    'tetrahedron': tetrahedron(),
    'octahedron': octahedron(),
    'icosahedron': icosahedron(),
    'dodecahedron': dodecahedron(),
    'sphere': sphere(),
    'torus': torus(),
    'helix': helix(),
    'double_helix': double_helix(),
    'mobius': mobius(),
    'wave': wave(),
    'spiral': spiral(),
}

# A default cell scale per mesh: the denser the wireframe, the more
# room it needs to stay readable.
_MESH_SCALES = {
    'cube': 8,
    'box': 8,
    'tetrahedron': 7,
    'octahedron': 7,
    'icosahedron': 8,
    'dodecahedron': 8,
    'sphere': 10,
    'torus': 9,
    'helix': 9,
    'double_helix': 8,
    'mobius': 7,
    'wave': 9,
    'spiral': 8,
}


def render(name: str, yaw: float = 30.0, pitch: float = 25.0,
           roll: float = 0.0, scale: float | None = None,
           zoom: float = 1.0, margin: int = 0) -> str:
    """Render a named theoretic mesh as ASCII.

    Args:
        name: Key of :data:`MESHES` (e.g. ``'cube'``, ``'torus'``).
        yaw: Rotation around the vertical axis, degrees.
        pitch: Nod rotation, degrees.
        roll: Tilt rotation, degrees.
        scale: Mesh size in character cells (``None`` picks a
            per-mesh default).
        zoom: Extra scale factor.
        margin: Blank border in cells.

    Returns:
        The rendered ASCII art.

    Raises:
        KeyError: If *name* is not in :data:`MESHES`.
    """
    from .wireframe import render_mesh
    if name not in MESHES:
        raise KeyError(f'unknown mesh {name!r}; choose one of '
                       f'{sorted(MESHES)}')
    shape = MESHES[name]
    if scale is None:
        scale = _MESH_SCALES.get(name, 8)
    return render_mesh(shape.vertices, shape.edges, yaw=yaw, pitch=pitch,
                       roll=roll, scale=scale, zoom=zoom, margin=margin)
