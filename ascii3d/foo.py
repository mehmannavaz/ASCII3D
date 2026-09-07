"""Backwards compatible import path.

Historically the engine lived in this module, which is why the name is
``foo``.  The real implementation now lives in :mod:`ascii3d.engine`;
    this module re-exports it so that ``from ascii3d.foo import ascii``
    keeps working.
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

__all__ = [
    'SHADE_RAMP',
    'Ascii3D',
    'ascii',
    'mirror',
    'normalize',
    'turn',
    'turn_left',
    'turn_right',
]
