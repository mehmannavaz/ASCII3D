"""Tests for the theoretic (mathematical) ASCII arts."""

import numpy as np
import pytest

from ascii3d.theory import (MESHES, Mesh, cube, tetrahedron,
                            octahedron, icosahedron,
                            dodecahedron, sphere, torus, helix,
                            double_helix, mobius, wave, render)


class TestPlatonicSolids:
    def test_cube_topology(self):
        shape = cube()
        assert shape.n_vertices == 8
        assert shape.n_edges == 12

    def test_tetrahedron_topology(self):
        shape = tetrahedron()
        assert shape.n_vertices == 4
        assert shape.n_edges == 6

    def test_octahedron_topology(self):
        shape = octahedron()
        assert shape.n_vertices == 6
        assert shape.n_edges == 12

    def test_icosahedron_topology(self):
        shape = icosahedron()
        assert shape.n_vertices == 12
        assert shape.n_edges == 30

    def test_dodecahedron_topology(self):
        shape = dodecahedron()
        assert shape.n_vertices == 20
        assert shape.n_edges == 30

    @pytest.mark.parametrize('name', ['cube', 'tetrahedron',
                                      'octahedron', 'icosahedron',
                                      'dodecahedron'])
    def test_solids_are_centred(self, name):
        verts = MESHES[name].vertices
        assert np.allclose(verts.mean(axis=0), 0.0, atol=1e-9)

    @pytest.mark.parametrize('name', ['cube', 'tetrahedron',
                                      'octahedron', 'icosahedron',
                                      'dodecahedron'])
    def test_platonic_edges_have_equal_length(self, name):
        verts, edges = MESHES[name].vertices, MESHES[name].edges
        lengths = {round(float(np.linalg.norm(verts[i] - verts[j])), 6)
                   for i, j in edges}
        assert len(lengths) == 1


class TestCurvedShapes:
    def test_sphere_topology(self):
        shape = sphere(lats=4, lons=8)
        # 2 poles + 3 rings of 8
        assert shape.n_vertices == 2 + 3 * 8

    def test_torus_topology(self):
        shape = torus(major=8, minor=5)
        assert shape.n_vertices == 40
        assert shape.n_edges == 80

    def test_helix_is_one_chain(self):
        shape = helix(steps=40)
        assert shape.n_edges == 39

    def test_double_helix_has_rungs(self):
        single = helix(steps=40)
        double = double_helix(steps=40)
        assert double.n_edges > 2 * single.n_edges

    def test_mobius_is_one_sided_band(self):
        shape = mobius(steps=8)
        # 8 steps of 3 rows each
        assert shape.n_vertices == 24

    def test_wave_grid(self):
        shape = wave(nx=7, ny=5)
        assert shape.n_vertices == 35
        # the sine field really oscillates
        ys = shape.vertices[:, 1]
        assert ys.min() < -0.5
        assert ys.max() > 0.5

    def test_mesh_dataclass_coerces_to_float(self):
        shape = Mesh([[1, 2, 3], [4, 5, 6]], [(0, 1)])
        assert shape.vertices.dtype == float


class TestRendering:
    @pytest.mark.parametrize('name', sorted(MESHES))
    def test_every_mesh_renders(self, name):
        frame = render(name)
        assert frame.strip(), name
        assert set(frame) <= set(' _|/\\\n')

    def test_unknown_mesh_is_rejected(self):
        with pytest.raises(KeyError):
            render('hypercube')

    def test_rotation_changes_the_view(self):
        front = render('cube', yaw=0, pitch=90)
        angled = render('cube', yaw=45, pitch=45)
        assert front != angled

    def test_render_uses_per_mesh_default_scales(self):
        # smoke: scale=None must not crash for any mesh
        for name in MESHES:
            assert render(name, scale=None).strip()
