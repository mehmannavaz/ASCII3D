# The 360 degree rotation

The full answer to *"look anywhere"*: spin the turned art around a
whole circle. The spin is a sequence of **turned poses**
(`ascii3d/pose.py`), not a free-angle projection:

* the camera stays **above** the box for the whole sweep -- the top
  face is visible in every frame and the depth always marches
  **down** the side face ("only going down", never looking up),
* the flat, forward, "normal" view never appears -- near face-on
  the box keeps a gentle half lean and a visible top face,
* frame 0 **is** the docs' classic turn, i.e. `cube_turned`,
* every stroke is a single character (`|`, `/`, `\`, one per row)
  and the side face carries the depth gradient.

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

Four frames of the cube spin (of sixteen, starting on the classic
turn):

```python
from ascii3d.rotation import frames
from ascii3d.examples import EXAMPLES

timeline = frames(EXAMPLES['cube'], steps=16)
for i in (0, 4, 8, 12):        # the turn, the mirror, the back, the return
    print(timeline[i])
```
```
   _______         _______         _______         _______    
  /      /\       /\      \       /      /\       /\      \   
 /      /. \     / .\      \     /      /. \     / .\      \  
/______/. : \   / : .\______\   /______/. : \   / : .\______\ 
\ _  _ \. : /   \ : ./ _  _ /   \ _  _ \. : /   \ : ./ _  _ / 
 \\_\\_\\. /     \ .//_//_//     \\_\\_\\. /     \ .//_//_//  
  \______\/       \/______/       \______\/       \/______/   
```

The sweep walks the four honest quadrants of the turntable: the
art (turned, never flat) for the first quarter, its mirror where
the box passes edge-on -- the "mirror the strokes and swap the
faces" back view of `01-Theory/03-LookAnywhere.md` -- the mirrored
content marching back the other way for the third quarter, and the
art again for the last.  Every frame is a closed box: the front
face's bottom edge never drops, the side face's far edge meets the
bottom closure exactly on the shared corner, and the depth
gradient stays inside the walls.

## Options

| Argument | Meaning |
|----------|---------|
| `steps` | number of frames (default 24) |
| `start` | yaw of the first frame in degrees (default 45 = the docs' turn) |
| `pitch` | constant downward look, degrees (default 30; above 40 the top face grows) |
| `depth` | box depth (`None` = auto, substantial) |
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
