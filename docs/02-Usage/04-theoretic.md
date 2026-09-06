# Theoretic arts: mathematics drawn as ASCII

The theoretic arts do not come from a drawing -- they come from
*equations*. Each generator returns a `Mesh` (vertices + edges) that
the wireframe renderer projects onto the character grid:

| Name | Shape |
|------|-------|
| `cube`, `box` | the Platonic classic (8 vertices, 12 edges) |
| `tetrahedron`, `octahedron`, `icosahedron`, `dodecahedron` | the other Platonic solids |
| `sphere` | wireframe globe: latitude rings + meridians |
| `torus` | the donut |
| `helix`, `double_helix` | a spring, and DNA with rungs |
| `mobius` | one side, one edge |
| `wave` | the field `y = sin(x) * cos(z)` |
| `spiral` | Archimedean spiral |

## Rendering

```python
from ascii3d.theory import render, MESHES

print(render('cube'))        # default isometric-ish view
print(render('sphere'))      # 10-cell globe
print(MESHES['torus'].n_edges)   # 80 edges
```
```
  /\_________
  /\\       /\\
 // \\      /  \\
 /    \____________
//     /  //      /
\_____//__\      //
\\    /   \\    //
 \\  /      \\ //
  \\//_________/
   \/
```

Every mesh accepts `yaw`, `pitch`, `roll` and `scale`:

```python
print(render('double_helix', yaw=60, pitch=15, scale=9))
```

## Spinning them

The theoretic arts are the showpieces of the
[360 degree rotation](02-rotation.md):

```python
from ascii3d.rotation import mesh_frames, mesh_to_gif, play_frames
from ascii3d.theory import MESHES

torus = MESHES['torus']
play_frames(mesh_frames(torus.vertices, torus.edges, steps=36), fps=12)
mesh_to_gif(torus.vertices, torus.edges, 'torus.gif', steps=36)
```

## Command line

```shell
ascii3d --theoretic sphere
ascii3d --theoretic dodecahedron --spin
ascii3d --theoretic torus --gif torus.gif
ascii3d --meshes              # list them all
```

## Building your own

A mesh is just vertices and index pairs -- the wave mesh is a dozen
lines of numpy:

```python
import numpy as np
from ascii3d.theory import mesh

nx, ny = 7, 5
verts = [(x, np.sin(x) * np.cos(z), z)
         for x in np.linspace(-np.pi, np.pi, nx)
         for z in np.linspace(-np.pi, np.pi, ny)]
edges = [(i, i + 1) for i in range(len(verts)) if (i + 1) % ny]
edges += [(i, i + ny) for i in range(len(verts) - ny)]
mine = mesh('mine', verts, edges)
```

Feed `mine.vertices` and `mine.edges` to `mesh_frames` (or
`ascii3d.wireframe.render_mesh`) and it becomes a spinning ASCII art
too.
