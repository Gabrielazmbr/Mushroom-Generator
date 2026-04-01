import numpy as np
import pytest

from mushroomgen.generators.geometry import catmull_rom, hermite_curve

# Hermite Curve


def test_hermite_curve_shape():
    # Inputs
    p0 = [0.0, 0.0, 0.0]
    p1 = [1.0, 1.0, 1.0]
    t0 = [0.0, 0.0, 0.0]
    t1 = [1.0, 1.0, 1.0]

    segments = 5
    curve1 = hermite_curve(p0, p1, t0, t1, segments)
    # Tests array shape
    assert curve1.shape == (5, 3)
    # test a full curve to return start and end points
    np.testing.assert_allclose(curve1[0], p0)
    np.testing.assert_allclose(curve1[-1], p1)

    segments = 1
    curve2 = hermite_curve(p0, p1, t0, t1, segments)
    # Tests array shape
    assert curve2.shape == (1, 3)
    # test a 1 segment curve to return a start point
    np.testing.assert_allclose(curve2[0], p0)

    segments = 2
    curve3 = hermite_curve(p0, p1, t0, t1, segments)
    # Tests array shape
    assert curve3.shape == (2, 3)
    # test a 2 segments curve to return a start point and end point
    np.testing.assert_allclose(curve3[0], p0)
    np.testing.assert_allclose(curve3[-1], p1)


def test_linear_interpolation():
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array([1.0, 1.0, 1.0])
    t0 = p1 - p0
    t1 = p1 - p0

    segments = 10
    curve = hermite_curve(p0, p1, t0, t1, segments)
    # makes an array (t) and then converts the shape
    t = np.linspace(0, 1, segments)[:, None]
    curve_test = ((1 - t) * p0) + (t * p1)
    # check curve_test
    np.testing.assert_allclose(curve, curve_test, atol=1e-6)


def test_tangents():
    # A straight curve
    curve_01 = hermite_curve(
        p0=[0.0, 0.0, 0.0],
        p1=[1.0, 0.0, 0.0],
        t0=[0.0, 0.0, 0.0],
        t1=[0.0, 0.0, 0.0],
        segments=10,
    )
    # A bended curve
    curve_02 = hermite_curve(
        p0=[0.0, 0.0, 0.0],
        p1=[1.0, 0.0, 0.0],
        t0=[1.0, 1.0, 0.0],
        t1=[1.0, -1.0, 0.0],
        segments=10,
    )
    # Tests that its a straight line
    np.testing.assert_allclose(curve_01[:, 1], 0)
    # Tests that is not a straight line
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(curve_02[:, 1], 0)


def test_nans_infs():
    p0 = [0.0, 0.0, 0.0]
    p1 = [0.5, 0.5, 0.5]
    t0 = [0.7, 0.7, 0.7]
    t1 = [1.0, 1.0, 1.0]

    # Tests for posible NaNs or Infs
    curve = hermite_curve(p0, p1, t0, t1, 10)
    assert not np.isnan(curve).any()
    assert not np.isinf(curve).any()


# Catmull Rom


def catmull_rom_shape():
    points = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]
    )
    segments = 10
    curve = catmull_rom(points, segments)
    # Checks that the start point is P1
    np.testing.assert_allclose(curve[0], points[0])
    # Checks that the end point is P2
    np.testing.assert_allclose(curve[-1], points[2])
    # Checks that the 4 points return 1 hermite segment
    assert curve.shape == (segments, 3)
    # Y and Z are 0
    assert np.allclose(curve[:, 1], 0.0, atol=1e-6)


@pytest.mark.parametrize(
    "points",
    [
        np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [2, 1, 0],
                [3, 1, 0],
                [4, 0, 0],
                [5, -1, 0],
                [6, 0, 0],
            ]
        ),
        np.array(
            [
                [0, 0, 0],
                [1, 1, 0],
                [2, 2, 0],
                [3, 1, 0],
                [4, 0, 0],
                [5, -1, 0],
                [6, 0, 1],
                [7, 1, 1],
                [8, 2, 3],
                [9, 4, 4],
            ]
        ),
    ],
)
def test_continuity(points):
    segments = 5
    curve = catmull_rom(points, segments)
    # No NaNs or Infs
    assert np.isfinite(curve).all()
    # X should not decrease
    assert np.all(np.diff(curve[:, 0]) >= -1e-6)

    joints = [segments * i - 1 for i in range(1, len(points) - 3)]

    for i in joints:
        # C0, positional continuity
        np.testing.assert_allclose(curve[i], curve[i + 1], atol=1e-6)
