import numpy as np
import pytest

from mushroomgen.generators.curves import Curves


# Generate
def test_generate():
    curve = Curves(segments=5, height=10, curve_type="NoType", radius=None)
    with pytest.raises(ValueError):
        curve.generate()


def test_stem_ring_shape():
    # stem_ring maps to the default stem curve generator
    segments = 6
    height = 10.0
    radius = 1.0
    curve = Curves(
        segments=segments, height=height, curve_type="Stem Ring", radius=radius
    )
    points = curve.generate()

    n_segments = 12
    expected_rows = n_segments * segments
    assert points.shape == (expected_rows, 3)
    assert points.ndim == 2
    # Overall the stem should rise from start to end
    assert points[-1, 2] >= points[0, 2] - 1e-6


def test_volume_stem_shape():
    # stem_bulb maps to the _volume_stem_draw generator
    segments = 5
    height = 8.0
    radius = 0.8
    curve = Curves(
        segments=segments, height=height, curve_type="Stem Bulb", radius=radius
    )
    points = curve.generate()

    n_segments = 12
    expected_rows = n_segments * segments
    assert points.shape == (expected_rows, 3)
    assert points.ndim == 2
    # Overall the stem should rise from start to end
    assert points[-1, 2] >= points[0, 2] - 1e-6


def test_cap_round_requires_radius_and_valid_number():
    # If radius is not provided: ValueError
    curve = Curves(segments=6, height=6, curve_type="Round Cap")
    with pytest.raises(ValueError):
        curve.generate()

    # No int radius should raise ValueError
    curve_bad = Curves(segments=6, height=6, curve_type="Round Cap", radius="one")
    with pytest.raises(ValueError):
        curve_bad.generate()


def test_round_cap_shape_and_properties():
    # With valid radius the cap curve should be generated
    segments = 6
    height = 10.0
    radius = 1.0
    curve = Curves(
        segments=segments, height=height, curve_type="Round Cap", radius=radius
    )
    points = curve.generate()

    n_segments = 9
    expected_rows = n_segments * segments
    assert points.shape == (expected_rows, 3)
    assert points.ndim == 2

    # Basic numeric sanity
    assert np.isfinite(points).all()
    assert not np.isnan(points).any()


def test_round_capboundaries():
    segments = 6
    height = 10.0
    radius = 1.0
    curve = Curves(
        segments=segments,
        height=height,
        curve_type="Round Cap",
        radius=radius,
    )
    points = curve.generate()

    # Cap z should be mostly negative.
    assert np.all(points[:, 2] <= 0.5)
    assert points[:, 2].min() >= -height - 0.1

    # X should span up to the radius; ensure extreme values are reasonable
    assert points[:, 0].min() >= -(radius + 1e-6)
    assert points[:, 0].max() >= radius + 1e-6

    # Y component should be essentially zero for the 2D curve generator
    assert np.all(np.abs(points[:, 1]) < 1e-6)


def test_cone_cap_shape_basic():
    # Ensure cone cap generator produces points when radius provided
    segments = 4
    height = 5.0
    radius = 0.8
    curve = Curves(
        segments=segments, height=height, curve_type="Cone Cap", radius=radius
    )
    pts = curve.generate()
    n_segments = 9
    expected_rows = n_segments * segments
    assert pts.shape == (expected_rows, 3)
    assert np.isfinite(pts).all()
