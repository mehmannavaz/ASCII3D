# ASCII3D
The whole idea to make ASCII arts looks like 3D -- and now an engine that
actually does it.

## Getting start:
First of all install the ASCII3D library with:
```shell
pip install ascii3d
```
and here and example:
```python
from ascii3d import turn

print(turn(" _\n|_|"))
```
```
 __
/_/\
\_\/
```

That is the exact same box as `01-Theory/00-SimpleGaze.md` draws by hand:
the front face leans, the top face appears, the right side shows up.

Want it deeper? Pass a bigger `depth`:
```python
print(turn(" _\n|_|", depth=2, side=False))
```
```
  __
 / /
/_/
\_\
```

Check the [Usage](02-Usage/00-usage.md) pages for the full API --
turning right, shading the side face, the command line interface --
plus the new features: the [nine routes](02-Usage/01-routes.md), the
[360 degree rotation](02-Usage/02-rotation.md), [VLM
arts](02-Usage/03-vlm.md) and [theoretic arts](02-Usage/04-theoretic.md).
The [Theory](01-Theory/00-SimpleGaze.md) section explains how it all
works.

```python
from ascii3d import route
from ascii3d.rotation import play

print(route(" _\n|_|", "leftup"))   # look from the top-left corner
play(" _\n|_|", steps=12)           # spin it a full 360 degrees
```

## What's next?
You can continue this documentation with the `Next` button.
