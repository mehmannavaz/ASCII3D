"""Tests for the ASCII3D rendering engine.

The golden outputs in this file were checked against the hand drawn
examples of the theory documentation (``docs/01-Theory``).
"""

import pytest

from ascii3d import ascii, turn, turn_left, turn_right, mirror, normalize


DOT = """\
 _
|_|
"""

CUBE = """\
 ______
| _  _ |
||_||_||
|______|
"""

# docs/01-Theory/00-SimpleGaze.md -- "to the left"
DOT_TURNED = (
    ' __\n'
    '/_/\\\n'
    '\\_\\/'
)

CUBE_TURNED_D2 = (
    '  _______\n'
    ' /      /\\\n'
    '/______/  \\\n'
    '\\ _  _ \\   \\\n'
    ' \\\\_\\\\_\\\\  /\n'
    '  \\______\\/'
)


class TestParsing:
    def test_dimensions(self):
        art = ascii(DOT)
        assert art.length == 2
        assert art.width == 3

    def test_leading_and_trailing_blank_lines_are_dropped(self):
        art = ascii('\n\n' + DOT + '\n\n')
        assert art.length == 2

    def test_interior_blank_line_is_kept(self):
        art = ascii(' __ \n|__|\n\n|__|')
        assert art.length == 4

    def test_rows_are_padded_to_a_rectangle(self):
        rows = normalize('ab\na')
        assert rows == ['ab', 'a ']

    def test_matrix_shape(self):
        art = ascii(DOT)
        assert art.matrix.shape == (2, 3)
        assert art.matrix[1, 0] == '|'

    def test_doc_formulas(self):
        art = ascii(DOT)
        assert art.turned_length == art.length + 1
        assert art.turned_width == art.width + art.length - 1

    def test_empty_art_is_rejected(self):
        with pytest.raises(ValueError):
            ascii('   \n  ')

    def test_non_string_is_rejected(self):
        with pytest.raises(TypeError):
            ascii([' _ ', '|_|'])

    def test_str_returns_normalized_art(self):
        assert str(ascii(DOT)) == ' _\n|_|'


class TestTurnLeft:
    def test_golden_output_from_the_docs(self):
        assert ascii(DOT).turn_left() == DOT_TURNED

    def test_golden_output_cube(self):
        assert ascii(CUBE).turn_left(depth=2) == CUBE_TURNED_D2

    def test_verticals_become_backslashes(self):
        turned = ascii(CUBE).turn_left()
        assert '|' not in turned
        assert '\\' in turned

    def test_height_grows_with_depth(self):
        art = ascii(CUBE)
        for depth in range(0, 4):
            lines = art.turn_left(depth=depth).splitlines()
            assert len(lines) == art.length + depth

    def test_depth_zero_returns_the_art(self):
        assert ascii(CUBE).turn_left(depth=0) == str(ascii(CUBE))

    def test_depth_must_be_positive(self):
        with pytest.raises(ValueError):
            ascii(DOT).turn_left(depth=-1)

    def test_side_face_is_optional(self):
        with_side = ascii(CUBE).turn_left(depth=1)
        without_side = ascii(CUBE).turn_left(depth=1, side=False)
        # The side face adds the far edge and the closing bottom edge.
        assert len(without_side) < len(with_side)

    def test_shading_fills_the_side_face(self):
        shaded = ascii(CUBE).turn_left(depth=3, shade=True)
        outline = ascii(CUBE).turn_left(depth=3)
        assert any(ch in '.:/X#' for ch in shaded)
        assert not any(ch in 'X#' for ch in outline)

    def test_uniform_fill(self):
        filled = ascii(CUBE).turn_left(depth=3, fill='/')
        assert filled.count('/') > ascii(CUBE).turn_left(depth=3).count('/')


class TestTurnRight:
    def test_golden_output_from_the_docs(self):
        # docs/01-Theory/00-SimpleGaze.md -- "to the right"
        assert ascii(DOT).turn_right() == ' __\n/\\_\\\n\\/_/'

    def test_turn_right_is_the_mirror_of_turn_left(self):
        art = ascii(CUBE)
        assert art.turn_right(depth=2) == mirror(art.turn_left(depth=2))

    def test_verticals_become_slashes(self):
        turned = ascii(CUBE).turn_right()
        assert '|' not in turned
        assert '/' in turned


class TestTurnDispatch:
    def test_turn_defaults_to_left(self):
        assert turn(CUBE) == ascii(CUBE).turn_left()

    def test_turn_right_dispatch(self):
        assert turn(CUBE, 'right') == ascii(CUBE).turn_right()

    def test_unknown_direction(self):
        with pytest.raises(ValueError):
            turn(CUBE, 'up')

    def test_shortcuts(self):
        assert turn_left(CUBE) == ascii(CUBE).turn_left()
        assert turn_right(CUBE) == ascii(CUBE).turn_right()

    def test_render_alias(self):
        assert ascii(CUBE).render() == ascii(CUBE).turn()


class TestMirror:
    def test_mirror_swaps_diagonals(self):
        assert mirror('/\\') == '/\\'

    def test_mirror_swaps_brackets(self):
        # '([)' reversed is ')['+'(' and each bracket is swapped
        assert mirror('([)') == '(])'

    def test_mirror_reverses_plain_text(self):
        assert mirror('abc') == 'cba'

    def test_mirror_is_an_involution(self):
        art = CUBE
        assert mirror(mirror(art)) == '\n'.join(
            line.rstrip() for line in normalize(art))
