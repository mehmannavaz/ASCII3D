# Look Anywhere

> **STATUS (v0.2.0):** implemented! The nine routes are live:
> `route(art, 'leftup')` and friends -- see the
> [Routes](../02-Usage/01-routes.md) usage page. The notes below are the
> original theory sketch, now backed by a real renderer.

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
instead of shearing the *rows* sideways, shear the *columns* up or
down. Looking down on an art shows its **top face** dominating the
frame; looking up shows the bottom face. In the engine this is done
with a true 3D camera (see `ascii3d/wireframe.py`) rather than a
shear, because a vertical shear would collide with the half-height
raster of the `_` strokes.

```
 ____________          __________
|           /|        //        \\
\____________/         ____________
 \          /         |__________|
 \__________/         |          |
   up (roomy,           down (roomy,
   depth 3)             depth 3)
```

## Down Left / Down Right / Up Left / Up Right

The diagonals combine a horizontal and a vertical gaze; the camera
sits on the corresponding corner of the 3x3 grid above. The wireframe
renderer extrudes the art into a box, rotates it to the corner angle
and masks the hidden lines behind the opaque front face, which keeps
the hand-drawn look of the two-face closure:

```
 ________/              /\_______
_________\\\           //\\     \\
___     ___ \          \\ \\      \\
   ___     ___\          \ \\ ________
      _________/          \//______/
  leftup (roomy)         rightdown (roomy)
```

## Behind

Looking at the art from the back is the one route the shear trick
cannot fake (the engine would need to mirror the strokes *and* swap
the faces). The 360 degree rotation
(`ascii3d.rotation.frames`) passes through the behind view naturally
as the turntable sweeps, which is the honest way to see it.
