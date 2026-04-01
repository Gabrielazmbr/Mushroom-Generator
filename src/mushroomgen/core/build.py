import numpy as np

from mushroomgen.core.species import MushroomType
from mushroomgen.generators.curves import Curves
from mushroomgen.generators.noiseFields import NoiseFields


class Build:
    def __init__(self, species: MushroomType) -> None:
        self.species = species
        self._init_cap_noise()

    def _resample_curve(self, points, n_samples):
        """
        Resample a 3D curve evenly along arc length.
        """
        points = np.asarray(points)
        distances = np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))
        distances = np.insert(distances, 0, 0)
        total_length = distances[-1]

        # Uniform distances along the curve
        uniform_d = np.linspace(0, total_length, n_samples)

        # Interpolate each coordinate
        new_points = np.empty((n_samples, points.shape[1]))
        for i in range(points.shape[1]):
            new_points[:, i] = np.interp(uniform_d, distances, points[:, i])
        return new_points

    def buildStem(self):
        s = self.species
        # Gets a curve for the stem
        stem_curve = Curves(
            s.stem_segments,
            s.stem_height,
            s.stem_curve_type,
            s.stem_radius,
        )
        self.stem_points = stem_curve.generate()

        # Resample
        n_radius = s.stem_row_segments
        self.stem_points = self._resample_curve(self.stem_points, n_radius)
        stem_points_array = np.asarray(self.stem_points, dtype=float)

        n_angles = s.stem_segments
        angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)

        # Empty numpy arrays
        X = np.empty((n_angles, n_radius), dtype=float)
        Y = np.empty_like(X)
        Z = np.empty_like(X)

        # Revolves the curve to create a cap with thickness
        for i, theta in enumerate(angles):
            cos_t, sin_t = np.cos(theta), np.sin(theta)
            X[i, :] = stem_points_array[:, 0] * cos_t
            Y[i, :] = stem_points_array[:, 0] * sin_t
            Z[i, :] = stem_points_array[:, 2]

        return X, Y, Z

    def buildStemMesh(self, cap_ends: bool = True):
        """
        Gets X,Y,Z points from buildStem. Builds vertices, applies noise and then triangulates faces.
        """
        X, Y, Z = self.buildStem()
        s = self.species

        # Noise
        noise_params = {}
        noise_field = NoiseFields(**noise_params)
        depth = s.stem_noise

        n_angles, n_radius = X.shape

        stem_angle_count = s.stem_segments
        stem_angles = np.linspace(0, 2 * np.pi, stem_angle_count, endpoint=False)

        # Vertex count
        verts_count = stem_angle_count * n_radius
        if cap_ends:
            verts_count += 2

        # Prealocate arrays
        vertices = np.empty((verts_count, 3), dtype=float)

        # Build vertices
        verts_idx = 0
        for i, theta in enumerate(stem_angles):
            # Map sample index into the X/Y/Z angular resolution
            angle_index = int(round(i * n_angles / stem_angle_count)) % n_angles
            for r in range(n_radius):
                x = float(X[angle_index, r])
                y = float(Y[angle_index, r])
                z = float(Z[angle_index, r])
                # Apply noise
                noise = noise_field.evaluate(x, y, z)
                x_new = x - noise * depth
                y_new = y - noise * depth
                z_new = z - noise * depth
                vertices[verts_idx] = [x_new, y_new, z_new]
                verts_idx += 1

        # Add center points for caps
        if cap_ends:
            center0 = verts_idx
            vertices[verts_idx] = [0.0, 0.0, float(self.stem_points[0][2])]
            verts_idx += 1
            center1 = verts_idx
            vertices[verts_idx] = [0.0, 0.0, float(self.stem_points[-1][2])]
            verts_idx += 1

        # Build faces between radial rings
        faces_count = 2 * stem_angle_count * (n_radius - 1) if n_radius > 1 else 0
        if cap_ends:
            faces_count += 2 * stem_angle_count

        # Prealocate faces arrays
        faces = np.empty((faces_count, 3), dtype=int)

        faces_idx = 0
        for i in range(stem_angle_count):
            next_i = (i + 1) % stem_angle_count
            base0 = i * n_radius
            base1 = next_i * n_radius
            for k in range(n_radius - 1):
                a = base0 + k
                b = base0 + k + 1
                c = base1 + k + 1
                d = base1 + k
                faces[faces_idx] = (a, b, c)
                faces[faces_idx + 1] = (a, c, d)
                faces_idx += 2
        # Flip faces for OpenGl
        faces = faces[:, ::-1]

        # End caps
        if cap_ends:
            # base cap (z at bottom)
            for k in range(stem_angle_count):
                a = k * n_radius
                b = ((k + 1) % stem_angle_count) * n_radius
                faces[faces_idx] = (center0, b, a)
                faces_idx += 1
            # top cap (z at top)
            base = n_radius - 1  # index within each ring
            for k in range(stem_angle_count):
                a = k * n_radius + base
                b = ((k + 1) % stem_angle_count) * n_radius + base
                faces[faces_idx] = (center1, b, a)
                faces_idx += 1

        assert verts_idx == verts_count
        assert faces_idx == faces_count

        self.stem_mesh = (vertices, faces)
        return vertices, faces

    def _transform_to_stem_frame(
        self,
        vertices_local: np.ndarray,
        stem_tip: np.ndarray,
        n_tip: np.ndarray,
        bn_tip: np.ndarray,
        t_tip: np.ndarray,
    ):
        """
        Transforms local vertices into world-space coordinates.
        """
        R = np.column_stack([n_tip, bn_tip, t_tip])
        return vertices_local.dot(R.T) + stem_tip

    def get_stem_frame(self):
        """
        Gets stem tip center (last revolved ring) with an orthonormal basis (n_tip, bn_tip, t_tip).
        """
        # Use pre-noise revolve points
        X, Y, Z = self.buildStem()
        X = np.asarray(X)
        Y = np.asarray(Y)
        Z = np.asarray(Z)

        # last-ring centroid
        xs, ys, zs = X[:, -1], Y[:, -1], Z[:, -1]
        stem_tip = np.array([xs.mean(), ys.mean(), zs.mean()], dtype=float)

        # previous-ring centroid
        if X.shape[1] >= 2:
            prev = np.array(
                [X[:, -2].mean(), Y[:, -2].mean(), Z[:, -2].mean()], dtype=float
            )
            t_tip = stem_tip - prev
            n = np.linalg.norm(t_tip)
            t_tip = t_tip / n if n != 0.0 else np.array([0.0, 0.0, 1.0])
        else:
            t_tip = np.array([0.0, 0.0, 1.0])

        # stable orthonormal axes perpendicular to tangent
        arb = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(arb, t_tip)) > 0.99:
            arb = np.array([0.0, 1.0, 0.0])
        n_tip = np.cross(t_tip, arb)
        n_tip = n_tip / (np.linalg.norm(n_tip) or 1.0)
        bn_tip = np.cross(t_tip, n_tip)
        bn_tip = bn_tip / (np.linalg.norm(bn_tip) or 1.0)

        return stem_tip, n_tip, bn_tip, t_tip

    def _init_cap_noise(self):
        """
        Extracts NoiseFields parameters applied to the cap to copy into gills.
        """
        s = self.species
        self._cap_noise_field = NoiseFields(
            frequency=1,
            lacunarity=2.0,
            persistence=0.5,
            octaves=1,
        )

    def _cap_displacement(self, x, y, z):
        """
        Returns displacement caused by cap noise,
        faded out near the cap edge.
        """
        s = self.species

        # Normalize noise space
        inv_radius = 1.0 / max(s.cap_radius, 1e-6)
        inv_height = 1.0 / max(s.cap_height, 1e-6)

        nx = x * inv_radius
        ny = y * inv_radius
        nz = z * inv_height

        # Base noise
        n = self._cap_noise_field.evaluate(nx, ny, nz)

        # Radial falloff
        r = np.sqrt(x * x + y * y)
        r_norm = np.clip(r * inv_radius, 0.0, 1.0)
        edge_start = 0.85
        t = np.clip((r_norm - edge_start) / (1.0 - edge_start), 0.0, 1.0)
        edge_mask = 1.0 - (t * t * (3.0 - 2.0 * t))

        return n * s.cap_noise * edge_mask

    def buildCap(self):
        """
        Gets a curve for the cap based on the mushroom species.
        Then revolves it to create points for a cap with thickness.
        """

        s = self.species

        # Gets a round based curve for the cap
        cap_curve = Curves(
            s.cap_curve_segments,
            s.cap_height,
            s.cap_curve_type,
            s.cap_radius,
        )
        self.cap_points = cap_curve.generate()
        self.inner_points = cap_curve.get_inner_cap(self.cap_points, n_ctrl_points=12)

        # Resample
        n_radius = len(self.cap_points)
        self.cap_points = self._resample_curve(self.cap_points, n_radius)
        cap_points_array = np.asarray(self.cap_points, dtype=float)

        n_angles = s.cap_angle_segments
        angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)

        X = np.empty((n_angles, n_radius), dtype=float)
        Y = np.empty_like(X)
        Z = np.empty_like(X)

        # Revolves the curve to create a cap with thickness
        for i, theta in enumerate(angles):
            cos_t, sin_t = np.cos(theta), np.sin(theta)
            X[i, :] = cap_points_array[:, 0] * cos_t
            Y[i, :] = cap_points_array[:, 0] * sin_t
            Z[i, :] = cap_points_array[:, 2]

        return X, Y, Z

    def buildCapMesh(self):
        """
        Gets X,Y,Z points to build cap vertices. Applies noise and then triangulates faces.
        """

        X, Y, Z = self.buildCap()
        s = self.species

        # Noise
        self._init_cap_noise()

        # Shape
        n_angles, n_radius = X.shape

        # Precompute counts
        verts_count = n_angles * n_radius
        vertices = np.empty((verts_count, 3), dtype=float)

        idx = 0
        for i in range(n_angles):
            for r in range(n_radius):
                x = X[i, r]
                y = Y[i, r]
                z = Z[i, r]

                disp = self._cap_displacement(x, y, z)

                vertices[idx, 0] = x
                vertices[idx, 1] = y
                vertices[idx, 2] = z - disp
                idx += 1

        # Precompute counts
        faces_count = 2 * n_angles * (n_radius - 1)
        faces = np.empty((faces_count, 3), dtype=int)
        faces_idx = 0

        for i in range(n_angles):
            base0 = i * n_radius
            base1 = ((i + 1) % n_angles) * n_radius
            for k in range(n_radius - 1):
                a = base0 + k
                b = base0 + k + 1
                c = base1 + k + 1
                d = base1 + k
                faces[faces_idx] = (a, b, c)
                faces[faces_idx + 1] = (a, c, d)
                faces_idx += 2

        # radius index of each vertex per face
        radius_indices = faces % n_radius
        offset = 6

        # inner radius limit from the same curve used by gills
        inner_r_max = n_radius - (len(self.inner_points) + offset)

        # face is inner only if *all* vertices are inside inner radius
        inner_mask = (radius_indices >= inner_r_max).all(axis=1)

        inner_faces = faces[inner_mask]
        outer_faces = faces[~inner_mask]

        # Store
        self.cap = vertices
        self.cap_mesh = (vertices, faces)
        self.cap_outer_faces = outer_faces
        self.cap_inner_faces = inner_faces

        return vertices, inner_faces, outer_faces

    def buildGills(self):
        """
        Build curves along the inner hemisphere of the cap.
        Cuts the length of some of them randomly and applies a wave style noise on them.
        """
        # Resample
        n_radius = len(self.inner_points)
        self.inner_points = self._resample_curve(self.inner_points, n_radius)
        inner_points_array = np.asarray(self.inner_points, dtype=float)

        s = self.species
        gills_count = s.gills_segments

        # Preallocate gills array
        gill_array = np.empty((gills_count, n_radius, 3), dtype=float)
        lengths = np.zeros(gills_count, dtype=int)

        # random cut
        rng = np.random.default_rng(s.gills_seed)

        # Revolves to get lines with different lengths
        angles = np.linspace(0, 2 * np.pi, gills_count, endpoint=False)
        for i, theta in enumerate(angles):
            cos_t, sin_t = np.cos(theta), np.sin(theta)
            xs = inner_points_array[:, 0] * cos_t
            ys = inner_points_array[:, 0] * sin_t
            zs = inner_points_array[:, 2]
            line = np.column_stack((xs, ys, zs))
            for p in line:
                disp = self._cap_displacement(p[0], p[1], p[2])
                p[2] -= disp

            # Choose a random cut for each gill
            if n_radius <= 2:
                cut = 0
            else:
                max_cut = n_radius - 2
                cut = int(rng.integers(0, max_cut + 1))

            if cut > 0:
                truncated = line[:-cut]
                # Inverse logic for my noise amplitude
                min_cut = 1
                max_cut = n_radius - 2
                cut_clamped = np.clip(cut, min_cut, max_cut)
                dir_freq = np.interp(cut_clamped, [min_cut, max_cut], [2.0, 0.1])
                dir_freq = np.clip(dir_freq, 0.1, 2.0)

                # Wave noise
                wave_amp = s.gills_noise
                phase = rng.uniform(0, 2 * np.pi)
                phase_rad = np.deg2rad(phase)
                n_pts = truncated.shape[0]
                t = np.linspace(0, 1, n_pts)
                freq = 0.5
                carrier = wave_amp * np.sin(2 * np.pi * freq * t + phase_rad)
                envelope = np.sin(2 * np.pi * dir_freq * t)
                wave = carrier * envelope

                # Apply perpendicular to radius (tangent to circle)
                truncated[:, 0] += -np.sin(theta) * wave
                truncated[:, 1] += np.cos(theta) * wave
            else:
                truncated = line

            # Store
            curve_points = truncated.shape[0]
            gill_array[i, :curve_points, :] = truncated
            lengths[i] = curve_points

        return gill_array, lengths

    def buildGillsMesh(self):
        """
        Gets the curves from BuildGills and makes a plane triangle with and offset point in Z axis.
        Makes a second curve that goes from outer point to inner point with an offset (midpoint) and then a decreasing point.
        Adds thickness to each plane and assembles vertices andfaces.
        """
        gill_array, lengths = self.buildGills()
        s = self.species
        gills_count = int(gill_array.shape[0])
        gills_width = s.gills_width
        gills_half_width = gills_width / 2

        # Counts for prealocation
        total_vertices = 0
        total_faces = 0
        # Just counts the vertices and faces that have a value
        for i in range(gills_count):
            curve_points = int(lengths[i])
            if curve_points < 2:
                continue
            if gills_half_width == 0.0:
                # thin gills
                total_vertices += 2 * curve_points
                total_faces += 2 * (curve_points - 1)
            else:
                total_vertices += 4 * curve_points  # two vertices per curve point
                total_faces += 8 * (curve_points - 1) + 4  # seg faces + endcaps

        # Preallocate exact-sized arrays
        vertices = np.empty((total_vertices, 3), dtype=float)
        faces = np.empty((total_faces, 3), dtype=int)

        # Offset point in Z to make the triangle plane later
        target_z = -s.cap_height

        vert_idx = 0
        face_idx = 0
        for i in range(gills_count):
            curve_points = int(lengths[i])
            if curve_points < 2:
                continue

            points = gill_array[i, :curve_points].astype(float)
            j_idx = np.arange(curve_points)
            # normalized param along the curve to know how far we are from the end
            s_curve = j_idx / (curve_points - 1) if curve_points > 1 else np.zeros(1)
            midpoint = 0.5 * (points[:, 2] + target_z)

            # For the first half of the curve we go for midpoint offset, then it decreases to points[:,2]
            decreasing_point = s_curve > 0.5
            offset_z = midpoint.copy()
            if np.any(decreasing_point):
                t = (s_curve[decreasing_point] - 0.5) / 0.5
                eased = np.sin(t * (np.pi / 2.0))
                offset_z[decreasing_point] = (1.0 - eased) * midpoint[
                    decreasing_point
                ] + eased * points[:, 2][decreasing_point]

            if gills_half_width == 0.0:
                # thin ribbon: orig + offset (2 verts per point)
                origin_verts = points
                offset_verts = points.copy()
                offset_verts[:, 2] = offset_z
                # interleave origin and offset
                g_verts = np.empty((2 * curve_points, 3), dtype=float)
                g_verts[0::2] = origin_verts
                g_verts[1::2] = offset_verts
                vertices[vert_idx : vert_idx + 2 * curve_points] = g_verts

                # Face assembly
                base = vert_idx
                idx = np.arange(2 * curve_points).reshape(curve_points, 2)
                a = base + idx[:-1, 0]
                b = base + idx[1:, 0]
                c = base + idx[1:, 1]
                d = base + idx[:-1, 1]

                top = np.column_stack((a, b, c))
                bottom = np.column_stack((a, c, d))
                stacked = np.vstack((top, bottom))
                faces[face_idx : face_idx + stacked.shape[0]] = stacked
                face_idx += stacked.shape[0]
                vert_idx += 2 * curve_points
                continue

            # Thickness snippet based on:
            # OpenAI. (2024). ChatGPT (GPT-4) [Large language model]. https://chat.openai.com/
            """
                # Compute tangent vectors along the curve
                tangents = np.zeros_like(points)
                tangents[1:-1] = points[2:] - points[:-2]
                tangents[0] = points[1] - points[0]
                tangents[-1] = points[-1] - points[-2]

                # Perpendicular direction in the XY plane
                normals = np.column_stack((
                    -tangents[:, 1],
                     tangents[:, 0],
                     np.zeros(len(points))
                ))
            """

            # Thickness path (4 vertices per point), tangents for central differences, endpoints
            if curve_points == 2:
                tang = np.empty((2, 3), dtype=float)
                tang[0] = points[1] - points[0]
                tang[1] = tang[0]
            else:
                tang = np.empty((curve_points, 3), dtype=float)
                tang[0] = points[1] - points[0]
                tang[-1] = points[-1] - points[-2]
                tang[1:-1] = points[2:] - points[:-2]

            # Creates a perpendicular vector for each point
            nx = -tang[:, 1]
            ny = tang[:, 0]
            norm = np.sqrt(nx * nx + ny * ny)
            norm[norm <= 1e-12] = 1.0
            nd = np.column_stack((nx / norm, ny / norm, np.zeros(curve_points)))
            shift = nd * gills_half_width

            off_pts = points.copy()
            off_pts[:, 2] = offset_z

            # 4 Vertes columns per point
            A = points + shift  # Top/outer
            B = points - shift  # Top/inner
            C = off_pts + shift  # Bottom/outer
            D = off_pts - shift  # Bottom/inner

            # Packing
            g_verts = np.empty((4 * curve_points, 3), dtype=float)
            g_verts[0::4] = A
            g_verts[1::4] = B
            g_verts[2::4] = C
            g_verts[3::4] = D
            vertices[vert_idx : vert_idx + 4 * curve_points] = g_verts

            base = vert_idx
            # build faces with reshaped indices (per-point 4 columns: A,B,C,D)
            idx = np.arange(4 * curve_points).reshape(curve_points, 4)
            A0 = base + idx[:-1, 0]
            A1 = base + idx[1:, 0]
            B0 = base + idx[:-1, 1]
            B1 = base + idx[1:, 1]
            C0 = base + idx[:-1, 2]
            C1 = base + idx[1:, 2]
            D0 = base + idx[:-1, 3]
            D1 = base + idx[1:, 3]

            # Face assembly
            top1 = np.column_stack((A0, A1, C1))
            top2 = np.column_stack((A0, C1, C0))
            bot1 = np.column_stack((B0, D1, B1))
            bot2 = np.column_stack((B0, D0, D1))
            side1 = np.column_stack((A0, A1, B1))
            side2 = np.column_stack((A0, B1, B0))
            side3 = np.column_stack((C0, C1, D1))
            side4 = np.column_stack((C0, D1, D0))

            seg_faces = np.vstack((top1, top2, bot1, bot2, side1, side2, side3, side4))
            faces[face_idx : face_idx + seg_faces.shape[0]] = seg_faces
            face_idx += seg_faces.shape[0]

            # caps
            s_idx = base + idx[0]  # array of 4 indices for start [A,B,C,D]
            e_idx = base + idx[-1]  # array of 4 indices for end
            faces[face_idx] = [s_idx[0], s_idx[2], s_idx[1]]
            faces[face_idx + 1] = [s_idx[1], s_idx[2], s_idx[3]]
            faces[face_idx + 2] = [e_idx[0], e_idx[1], e_idx[2]]
            faces[face_idx + 3] = [e_idx[1], e_idx[3], e_idx[2]]
            face_idx += 4
            vert_idx += 4 * curve_points

        assert vert_idx == total_vertices
        assert face_idx == total_faces

        self.gills_mesh = (vertices, faces)
        return vertices, faces

    def scalesModel(self, radius=1.0, lat_segments=8, lon_segments=8):
        """
        Returns a Scale model for the Mushroom.
        """

        verts = []
        for i in range(1, lat_segments):
            theta = np.pi * i / lat_segments
            sin_t = np.sin(theta)
            cos_t = np.cos(theta)
            for j in range(lon_segments):
                phi = 2.0 * np.pi * j / lon_segments
                x = radius * sin_t * np.cos(phi)
                y = radius * sin_t * np.sin(phi)
                z = radius * cos_t
                verts.append([x, y, z])

        top_idx = len(verts)
        verts.append([0.0, 0.0, radius])
        bottom_idx = len(verts)
        verts.append([0.0, 0.0, -radius])

        verts = np.asarray(verts, dtype=float)

        faces = []
        ring_count = lat_segments - 1
        for i in range(ring_count - 1):
            for j in range(lon_segments):
                next_j = (j + 1) % lon_segments
                a = i * lon_segments + j
                b = (i + 1) * lon_segments + j
                c = (i + 1) * lon_segments + next_j
                d = i * lon_segments + next_j

                faces.append((a, b, c))
                faces.append((a, c, d))

        for j in range(lon_segments):
            next_j = (j + 1) % lon_segments
            faces.append((top_idx, next_j, j))

        base = (ring_count - 1) * lon_segments
        for j in range(lon_segments):
            next_j = (j + 1) % lon_segments
            a = base + j
            b = base + next_j
            faces.append((bottom_idx, a, b))

        faces = np.asarray(faces, dtype=int)
        return verts, faces

    def buildScalesMesh(self, cap_vertices, cap_faces_outer, count=None):
        """
        Build scattered scales on the outer cap.
        """
        s = self.species

        scales_count = s.scales_count
        scales_radius = max(0.01, s.scales_radius)
        radius_jitter = s.scales_radius_jitter
        depth = s.scales_noise
        seed = s.scales_seed
        lat_segs = s.scale_lat_segments
        lon_segs = s.scale_lon_segments

        # Vertex Sampling based on:
        # OpenAI. (2024). ChatGPT (GPT-4) [Large language model]. https://chat.openai.com/
        """
            surface_indices = np.unique(faces.reshape(-1))
            surface_vertices = vertices[surface_indices]

            m = min(sample_count, surface_vertices.shape[0])

            chosen_local = rng.choice(
                surface_vertices.shape[0],
                size=m,
                replace=False
            )

            chosen_global = surface_indices[chosen_local]

            return vertices[chosen_global]
        """

        rng = np.random.default_rng(seed)

        # Remove duplicates
        outer_idx = np.unique(cap_faces_outer.reshape(-1))
        # Candidate positions for scales
        outer_positions = cap_vertices[outer_idx]

        if outer_positions.shape[0] == 0:
            return np.empty((0, 3)), np.empty((0, 3), dtype=int)

        # Build per-vertex normals for outer cap
        face_vs0 = cap_vertices[cap_faces_outer[:, 0]]
        face_vs1 = cap_vertices[cap_faces_outer[:, 1]]
        face_vs2 = cap_vertices[cap_faces_outer[:, 2]]
        face_normals = np.cross(face_vs1 - face_vs0, face_vs2 - face_vs0)
        v_normals = np.zeros_like(cap_vertices, dtype=float)
        # accumulate into v_normals only for outer vertices
        np.add.at(
            v_normals,
            cap_faces_outer.flatten(),
            np.repeat(face_normals, 3, axis=0).reshape(-1, 3),
        )
        # Normalize
        lengths = np.linalg.norm(v_normals, axis=1)
        nonzero = lengths > 1e-12
        v_normals[nonzero] /= lengths[nonzero][:, None]

        # Choose centers without replacement
        n_candidates = outer_positions.shape[0]
        m = min(scales_count, n_candidates)  # no to spawn more scales than vertices

        # Vertex sampling
        chosen_local = rng.choice(n_candidates, size=m, replace=False)
        chosen_global_indices = outer_idx[chosen_local]
        # Scales positions and normals
        centers = cap_vertices[chosen_global_indices]
        centers_normals = v_normals[chosen_global_indices]
        # Backup if normals are zero
        for i, nrm in enumerate(centers_normals):
            if np.linalg.norm(nrm) <= 1e-12:
                centers_normals[i] = np.array([0.0, 0.0, 1.0])

        # Pregenerate a sphere for reuse
        sphere_unit_v, sphere_unit_f = self.scalesModel(
            radius=1.0, lat_segments=lat_segs, lon_segments=lon_segs
        )

        # Prealocate
        per_scale_verts = sphere_unit_v.shape[0]
        per_scale_faces = sphere_unit_f.shape[0]
        total_verts = per_scale_verts * m
        total_faces = per_scale_faces * m
        scales_vertices = np.empty((total_verts, 3), dtype=float)
        scales_faces = np.empty((total_faces, 3), dtype=int)

        # Noise generation
        noise_field = NoiseFields(
            frequency=depth,
            lacunarity=2.0,
            persistence=0.5,
            octaves=3,
        )

        v_off = 0
        f_off = 0

        for i in range(m):
            c = centers[i]
            nrm = centers_normals[i]
            r_scale = scales_radius * (0.5 + radius_jitter * (rng.uniform(-1.0, 1.0)))
            local_v = sphere_unit_v * r_scale

            for vi in range(local_v.shape[0]):
                dir_vec = local_v[vi]
                norm_dir = np.linalg.norm(dir_vec)
                if norm_dir > 1e-12:
                    dir_unit = dir_vec / norm_dir
                    # evaluate noise field at offset coordinates
                    n_val = noise_field.evaluate(
                        c[0] + dir_vec[0] * depth,
                        c[1] + dir_vec[1] * depth,
                        c[2] + dir_vec[2] * depth,
                    )
                    local_v[vi] += dir_unit * (r_scale * n_val * 0.8)

            local_v[:, 2] *= 0.6
            world_v = local_v + c + nrm * (r_scale * 0.1)

            scales_vertices[v_off : v_off + per_scale_verts] = world_v
            scales_faces[f_off : f_off + per_scale_faces] = sphere_unit_f + v_off
            v_off += per_scale_verts
            f_off += per_scale_faces

        return scales_vertices[:v_off], scales_faces[:f_off]

    def buildMushroomMesh(self):
        """
        Gathers separate meshes (vertices, faces).
        Assembles the Mushroom and stores it.
        """
        stem_v, stem_f = self.buildStemMesh()
        cap_v, cap_inner_f, cap_outer_f = self.buildCapMesh()
        gills_v, gills_f = self.buildGillsMesh()

        # Get stem frame for placement
        stem_tip, n_tip, bn_tip, t_tip = self.get_stem_frame()
        translation = stem_tip + 0.1 * t_tip

        # Store Original position for later use
        cap_v_local = cap_v.copy()
        gills_v_local = gills_v.copy()

        # Transform local coordinates to world coordinates for cap and gills
        cap_v = self._transform_to_stem_frame(
            cap_v_local, translation, n_tip, bn_tip, t_tip
        )
        gills_v = self._transform_to_stem_frame(
            gills_v_local, translation, n_tip, bn_tip, t_tip
        )

        # Combine
        vertices = []
        faces = []
        ranges = {}

        # Counters for index and vertex
        v_offset = 0
        i_offset = 0

        # Append stem
        vertices.append(stem_v)
        faces.append(stem_f + v_offset)
        ranges["stem"] = (i_offset, stem_f.size)
        v_offset += len(stem_v)
        i_offset += stem_f.size

        # Append cap vertices
        vertices.append(cap_v)
        # Append inner faces
        faces.append(cap_inner_f + v_offset)
        ranges["cap_inner"] = (i_offset, cap_inner_f.size)
        i_offset += cap_inner_f.size
        # Append outer faces
        faces.append(cap_outer_f + v_offset)
        ranges["cap_outer"] = (i_offset, cap_outer_f.size)
        i_offset += cap_outer_f.size

        # Build scales in cap-local coordinates and then transform
        scales_v_local, scales_f = self.buildScalesMesh(cap_v_local, cap_outer_f)
        scales_v = self._transform_to_stem_frame(
            scales_v_local, translation, n_tip, bn_tip, t_tip
        )

        # Append scales vertices and faces
        vertices.append(scales_v)
        faces.append(scales_f + v_offset + len(cap_v))
        ranges["scales"] = (i_offset, scales_f.size)
        i_offset += scales_f.size

        # Update v_offset
        v_offset += len(cap_v) + len(scales_v)

        # Append gills
        vertices.append(gills_v)
        faces.append(gills_f + v_offset)
        ranges["gills"] = (i_offset, gills_f.size)
        i_offset += gills_f.size
        v_offset += len(gills_v)

        vertices = np.vstack(vertices)
        faces = np.vstack(faces)

        self.submesh_ranges = ranges
        self.mushroom_mesh = (vertices, faces)
        return vertices, faces

    def exportMushroomToOBJ(self, path):
        """
        Exports the mushroom to an OBJ file.
        """
        vertices, faces = self.mushroom_mesh

        # Compute face normals
        v0 = vertices[faces[:, 0]]
        v1 = vertices[faces[:, 1]]
        v2 = vertices[faces[:, 2]]
        face_normals = np.cross(v1 - v0, v2 - v0)

        # Compute vertex normals by averaging face normals
        vertex_normals = np.zeros_like(vertices)
        for i in range(3):
            np.add.at(vertex_normals, faces[:, i], face_normals)
        # Normalize
        lengths = np.linalg.norm(vertex_normals, axis=1)
        nonzero = lengths > 1e-12
        vertex_normals[nonzero] /= lengths[nonzero][:, None]

        with open(path, "w") as f:
            f.write("# Mushroom OBJ export\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")

            # Write vertex normals
            for vn in vertex_normals:
                f.write(f"vn {vn[0]} {vn[1]} {vn[2]}\n")

            # Write faces
            for face in faces:
                # Ensure integers and +1 for OBJ
                a, b, c = face + 1
                f.write(f"f {a} {b} {c}\n")

    def return_line(self):
        # A temporal helper function to pass a curve
        s = self.species
        cap_curve = Curves(
            s.cap_curve_segments,
            s.cap_height,
            s.cap_curve_type,
            s.cap_radius,
        )
        points = cap_curve.generate()
        return points
