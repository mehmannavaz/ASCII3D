# The nine routes

A *route* is where you stand while looking at the art. The engine
speaks all nine of them:

```
leftup     up      rightup
left     center    right
leftdown  down     rightdown
```

Two rendering styles cooperate:

* **left / right** reuse the classic shear of the
  [turn](00-usage.md#turning) engine -- byte-for-byte the look of the
  theory docs.
* **up / down / the diagonals / center** use the true 3D wireframe:
  the art is extruded into a box, the camera moves to the requested
  compass position, and hidden lines behind the front face are
  masked out.

## Quick start

```python
from ascii3d import route, nine_routes, contact_sheet
from ascii3d.examples import EXAMPLES

roomy = EXAMPLES['roomy']

print(route(roomy, 'left'))      # classic engine turn
print(route(roomy, 'leftup'))    # true 3D corner view
print(route(roomy, 'up'))        # look down on the top face
```

`nine_routes(art)` renders all of them at once, and
`contact_sheet(art)` lays them out as a labelled 3x3 gallery:

```python
print(contact_sheet(EXAMPLES['dot']))
```
```
-- leftup --   -- up --   -- rightup --
 _/\           |_|        /\__
____           __|        ____

-- left --   -- center --   -- right --
  __          _              __
 / /\        |_|            /\ \
/_/ /                       \ \_\
\_\/                         \/_/

-- leftdown --   -- down --   -- rightdown --
 _               /_|           _
_//              |_|          /\_\
\\\                           \/_/
```

## Direction convention

`route(art, 'left')` means the **art turns to the left** -- its right
side face becomes visible -- exactly matching
`turn(art, 'left')`. Symmetrically, `up` means the art tips away so
we look down on its **top** face, `down` looks at the bottom, and
the diagonals combine both components.

## Options

| Argument | Meaning |
|----------|---------|
| `direction` | one of the nine routes |
| `depth` | box depth (`None` = auto: scales with the art) |
| `zoom` | scale factor of the wireframe routes |
| `style` | `'auto'` (default), `'engine'` (left/right/center only) or `'wire'` (force the 3D renderer) |

## Command line

```shell
ascii3d -e roomy -t leftup          # one route
ascii3d --nine -e roomy             # the 3x3 contact sheet
cat myart.txt | ascii3d --nine
```

`-t left` / `-t right` still use the shear engine, so all the old
commands behave exactly as before.
