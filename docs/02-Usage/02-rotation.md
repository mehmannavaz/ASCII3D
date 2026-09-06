# The 360 degree rotation

The full answer to *"look anywhere"*: spin the art around a whole
circle. The art is extruded into a 3D box and rotated frame by frame
on a turntable, and every frame shares one canvas size so the
animation is steady.

```python
from ascii3d.rotation import frames, play, to_gif, save_frames
from ascii3d.examples import EXAMPLES

roomy = EXAMPLES['roomy']

timeline = frames(roomy, steps=24)     # 24 frames around 360 degrees
play(roomy, steps=24, fps=10)          # watch it spin in the terminal
save_frames(roomy, 'spin', steps=24)   # spin000.txt, spin001.txt, ...
to_gif(roomy, 'spin.gif', steps=24)    # animated GIF (needs Pillow)
```

## Axes

The turntable is not the only dance move:

| Axis | Motion |
|------|--------|
| `'y'` | turntable (default) |
| `'x'` | cartwheel |
| `'z'` | coin spin |

```python
play(roomy, axis='x', steps=24)   # end-over-end
play(roomy, axis='z', steps=24)   # flat spin
```

The `pitch` argument tips the camera down (default 20 degrees) so
the top face stays visible during a turntable spin.

## Meshes spin too

The theoretic arts ([theoretic](04-theoretic.md)) rotate with the
same machinery:

```python
from ascii3d.rotation import mesh_frames, mesh_to_gif
from ascii3d.theory import MESHES

torus = MESHES['torus']
timeline = mesh_frames(torus.vertices, torus.edges, steps=36)
mesh_to_gif(torus.vertices, torus.edges, 'torus.gif', steps=36)
```

## Command line

```shell
ascii3d --spin -e roomy              # 24-frame terminal spin
ascii3d --spin 60 --fps 15 -e roomy  # longer, faster
ascii3d --gif spin.gif -e roomy      # animated GIF instead
ascii3d --theoretic torus --spin     # spin a theoretic art
```

The GIF is drawn with a monospaced font on a dark background,
exactly like the terminal would show it.
