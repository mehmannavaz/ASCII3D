# The nine routes

A *route* is where you stand while looking at the art. The engine
speaks all nine of them:

```
leftup     up      rightup
left     center    right
leftdown  down     rightdown
```

Two renderers cooperate:

* **left / right** reuse the classic shear of the
  [turn](00-usage.md#turning) engine -- byte-for-byte the look of the
  theory docs.
* **everything else** uses the *box camera* (`ascii3d/pose.py`): the
  art is the front face of a real box and the camera sits at the
  requested compass position. Every face is drawn with single
  marching strokes (`|`, `/`, `\`, one character per row) and the
  side face carries the depth gradient of the 2Sides note -- no
  character is ever stretched or doubled to fake depth.

## Quick start

```python
from ascii3d import route, nine_routes, contact_sheet
from ascii3d.examples import EXAMPLES

roomy = EXAMPLES['roomy']

print(route(roomy, 'left'))      # classic engine turn
print(route(roomy, 'leftup'))    # turned + looking down
print(route(roomy, 'up'))        # the top face dominating the frame
```

`nine_routes(art)` renders all of them at once, and
`contact_sheet(art)` lays them out as a labelled 3x3 gallery:

```python
print(contact_sheet(EXAMPLES['dot']))
```
```
-- leftup --     -- up --       -- rightup --  
      __               __       __             
     / /              / /       \ \            
    / /              / /         \ \           
   / /              / /           \ \          
  / /\             / /            /\ \         
 / /./            / /             \.\ \        
/_/./            /_/               \.\_\       
\_\/             |_|                \/_/       

-- left --       -- center --   -- right --    
   __              __            __            
  / /\            / /           /\ \           
 / / /           /_/            \ \ \          
/_/ /            |_|             \ \_\         
\_\/                              \/_/         

-- leftdown --   -- down --     -- rightdown --
 _                _                    _       
\_\              |_|                  /_/      
\  \             \  \                /  /      
 \  \             \  \              /  /       
  \  \             \  \            /  /        
   \  \             \  \          /  /         
    \  \             \  \        /  /          
     |_|\             |_|\      /|_|           
```

## How the box camera draws a view

A `Pose` places the box on the character grid with three numbers
(see `ascii3d/pose.py`):

* **lean** -- how many columns per row the front face marches
  sideways. `1` is the docs' 45 degree turn (`|` walls become `\`),
  `0.5` a gentle turn, negative the mirror image.
* **rise** -- rows of recede per depth unit, sign = looking down
  (+) or up (-). `1` is the classic turn, `2` makes the top face
  dominate (the `up` routes).
* **reach** -- how far the depth axis stretches sideways, 0 (face
  on) to 1.4 (edge on): the side face widens as the box rotates.

```python
from ascii3d.pose import Pose, render_pose, auto_depth

cube = EXAMPLES['cube']
print(render_pose(cube, Pose(lean=1, rise=1, side='right'),
                  depth=auto_depth(cube)))
```
```
   _______
  /      /\
 /      /  \
/______/    \
\ _  _ \. X /
 \\_\\_\\: /
  \______\/
```

At the classic 45 degree pose the box camera is **byte-identical**
to the docs engine -- `render_pose(art, Pose(lean=1, rise=1,
side='right', shade=False), depth=d) == turn(art, 'left', depth=d)`
for every example art.

## Direction convention

`route(art, 'left')` means the **art turns to the left** -- its
right side face becomes visible -- exactly matching
`turn(art, 'left')`. Symmetrically, `up` means we look down on the
art's **top** face, `down` looks up at the bottom face from below,
and the diagonals combine both components. `center` is the
straight-on view *with* the top face receding down -- even the
center cell of the gallery is a 3D view, never the flat 2D art.

## Options

| Argument | Meaning |
|----------|---------|
| `direction` | one of the nine routes |
| `depth` | box depth (`None` = auto: scales with the art, always substantial) |
| `style` | `'auto'` (default), `'engine'` (left/right/center only) or `'pose'` (force the box camera) |

## Command line

```shell
ascii3d -e roomy -t leftup          # one route
ascii3d --nine -e roomy             # the 3x3 contact sheet
cat myart.txt | ascii3d --nine
```

`-t left` / `-t right` still use the shear engine, so all the old
commands behave exactly as before.
