# Usage

## The library

Wrap an art with the `ascii` class (or use the `turn` shortcut) and ask
it to turn:

```python
from ascii3d import ascii, turn

art = ascii("""
 ______
| _  _ |
||_||_||
|______|
""")

print(art.turn_left(depth=2))
```

```
  _______
 /      /\
/______/  \
\ _  _ \   \
 \\_\\_\\  /
  \______\/
```

### Options

| Option | Values | What it does |
|--------|--------|--------------|
| `direction` | `'left'` (default) / `'right'` | where the art turns to; turning left reveals the right side face |
| `depth` | `0, 1, 2, ...` (default `1`) | how deep the box is; grows the top and side faces |
| `side` | `True` (default) / `False` | draw the visible side face; ragged arts (the invader) look best without it |
| `shade` | `False` (default) / `True` | fill the side face with a depth gradient `.:/X#` (light near, dark far) |
| `fill` | a character | fill the side face uniformly instead of the gradient |

```python
print(art.turn(direction='right', depth=3))
```

```
   _______
  /\      \
 /  \______\
/   / _  _ /
\  //_//_//
 \/______/
```

### Attributes

```python
art.length, art.width    # rows and columns of the front face
art.matrix               # numpy 2D char matrix of the art
art.turned_length        # length + 1  (the docs' formula, depth = 1)
art.turned_width         # width + length - 1
```

### Shading

The `10-TODO/01-2Sides3dRendering.md` idea ("show the depth with
white-gray-black from 0 to 1") is implemented as `shade`:

```python
from ascii3d.examples import EXAMPLES

print(turn(EXAMPLES['roomy'], depth=4, shade=True))
```

```
    ___________
   /          /\
  /          /X#\
 /          /:XX#\
/__________/.::XX#\
\          \..::XX#\
 \          \..::XX/
  \          \..::/
   \          \../
    \__________\/
```

A uniform texture works too, Rubik style: `fill='/'`.

## The command line

Install the package and an `ascii3d` command appears (it also works as
`python -m ascii3d`):

```shell
ascii3d --help
ascii3d --demo                          # render the built-in examples
ascii3d --list                          # show the built-in arts
ascii3d --example cube -d 2             # render an example
ascii3d examples/head.txt -t right      # render a file
cat myart.txt | ascii3d -d 3 --shade    # pipe art in
```

The same options as the library are available as flags: `-t/--direction`,
`-d/--depth`, `--side/--no-side`, `--shade` and `--fill`.

## Built-in examples

`dot`, `cube`, `head`, `roomy`, `rubik` and `invader` live in
`ascii3d.examples` (and as `.txt` files under `examples/`). The invader
is the art that started it all:

```shell
ascii3d --example invader -d 2 --no-side
```

```
      ___
     /  /
    /__/
   _\  \_
  _\      \_
  \  _    _  \
   \ \_\  \_\ \
    \  _    _  \  _
     \_\_\_\ \__\ \_\_\_\
       \_\_        _\_\
          \_\      \_\
```
