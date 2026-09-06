"""Command line interface for ASCII3D.

Run it as a module::

    python -m ascii3d --demo

or, once the package is installed, as a console script::

    ascii3d --demo
"""

from __future__ import annotations

import argparse
import sys

from .engine import turn
from .examples import EXAMPLES
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
        '-t', '--direction', choices=['left', 'right'], default='left',
        help='where the art turns to (default: left, showing the right side)')
    parser.add_argument(
        '-d', '--depth', type=int, default=1, metavar='N',
        help='how deep the box is, i.e. the size of the top/side faces '
             '(default: 1)')
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
        '--demo', action='store_true',
        help='render the built-in examples with both directions')
    parser.add_argument(
        '--list', action='store_true', dest='list_examples',
        help='list the built-in example arts')
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
    return turn(
        art,
        direction=args.direction,
        depth=args.depth,
        side=args.side,
        shade=args.shade,
        fill=args.fill[:1] if args.fill else None,
    )


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
            print('\n'.join(line.rstrip()
                           for line in EXAMPLES[name].splitlines()))
            print()
        return 0

    if args.demo:
        _run_demo()
        return 0

    art = _read_art(args)
    if art is None or not art.strip():
        parser.print_help()
        print('\nNo input art given. Try one of:')
        print('  ascii3d --demo            # watch the examples turn')
        print('  ascii3d --example cube -d 2')
        print('  cat box.txt | ascii3d -d 2')
        return 1

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
