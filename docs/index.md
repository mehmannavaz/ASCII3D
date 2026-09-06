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

Check the [Usage](02-Usage/00-usage.md) page for the full API (turning
right, shading the side face, the command line interface), and the
[Theory](01-Theory/00-SimpleGaze.md) section for how it all works.

## What's next?
You can continue this documentation with the `Next` button.
