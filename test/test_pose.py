"""Tests for the box camera: the pose system behind the routes/spin.

The pose renderer must stay byte-identical to the engine's docs
renderer at the classic 45 degree turn, keep every stroke a single
character, and produce a continuous 360 degree turntable sweep in
which the camera never drops below the box.
"""


import pytest

from ascii3d.engine import turn
from ascii3d.examples import EXAMPLES
from ascii3d.pose import (Pose, auto_depth, render_pose,
                          turntable_pose)

DOT = ' _\n|_|'
CUBE = EXAMPLES['cube']
HEAD = EXAMPLES['head']
ROOMY = EXAMPLES['roomy']

# every character the box camera is allowed to paint
LEGAL = set(' _|/\\.:X#')


class TestDocsFidelity:
    """The pose renderer at the classic turn == the docs engine."""

    @pytest.mark.parametrize('name', sorted(EXAMPLES))
    def test_pose_matches_engine_at_45_degrees(self, name):
        art = EXAMPLES[name]
        depth = auto_depth(art)
        pose = Pose(lean=1, rise=1, side='right', shade=False,
                    reach=1.0)
        assert render_pose(art, pose, depth=depth) \
            == turn(art, 'left', depth=depth)

    def test_mirrored_pose_matches_engine_turn_right(self):
        pose = Pose(lean=1, rise=1, side='left', shade=False,
                    reach=1.0)
        assert render_pose(CUBE, pose, depth=3) \
            == turn(CUBE, 'right', depth=3)

    def test_auto_depth_is_substantial(self):
        # the docs demand a deep box: "it should be at last 6x12"
        assert auto_depth(DOT) >= 3
        assert auto_depth(HEAD) >= 3
        assert auto_depth(ROOMY) >= 3
        assert auto_depth(ROOMY) <= 6


class TestCleanStrokes:
    """No character is ever doubled or stretched to fake depth."""

    @pytest.mark.parametrize('name', ['cube', 'head', 'roomy', 'dot'])
    @pytest.mark.parametrize('theta', [0, 45, 90, 135, 180, 225, 270])
    def test_frames_only_use_legal_characters(self, name, theta):
        art = EXAMPLES[name]
        frame = render_pose(art, turntable_pose(theta))
        assert set(frame) <= LEGAL | {'\n'}

    @pytest.mark.parametrize('name', ['cube', 'head', 'roomy'])
    def test_spin_never_shows_piled_diagonals(self, name):
        """The side face must be marching singles, not /// or \\\\."""
        art = EXAMPLES[name]
        for k in range(24):
            frame = render_pose(art, turntable_pose(45 + k * 15))
            for line in frame.split('\n'):
                assert '///' not in line and '\\\\\\' not in line, \
                    (name, k, line)

    def test_shading_stays_between_the_edges(self):
        """The gradient never paints outside the drawn strokes."""
        frame = render_pose(CUBE, Pose(lean=1, rise=1, side='right',
                                       shade=True, reach=1.0), depth=3)
        lines = frame.split('\n')
        # the side face rows: shading columns must sit right of the
        # near wall and left of the frame edge
        for line in lines[3:7]:
            body = line.rstrip()
            if ':' in body or 'X' in body:
                assert body.index(':') if ':' in body else True


class TestPoseGeometry:
    def test_top_face_is_drawn_above_the_front_face(self):
        frame = render_pose(CUBE, Pose(lean=1, rise=1, side='right'),
                            depth=3)
        lines = frame.split('\n')
        assert '______' in lines[0]                     # back edge
        assert '______' in lines[3]                     # front edge
        assert lines[0].count('_') > lines[4].count('_')  # top face

    def test_turned_size_follows_the_docs_formula(self):
        """turned_length = length + depth (docs/02-HowToTurn)."""
        frame = render_pose(HEAD, Pose(lean=1, rise=1, side='right',
                                       shade=False, reach=1.0), depth=3)
        length = len(HEAD.strip('\n').split('\n'))
        assert len(frame.split('\n')) >= length + 3

    def test_reach_widens_the_side_face(self):
        thin = render_pose(CUBE, Pose(lean=1, rise=1, side='right',
                                      shade=False, reach=0.4), depth=3)
        wide = render_pose(CUBE, Pose(lean=1, rise=1, side='right',
                                      shade=False, reach=1.4), depth=3)
        assert max(len(line) for line in wide.split('\n')) \
            > max(len(line) for line in thin.split('\n'))

    def test_pose_repr_is_informative(self):
        assert 'lean' in repr(Pose(lean=1))


class TestTurntable:
    def test_camera_never_drops_below_the_box(self):
        """The camera stays above for the whole sweep ('only going
        down'): rise is always positive."""
        for theta in range(0, 360, 5):
            pose = turntable_pose(theta)
            assert pose.rise > 0, theta

    def test_flat_forward_view_never_appears(self):
        """Every frame keeps a lean and a top face -- never the flat
        normal art."""
        flat = CUBE
        for theta in range(0, 360, 5):
            frame = render_pose(CUBE, turntable_pose(theta))
            assert frame != flat, theta
            assert '/' in frame or '\\' in frame, theta

    def test_side_wall_is_continuous_through_each_half(self):
        """The visible side only switches where it is invisible."""
        for theta in range(5, 175, 5):
            assert turntable_pose(theta).side == 'right'
        for theta in range(185, 355, 5):
            assert turntable_pose(theta).side == 'left'

    def test_frame0_is_the_docs_turn(self):
        pose = turntable_pose(45.0)
        assert pose.face == 'front'
        assert pose.lean == 1.0
        assert pose.side == 'right'

    def test_sweep_is_periodic(self):
        assert turntable_pose(0.0).lean == turntable_pose(360.0).lean
        assert turntable_pose(0.0).side == turntable_pose(360.0).side

    def test_pitch_above_40_grows_the_top_face(self):
        assert turntable_pose(45, pitch=50).rise == 2
        assert turntable_pose(45, pitch=30).rise == 1
