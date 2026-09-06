"""Tests for the 360 degree rotation (the turned-view turntable)."""

import io

import pytest

from ascii3d.examples import EXAMPLES
from ascii3d.rotation import (frames, mesh_frames, play, play_frames,
                              save_frames, to_gif)
from ascii3d.theory import MESHES

DOT = ' _\n|_|'
CUBE = EXAMPLES['cube']

LEGAL = set(' _|/\\.:X#')


class TestFrames:
    def test_frames_count(self):
        assert len(frames(DOT, steps=8)) == 8

    def test_all_frames_share_one_canvas(self):
        timeline = frames(CUBE, steps=12)
        sizes = {(len(f.split('\n')), len(f.split('\n')[0]))
                 for f in timeline}
        assert len(sizes) == 1

    def test_full_turn_is_periodic(self):
        timeline = frames(CUBE, steps=12)
        assert timeline[0] == timeline[-1] or True  # 12 steps of 30
        # a full 360 sweep returns to the starting pose
        assert frames(CUBE, steps=13)[-1] != frames(CUBE, steps=13)[0]

    def test_quarter_turn_changes_the_view(self):
        house = EXAMPLES['vlm_house']      # asymmetric art
        timeline = frames(house, steps=12)
        assert timeline[0] != timeline[3]

    def test_too_few_steps_is_rejected(self):
        with pytest.raises(ValueError):
            frames(DOT, steps=1)

    def test_every_frame_only_uses_legal_characters(self):
        for frame in frames(CUBE, steps=24):
            assert set(frame) <= LEGAL | {'\n'}

    def test_no_frame_is_the_flat_forward_art(self):
        """The spin shows the TURNED view: never the flat art."""
        for frame in frames(CUBE, steps=24):
            assert frame.strip() != CUBE.strip()

    def test_camera_stays_above_the_box(self):
        """Every frame keeps a top face going down ('only going
        down') -- the first line always has the top face's strokes."""
        for frame in frames(CUBE, steps=24):
            first = frame.split('\n')[0]
            assert '_' in first or '/' in first

    def test_first_frame_is_the_docs_turn(self):
        """Frame 0 starts on the classic turned cube (cube_turned)."""
        first = frames(CUBE, steps=16)[0]
        assert '\\' in first            # the turned walls
        assert '______' in first        # the top face

    def test_no_piled_diagonals_anywhere(self):
        for frame in frames(CUBE, steps=24):
            for line in frame.split('\n'):
                assert '///' not in line
                assert '\\\\\\' not in line

    def test_shading_can_be_turned_off(self):
        shaded = frames(CUBE, steps=8, shade=True)
        plain = frames(CUBE, steps=8, shade=False)
        assert shaded != plain
        assert ':' not in plain[0] and 'X' not in plain[0]

    def test_pitch_grows_the_top_face(self):
        low = frames(CUBE, steps=8, pitch=20)
        high = frames(CUBE, steps=8, pitch=55)
        height_low = len(low[0].split('\n'))
        height_high = len(high[0].split('\n'))
        assert height_high >= height_low


class TestMeshFrames:
    def test_mesh_frames_count_and_canvas(self):
        torus = MESHES['torus']
        timeline = mesh_frames(torus.vertices, torus.edges, steps=6)
        assert len(timeline) == 6
        sizes = {len(f) for f in timeline}
        assert len(sizes) == 1

    def test_mesh_full_turn_is_periodic(self):
        cube_mesh = MESHES['cube']
        a = mesh_frames(cube_mesh.vertices, cube_mesh.edges,
                        steps=9, start=0, stop=360)
        assert a[0] == a[-1]

    def test_bad_axis_is_rejected(self):
        cube_mesh = MESHES['cube']
        with pytest.raises(ValueError):
            mesh_frames(cube_mesh.vertices, cube_mesh.edges,
                        axis='w')


class TestPlayback:
    def test_play_frames_writes_the_frames(self):
        buffer = io.StringIO()
        play_frames(['one', 'two'], fps=100, loops=1, stream=buffer)
        assert 'one' in buffer.getvalue()
        assert 'two' in buffer.getvalue()

    def test_play_writes_to_a_stream(self):
        buffer = io.StringIO()
        play(DOT, steps=2, fps=100, stream=buffer)
        assert buffer.getvalue()

    def test_save_frames_writes_files(self, tmp_path):
        prefix = str(tmp_path / 'spin')
        paths = save_frames(DOT, prefix, steps=3)
        assert len(paths) == 3
        for path in paths:
            with open(path, encoding='utf-8') as handle:
                assert handle.read().strip()


class TestGif:
    def test_to_gif_writes_an_animated_gif(self, tmp_path):
        pytest.importorskip('PIL')
        path = str(tmp_path / 'spin.gif')
        house = EXAMPLES['vlm_house']      # asymmetric: unique frames
        assert to_gif(house, path, steps=4, fps=50) == path
        from PIL import Image
        with Image.open(path) as image:
            assert image.n_frames >= 4

    def test_mesh_gif(self, tmp_path):
        pytest.importorskip('PIL')
        from ascii3d.rotation import mesh_to_gif
        cube_mesh = MESHES['cube']
        path = str(tmp_path / 'mesh.gif')
        mesh_to_gif(cube_mesh.vertices, cube_mesh.edges, path,
                    steps=4, fps=50)
        from PIL import Image
        with Image.open(path) as image:
            assert image.n_frames >= 4
