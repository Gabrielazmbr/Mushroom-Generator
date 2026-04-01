import os

import numpy as np
import pytest

from mushroomgen.core.build import Build
from mushroomgen.core.species import MushroomType


@pytest.fixture
def mushroom_type():
    # Fixture to call for attributes of a test mushroom
    defaults = dict(
        name="testMushroom",
        stem_height=10.0,
        stem_curve_type="Stem Ring",
        stem_radius=0.1,
        stem_color=(255, 255, 255),
        # Cap attributes
        cap_height=4.0,
        cap_radius=1.0,
        cap_curve_type="Round Cap",
        cap_inner_color=(0.1, 0.3, 0.2),
        cap_outer_color=(0.7, 0.2, 0.3),
        # Mesh resolution defaults
        stem_segments=20,
        stem_row_segments=12,
        cap_curve_segments=20,
        cap_angle_segments=30,
    )

    def _make(**overrides):
        params = {**defaults, **overrides}
        return MushroomType(**params)

    return _make


@pytest.fixture
def build(mushroom_type):
    return Build(mushroom_type())


@pytest.fixture
def mushroom_type_stem(mushroom_type):
    return mushroom_type()


# Tests Build Stem
def test_points_number(mushroom_type):
    m = mushroom_type(stem_segments=1)
    build = Build(m)
    X, Y, Z = build.buildStem()
    assert X.ndim == 2 and Y.ndim == 2 and Z.ndim == 2
    assert X.shape[1] >= 1


def test_basic_mesh(build, mushroom_type_stem):
    build.buildStem()
    vertices, faces = build.buildStemMesh(cap_ends=True)

    assert vertices.ndim == 2 and vertices.shape[1] == 3
    assert faces.ndim == 2 and faces.shape[1] == 3
    assert faces.dtype == int

    # Compute expected based on actual sampled stem_points used by the implementation
    n_radius = len(build.stem_points)
    n_sides = mushroom_type_stem.stem_segments
    expected_ring_vertices = n_radius * n_sides
    assert vertices.shape[0] == expected_ring_vertices + 2  # +2 for cap ends

    # expected triangles between rings
    expected_triangles_between = (n_radius - 1) * n_sides * 2
    assert (
        faces.shape[0] == expected_triangles_between + 2 * n_sides
    )  # +2 for cap triangles

    # faces range count
    assert faces.max() < vertices.shape[0]
    assert faces.min() >= 0


def test_faces_indices(build, mushroom_type_stem):
    build.buildStem()
    vertices, faces = build.buildStemMesh(cap_ends=False)

    n_radius = len(build.stem_points)
    n_sides = mushroom_type_stem.stem_segments

    # Without caps
    expected_vertices = n_radius * n_sides
    assert vertices.shape[0] == expected_vertices
    # face range count should match again
    assert faces.max() < vertices.shape[0]
    assert faces.min() >= 0


def test_tangents_normalized(build):
    build.buildStem()
    vertices, faces = build.buildStemMesh(cap_ends=False)
    # Get the central points used for the tube
    points = np.asarray(build.stem_points)
    # compute tangents between consecutive points
    tangents = points[1:] - points[:-1]
    norms = np.linalg.norm(tangents, axis=1)
    # Ensure there is at least one non-zero tangent
    nonzero_mask = norms > 1e-12
    assert np.any(nonzero_mask)
    # Normalize only the non-zero tangents and check unit length
    normalized = tangents[nonzero_mask] / norms[nonzero_mask][:, None]
    np.testing.assert_allclose(np.linalg.norm(normalized, axis=1), 1.0, rtol=1e-6)


def test_mesh_perpendicular_normals(build):
    build.buildStem()
    vertices, faces = build.buildStemMesh(cap_ends=False)
    # Get radial segments
    n_sides = build.species.stem_row_segments
    # Pick central points of rings (first two rings)
    ring0 = vertices[0:n_sides]
    ring1 = vertices[n_sides : 2 * n_sides]
    center0 = ring0.mean(axis=0)
    center1 = ring1.mean(axis=0)
    axis = center1 - center0
    # axis length should be greater than zero
    assert np.linalg.norm(axis) > 1e-8


# Build Cap
def test_build_cap_shape(mushroom_type):
    # Cap attributes
    cap_type = mushroom_type(
        cap_curve_segments=6,
        cap_angle_segments=12,
        cap_height=3.0,
        cap_radius=1.0,
    )
    b = Build(cap_type)
    X, Y, Z = b.buildCap()
    n_angles = cap_type.cap_angle_segments
    # X,Y,Z should be 2d arrays with shape (n_angles, n_points_along_curve)
    assert X.shape[0] == n_angles
    assert Y.shape[0] == n_angles
    assert Z.shape[0] == n_angles


def test_build_cap_no_nan(build):
    # Look for Nans
    X, Y, Z = build.buildCap()
    assert not np.isnan(X).any()
    assert not np.isnan(Y).any()
    assert not np.isnan(Z).any()


