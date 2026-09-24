# The 360 degree rotation

The full answer to *"look anywhere"*: spin the turned art around a
whole circle. The spin is a sequence of **turned poses**
(`ascii3d/pose.py`), not a free-angle projection:

* the camera stays **above** the box for the whole sweep -- the top
  face is visible in every frame and the depth always marches
  **down** the side face ("only going down", never looking up),
* the flat, forward, "normal" view never appears -- near face-on
  the box keeps a visible side sliver and a top face,
* frame 0 starts on a classic 45 degree turn (a deep `cube_turned`),
* every stroke is a single character (`|`, `/`, `\`, one per row)
  and the side face carries the depth gradient,
* **every frame visibly turns**: the silhouette breathes one cell
  per frame and no frame is ever a repeat of its neighbour.

```python
from ascii3d.rotation import frames, play, to_gif, save_frames
from ascii3d.examples import EXAMPLES

roomy = EXAMPLES['roomy']

timeline = frames(roomy, steps=24)     # 24 turned frames around 360
play(roomy, steps=24, fps=10)          # watch it spin in the terminal
save_frames(roomy, 'spin', steps=24)   # spin000.txt, spin001.txt, ...
to_gif(roomy, 'spin.gif', steps=24)    # animated GIF (needs Pillow)
```

## What a spin looks like

Six frames of the cube spin (of twenty-four, starting on the turn;
the side face breathes from 6 cells at the start to the full 9 at
edge-on and back down to 3 as the box passes face-on):

```python
from ascii3d.rotation import frames
from ascii3d.examples import EXAMPLES

timeline = frames(EXAMPLES['cube'], steps=24)
for i in (0, 3, 8):        # the turn, edge-on, the thinnest moment
    print(timeline[i])
```
```
                               _______
                              /      /\
                             /      /. \
      _______               /      /. : \
     /      /\             /      /. . :/
    /      /. \           /      /. . :/        _______
   /      /. : \         /      /. . :/        /      /\
  /      /. . :/        /      /. . :/        /      /. \
 /      /. . :/        /      /. . :/        /      /. : \
/______/. . :/        /______/. . :/        /______/. . :/
\ _  _ \. : /         \ _  _ \. : /         \ _  _ \. : /
 \\_\\_\\. /           \\_\\_\\. /           \\_\\_\\. /
  \______\/             \______\/             \______\/

                         _______
                        /\      \
                       / .\      \
                      / : .\      \
                      \: . .\      \
                       \: . .\      \
   _______              \: . .\      \         _______
  /\      \              \: . .\      \       /      /\
 / .\      \              \: . .\      \     /      /. \
/ : .\______\              \: . .\______\   /______/. : \
\ : ./ _  _ /               \ : ./ _  _ /   \ _  _ \. : /
 \ .//_//_//                 \ .//_//_//     \\_\\_\\. /
  \/______/                   \/______/       \______\/
```

The first strip is the first quarter (the box yawing deeper and
deeper into the turn); the second strip passes through the face-on
moment at 180 degrees -- the thinnest box, where the side wall
flips -- and returns toward the mirrored back view.

The rotation is honest physics mapped onto the docs' shear
language, and it reads through the silhouette *breathing*:

* the visible side face sweeps its width with the projected
  `|sin|` of the yaw -- a sliver at face-on, the full depth at
  edge-on, twice per turn (stepped one cell per frame, so no frame
  ever stalls or repeats);
* the face content swaps where the art face passes edge-on
  (90/270 degrees): the back half shows the mirrored art -- "mirror
  the strokes and swap the faces", `01-Theory/03-LookAnywhere.md`;
* the side wall switches left/right where the box passes face-on
  (0/180 degrees) -- exactly where the side face is thinnest, so
  the flip lands at the least noticeable moment, never as a jump
  at maximum width.

Every frame is a closed box: the front face's bottom edge never
drops, the side face's far edge meets the bottom closure exactly on
the shared corner, and the depth gradient stays inside the walls.
The whole sweep is VLM-audited: every frame a closed, turned box
with visible rotation (the review sheet and GIF live in the
repository's release assets).

## Options

| Argument | Meaning |
|----------|---------|
| `steps` | number of frames (default 24) |
| `start` | yaw of the first frame in degrees (default 45 = the turned view) |
| `pitch` | constant downward look, degrees (default 30; above 40 the top face grows) |
| `depth` | box depth (`None` = auto: deep, cube-like, sized so every frame steps) |
| `shade` | fill the side face with the depth gradient (default on) |

```python
to_gif(EXAMPLES['cube'], 'cube_turned_spin.gif', steps=24, fps=12)
```

## Meshes spin too

The theoretic arts ([theoretic](04-theoretic.md)) rotate with the
wireframe camera and support the extra axes:

| Axis | Motion |
|------|--------|
| `'y'` | turntable (default) |
| `'x'` | cartwheel |
| `'z'` | coin spin |

```python
from ascii3d.rotation import mesh_frames, mesh_to_gif
from ascii3d.theory import MESHES

torus = MESHES['torus']
timeline = mesh_frames(torus.vertices, torus.edges, steps=36)
mesh_to_gif(torus.vertices, torus.edges, 'torus.gif', steps=36)
```

## Command line

```shell
ascii3d --spin -e roomy              # spin in the terminal
ascii3d --gif spin.gif -e roomy      # ...or export a GIF
ascii3d --spin -e cube --pitch 50    # a taller top face
ascii3d --theoretic torus --spin     # the theoretic meshes spin too
```
