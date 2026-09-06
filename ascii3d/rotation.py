"""The 360 degree rotation: spin an ASCII art like a turntable.

The art is extruded into a 3D box (see :mod:`ascii3d.wireframe`) and
rotated around a full circle, frame by frame.  The frames share one
canvas so the object does not jump around, and you can

* iterate over them (:func:`frames`),
* watch them spin in the terminal (:func:`play`),
* save them as text files (:func:`save_frames`), or
* export an animated GIF (:func:`to_gif`, needs Pillow).

Example:
    >>> from ascii3d.rotation import frames
    >>> for frame in frames(' _\\n|_|', steps=4):
    ...     print(frame)
    ...
"""

from __future__ import annotations

import sys
import time

from .routes import _auto_depth
from .wireframe import render_art as _render_art

__all__ = ['SPIN_AXES', 'frames', 'mesh_frames', 'play',
           'play_frames', 'save_frames', 'to_gif', 'mesh_to_gif']

SPIN_AXES = ('y', 'x', 'z')


def frames(art: str, steps: int = 24, start: float = 0.0,
           stop: float = 360.0, axis: str = 'y', pitch: float = 20.0,
           depth: int | None = None, zoom: float = 1.0,
           perspective: bool = True) -> list[str]:
    """Render *art* spinning through a full circle.

    The camera orbits around *axis*; *pitch* tips the camera down so
    the top face stays visible during a turntable spin (axis ``'y'``).

    Args:
        art: The ASCII art as a plain string.
        steps: Number of frames in the sweep.
        start: First angle, degrees.
        stop: Last angle, degrees (360 for a full turn).
        axis: Rotation axis: ``'y'`` (turntable), ``'x'`` (cartwheel)
            or ``'z'`` (coin spin).
        pitch: Constant camera elevation for axis ``'y'`` spins.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor.
        perspective: Unused placeholder for API symmetry (the
            wireframe camera is always weakly perspective).

    Returns:
        The list of frames, all padded to the same canvas size so
        they can replace each other cleanly.

    Raises:
        ValueError: If *axis* is unknown or *steps* is < 2.
    """
    if axis not in SPIN_AXES:
        raise ValueError(f'axis must be one of {SPIN_AXES}, '
                         f'not {axis!r}')
    if steps < 2:
        raise ValueError('steps must be >= 2')
    if depth is None:
        depth = _auto_depth(art)

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
        raw.append(_render_art(art, yaw=yaw, pitch=pitch_deg, roll=roll,
                               depth=depth, zoom=zoom))
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


def mesh_frames(vertices, edges, steps: int = 24, start: float = 0.0,
                stop: float = 360.0, axis: str = 'y', pitch: float = 20.0,
                scale: float | None = None, zoom: float = 1.0
                ) -> list[str]:
    """Render a theoretic mesh spinning through a full circle.

    The 360 degree counterpart of :func:`frames` for the meshes of
    :mod:`ascii3d.theory` (or any vertices + edges pair).

    Args:
        vertices: ``(n, 3)`` array of vertex positions (math units).
        edges: ``(i, j)`` index pairs.
        steps: Number of frames in the sweep.
        start: First angle, degrees.
        stop: Last angle, degrees.
        axis: Rotation axis: ``'y'``, ``'x'`` or ``'z'``.
        pitch: Constant camera elevation for axis ``'y'`` spins.
        scale: Mesh size in character cells.
        zoom: Extra scale factor.

    Returns:
        The frames, all padded to one canvas size.

    Raises:
        ValueError: If *axis* is unknown or *steps* is < 2.
    """
    from .wireframe import render_mesh
    if axis not in SPIN_AXES:
        raise ValueError(f'axis must be one of {SPIN_AXES}, '
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
         axis: str = 'y', pitch: float = 20.0,
         depth: int | None = None, zoom: float = 1.0,
         loops: int = 1, stream=None) -> None:
    """Play the 360 degree rotation of *art* in the terminal.

    Args:
        art: The ASCII art as a plain string.
        steps: Number of frames in the sweep.
        fps: Frames per second.
        axis: See :func:`frames`.
        pitch: Camera elevation for turntable spins.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor.
        loops: How many full sweeps to play (``-1`` = forever).
        stream: Writable stream (defaults to ``sys.stdout``).
    """
    timeline = frames(art, steps=steps, axis=axis, pitch=pitch,
                      depth=depth, zoom=zoom)
    play_frames(timeline, fps=fps, loops=loops, stream=stream)


def save_frames(art: str, prefix: str, steps: int = 24,
                axis: str = 'y', pitch: float = 20.0,
                depth: int | None = None, zoom: float = 1.0) -> list[str]:
    """Save every rotation frame to a numbered text file.

    Args:
        art: The ASCII art as a plain string.
        prefix: File path prefix; frames become ``prefix000.txt``,
            ``prefix001.txt``, ...
        steps: Number of frames in the sweep.
        axis: See :func:`frames`.
        pitch: Camera elevation for turntable spins.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor.

    Returns:
        The list of file paths written.
    """
    paths = []
    for i, frame in enumerate(frames(art, steps=steps, axis=axis,
                                     pitch=pitch, depth=depth, zoom=zoom)):
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
           axis: str = 'y', pitch: float = 20.0, depth: int | None = None,
           zoom: float = 1.0, font_size: int = 14) -> str:
    """Export the 360 degree rotation of *art* as an animated GIF.

    Each frame is drawn with a monospaced font on a dark background,
    exactly like it would look in a terminal.

    Args:
        art: The ASCII art as a plain string.
        path: Output file path (``.gif``).
        steps: Number of frames in the sweep.
        fps: Frames per second.
        axis: See :func:`frames`.
        pitch: Camera elevation for turntable spins.
        depth: Depth of the 3D box (``None`` = auto).
        zoom: Scale factor.
        font_size: Glyph size in pixels.

    Returns:
        The *path* written.

    Raises:
        ImportError: If Pillow is not installed.
    """
    from .raster import text_to_image  # noqa: F401  (optional dep guard)

    timeline = frames(art, steps=steps, axis=axis, pitch=pitch,
                      depth=depth, zoom=zoom)
    return _save_gif(timeline, path, fps=fps, font_size=font_size)


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
        pitch: Camera elevation for turntable spins.
        scale: Mesh size in character cells.
        zoom: Extra scale factor.
        font_size: Glyph size in pixels.

    Returns:
        The *path* written.
    """
    timeline = mesh_frames(vertices, edges, steps=steps, axis=axis,
                           pitch=pitch, scale=scale, zoom=zoom)
    return _save_gif(timeline, path, fps=fps, font_size=font_size)
