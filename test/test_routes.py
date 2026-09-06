"""Tests for the nine routes."""

import pytest

from ascii3d.engine import turn
from ascii3d.examples import EXAMPLES
from ascii3d.pose import auto_depth
from ascii3d.routes import (ROUTES, contact_sheet, nine_routes,
                            route)

DOT = ' _\n|_|'
ROOMY = EXAMPLES['roomy']

LEGAL = set(' _|/\\.:X#')


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

    def test_engine_style_rejects_pose_only_routes(self):
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

    def test_center_route_shows_the_top_face_going_down(self):
        frame = route(DOT, 'center')
        assert frame != DOT                      # never the flat art
        assert '_' in frame.split('\n')[0]       # a top face is there

    def test_up_and_down_differ(self):
        assert route(ROOMY, 'up') != route(ROOMY, 'down')

    def test_all_nine_routes_are_distinct_for_roomy(self):
        renders = nine_routes(ROOMY)
        assert len(set(renders.values())) == len(ROUTES)

    def test_pose_routes_only_use_legal_characters(self):
        for direction in ('up', 'down', 'leftup', 'leftdown',
                          'rightup', 'rightdown', 'center'):
            frame = route(ROOMY, direction)
            assert set(frame) <= LEGAL | {'\n'}, direction

    def test_pose_routes_never_show_piled_diagonals(self):
        for direction in ('up', 'down', 'leftup', 'leftdown',
                          'rightup', 'rightdown'):
            for line in route(ROOMY, direction).split('\n'):
                assert '///' not in line and '\\\\\\' not in line

    def test_left_and_right_poses_match_the_engine(self):
        # the pose pipeline can draw the classic turns too
        assert route(DOT, 'left', depth=3, style='pose') \
            == turn(DOT, 'left', depth=3)
        assert route(DOT, 'right', depth=3, style='pose') \
            == turn(DOT, 'right', depth=3)

    def test_auto_depth_scales_with_the_art(self):
        assert auto_depth(DOT) >= 3
        assert auto_depth(ROOMY) >= auto_depth(DOT)


class TestNineRoutes:
    def test_nine_routes_returns_all_routes(self):
        renders = nine_routes(DOT)
        assert list(renders) == list(ROUTES)

    def test_nine_routes_reading_order(self):
        assert list(nine_routes(DOT))[:3] == \
            ['leftup', 'up', 'rightup']

    def test_contact_sheet_mentions_every_route(self):
        sheet = contact_sheet(DOT)
        for name in ROUTES:
            assert f'-- {name} --' in sheet

    def test_contact_sheet_is_a_rectangle_per_row(self):
        sheet = contact_sheet(DOT)
        widths = {len(line) for line in sheet.split("\n") if line.strip()}
        assert len(widths) == 1

    def test_routes_render_the_vlm_examples(self):
        for name in ('vlm_cat', 'vlm_house', 'vlm_rocket',
                     'vlm_robot'):
            art = EXAMPLES[name]
            for direction in ROUTES:
                assert route(art, direction).strip(), (name, direction)
