# ASCII3D
An engine to make ASCII looks like 3D!

Give it any 2D ASCII art and it will *turn* it for you: the front face is
sheared, a top face and a side face are added, and the vertical strokes
become diagonals -- the same trick the theory docs in this repository
have been sketching by hand since day one, now done automatically.

```
 ______      turned to the left (depth 2)      turned to the right (depth 2)
| _  _ |
||_||_||       _______                           _______
|______|      /      /\                         /\      \
             /______/  \                       /  \______\
             \ _  _ \   \                     /   / _  _ /
              \\_\\_\\  /                     \  //_//_//
               \______\/                       \/______/
```

New in the `pose` line: view the art from **nine directions**,
spin the *turned* cube a full **360 degrees** (the camera always
above the box, the depth always marching down -- never the flat
forward view), draw **theoretic** (mathematical) shapes, and
generate or analyse arts with a **vision language model**:

```
cube_turned_spin.gif, four of the 24 frames:

   _______             _______           _______            _______
  /      /\           /      /\         /\      \          /      /\
 /      /  \         /      /  \       /  \      \        /      /  \
/______/    \       ______ /    \     /    \______\      / ______   \
\ _  _ \. X /             \. : #/     \ X ./ _  _ /       | _  _ |: /
 \\_\\_\\: /               \. X/       \ ://_//_//         ||_||_||/
  \______\/                 \ /         \/______/          |______|

   45 degrees        90: edge on,      225: the back,     337: coming
   (the docs'        the art hides     shows the          back around,
   classic turn,     behind the box    mirrored art       still turned
   = cube_turned)                      (LookAnywhere)     -- never flat
```


