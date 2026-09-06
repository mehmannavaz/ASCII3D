"""Command line interface for ASCII3D.

Run it as a module::

    python -m ascii3d --demo
    python -m ascii3d --nine -e roomy
    python -m ascii3d --spin -e cube

or, once the package is installed, as a console script::

    ascii3d --demo
"""

from __future__ import annotations

import argparse
import sys

from .engine import turn
from .examples import EXAMPLES
from .routes import ROUTES, contact_sheet, route as route_render
from .rotation import play, to_gif
from .theory import MESHES
from . import utils
from .version import __version__

__all__ = ['main']


def build_parser() -> argparse.ArgumentParser:
    """Build the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog='ascii3d',
        description='An engine to make ASCII art look 3D.',
        epilog='Pipe art in via stdin:  cat box.txt | ascii3d -d 2')
    parser.add_argument(
        'files', nargs='*', metavar='FILE',
        help='ASCII art file(s) to turn (default: stdin when piped)')
    parser.add_argument(
        '-e', '--example', metavar='NAME', choices=sorted(EXAMPLES),
        help='use a built-in example art instead of a file')
    parser.add_argument(
        '-t', '--direction', choices=sorted(ROUTES), default='left',
        help='where the art turns to: left/right use the classic '
             'engine shear, the other routes use the box camera pose '
             'renderer (default: left)')
    parser.add_argument(
        '-d', '--depth', type=int, default=1, metavar='N',
        help='how deep the box is, i.e. the size of the top/side '
             'faces (default: 1, routes/spins pick a fitting value '
             'when left at 1)')
    parser.add_argument(
        '--side', dest='side', action='store_true', default=True,
        help='draw the visible side face (default)')
    parser.add_argument(
        '--no-side', dest='side', action='store_false',
        help='only draw the front and top faces (best for ragged art '
             'such as the invader)')
    parser.add_argument(
        '--shade', action='store_true',
        help='shade the side face with a depth gradient (.:/X#)')
    parser.add_argument(
        '--fill', metavar='CHAR',
        help='fill the side face uniformly with CHAR (e.g. "/")')
    parser.add_argument(
        '--zoom', type=float, default=1.0, metavar='F',
        help='(deprecated) kept for compatibility, ignored')
    parser.add_argument(
        '--no-shade', dest='shade', action='store_false', default=True,
        help='spin frames: leave the side face unshaded')
    parser.add_argument(
        '--nine', action='store_true',
        help='render the art from all nine routes as a 3x3 gallery')
    parser.add_argument(
        '--spin', nargs='?', type=int, const=24, metavar='STEPS',
        help='play a 360 degree rotation in the terminal '
             '(default steps: 24)')
    parser.add_argument(
        '--fps', type=float, default=10.0, metavar='F',
        help='frames per second of --spin (default: 10)')
    parser.add_argument(
        '--axis', choices=('y', 'x', 'z'), default='y', metavar='A',
        help='rotation axis for --theoretic spins: y (turntable), '
             'x (cartwheel) or z (coin spin) (default: y)')
    parser.add_argument(
        '--pitch', type=float, default=30.0, metavar='DEG',
        help='constant downward look of --spin in degrees; the '
             'camera always stays above the box (default: 30)')
    parser.add_argument(
        '--gif', metavar='PATH',
        help='export the 360 degree rotation as an animated GIF '
             'instead of playing it (needs Pillow)')
    parser.add_argument(
        '--theoretic', metavar='NAME', choices=sorted(MESHES),
        help='render a theoretic (mathematical) ASCII art: cube, '
             'sphere, torus, helix, ...')
    parser.add_argument(
        '--vlm', metavar='PROMPT',
        help='generate an ASCII art with a vision language model '
             '(needs ASCII3D_API_KEY), then render it normally')
    parser.add_argument(
        '--vlm-describe', action='store_true',
        help='let the VLM describe the input art (text mode)')
    parser.add_argument(
        '--vlm-vision', action='store_true',
        help='let the VLM describe the rendered 3D frame (image '
             'mode, needs Pillow)')
    parser.add_argument(
        '--raw', action='store_true',
        help='with --vlm: print the generated art without rendering')
    parser.add_argument(
        '--demo', action='store_true',
        help='render the built-in examples with both directions')
    parser.add_argument(
        '--list', action='store_true', dest='list_examples',
        help='list the built-in example arts')
    parser.add_argument(
        '--meshes', action='store_true', dest='list_meshes',
        help='list the theoretic meshes')
    parser.add_argument(
        '--version', action='version',
        version=f'%(prog)s {__version__}')
    return parser


def _read_art(args: argparse.Namespace) -> str | None:
    """Collect the art to render from --example, files or stdin."""
    if args.example:
        return EXAMPLES[args.example]
    if args.files:
        chunks = []
        for path in args.files:
            with open(path, encoding='utf-8') as handle:
                chunks.append(handle.read())
        return '\n'.join(chunks)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def _render(art: str, args: argparse.Namespace) -> str:
    """Render one art with the CLI options."""
    if args.direction in ('left', 'right'):
        # Classic engine shear: exact look of the theory docs.
        return turn(
            art,
            direction=args.direction,
            depth=args.depth,
            side=args.side,
            shade=args.shade,
            fill=args.fill[:1] if args.fill else None,
        )
    # Any of the other routes: the box camera pose renderer.
    depth = None if args.depth <= 1 else args.depth
    return route_render(art, direction=args.direction, depth=depth)


def _warn_if_wide(rendered: str) -> None:
    """Gently warn when the result is wider than the terminal."""
    width = max((len(line) for line in rendered.splitlines()), default=0)
    try:
        if not utils.fit_size(width, 0):
            print(f'ascii3d: note: output is {width} columns wide, '
                  'your terminal may wrap it', file=sys.stderr)
    except Exception:  # pragma: no cover - never crash on a size check
        pass


def _run_demo() -> None:
    """Render the built-in examples with both directions."""
    for name in ('cube', 'head'):
        art = EXAMPLES[name]
        print(f'# {name} (front view)')
        print('\n'.join(line.rstrip() for line in art.splitlines()))
        for direction in ('left', 'right'):
            print(f'# {name} turned to the {direction}, depth 2')
            print(turn(art, direction=direction, depth=2))
            print()
    print('# invader turned to the left, depth 2 (no side face)')
    print(turn(EXAMPLES['invader'], direction='left', depth=2, side=False))


def _run_vlm(args: argparse.Namespace, art: str | None) -> int:
    """Handle the --vlm / --vlm-describe / --vlm-vision flags."""
    from .vlm import VLMArtist
    artist = VLMArtist()
    try:
        if args.vlm:
            generated = artist.generate(args.vlm)
            if args.raw:
                print(generated)
                return 0
            print('# generated by the VLM:')
            print(generated)
            print(f'# rendered to {args.direction}:')
            print(_render(generated, args))
            return 0
        if args.vlm_vision:
            if not art:
                print('ascii3d: --vlm-vision needs an art '
                      '(use -e NAME, a FILE or stdin)',
                      file=sys.stderr)
                return 1
            answer = artist.describe_render(
                art, direction=args.direction,
                depth=None if args.depth <= 1 else args.depth)
            print(answer)
            return 0
        if args.vlm_describe:
            if not art:
                print('ascii3d: --vlm-describe needs an art '
                      '(use -e NAME, a FILE or stdin)',
                      file=sys.stderr)
                return 1
            print(artist.describe(art))
            return 0
    except Exception as exc:
        print(f'ascii3d: vlm error: {exc}', file=sys.stderr)
        return 1
    return 0  # pragma: no cover - unreachable


def main(argv: list[str] | None = None) -> int:
    """Entry point of the ``ascii3d`` command.

    Args:
        argv: The command line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit code (0 on success, 1 on bad input).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_examples:
        for name in sorted(EXAMPLES):
            print(f'{name}:')
            art_lines = EXAMPLES[name].splitlines()
            print('\n'.join(line.rstrip() for line in art_lines))
            print()
        return 0

    if args.list_meshes:
        for name in sorted(MESHES):
            shape = MESHES[name]
            print(f'{name:14s} {shape.n_vertices:3d} vertices, '
                  f'{shape.n_edges:3d} edges')
        return 0

    if args.demo:
        _run_demo()
        return 0

    if args.vlm or args.vlm_describe or args.vlm_vision:
        art = None
        if not args.vlm:
            art = _read_art(args)
            if art is not None:
                art = art.strip('\n')
        return _run_vlm(args, art)

    if args.theoretic:  # noqa: E128
        from .rotation import (mesh_frames, mesh_to_gif, play_frames)
        from .theory import render as render_mesh
        shape = MESHES[args.theoretic]
        if args.gif:
            mesh_to_gif(shape.vertices, shape.edges, args.gif,
                        steps=args.spin or 24, fps=args.fps,
                        axis=args.axis, pitch=args.pitch)
            print(f'ascii3d: wrote {args.gif}')
            return 0
        if args.spin:
            timeline = mesh_frames(shape.vertices, shape.edges,
                                   steps=args.spin, axis=args.axis,
                                   pitch=args.pitch)
            play_frames(timeline, fps=args.fps)
            return 0
        print(render_mesh(args.theoretic, pitch=args.pitch))
        return 0

    art = _read_art(args)
    if art is None or not art.strip():
        parser.print_help()
        print('\nNo input art given. Try one of:')
        print('  ascii3d --demo            # watch the examples turn')
        print('  ascii3d --example cube -d 2')
        print('  ascii3d --nine -e roomy    # all nine routes')
        print('  ascii3d --spin -e roomy    # 360 degree rotation')
        print('  ascii3d --theoretic sphere # theoretic ascii art')
        print('  cat box.txt | ascii3d -d 2')
        return 1
    art = art.strip('\n')

    if args.gif:
        to_gif(art, args.gif, steps=args.spin or 24, fps=args.fps,
               pitch=args.pitch, shade=args.shade,
               depth=None if args.depth <= 1 else args.depth)
        print(f'ascii3d: wrote {args.gif}')
        return 0

    if args.spin:
        play(art, steps=args.spin, fps=args.fps, pitch=args.pitch,
             shade=args.shade,
             depth=None if args.depth <= 1 else args.depth)
        return 0

    if args.nine:
        print(contact_sheet(
            art, depth=None if args.depth <= 1 else args.depth))
        return 0

    rendered = _render(art, args)
    _warn_if_wide(rendered)
    print(rendered)
    return 0


if __name__ == '__main__':  # pragma: no cover
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # The consumer closed the pipe (e.g. `ascii3d --demo | head`).
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        raise SystemExit(0)
