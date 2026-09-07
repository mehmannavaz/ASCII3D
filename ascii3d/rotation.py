"""The 360 degree rotation: the *turned* box spinning on a turntable.

The spin is a sequence of turned poses (:mod:`ascii3d.pose`), not a
free-angle projection.  The camera stays ABOVE the box for the whole
sweep -- every frame shows the top face receding DOWN and the depth
marching down the side face, exactly like the hand-drawn turned view
of the theory docs.  The flat, forward, "normal" view never appears;
frame 0 *is* the docs' classic turn (45 degrees), i.e. the turned
cube ``cube_turned``.

Every frame is drawn with single marching strokes (``|``, ``/``,
``\\``, one character per row) and a shaded side face -- no character
is ever stretched or doubled to fake depth.

Use it as:

* iterate over the frames (:func:`frames`),
* watch them spin in the terminal (:func:`play`),
* save them as text files (:func:`save_frames`), or
* export an animated GIF (:func:`to_gif`, needs Pillow).

Example:
    >>> from ascii3d.rotation import frames
    >>> for frame in frames(' _\\n|_|', steps=8):
    ...     print(frame)
    ...
"""

from __future__ import annotations

import sys
import time

from .pose import render_pose as _render_pose
from .pose import turntable_pose as _turntable_pose

__all__ = ['frames', 'play', 'play_frames', 'save_frames', 'to_gif',
           'mesh_frames', 'mesh_to_gif']


def frames(art: str, steps: int = 24, start: float = 45.0,
           pitch: float = 30.0, depth: int | None = None,
           shade: bool = True) -> list[str]:
    """Render *art* spinning through a full circle of turned views.

    The box yaws around the vertical axis while the camera keeps a
    constant downward look (*pitch*): the top face is visible in
    every frame and the depth always marches down -- the spin is
    "only going down", never the flat forward view.  Frame 0 is the
    docs' classic 45 degree turn (the turned cube).

    Args:
        art: The ASCII art as a plain string (the front face).
        steps: Number of frames in the sweep.
        start: Yaw of the first frame, degrees (45 = the docs'
            turned look; the default starts the spin on the turn).
        pitch: Constant downward look in degrees; above 40 the top
            face grows taller.  The sign is forced positive -- the
            camera never dips below the box.
        depth: Depth of the 3D box (``None`` = auto, substantial
            as the docs demand).
        shade: Fill the side face with the depth gradient.

    Returns:
        The list of frames, all padded to one canvas size so they
        can replace each other cleanly in a terminal or GIF.

    Raises:
        ValueError: If *steps* is < 2.
    """
    if steps < 2:
        raise ValueError('steps must be >= 2')
    raw = []
    for i in range(steps):
        theta = start + i * 360.0 / steps
        pose = _turntable_pose(theta, pitch=pitch)
        raw.append(_render_pose(art, pose, depth=depth, shade=shade))
    return _normalize_canvas(raw)


def _normalize_canvas(raw: list[str]) -> list[str]:
    """Pad every frame in *raw* to the same width and height.

    All frames of an animation must share one canvas size, otherwise
    the terminal redraw jitters frame by frame.
    """
    widths = [max((len(line) for line in frame.split('\n')), default=0)
              for frame in raw]
    heights = [frame.count('\n') + 1 for frame in raw]
    width, height = max(widths), max(heights)
    out = []
    for frame in raw:
        lines = frame.split('\n')
        lines = [line.ljust(width) for line in lines]
        top = (height - len(lines)) // 2
        bottom = height - len(lines) - top
        lines = [' ' * width] * top + lines + [' ' * width] * bottom
        out.append('\n'.join(lines))
    return out


def play_frames(timeline: list[str], fps: float = 10.0, loops: int = 1,
                stream=None) -> None:
    """Play a ready-made frame *timeline* in the terminal.

    Uses ANSI escape codes to redraw in place (hide cursor, home
    cursor, draw frame, repeat).  Pass ``loops=-1`` to spin forever
    until interrupted with Ctrl-C.  When the stream is not a tty the
    frames are just printed one after another.

    Args:
        timeline: Frames of identical canvas size (see
            :func:`frames`).
        fps: Frames per second.
        loops: How many full sweeps to play (``-1`` = forever).
        stream: Writable stream (defaults to ``sys.stdout``).
    """
    stream = stream if stream is not None else sys.stdout
    is_tty = hasattr(stream, 'isatty') and stream.isatty()
    hide, show, home, clear = ('', '', '', '')
    if is_tty:
        hide, show = '\x1b[?25l', '\x1b[?25h'
        home, clear = '\x1b[H', '\x1b[2J\x1b[H'
    delay = 1.0 / max(fps, 0.01)
    try:
        stream.write(hide + clear)
        loop = 0
        while loops < 0 or loop < loops:
            for frame in timeline:
                stream.write(home + frame + '\n')
                stream.flush()
                time.sleep(delay)
            loop += 1
    except KeyboardInterrupt:
        pass
    finally:
        stream.write(show + '\n')
        stream.flush()


def play(art: str, steps: int = 24, fps: float = 10.0,
         pitch: float = 30.0, depth: int | None = None,
         shade: bool = True, loops: int = 1, stream=None) -> None:
    """Play the 360 degree rotation of *art* in the terminal.

    Args:
        art: The ASCII art as a plain string.
        steps: Number of frames in the sweep.
        fps: Frames per second.
        pitch: Constant downward look, degrees (see :func:`frames`).
        depth: Depth of the 3D box (``None`` = auto).
        shade: Fill the side face with the depth gradient.
        loops: How many full sweeps to play (``-1`` = forever).
        stream: Writable stream (defaults to ``sys.stdout``).
    """
    timeline = frames(art, steps=steps, pitch=pitch, depth=depth,
                      shade=shade)
    play_frames(timeline, fps=fps, loops=loops, stream=stream)


