import numpy as np

from mushroomgen.generators.geometry import catmull_rom


class Curves:
    def __init__(
        self,
        segments,
        height,
        curve_type,
        radius=None,
    ):
        self.segments = segments
        self.height = height
        self.curve_type = curve_type
        self.radius = radius

    def generate(self):
        """
        Dispatch to the correct curve generator based on the curve type.
        """
        if self.curve_type == "Stem Ring":
            return self._default_stem_draw()
        elif self.curve_type == "Stem Bulb":
            return self._volume_stem_draw()
        elif self.curve_type == "Round Cap":
            if self.radius is None:
                raise ValueError("Round curve needs radius.")
            try:
                radius = float(self.radius)
            except Exception:
                raise ValueError("Radius is a numeric value.")
            self.radius = radius
            return self._round_cap_draw()
        elif self.curve_type == "Cone Cap":
            if self.radius is None:
                raise ValueError("Round curve needs radius.")
            try:
                radius = float(self.radius)
            except Exception:
                raise ValueError("Radius is a numeric value.")
            self.radius = radius
            return self._cone_cap_draw()
        else:
            raise ValueError(f"Unknown curve type: {self.curve_type}")

    def _default_stem_draw(self):
        """
        Use Catmull-Rom splines to draw a curve for a straight stem with a ring (annuals).
        """
        h = self.height
        r = self.radius

        # Points
        P0 = np.array([0.0, 0.0, 0.0])
        # Initial bump
        P1 = np.array([r, 0.0, 0.0])
        P2 = np.array([r * 1.5, 0.0, h * 0.03])
        P3 = np.array([r * 1.5, 0.0, h * 0.1])

        P4 = np.array([r * 0.8, 0.0, h * 0.30])
        # lower ring
        P5 = np.array([r * 1.0, 0.0, h * 0.46])
        P6 = np.array([r * 1.1, 0.0, h * 0.50])
        P7 = np.array([r * 0.8, 0.0, h * 0.48])
        # Upper ring
        P8 = np.array([r * 0.8, 0.0, h * 0.60])
        P9 = np.array([r * 1.5, 0.0, h * 0.51])
        P10 = np.array([r * 1.2, 0.0, h * 0.60])
        # Shrinked tube
        P11 = np.array([r * 0.8, 0.0, h * 0.65])
        P12 = np.array([r * 0.7, 0.0, h * 0.91])
        P13 = np.array([r * 0.6, 0.0, h])
        P14 = np.array([r * 0.5, 0.0, h])

        points = [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13, P14]

        curve = catmull_rom(points, self.segments)
        return curve

    def _volume_stem_draw(self):
        """
        Use Catmull-Rom splines to draw a curve for a volume stem with bulb.
        """
        h = self.height
        r = self.radius

        # Points
        P0 = np.array([0.0, 0.0, 0.0])

        P1 = np.array([r * 0.0, 0.0, 0.0])
        P2 = np.array([r * 0.8, 0.0, h * 0.01])
        P3 = np.array([r * 1.3, 0.0, h * 0.03])
        P4 = np.array([r * 1.8, 0.0, h * 0.1])

        P5 = np.array([r * 1.8, 0.0, h * 0.15])
        P6 = np.array([r * 1.6, 0.0, h * 0.20])
        P7 = np.array([r * 1.5, 0.0, h * 0.25])

        P8 = np.array([r * 1.3, 0.0, h * 0.23])
        P9 = np.array([r * 1.4, 0.0, h * 0.3])
        P10 = np.array([r * 0.8, 0.0, h * 0.5])

        P11 = np.array([r * 0.6, 0.0, h * 0.8])
        P12 = np.array([r * 0.4, 0.0, h * 0.9])
        P13 = np.array([r * 0.2, 0.0, h])
        P14 = np.array([r * 0.2, 0.0, h])

        points = [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13, P14]

        curve = catmull_rom(points, self.segments)
        return curve

    def _round_cap_draw(self):
        """
        Draws a round type cap with outer and inner segments using Catmull-Rom splines.
        """

        # Control Point P0
        P0 = np.array([0.2, 0.0, 0.0])

        # Start Point P1
        P1 = np.array([0.0, 0.0, 0.0])

        # Outer early Point P2
        P2 = np.array([self.radius * 0.4, 0.0, 0.0])

        # Outer Center Point P3
        P3 = np.array([self.radius * 0.8, 0.0, -self.height * 0.3])

        # Tip Outer Point P4
        P4 = np.array([self.radius * 0.9, 0.0, -self.height * 0.5])

        # Tip Outer Point P5
        P5 = np.array([self.radius, 0.0, -self.height * 0.8])

        # Tip Point P6
        P6 = np.array(
            [
                self.radius,
                0.0,
                -self.height,
            ]
        )

        # Inner late Point P7
        P7 = np.array(
            [
                self.radius * 0.9,
                0.0,
                -self.height * 0.8,
            ]
        )

        # Inner Center Point P8
        P8 = np.array([self.radius * 0.4, 0.0, -self.height * 0.4])

        # Inner early Point P9
        P9 = np.array([self.radius * 0.2, 0.0, -self.height * 0.1])

        # Inner early Point P10
        P10 = np.array([0.0, 0.0, -self.height * 0.1])

        # Inner early Point P11
        P11 = P0.copy()

        points = [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11]

        curve = catmull_rom(points, self.segments)

        return curve

    def _cone_cap_draw(self):
        """
        Draws a cone type cap with outer and inner segments using Catmull-Rom splines.
        """

        # Control Point P0
        P0 = np.array([0.2, 0.0, 0.0])

        # Start Point P1
        P1 = np.array([0.0, 0.0, 0.0])

        # Outer early Point P2
        P2 = np.array([self.radius * 0.2, 0.0, 0.0])

        # Outer early Point P3
        P3 = np.array([self.radius * 0.4, 0.0, -self.height * 0.2])

        # Tip Point P4
        P4 = np.array([self.radius * 0.6, 0.0, -self.height * 0.6])

        # Tip  Point P5
        P5 = np.array([self.radius, 0.0, -self.height * 0.85])

        # Tip Point P6
        P6 = np.array(
            [
                self.radius,
                0.0,
                -self.height,
            ]
        )

        # Inner Point P7
        P7 = np.array(
            [
                self.radius * 0.9,
                0.0,
                -self.height * 0.85,
            ]
        )

        # Inner  Point P8
        P8 = np.array([self.radius * 0.4, 0.0, -self.height * 0.6])

        # Inner  Point P9
        P9 = np.array([self.radius * 0.2, 0.0, -self.height * 0.2])

        # Inner early Point P10
        P10 = np.array([0.0, 0.0, -self.height * 0.1])

        # Inner early Point P11
        P11 = P0.copy()

        points = [P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11]

        curve = catmull_rom(points, self.segments)

        return curve

    def get_inner_cap(self, curve, n_ctrl_points):
        """
        Gets the inner segments of the Cap curve.
        """
        total_segments = n_ctrl_points - 2
        s = self.segments

        start_segments = total_segments // 2
        index = start_segments * s
        return curve[index:]
