import numpy as np


def hermite_curve(
    p0: list[float], p1: list[float], t0: list[float], t1: list[float], segments
) -> np.ndarray:
    """
    Returns a Hermite curve using the given control points and tangents.
    """

    # Start and End points
    p0 = np.array(p0)  # list of floats
    p1 = np.array(p1)

    # Tangent vectors
    t0 = np.array(t0)
    t1 = np.array(t1)

    # Variables
    t = np.linspace(0, 1, segments)  # numpy line
    t2 = t**2
    t3 = t**3

    # Hermite basis functions
    h00 = 2 * t3 - 3 * t2 + 1
    h01 = t3 - 2 * t2 + t
    h02 = -2 * t3 + 3 * t2
    h03 = t3 - t2

    # Combine points
    curve = (
        np.outer(h00, p0) + np.outer(h01, t0) + np.outer(h02, p1) + np.outer(h03, t1)
    )

    return curve


def catmull_rom(points, segments):
    """
    Returns a curve using catmull-rom formula and calling hermite curves for each segment
    of the curve.
    """
    curve = []
    for i in range(1, len(points) - 2):
        # HermiteSegments
        p0, p1, p2, p3 = points[i - 1], points[i], points[i + 1], points[i + 2]
        # Tangents at endpoints
        t1 = 0.5 * (p2 - p0)
        t2 = 0.5 * (p3 - p1)
        # Call hermite_curve function for each segment
        segment = hermite_curve(p1, p2, t1, t2, segments)
        curve.append(segment)
    return np.vstack(curve)
