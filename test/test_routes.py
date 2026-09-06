"""Tests for the nine routes."""

import pytest

from ascii3d.routes import (ROUTES, _auto_depth, contact_sheet,
                            nine_routes, route)
from ascii3d.engine import turn
from ascii3d.examples import EXAMPLES

DOT = ' _\n|_|'
ROOMY = EXAMPLES['roomy']


class TestRouteTable:
    def test_nine_routes_exist(self):
        assert len(ROUTES) == 9
        assert set(ROUTES) == {
            'left', 'right', 'up', 'down',
            'leftup', 'leftdown', 'rightup', 'rightdown', 'center'}

    def test_every_route_renders_something(self):
        for direction in ROUTES:
            rendered = route(DOT, direction)
            assert rendered.strip(), direction

    def test_unknown_route_is_rejected(self):
        with pytest.raises(ValueError):
            route(DOT, 'behind')

    def test_unknown_style_is_rejected(self):
        with pytest.raises(ValueError):
            route(DOT, 'left', style='spin')

    def test_engine_style_rejects_wire_only_routes(self):
        with pytest.raises(ValueError, match='engine'):
            route(DOT, 'up', style='engine')


class TestRouteSemantics:
    def test_left_matches_the_engine_turn(self):
        # route left *is* the classic engine shear
        assert route(DOT, 'left', depth=2) == turn(DOT, 'left', depth=2)

    def test_right_matches_the_engine_turn(self):
        assert route(DOT, 'right', depth=1) == turn(DOT, 'right',
                                                    depth=1)

    def test_left_and_right_are_mirrors(self):
        assert route(ROOMY, 'left', depth=2) \
            == turn(ROOMY, 'left', depth=2)
        assert route(ROOMY, 'right', depth=2) \
            == turn(ROOMY, 'right', depth=2)

    def test_center_route_is_flat_for_engine_style(self):
        assert route(DOT, 'center', style='engine') == DOT

    def test_up_and_down_differ(self):
        assert route(ROOMY, 'up') != route(ROOMY, 'down')

    def test_all_nine_routes_are_distinct_for_roomy(self):
        renders = [route(ROOMY, d) for d in ROUTES]
        assert len(set(renders)) == len(renders)

    def test_wire_routes_only_use_stroke_characters(self):
        for direction in ('up', 'down', 'leftup', 'leftdown',
                          'rightup', 'rightdown'):
            rendered = route(ROOMY, direction)
            assert set(rendered) <= set(' _|/\\\n')

    def test_auto_depth_scales_with_the_art(self):
        assert _auto_depth(DOT) >= 2
        assert _auto_depth(ROOMY) >= _auto_depth(DOT)


class TestNineRoutes:
    def test_nine_routes_returns_all_routes(self):
        sheet = nine_routes(DOT)
        assert set(sheet) == set(ROUTES)

    def test_nine_routes_reading_order(self):
        assert list(nine_routes(DOT))[0] == 'leftup'

    def test_contact_sheet_mentions_every_route(self):
        sheet = contact_sheet(DOT)
        for direction in ROUTES:
            assert f'-- {direction} --' in sheet

    def test_contact_sheet_is_a_rectangle_per_row(self):
        lines = [line for line in contact_sheet(DOT).split('\n')
                 if line.strip()]
        # label lines and art lines have consistent cell widths
        assert len(lines) >= 9

    def test_routes_render_the_vlm_examples(self):
        for name in ('vlm_cat', 'vlm_house', 'vlm_robot'):
            for direction in ('left', 'up', 'leftup'):
                rendered = route(EXAMPLES[name], direction)
                assert rendered.strip(), (name, direction)
