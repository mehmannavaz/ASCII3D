"""ASCII3D -- an engine to make ASCII art look 3D.

Library usage::

    from ascii3d import ascii, turn

    print(turn(' _\\n|_|', direction='left', depth=1))

Command line usage::

    python -m ascii3d --help
    ascii3d --demo
"""

from .engine import (  # noqa: F401
    SHADE_RAMP,
    Ascii3D,
    ascii,
    mirror,
    normalize,
    turn,
    turn_left,
    turn_right,
)
from . import version, utils, examples

__version__ = version.__version__

__all__ = [
    'ascii',
    'Ascii3D',
    'turn',
    'turn_left',
    'turn_right',
    'mirror',
    'normalize',
    'SHADE_RAMP',
    'version',
    'utils',
    'examples',
]
