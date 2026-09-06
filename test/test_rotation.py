"""Tests for the 360 degree rotation."""

from pathlib import Path

import pytest

from ascii3d.rotation import (SPIN_AXES, frames, mesh_frames, play,
                              play_frames, save_frames, to_gif)
from ascii3d.theory import MESHES
from ascii3d.examples import EXAMPLES

DOT = ' _\n|_|'
ROOMY = EXAMPLES['roomy']


class TestFrames:
    def test_frames_count(self):
        assert len(frames(DOT, steps=12)) == 12

    def test_all_frames_share_one_canvas(self):
        timeline = frames(ROOMY, steps=16)
        widths = {max(len(line) for line in f.split('\n'))
                  for f in timeline}
        heights = {f.count('\n') + 1 for f in timeline}
        assert len(widths) == 1
        assert len(heights) == 1

    def test_full_turn_is_periodic(self):
        # 0 degrees and 360 degrees render the same box
        timeline = frames(ROOMY, steps=2, start=0, stop=360)
        assert timeline[0] == timeline[1]

    def test_quarter_turn_changes_the_view(self):
        zero = frames(ROOMY, steps=2, start=0, stop=0.1)[0]
        quarter = frames(ROOMY, steps=2, start=0, stop=90.1)[1]
        assert zero != quarter

    def test_bad_axis_is_rejected(self):
        with pytest.raises(ValueError):
            frames(DOT, axis='w')

    def test_too_few_steps_is_rejected(self):
        with pytest.raises(ValueError):
            frames(DOT, steps=1)

    def test_every_axis_works(self):
        for axis in SPIN_AXES:
            timeline = frames(DOT, steps=4, axis=axis)
            assert len(timeline) == 4
            assert all(f.strip() for f in timeline)

    def test_frames_only_use_stroke_characters(self):
        for frame in frames(ROOMY, steps=8):
            assert set(frame) <= set(' _|/\\\n')


class TestMeshFrames:
    def test_mesh_frames_count_and_canvas(self):
        cube = MESHES['cube']
        timeline = mesh_frames(cube.vertices, cube.edges, steps=10)
        assert len(timeline) == 10
        heights = {f.count('\n') + 1 for f in timeline}
        assert len(heights) == 1

    def test_mesh_full_turn_is_periodic(self):
        cube = MESHES['cube']
        timeline = mesh_frames(cube.vertices, cube.edges, steps=2,
                               start=0, stop=360)
        assert timeline[0] == timeline[1]


class TestPlayback:
    def test_play_frames_writes_the_frames(self):
        import io
        stream = io.StringIO()
        timeline = frames(DOT, steps=3)
        play_frames(timeline, fps=1000.0, stream=stream)
        out = stream.getvalue()
        for frame in timeline:
            assert frame in out

    def test_play_writes_to_a_stream(self):
        import io
        stream = io.StringIO()
        play(DOT, steps=2, fps=1000.0, stream=stream)
        assert stream.getvalue().count('\n') >= 4

    def test_save_frames_writes_files(self, tmp_path):
        prefix = str(tmp_path / 'frame')
        paths = save_frames(DOT, prefix, steps=3)
        assert len(paths) == 3
        for path in paths:
            assert Path(path).exists()
            assert Path(path).read_text().strip()


class TestGif:
    def test_to_gif_writes_an_animated_gif(self, tmp_path):
        pytest.importorskip('PIL')
        from PIL import Image
        path = str(tmp_path / 'spin.gif')
        result = to_gif(DOT, path, steps=6, fps=25.0)
        assert result == path
        with Image.open(path) as image:
            assert image.n_frames == 6

    def test_mesh_gif(self, tmp_path):
        pytest.importorskip('PIL')
        from ascii3d.rotation import mesh_to_gif
        from PIL import Image
        cube = MESHES['cube']
        path = str(tmp_path / 'mesh.gif')
        mesh_to_gif(cube.vertices, cube.edges, path, steps=4)
        with Image.open(path) as image:
            assert image.n_frames == 4
