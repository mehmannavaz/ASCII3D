"""ASCII3D -- an engine to make ASCII art look 3D.

Library usage::

    from ascii3d import ascii, turn, route, nine_routes
    from ascii3d.rotation import frames, play, to_gif
    from ascii3d.theory import MESHES, render as render_mesh
    from ascii3d.vlm import VLMArtist

    print(turn(' _\\n|_|', direction='left', depth=1))
    print(route(' _\\n|_|', 'leftup'))
    for frame in frames(' _\\n|_|', steps=12):
        ...

Command line usage::

    python -m ascii3d --help
    ascii3d --demo
    ascii3d --nine -e roomy
    ascii3d --spin -e cube --gif spin.gif
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
from .routes import (  # noqa: F401
    ROUTES,
    contact_sheet,
    nine_routes,
    route,
)
from . import version, utils, examples  # noqa: F401
from . import wireframe, rotation, theory, raster  # noqa: F401

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
    'route',
    'ROUTES',
    'nine_routes',
    'contact_sheet',
    'version',
    'utils',
    'examples',
    'wireframe',
    'rotation',
    'theory',
    'raster',
]