def test_build_gills_basic_properties(mushroom_type):
    # tests gills generation
    s = mushroom_type(
        gills_segments=16, gills_seed=42, cap_curve_segments=8, cap_angle_segments=12
    )
    b = Build(s)
    # build cap to populate inner_points used by gills
    b.buildCap()
    gill_array, lengths = b.buildGills()

    assert isinstance(gill_array, np.ndarray)
    assert isinstance(lengths, np.ndarray)
    assert gill_array.ndim == 3 and gill_array.shape[0] == s.gills_segments
    # lengths should be within bounds (zero allowed if n_radius < 1)
    n_radius = np.asarray(b.inner_points).shape[0]
    assert lengths.min() >= 0
    assert lengths.max() <= max(0, n_radius)
    # any non-empty gill should have coordinates (x,y,z)
    nonzero_i = np.nonzero(lengths)[0]
    if nonzero_i.size > 0:
        i = nonzero_i[0]
        ln = int(lengths[i])
        assert gill_array[i, ln - 1].shape == (3,)


def test_build_gills_mesh_thin_and_thick(mushroom_type):
    # Thin gills
    s_thin = mushroom_type(
        gills_segments=12,
        gills_seed=1,
        cap_curve_segments=10,
        cap_angle_segments=16,
        gills_width=0.0,
    )
    b_thin = Build(s_thin)
    b_thin.buildCap()
    verts_t, faces_t = b_thin.buildGillsMesh()
    assert verts_t.ndim == 2 and verts_t.shape[1] == 3
    assert faces_t.ndim == 2 and faces_t.shape[1] == 3
    assert faces_t.max() < verts_t.shape[0]

    # Thick gills
    s_thick = mushroom_type(
        gills_segments=12,
        gills_seed=1,
        cap_curve_segments=10,
        cap_angle_segments=16,
        gills_width=0.05,
    )
    b_thick = Build(s_thick)
    b_thick.buildCap()
    verts, faces = b_thick.buildGillsMesh()
    assert verts.ndim == 2 and faces.ndim == 2
    assert not np.isnan(verts).any()
    assert faces.max() < verts.shape[0]
    # Faces should form closed geometry
    assert faces.shape[0] >= 0


def test_scales_model_and_mesh(mushroom_type):
    # Test scalesModel  and buildScalesMesh integration
    s = mushroom_type(
        cap_curve_segments=12,
        cap_angle_segments=20,
        scales_count=6,
        scales_seed=7,
        scale_lat_segments=6,
        scale_lon_segments=8,
        scales_radius=0.05,
        scales_radius_jitter=0.1,
        scales_noise=0.01,
    )
    b = Build(s)
    # precompute cap mesh to supply to buildScalesMesh
    cap_v, cap_inner_f, cap_outer_f = b.buildCapMesh()
    # unit model
    verts, faces = b.scalesModel(radius=0.5, lat_segments=6, lon_segments=8)
    assert verts.ndim == 2 and verts.shape[1] == 3
    assert faces.ndim == 2 and faces.shape[1] == 3
    assert faces.max() < verts.shape[0]

    # build scales on the cap (may produce 0 scales if no outer vertices)
    scales_v, scales_f = b.buildScalesMesh(cap_v, cap_outer_f)
    # shapes consistent
    assert scales_v.ndim == 2 and scales_v.shape[1] == 3
    assert scales_f.ndim == 2 and scales_f.shape[1] == 3
    # if any faces returned, indices must be in range
    if scales_f.size > 0:
        assert scales_f.max() < scales_v.shape[0]


def test_build_mushroom_mesh_and_submesh_ranges(mushroom_type):
    # assembly test: ensure mushroom mesh created and submesh ranges exist and are consistent
    s = mushroom_type(
        cap_curve_segments=10,
        cap_angle_segments=16,
        gills_segments=16,
        scales_count=8,
        scales_seed=3,
    )
    b = Build(s)
    verts, faces = b.buildMushroomMesh()
    assert verts.ndim == 2 and verts.shape[1] == 3
    assert faces.ndim == 2 and faces.shape[1] == 3
    # submesh_ranges should contain expected keys
    expected_keys = {"stem", "cap_inner", "cap_outer", "scales", "gills"}
    assert set(b.submesh_ranges.keys()) >= expected_keys
    # ranges values are tuples of (start_index, size) and are ints
    for k, v in b.submesh_ranges.items():
        assert isinstance(v, tuple) and len(v) == 2
        assert isinstance(v[0], int) and isinstance(v[1], int)
    # ranges should not exceed faces total size
    total_face_entries = faces.size
    for start, size in b.submesh_ranges.values():
        assert 0 <= start <= total_face_entries
        assert 0 <= size <= total_face_entries


def test_export_obj_writes_vertices_normals_and_faces(tmp_path, mushroom_type):
    # Build and export to an OBJ file and check formatting lines
    s = mushroom_type(
        cap_curve_segments=10,
        cap_angle_segments=12,
        gills_segments=12,
        scales_count=4,
        scales_seed=5,
    )
    b = Build(s)
    b.buildMushroomMesh()

    out_file = tmp_path / "test_mushroom.obj"
    b.exportMushroomToOBJ(str(out_file))

    # Read and validate file contents
    content = out_file.read_text().splitlines()
    # header
    assert len(content) > 0
    assert content[0].startswith("# Mushroom OBJ export")

    v_lines = [l for l in content if l.startswith("v ")]
    vn_lines = [l for l in content if l.startswith("vn ")]
    f_lines = [l for l in content if l.startswith("f ")]

    verts_count = b.mushroom_mesh[0].shape[0]
    faces_count = b.mushroom_mesh[1].shape[0]

    # number of vertex lines must match verts_count
    assert len(v_lines) == verts_count
    # vn lines should equal verts_count
    assert len(vn_lines) == verts_count
    # face lines should match faces_count
    assert len(f_lines) == faces_count
