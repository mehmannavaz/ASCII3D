"""Example arts from the original test file, now used for real tests.

The Example1-4 arts below are kept exactly as they were written when
the project started; they are now rendered through the engine to make
sure every documented example still turns correctly.
"""

from pathlib import Path

import pytest

from ascii3d import ascii
from ascii3d.examples import EXAMPLES
from ascii3d.__main__ import main

Example1 = """
         __
       _|  |_
     _|      |_
    |  _    _  |
    | |_|  |_| |
 _  |  _    _  |  _
|_|_|_| |__| |_|_|_|
  |_|_        _|_|
    |_|      |_|
"""

Example2 = """
 __________
|  __  __  |
|_|0 ||0 |_|
| |__||__| |
|   ____   |
|__________|
"""

Example3 = """
 __________
|  __  __  |
| |  ||  | |
| |__||__| |
|          |
|__________|
"""

Example4 = """
 ______
| _  _ |
||_||_||
|______|
"""

ALL_EXAMPLES = ([Example1, Example2, Example3, Example4]
                + list(EXAMPLES.values()))


def test_answer():
    """Every example art turns in both directions without exploding."""
    for art in ALL_EXAMPLES:
        for direction in ('left', 'right'):
            for depth in (1, 2, 3):
                rendered = ascii(art).turn(direction, depth=depth)
                assert rendered.strip()
                assert '|' not in rendered
                # The height grows with the depth (turned_length = length + d)
                expected_rows = ascii(art).length + depth
                assert len(rendered.splitlines()) == expected_rows


@pytest.mark.parametrize('name', sorted(EXAMPLES))
def test_builtin_examples_render(name):
    art = EXAMPLES[name]
    assert ascii(art).turn_left(depth=2).strip()


def test_examples_directory_matches_the_module():
    for name, art in EXAMPLES.items():
        path = Path(__file__).parent.parent / 'examples' / f'{name}.txt'
        assert path.read_text(encoding='utf-8') == art


def test_demo_command(capsys):
    assert main(['--demo']) == 0
    out = capsys.readouterr().out
    assert 'invader' in out
    assert '/\\' in out


def test_cli_example_render(capsys):
    assert main(['--example', 'cube', '-d', '2']) == 0
    out = capsys.readouterr().out
    assert '\\' in out
    assert '/' in out


def test_cli_right_direction(capsys):
    assert main(['--example', 'cube', '-t', 'right', '-d', '1']) == 0
    out = capsys.readouterr().out
    assert '/' in out


def test_cli_no_input_prints_help(capsys, monkeypatch):
    class FakeTty:
        def isatty(self):
            return True

        def read(self):
            return ''

    monkeypatch.setattr('sys.stdin', FakeTty())
    assert main([]) == 1
    assert 'ascii3d' in capsys.readouterr().out


def test_cli_reads_a_file(tmp_path, capsys):
    art_file = tmp_path / 'box.txt'
    art_file.write_text(' _\n|_|', encoding='utf-8')
    assert main([str(art_file), '-d', '1']) == 0
    assert capsys.readouterr().out == ' __\n/_/\\\n\\_\\/\n'


def test_cli_list(capsys):
    assert main(['--list']) == 0
    out = capsys.readouterr().out
    for name in EXAMPLES:
        assert name in out