Every frame is drawn with single marching strokes (`|`, `/`, `\`,
one character per row) and a shaded side face -- no character is
ever stretched or doubled to fake depth.

## Installation:
### PyPi(TODO):
```shell
pip install ascii3d
```

### Manual:
```shell
git clone https://github.com/mehmannavaz/ASCII3D.git
cd ASCII3D
pip install .
```

## Usage:
### Module
```shell
python -m ascii3d --help
# OR
ascii3d --help
```

Render a file, a built-in example or piped input:
```shell
ascii3d examples/cube.txt -d 2            # turn to the left, depth 2
ascii3d --example cube -t right -d 2      # turn to the right
ascii3d --example invader -d 2 --no-side  # ragged art looks best without a side face
ascii3d --nine -e roomy                   # the 3x3 gallery of all nine routes
ascii3d --spin -e roomy                   # 360 degree rotation in the terminal
ascii3d --gif spin.gif -e roomy           # ...or as an animated GIF
ascii3d --theoretic torus                 # a mathematical donut
ascii3d --vlm "a dragon" -t leftup        # let a vision model draw it
ascii3d --demo                            # watch all examples turn
cat myart.txt | ascii3d -d 3 --shade
```

### Library
```python
from ascii3d import ascii, turn, route, nine_routes

# quick one-liner
print(turn(' _\n|_|', depth=1))
#  __
# /_/\
# \_\/

# or keep the art around as an object
art = ascii(open('examples/head.txt').read())
print(art.turn_left(depth=3))
#    ___________
#   /          /\
#  /          /  \
# /__________/    \
# \  __  __  \     \
#  \ \  \\  \ \     \
#   \ \__\\__\ \    /
#    \          \  /
#     \__________\/

# look from any of the nine directions
print(route(' _\n|_|', 'leftup'))

# the 360 degree rotation
from ascii3d.rotation import frames, play, to_gif
timeline = frames(art.art, steps=24)   # turned frames, same canvas
play(art.art, fps=10)                  # terminal animation (camera above)
to_gif(art.art, 'spin.gif')            # animated GIF
```

### VLM arts
With an OpenAI-compatible API key in `ASCII3D_API_KEY` (default
endpoint: Z.ai):

```python
from ascii3d.vlm import VLMArtist

artist = VLMArtist()
cat = artist.generate('a sitting cat, side view, clean outline')
print(artist.describe_render(cat, 'leftup'))  # the VLM looks at the 3D frame
```

The `vlm_cat`, `vlm_house`, `vlm_rocket` and `vlm_robot` examples
were generated this way -- a vision model drew them, the engine turns
them.

### Theoretic arts
```python
from ascii3d.theory import MESHES, render
from ascii3d.rotation import mesh_frames, play_frames

print(render('dodecahedron'))
torus = MESHES['torus']
play_frames(mesh_frames(torus.vertices, torus.edges, steps=36), fps=12)
```

Platonic solids, a wireframe sphere, torus, helices, a Moebius strip
and a sine field -- all spinning in ASCII.

Shading fills the side face with a depth gradient (light near, dark far),
like the `2Sides3dRendering` TODO asked for:

```python
from ascii3d import turn
from ascii3d.examples import EXAMPLES

print(turn(EXAMPLES['rubik'], depth=3, fill='/'))
#    ___________
#   /          /\
#  /          ///\
# /__________/////\
# \   \  \   \/////\
#  \   \  \   \/////\
#   \   \  \   \/////
#    \   \  \   \///
#     \___\__\___\/
```

## How does it work?
The whole theory lives in the `docs/` folder (start with
`01-Theory/00-SimpleGaze.md`); the engine implements it in four steps:

1. **Shear the front face** -- every row of the art is shifted one column
   to the right (turning left) which makes the face lean like a 3D plane.
2. **Tilt the verticals** -- every `|` becomes `\` (left turn) or `/`
   (right turn) so the vertical edges of the art follow the shear.
3. **Build the top face** -- the first row of the art is pushed up and
   aside, closed with `/` diagonals; this is the "add one line to the
   top" rule from `02-HowToTurn.md`.
4. **Close the silhouette** -- the visible side face (right one when
   turning left) is drawn with `\` edges and can be shaded by depth.

The new features add a second renderer under the same roof:
`ascii3d.pose` -- the *box camera* -- generalises the docs' shear to
any viewing angle with three grid numbers (`lean`, `rise`, `reach`),
draws every face between computed corner points with one-character
marching strokes, and shades the side face with the depth gradient
of the `2Sides3dRendering` TODO. At the classic 45 degree pose it is
**byte-identical** to the engine above (verified by the test suite
for every example art). The nine routes, the 360 rotation and the
spins all ride on this renderer; the routes `left`/`right` still use
the classic shear so the doc examples stay byte-identical. The
theoretic meshes keep their own wireframe camera
(`ascii3d.wireframe`), which parses strokes into real 3D segments
and rotates them with yaw/pitch matrices.

The size formulas from the theory docs hold:

```python
art = ascii(' _\n|_|')
art.length, art.width          # 2, 3
art.turned_length              # length + depth = 3
art.turned_width               # width  + length - 1 = 4
```

## API cheat sheet
| Call | What it does |
|------|--------------|
| `ascii(art)` | wrap an art (rows/cols/matrix attributes) |
| `art.turn_left(depth=1, side=True, shade=False, fill=None)` | turn to the left, reveal the right side |
| `art.turn_right(depth=1, ...)` | turn to the right, reveal the left side |
| `art.turn(direction, ...)` | dispatch on `'left'` / `'right'` |
| `turn(art, direction, ...)` | module level shortcut |
| `mirror(art)` | horizontal mirror (swaps `/` `\` and brackets) |
| `route(art, direction, ...)` | one of the **nine routes** (leftup ... rightdown) |
| `render_pose(art, pose)` / `Pose(...)` | the box camera at any angle |
| `nine_routes(art)` | dict of all nine route renders |
| `contact_sheet(art)` | the labelled 3x3 gallery |
| `frames(art, steps=24, pitch=30)` | the 360 rotation of the *turned* view |
| `play(art)` / `play_frames(timeline)` | terminal animation |
| `to_gif(art, 'spin.gif')` | animated GIF export (Pillow) |
| `MESHES` / `render('torus')` | theoretic meshes and their renders |
| `mesh_frames(vertices, edges)` | 360 rotation for meshes |
| `VLMArtist().generate(prompt)` | ASCII art from a vision model |
| `VLMArtist().describe_render(art)` | the model judges the rendered 3D frame |

## Development
```shell
pip install -r requirements.txt
pytest                 # 226 tests, including golden outputs from the docs
python -m ascii3d --demo
python -m ascii3d --nine -e roomy
mkdocs serve           # preview the documentation
```

## Roadmap
- [x] Turn left / right with adjustable depth
- [x] Top and side faces with optional depth shading
- [x] Look anywhere: the nine routes (up / down / diagonals)
- [x] 360 degree rotation (terminal animation + GIF)
- [x] Theoretic ASCII arts (Platonic solids, sphere, torus, ...)
- [x] VLM integration (generate + analyse)
- [ ] Publish to PyPI

## Origin of the idea
This project starts when I saw this [Invader ASCII art](https://www.asciiart.eu/video-games/other):
```
Invader
    ____   Turned invader               Normal invader
   /___/\_                                __
  _\   \/_/\__                          _|  |_
__\       \/_/\                       _|      |_
\   __    __ \ \                     |  _    _  |
__\  \_\   \_\ \ \   __               | |_|  |_| |
/_/\\   __   __  \ \_/_/\           _  |  _    _  |  _
\_\/_\__\/\__\/\__\/_\_\/          |_|_|_| |__| |_|_|_|
   \_\/_/\       /_\_\/              |_|_        _|_|
      \_\/       \_\/                  |_|      |_|
```
so I said to myself... it can be an engine!
