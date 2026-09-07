"""Tests for the 3D wireframe renderer."""

import numpy as np

from ascii3d.wireframe import (
    art_segments,
    merge_strokes,
    extrude_segments,
    mesh_segments,
    rotate,
    project,
    rasterize,
    grid_to_text,
    render_art,
    render_mesh,
    Segment,
)
from ascii3d.examples import EXAMPLES

DOT = ' _\n|_|'
ROOMY = EXAMPLES['roomy']


class TestParsing:
    def test_dot_parses_into_four_segments(self):
        # '_' at (1,0), '|' at (0,1), '_' at (1,1), '|' at (2,1)
        assert len(art_segments(DOT)) == 4

    def test_underscore_sits_on_the_bottom_edge(self):
        segs = art_segments(' _ ')
        assert segs[0].start[1] == -2.0
        assert segs[0].end[1] == -2.0
        assert segs[0].start[0] == 1
        assert segs[0].end[0] == 2

    def test_pipe_spans_the_cell(self):
        segs = art_segments('|')
        assert segs[0].start[0] == 0.5
        assert segs[0].end[1] == -2.0

    def test_first_row_is_the_top_of_the_world(self):
        # world y points up, so the first art row is the *highest*
        segs = art_segments('|_|\n|_|')
        ys = [p[1] for s in segs for p in (s.start, s.end)]
        assert min(ys) == -4.0
        assert max(ys) == 0.0

    def test_non_stroke_characters_are_ignored(self):
        assert art_segments('ab c') == []

    def test_merge_chains_underscore_runs(self):
        segs = art_segments(' _____ ')
        merged = merge_strokes(segs)
        assert len(merged) == 1
        assert merged[0].start[0] == 1
        assert merged[0].end[0] == 6

    def test_merge_chains_vertical_pipe_runs(self):
        segs = art_segments('|\n|\n|')
        merged = merge_strokes(segs)
        assert len(merged) == 1

    def test_merge_keeps_diagonal_directions_separate(self):
        segs = art_segments('/\n\\')
        assert len(merge_strokes(segs)) == 2

    def test_merge_never_inverts_a_stroke(self):
        # every merged segment keeps the direction of its parts
        for art in (ROOMY, EXAMPLES['cube'], EXAMPLES['invader']):
            for s in merge_strokes(art_segments(art)):
                delta = s.end - s.start
                assert delta[0] >= 0  # parsing order is left-to-right


class TestExtrusion:
    def test_depth_zero_returns_the_flat_art(self):
        front = merge_strokes(art_segments(ROOMY))
        flat = extrude_segments(front, depth=0)
        assert len(flat) == len(front)

    def test_extrusion_adds_a_back_frame_and_connectors(self):
        front = merge_strokes(art_segments(ROOMY))
        box = extrude_segments(front, depth=3)
        assert len(box) > len(front)
        zs = [p[2] for s in box for p in (s.start, s.end)]
        assert min(zs) == -3.0

    def test_extrusion_centres_the_geometry(self):
        front = merge_strokes(art_segments(ROOMY))
        box = extrude_segments(front, depth=2)
        pts = np.array([p for s in box for p in (s.start, s.end)])
        assert abs(pts[:, 0].mean()) <= 1.0
        assert abs(pts[:, 1].mean()) <= 2.0


class TestRotation:
    def test_identity_keeps_segments(self):
        segs = art_segments(DOT)
        rotated = rotate(segs, 0, 0, 0)
        for before, after in zip(segs, rotated):
            assert np.allclose(before.start, after.start)
            assert np.allclose(before.end, after.end)

    def test_yaw_360_is_the_identity(self):
        segs = art_segments(DOT)
        rotated = rotate(segs, 360, 0, 0)
        for before, after in zip(segs, rotated):
            assert np.allclose(before.start, after.start, atol=1e-9)

    def test_yaw_keeps_verticals_vertical(self):
        # rotation around y maps (0, 1, 0) to (0, 1, 0)
        segs = [Segment(np.array([0.0, 0.0, 0.0]),
                        np.array([0.0, 2.0, 0.0]))]
        rotated = rotate(segs, yaw=37.0)
        delta = rotated[0].end - rotated[0].start
        assert abs(delta[0]) < 1e-9
        assert abs(delta[1] - 2.0) < 1e-9

    def test_project_shifts_into_the_first_quadrant(self):
        segs = extrude_segments(art_segments(DOT), depth=2)
        projected = project(rotate(segs, 30, 20))
        for u, v in projected:
            assert u[0] >= -0.5 and u[1] >= -0.5


class TestRasterizer:
    def test_round_trip_reproduces_the_art(self):
        for name in ('dot', 'cube', 'head', 'roomy', 'rubik',
                     'invader'):
            art = EXAMPLES[name]
            rendered = render_art(art, depth=0)
            assert rendered.rstrip('\n') == art.rstrip('\n'), name

    def test_rasterize_is_idempotent(self):
        grid = rasterize(project(art_segments(DOT)))
        text = grid_to_text(grid)
        assert grid_to_text(rasterize(project(art_segments(text)))) \
            == text

    def test_rendered_frames_only_use_stroke_characters(self):
        for yaw, pitch in ((0, 0), (45, 45), (-45, 30), (90, 0),
                           (0, 60)):
            frame = render_art(ROOMY, yaw=yaw, pitch=pitch, depth=3)
            assert set(frame) <= set(' _|/\\\n')

    def test_center_route_of_a_flat_art_is_the_art(self):
        frame = render_art(DOT, yaw=0, pitch=0, depth=0)
        assert frame == DOT.rstrip('\n')


class TestRenderArt:
    def test_empty_art_renders_empty(self):
        assert render_art('   \n  ') == ''

    def test_rotated_frames_are_non_empty(self):
        for yaw in (0, 30, 90, 180, 270):
            assert render_art(ROOMY, yaw=yaw, pitch=25, depth=2).strip()

    def test_zoom_grows_the_frame(self):
        small = render_art(DOT, yaw=45, pitch=45, depth=2, zoom=0.5)
        large = render_art(DOT, yaw=45, pitch=45, depth=2, zoom=1.0)

        def width(text):
            return max(len(line) for line in text.split('\n'))

        assert width(large) > width(small)


class TestMeshRendering:
    VERTS = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1],
                      [-1, 1, -1], [-1, -1, 1], [1, -1, 1],
                      [1, 1, 1], [-1, 1, 1]], dtype=float)
    EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7),
             (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]

    def test_mesh_segments_scale(self):
        segs = mesh_segments(self.VERTS, self.EDGES, scale=5)
        pts = np.array([p for s in segs for p in (s.start, s.end)])
        assert abs(pts[:, 0].max() - 5) < 1e-9

    def test_render_mesh_frame(self):
        frame = render_mesh(self.VERTS, self.EDGES, yaw=30, pitch=30)
        assert frame.strip()
        assert set(frame) <= set(' _|/\\\n')

    def test_mesh_full_rotation_is_periodic(self):
        # 0 and 360 degrees give the same picture
        zero = render_mesh(self.VERTS, self.EDGES, yaw=0, pitch=25)
        full = render_mesh(self.VERTS, self.EDGES, yaw=360, pitch=25)
        assert zero == full
