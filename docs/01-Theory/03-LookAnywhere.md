# Look Anywhere

> **STATUS (v0.3.0):** implemented! The nine routes are live:
> `route(art, 'leftup')` and friends -- see the
> [Routes](../02-Usage/01-routes.md) usage page. The notes below are
> the original theory sketch, now backed by the box camera renderer
> (`ascii3d/pose.py`).

The idea: a turned art is a box seen from one side. But a box can be
seen from **nine** interesting directions -- the eight compass points
plus the front view:

```
leftup     up      rightup
left     center    right
leftdown  down     rightdown
```

## Up and Down

The same trick that turns an art left/right also works vertically:
instead of marching the *rows* sideways, the *depth* of the box
recedes up (looking down) or down (looking up from below). Looking
down on an art shows its **top face** dominating the frame; looking
up shows the bottom face. Every stroke stays a single character and
the side faces keep the marching look of the classic turn:

```
         ___________
        /          /
       /          /
      /          /
     /          /
    /          /
   /          / \
  /          /   \
 __________ /     \
\          \. : X #\
 \          \. : X /
  \          \. X /
   \          \: /
    \__________\/
  leftup (roomy)

 __________
|          |
 |          |
 |          |
  |          |
  |__________|\
   \           \
    \           \
    \           \
     \           \
      \           \
       \           \
       \           \
        |__________|\
  down (roomy)
```

## Down Left / Down Right / Up Left / Up Right

The diagonals combine a horizontal and a vertical gaze; the camera
sits on the corresponding corner of the 3x3 grid above. The box
camera draws the turned front face plus a taller top face (or a
bottom face, seen from below) and the shaded side wall, all with
single marching strokes:

```
         ___________
        /          /
       /          /
      /          /
     /          /
    /          /
   /          / \
  /          /   \
 __________ /     \
\  __  __  \. : X #\
 \ \  \\  \ \. : X /
  \ \__\\__\ \. X /
   \          \: /
    \__________\/
  leftup (head)
```

## Behind

Looking at the art from the back is the one route the shear trick
cannot fake (the engine would need to mirror the strokes *and* swap
the faces). The 360 degree rotation
(`ascii3d.rotation.frames`) passes through the behind view naturally
as the turntable sweeps -- the back half of the spin shows the
dotted back face of the box, the honest way to see it.
