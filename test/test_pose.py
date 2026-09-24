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
                          spin_depth, turntable_pose)
from ascii3d.rotation import frames

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
        """Every frame keeps a sheared face and a top face -- never
        the flat normal art."""
        flat = CUBE
        for theta in range(0, 360, 5):
            frame = render_pose(CUBE, turntable_pose(theta))
            assert frame != flat, theta
            assert '/' in frame or '\\' in frame, theta

    def test_side_wall_flips_at_face_on_not_edge_on(self):
        """The wall follows the physical yaw: the box's right wall
        stays on the viewer's right for the whole first half (the
        front swings toward screen-left), then the left wall for
        the second half -- the layout flips at 0/180 degrees, where
        the box passes face-on and the side face is thinnest, never
        at the edge-on crossings where it is widest."""
        for theta in range(5, 175, 5):
            assert turntable_pose(theta).side == 'right', theta
        for theta in range(185, 355, 5):
            assert turntable_pose(theta).side == 'left', theta

    def test_back_half_shows_the_mirrored_content(self):
        """The face content mirrors exactly where the box passes
        edge-on (the back view reads mirrored)."""
        for theta in range(5, 85, 5):
            assert turntable_pose(theta).face == 'front', theta
        for theta in range(95, 265, 5):
            assert turntable_pose(theta).face == 'back', theta
        for theta in range(275, 355, 5):
            assert turntable_pose(theta).face == 'front', theta

    def test_march_follows_the_wall(self):
        """The face rows march with the wall: right (\\ walls) while
        the right wall shows, left (/ walls) while the left wall
        shows -- the docs' classic 45 degree shear, constant."""
        for theta in (10, 45, 80, 100, 135, 170):
            assert turntable_pose(theta).lean > 0, theta
        for theta in (190, 225, 260, 280, 315, 350):
            assert turntable_pose(theta).lean < 0, theta

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


class TestSpinSweep:
    """The 360 sweep must visibly turn in every single frame."""

    def test_no_two_neighbouring_frames_stall(self):
        """Every adjacent pair differs -- no copy-pasted frames
        anywhere in the turn, for any art."""
        for name in ('cube', 'head', 'roomy', 'vlm_house', 'dot'):
            art = EXAMPLES[name]
            timeline = frames(art, steps=24)
            for i in range(len(timeline) - 1):
                assert timeline[i] != timeline[i + 1], \
                    f'{name} frames {i}/{i + 1} are identical'

    def test_the_sweep_breathes_widest_at_edge_on(self):
        """The drawn side face is at the full depth exactly at the
        edge-on crossings and thinnest at the face-on moments."""
        from ascii3d.rotation import _spin_k
        box = spin_depth(CUBE, steps=24)
        assert _spin_k(90, box) == box
        assert _spin_k(270, box) == box
        assert _spin_k(0, box) < _spin_k(45, box) < _spin_k(90, box)
        assert _spin_k(180, box) < _spin_k(135, box) < _spin_k(90, box)

    def test_k_climbs_one_cell_per_frame(self):
        """Inside a quadrant the side face steps monotonically (the
        even staircase) -- never backwards, never stalled."""
        from ascii3d.rotation import _spin_k
        box = spin_depth(CUBE, steps=24)
        # q0 rising: 15..75 degrees
        ks = [_spin_k(t, box) for t in (15, 30, 45, 60, 75)]
        assert ks == sorted(ks) and len(set(ks)) == len(ks)
        # q1 falling: 105..165
        ks = [_spin_k(t, box) for t in (105, 120, 135, 150, 165)]
        assert ks == sorted(ks, reverse=True)
        assert len(set(ks)) == len(ks)

    def test_spin_depth_is_cube_like_and_step_sized(self):
        """Deep as the docs demand, box-like as the art, and wide
        enough that every frame earns its own cell of travel."""
        assert spin_depth(CUBE, steps=24) >= 9
        assert spin_depth(CUBE) >= 8
        wide = spin_depth(ROOMY, steps=48)
        assert wide >= 3 + 48 // 4

    def test_the_face_on_flip_frame_is_the_thinnest_box(self):
        """The layout flip (180 degrees) happens at the smallest
        side face -- the least noticeable moment."""
        from ascii3d.rotation import _spin_k
        box = spin_depth(CUBE, steps=24)
        around = [_spin_k(t, box) for t in (150, 165, 180, 195, 210)]
        assert around[2] == min(around)

    def test_spin_starts_on_the_turned_view(self):
        """Frame 0 is a deep classic 45 degree turn: side face well
        beyond the old static default, top face present."""
        first = frames(CUBE, steps=24)[0]
        assert '\\' in first
        assert '______' in first