def save_frames(art: str, prefix: str, steps: int = 24,
                pitch: float = 30.0, depth: int | None = None,
                shade: bool = True) -> list[str]:
    """Save every rotation frame to a numbered text file.

    Args:
        art: The ASCII art as a plain string.
        prefix: File path prefix; frames become ``prefix000.txt``,
            ``prefix001.txt``, ...
        steps: Number of frames in the sweep.
        pitch: Constant downward look, degrees.
        depth: Depth of the 3D box (``None`` = auto).
        shade: Fill the side face with the depth gradient.

    Returns:
        The list of file paths written.
    """
    paths = []
    for i, frame in enumerate(frames(art, steps=steps, pitch=pitch,
                                     depth=depth, shade=shade)):
        path = f'{prefix}{i:03d}.txt'
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(frame + '\n')
        paths.append(path)
    return paths


# ----------------------------------------------------------------------
# GIF export (optional, needs Pillow)
# ----------------------------------------------------------------------
def _save_gif(timeline: list[str], path: str, fps: float = 10.0,
              font_size: int = 14) -> str:
    """Write a frame *timeline* to *path* as an animated GIF."""
    from .raster import text_to_image
    duration = int(round(1000 / max(fps, 0.01)))
    images = [text_to_image(frame, font_size) for frame in timeline]
    images[0].save(path, save_all=True, append_images=images[1:],
                   duration=duration, loop=0, disposal=2)
    return path


def to_gif(art: str, path: str, steps: int = 24, fps: float = 10.0,
           pitch: float = 30.0, depth: int | None = None,
           shade: bool = True, font_size: int = 14) -> str:
    """Export the 360 degree rotation of *art* as an animated GIF.

    Each frame is drawn with a monospaced font on a dark background,
    exactly like it would look in a terminal.

    Args:
        art: The ASCII art as a plain string.
        path: Output file path (``.gif``).
        steps: Number of frames in the sweep.
        fps: Frames per second.
        pitch: Constant downward look, degrees.
        depth: Depth of the 3D box (``None`` = auto).
        shade: Fill the side face with the depth gradient.
        font_size: Glyph size in pixels.

    Returns:
        The *path* written.

    Raises:
        ImportError: If Pillow is not installed.
    """
    timeline = frames(art, steps=steps, pitch=pitch, depth=depth,
                      shade=shade)
    return _save_gif(timeline, path, fps=fps, font_size=font_size)


# ----------------------------------------------------------------------
# theoretic meshes keep the wireframe camera (they are not boxes)
# ----------------------------------------------------------------------
def mesh_frames(vertices, edges, steps: int = 24, start: float = 0.0,
                stop: float = 360.0, axis: str = 'y', pitch: float = 20.0,
                scale: float | None = None, zoom: float = 1.0
                ) -> list[str]:
    """Render a theoretic mesh spinning through a full circle.

    The 360 degree counterpart of :func:`frames` for the meshes of
    :mod:`ascii3d.theory` (or any vertices + edges pair), rendered
    with the wireframe camera of :mod:`ascii3d.wireframe`.

    Args:
        vertices: ``(n, 3)`` array of vertex positions (math units).
        edges: ``(i, j)`` index pairs.
        steps: Number of frames in the sweep.
        start: First angle, degrees.
        stop: Last angle, degrees.
        axis: Rotation axis: ``'y'`` (turntable), ``'x'`` (cartwheel)
            or ``'z'`` (coin spin).
        pitch: Constant camera elevation for axis ``'y'`` spins.
        scale: Mesh size in character cells.
        zoom: Extra scale factor.

    Returns:
        The frames, all padded to one canvas size.

    Raises:
        ValueError: If *axis* is unknown or *steps* is < 2.
    """
    from .wireframe import render_mesh
    if axis not in ('y', 'x', 'z'):
        raise ValueError(f"axis must be one of ('y', 'x', 'z'), "
                         f'not {axis!r}')
    if steps < 2:
        raise ValueError('steps must be >= 2')
    raw = []
    for i in range(steps):
        t = i / (steps - 1)
        angle = start + (stop - start) * t
        yaw = pitch_deg = roll = 0.0
        if axis == 'y':
            yaw, pitch_deg = angle, pitch
        elif axis == 'x':
            pitch_deg = angle
        else:
            roll = angle
        raw.append(render_mesh(vertices, edges, yaw=yaw,
                               pitch=pitch_deg, roll=roll, scale=scale,
                               zoom=zoom))
    return _normalize_canvas(raw)


def mesh_to_gif(vertices, edges, path: str, steps: int = 24,
                fps: float = 10.0, axis: str = 'y', pitch: float = 20.0,
                scale: float | None = None, zoom: float = 1.0,
                font_size: int = 14) -> str:
    """Export a spinning theoretic mesh as an animated GIF.

    Args:
        vertices: ``(n, 3)`` array of vertex positions (math units).
        edges: ``(i, j)`` index pairs.
        path: Output file path (``.gif``).
        steps: Number of frames in the sweep.
        fps: Frames per second.
        axis: See :func:`mesh_frames`.
        pitch: Constant camera elevation for turntable spins.
        scale: Mesh size in character cells.
        zoom: Extra scale factor.
        font_size: Glyph size in pixels.

    Returns:
        The *path* written.
    """
    timeline = mesh_frames(vertices, edges, steps=steps, axis=axis,
                           pitch=pitch, scale=scale, zoom=zoom)
    return _save_gif(timeline, path, fps=fps, font_size=font_size)
