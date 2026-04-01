from noise import snoise3


class NoiseFields:
    def __init__(
        self,
        frequency: float = 1.0,
        lacunarity: float = 2.0,
        persistence: float = 0.5,
        octaves: int = 1,
    ):
        """
        Gives expected arguments for Noise Library (octaves, persistance, lacunarity)
        """
        self.frequency = frequency
        self.lacunarity = lacunarity
        self.persistence = persistence
        self.octaves = octaves

    def evaluate(self, x: float, y: float, z: float) -> float:
        """
        Generates snoise3 (3D simplex noise) in a coordinate X,Y,Z.
        """
        value = 0.0
        freq = self.frequency
        amp = 1.0
        amp_sum = 0.0

        for _ in range(self.octaves):
            value += snoise3(x * freq, y * freq, z * freq) * amp
            amp_sum += amp

            freq *= self.lacunarity
            amp *= self.persistence

        return value / amp_sum if amp_sum > 0.0 else 0.0
