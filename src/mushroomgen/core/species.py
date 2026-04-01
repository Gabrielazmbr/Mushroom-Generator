from dataclasses import dataclass, field

from ncca.ngl import Vec3


@dataclass
class MushroomType:
    name: str

    # Stem attributes
    stem_height: float = 10.0
    stem_curve_type: str = "Stem Ring"
    stem_radius: float = 0.1
    stem_noise: float = 0.1
    stem_color: Vec3 = field(default_factory=lambda: Vec3(0.99, 0.99, 0.99))
    stem_segments: int = 20
    stem_row_segments: int = 20

    # Cap attributes
    cap_height: float = 8.0
    cap_radius: float = 2.0
    cap_curve_type: str = "Round Cap"
    cap_inner_color: Vec3 = field(default_factory=lambda: Vec3(0.99, 0.99, 0.99))
    cap_outer_color: Vec3 = field(default_factory=lambda: Vec3(0.99, 0.99, 0.99))
    cap_noise: float = 0.1
    cap_curve_segments: int = 20
    cap_angle_segments: int = 30

    # Gills Attributes
    gills_noise: float = 0.1
    gills_width: float = 0.05
    gills_seed: int = 0
    gills_segments: int = 200
    gills_color: Vec3 = field(default_factory=lambda: Vec3(0.99, 0.99, 0.99))

    # Scales Attributes
    scales_count: int = 120
    scales_radius: float = 0.05
    scales_radius_jitter: float = 0.5
    scales_noise: float = 2.0
    scales_seed: int = 0
    scales_color: Vec3 = field(default_factory=lambda: Vec3(0.99, 0.99, 0.99))
    scale_lat_segments: int = 10
    scale_lon_segments: int = 20


FLY_AGARIC = MushroomType(
    name="FlyAgaric",
    # Stem
    stem_curve_type="Stem Ring",
    stem_height=8.0,
    stem_radius=0.8,
    stem_noise=0.01,
    stem_color=Vec3(0.914, 0.851, 0.655),
    stem_segments=40,
    stem_row_segments=60,
    # Cap
    cap_curve_type="Round Cap",
    cap_height=3.0,
    cap_radius=4.0,
    cap_noise=0.1,
    cap_inner_color=Vec3(0.100, 0.030, 0.002),
    cap_outer_color=Vec3(0.702, 0.020, 0.027),
    cap_curve_segments=40,
    cap_angle_segments=60,
    # Gills
    gills_noise=0.05,
    gills_width=0.05,
    gills_segments=500,
    gills_seed=12,
    gills_color=Vec3(0.945, 0.812, 0.522),
    # Scales
    scales_count=240,
    scales_radius=0.2,
    scales_radius_jitter=0.7,
    scales_noise=2.0,
    scales_seed=35,
    scale_lat_segments=10,
    scale_lon_segments=20,
    scales_color=Vec3(0.95, 0.95, 0.80),
)
