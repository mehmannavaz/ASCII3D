"""Setup script for the ASCII3D package.

Run ``pip install .`` from the repository root to install the library
and the ``ascii3d`` console command.
"""

from pathlib import Path

from setuptools import setup

LIBRARY_DIR = Path('ascii3d')

ROOT = Path(__file__).parent

# Read the version without importing the package (it needs numpy).
version_file = LIBRARY_DIR / 'version.py'
namespace = {}
exec(version_file.read_text(encoding='utf-8'), namespace)
__version__ = namespace['__version__']

long_description = (ROOT / 'README.md').read_text(encoding='utf-8')

setup(
    name='ascii3d',
    version=__version__,
    description='An engine to make ASCII art look 3D',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='mehmannavaz',
    author_email='mohammadmahanmehmannavaz@gmail.com',
    url='https://github.com/mehmannavaz/ASCII3D',
    license='GPL-3.0-or-later',
    packages=[str(LIBRARY_DIR)],
    python_requires='>=3.9',
    install_requires=[
        'numpy>=1.20',
    ],
    entry_points={
        'console_scripts': [
            'ascii3d = ascii3d.__main__:main',
        ],
    },
    keywords='ascii art 3d terminal rendering engine',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Terminals',
    ],
)
