import math
from pathlib import Path

import numpy as np
import OpenGL.GL as gl
from ncca.ngl import (
    DefaultShader,
    IndexVertexData,
    Mat3,
    Mat4,
    ShaderLib,
    Transform,
    VAOFactory,
    VAOType,
    Vec3,
    Vec3Array,
    look_at,
    perspective,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QFileDialog

from mushroomgen.core.build import Build
from mushroomgen.core.species import FLY_AGARIC


class OpenGLScene(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.keys_pressed = set()

        self.mouse_global_tx: Mat4 = Mat4()
        self.window_width: int = 1024
        self.window_height: int = 720
        # Based on:
        # De Vries, J. (n.d.). Coordinate systems. LearnOpenGL.com.
        # Available from: https://learnopengl.com/Getting-started/Coordinate-Systems.
        self.view: Mat4 = Mat4()  # View matrix
        self.project: Mat4 = Mat4()  # Projection matrix
        self.model_position: Vec3 = Vec3()  # Position of the model in world space

        # Controllers based on:
        # Macey, Jon. (n.d.). PyNGLDemos/ObjViewer [Source code]
        # Available from: https://github.com/NCCA/PyNGLDemos/tree/main/ObjViewer
        # Mouse control
        self.rotate: bool = False
        self.translate: bool = False
        self.spin_x_face: int = 0
        self.spin_y_face: int = 0
        self.original_x_rotation: int = 0
        self.original_y_rotation: int = 0
        self.original_x_pos: int = 0
        self.original_y_pos: int = 0
        self.INCREMENT: float = 0.01  # Sensitivity for translation
        self.ZOOM: float = 0.1  # Sensitivity for zooming

    @Slot(int)
    def update_cap_height(self, value):
        self.species.cap_height = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_radius(self, value):
        self.species.cap_radius = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_noise(self, value):
        self.species.cap_noise = value / 10
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_rows(self, value):
        self.species.cap_curve_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_columns(self, value):
        self.species.cap_angle_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_inner_color(self, value):
        self.species.cap_inner_color = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_cap_outer_color(self, value):
        self.species.cap_outer_color = value
        self.rebuild_mushroom()
        self.update()

    @Slot(str)
    def update_cap_curve_type(self, text):
        self.species.cap_curve_type = text
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_height(self, value):
        self.species.stem_height = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_radius(self, value):
        self.species.stem_radius = value / 10
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_noise(self, value):
        self.species.stem_noise = value / 100
        self.rebuild_mushroom()
        self.update()

    @Slot(str)
    def update_stem_curve_type(self, text):
        self.species.stem_curve_type = text
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_rows(self, value):
        self.species.stem_row_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_columns(self, value):
        self.species.stem_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_stem_color(self, value):
        self.species.stem_color = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_gills_amount(self, value):
        self.species.gills_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_gills_width(self, value):
        self.species.gills_width = value / 100
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_gills_noise(self, value):
        self.species.gills_noise = value / 100
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_gills_seed(self, value):
        self.species.gills_seed = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_gills_color(self, value):
        self.species.gills_color = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_amount(self, value):
        self.species.scales_count = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_radius(self, value):
        self.species.scales_radius = value / 10
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_radius_jitter(self, value):
        self.species.scales_radius_jitter = value / 10
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_noise(self, value):
        self.species.scales_noise = value / 10
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_seed(self, value):
        self.species.scales_seed = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_rows(self, value):
        self.species.scale_lat_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_columns(self, value):
        self.species.scale_lon_segments = value
        self.rebuild_mushroom()
        self.update()

    @Slot(int)
    def update_scales_color(self, value):
        self.species.scales_color = value
        self.rebuild_mushroom()
        self.update()

    def export_obj(self, path):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Mushroom", "mushroom.obj", "OBJ Files (*.obj)"
        )

        if path:
            self.build.exportMushroomToOBJ(path)
            print(f"Mushroom exported to {path}")

    def initializeGL(self):
        self.makeCurrent()
        gl.glClearColor(0.4, 0.4, 0.4, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)

        shader_dir = Path(__file__).parent / "shaders"
        vs = shader_dir / "Vertex.glsl"
        fs = shader_dir / "Fragment.glsl"

        ShaderLib.load_shader("PBR", str(vs), str(fs))

        # Importing my mesh
        self.species = FLY_AGARIC
        self.build = Build(FLY_AGARIC)

        vertices, faces = self.build.buildMushroomMesh()
        # Convert my np arrays to float 32 and uint32
        vertices_32 = np.ascontiguousarray(vertices, dtype=np.float32)
        faces_32 = np.ascontiguousarray(faces, dtype=np.uint32)
        indices = faces_32.ravel()
        self.vertices_32 = vertices_32  # save on self for later use
        self.faces_32 = faces_32
        self.indices = indices

        # Compute Vertex and faces normals
        v0 = vertices_32[faces_32[:, 0]]
        v1 = vertices_32[faces_32[:, 1]]
        v2 = vertices_32[faces_32[:, 2]]
        face_normals = np.cross(v1 - v0, v2 - v0)
        vertex_normals = np.zeros_like(vertices_32, dtype=np.float32)
        # Adding face normals for each three vertex indices
        np.add.at(vertex_normals, faces_32[:, 0], face_normals)
        np.add.at(vertex_normals, faces_32[:, 1], face_normals)
        np.add.at(vertex_normals, faces_32[:, 2], face_normals)

        # Normalize vertex normals
        lengths = np.linalg.norm(vertex_normals, axis=1)
        nonzero = lengths > 1e-12
        vertex_normals[nonzero] /= lengths[nonzero][:, None]

        # Create N,6 array for positions and normals
        N = vertices_32.shape[0]
        vertex_data = np.empty((N, 6), dtype=np.float32)
        vertex_data[:, 0:3] = vertices_32
        vertex_data[:, 3:6] = vertex_normals

        # Recenter an scales in viewing size
        bb_min = vertices_32.min(axis=0)
        bb_max = vertices_32.max(axis=0)
        self.center = (bb_min + bb_max) / 2.0
        self.radius = np.max(np.linalg.norm(vertices_32 - self.center, axis=1))
        self.scale = 1.0 / (self.radius + 1e-8)

        # Model Matrix
        self.model_transform = Transform()
        self.model_transform.set_scale(self.scale, self.scale, self.scale)
        self.model_transform.set_position(
            -float(self.center[0]), -float(self.center[1]), -float(self.center[2])
        )
        # Translation
        model_translate = Mat4()
        model_translate[3][0] = -float(self.center[0])
        model_translate[3][1] = -float(self.center[1])
        model_translate[3][2] = -float(self.center[2])

        # Orientation fix for Y-up
        orientation = Mat4().rotate_y(180.0) @ Mat4().rotate_x(-90.0)
        # Scale
        scale_mat = Mat4()
        scale_mat[0][0] = float(self.scale)
        scale_mat[1][1] = float(self.scale)
        scale_mat[2][2] = float(self.scale)

        self.model_matrix_base = scale_mat @ orientation @ model_translate

        # Camera View
        scaled_radius = self.radius * self.scale
        degrees = 45.0
        fov = math.radians(degrees)
        margin = 1.2
        camera_distance = max(
            0.01, (scaled_radius / max(1e-6, math.sin(fov / 2.0))) * margin
        )
        vertical_offset = scaled_radius * -0.50

        self.camera_target = Vec3(0.0, 0.0, 0.0)
        self.camera_up = Vec3(0.0, 1.0, 0.0)
        self.camera_distance = camera_distance
        self.camera_vertical_offset = vertical_offset
        # View Matrix
        eye = Vec3(0.0, self.camera_vertical_offset, self.camera_distance)
        self.view = look_at(eye, self.camera_target, self.camera_up)

        # Create VAO
        self.vao = VAOFactory.create_vao(VAOType.SIMPLE_INDEX, gl.GL_TRIANGLES)

        with self.vao:
            ivd = IndexVertexData(
                vertex_data.flatten(),
                vertex_data.nbytes,
                self.indices,
                gl.GL_UNSIGNED_INT,
                gl.GL_DYNAMIC_DRAW,
            )
            self.vao.set_data(ivd)  # single buffer

            # Pointing attributes
            stride = int(vertex_data.strides[0])
            offset_pos = 0
            offset_norm = int(3 * vertex_data.itemsize)
            self.vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, stride, offset_pos)
            self.vao.set_vertex_attribute_pointer(
                1, 3, gl.GL_FLOAT, stride, offset_norm
            )

            # Indices to draw
            self.vao.set_num_indices(self.indices.size)

        # Shader constants
        self.light_world = np.array([0.0, 2.0, 2.0], dtype=np.float32)

    def rebuild_mushroom(self):
        self.build = Build(self.species)
        vertices, faces = self.build.buildMushroomMesh()

        vertices_32 = np.ascontiguousarray(vertices, dtype=np.float32)
        faces_32 = np.ascontiguousarray(faces, dtype=np.uint32)
        indices = faces_32.ravel()
        self.vertices_32 = vertices_32
        self.faces_32 = faces_32
        self.indices = indices

        v0 = vertices_32[faces_32[:, 0]]
        v1 = vertices_32[faces_32[:, 1]]
        v2 = vertices_32[faces_32[:, 2]]
        face_normals = np.cross(v1 - v0, v2 - v0)
        vertex_normals = np.zeros_like(vertices_32, dtype=np.float32)
        np.add.at(vertex_normals, faces_32[:, 0], face_normals)
        np.add.at(vertex_normals, faces_32[:, 1], face_normals)
        np.add.at(vertex_normals, faces_32[:, 2], face_normals)
        lengths = np.linalg.norm(vertex_normals, axis=1)
        nonzero = lengths > 1e-12
        vertex_normals[nonzero] /= lengths[nonzero][:, None]

        N = vertices_32.shape[0]
        vertex_data = np.empty((N, 6), dtype=np.float32)
        vertex_data[:, 0:3] = vertices_32
        vertex_data[:, 3:6] = vertex_normals

        bb_min = vertices_32.min(axis=0)
        bb_max = vertices_32.max(axis=0)
        self.center = (bb_min + bb_max) / 2.0
        self.radius = np.max(np.linalg.norm(vertices_32 - self.center, axis=1))
        self.scale = 1.0 / (self.radius + 1e-8)

        # Update model matrix base
        model_translate = Mat4()
        model_translate[3][0] = -float(self.center[0])
        model_translate[3][1] = -float(self.center[1])
        model_translate[3][2] = -float(self.center[2])

        orientation = Mat4().rotate_y(180.0) @ Mat4().rotate_x(-90.0)
        scale_mat = Mat4()
        scale_mat[0][0] = float(self.scale)
        scale_mat[1][1] = float(self.scale)
        scale_mat[2][2] = float(self.scale)
        self.model_matrix_base = scale_mat @ orientation @ model_translate

        # Update VAO
        with self.vao:
            ivd = IndexVertexData(
                vertex_data.flatten(),
                vertex_data.nbytes,
                self.indices,
                gl.GL_UNSIGNED_INT,
                gl.GL_STATIC_DRAW,
            )
            self.vao.set_data(ivd)

            stride = int(vertex_data.strides[0])
            offset_pos = 0
            offset_norm = int(3 * vertex_data.itemsize)
            self.vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, stride, offset_pos)
            self.vao.set_vertex_attribute_pointer(
                1, 3, gl.GL_FLOAT, stride, offset_norm
            )
            self.vao.set_num_indices(self.indices.size)

    def paintGL(self):
        self.makeCurrent()
        gl.glViewport(0, 0, self.window_width, self.window_height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Apply rotation based on user input
        rot_x = Mat4().rotate_x(self.spin_x_face)
        rot_y = Mat4().rotate_y(self.spin_y_face)
        self.mouse_global_tx = rot_y @ rot_x
        # Update model position
        self.mouse_global_tx[3][0] = self.model_position.x
        self.mouse_global_tx[3][1] = self.model_position.y
        self.mouse_global_tx[3][2] = self.model_position.z

        eye = Vec3(0.0, self.camera_vertical_offset, self.camera_distance)
        self.view = look_at(eye, self.camera_target, self.camera_up)

        model_matrix = getattr(
            self, "model_matrix_base", self.model_transform.get_matrix()
        )

        M_world = self.mouse_global_tx @ model_matrix

        # Get normal matrix
        # Compute Model-View and MVP
        MV = self.view @ self.mouse_global_tx @ model_matrix
        MVP = self.project @ MV
        # Build normal matrix as Mat3
        normal_mat = Mat3.from_mat4(MV)
        normal_mat.inverse()
        normal_mat.transpose()

        with self.vao:
            for name, shader in [
                ("stem", "PBR"),
                ("cap_inner", "PBR"),
                ("cap_outer", "PBR"),
                ("scales", "PBR"),
                ("gills", "PBR"),
            ]:
                start, count = self.build.submesh_ranges[name]

                ShaderLib.use(shader)

                # Matrices
                ShaderLib.set_uniform("MVP", MVP)
                ShaderLib.set_uniform("M", M_world)
                ShaderLib.set_uniform("normalMatrix", normal_mat)

                # Camera
                ShaderLib.set_uniform(
                    "camPos",
                    float(eye.x),
                    float(eye.y),
                    float(eye.z),
                )

                # Lights
                light_colors = Vec3Array(
                    [
                        Vec3(300.0, 300.0, 300.0),
                        Vec3(300.0, 300.0, 300.0),
                        Vec3(300.0, 300.0, 300.0),
                    ]
                )

                self.light_positions = Vec3Array(
                    [
                        Vec3(-10.0, 4.0, -10.0),
                        Vec3(10.0, 4.0, -10.0),
                        Vec3(10.0, 4.0, 10.0),
                    ]
                )
                for i in range(3):
                    ShaderLib.set_uniform(
                        f"lightPositions[{i}]", self.light_positions[i]
                    )
                    ShaderLib.set_uniform(f"lightColors[{i}]", light_colors[i])

                # Shaders
                if name == "stem":
                    ShaderLib.set_uniform(
                        "albedo",
                        self.species.stem_color.x,
                        self.species.stem_color.y,
                        self.species.stem_color.z,
                    )
                    ShaderLib.set_uniform("roughness", 0.8)
                elif name == "cap_inner":
                    ShaderLib.set_uniform(
                        "albedo",
                        self.species.cap_inner_color.x,
                        self.species.cap_inner_color.y,
                        self.species.cap_inner_color.z,
                    )
                    ShaderLib.set_uniform("roughness", 0.4)
                elif name == "cap_outer":
                    ShaderLib.set_uniform(
                        "albedo",
                        self.species.cap_outer_color.x,
                        self.species.cap_outer_color.y,
                        self.species.cap_outer_color.z,
                    )
                    ShaderLib.set_uniform("roughness", 0.4)
                elif name == "scales":
                    ShaderLib.set_uniform(
                        "albedo",
                        self.species.scales_color.x,
                        self.species.scales_color.y,
                        self.species.scales_color.z,
                    )
                    ShaderLib.set_uniform("roughness", 0.6)
                elif name == "gills":
                    ShaderLib.set_uniform(
                        "albedo",
                        self.species.gills_color.x,
                        self.species.gills_color.y,
                        self.species.gills_color.z,
                    )
                    ShaderLib.set_uniform("roughness", 0.9)

                ShaderLib.set_uniform("metallic", 0.0)
                ShaderLib.set_uniform("ao", 1.0)

                gl.glDrawElements(
                    gl.GL_TRIANGLES,
                    count,
                    gl.GL_UNSIGNED_INT,
                    gl.ctypes.c_void_p(start * 4),
                )

    def resizeGL(self, w: int, h: int):
        # Framebuffer size
        if hasattr(self, "devicePixelRatioF"):
            dpr = float(self.devicePixelRatioF())
        elif hasattr(self, "devicePixelRatio"):
            dpr = float(self.devicePixelRatio())
        else:
            dpr = 1.0
        self.window_width = max(1, int(round(w * dpr)))
        self.window_height = max(1, int(round(h * dpr)))
        aspect = self.window_width / self.window_height
        self.project = perspective(45.0, aspect, 0.1, 350)
        gl.glViewport(0, 0, self.window_width, self.window_height)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_W:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        elif key == Qt.Key_S:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        elif key == Qt.Key_Space:
            # Reset rotation and position
            self.spin_x_face = 0
            self.spin_y_face = 0
            self.model_position.set(0, 0, 0)
        else:
            # Call base implementation for unhandled keys
            super().keyPressEvent(event)

        self.update()

    def mouseMoveEvent(self, event) -> None:
        # Controllers based on:
        # Macey, Jon. (n.d.). PyNGLDemos/ObjViewer [Source code]
        # Available from: https://github.com/NCCA/PyNGLDemos/tree/main/ObjViewer
        if self.rotate and event.buttons() == Qt.LeftButton:
            position = event.position()
            diff_x = position.x() - self.original_x_rotation
            diff_y = position.y() - self.original_y_rotation
            self.spin_x_face += int(0.5 * diff_y)
            self.spin_y_face += int(0.5 * diff_x)
            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()
            self.update()
        elif self.translate and event.buttons() == Qt.RightButton:
            position = event.position()
            diff_x = int(position.x() - self.original_x_pos)
            diff_y = int(position.y() - self.original_y_pos)
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.model_position.x += self.INCREMENT * diff_x
            self.model_position.y -= self.INCREMENT * diff_y
            self.update()

    def mousePressEvent(self, event) -> None:
        # Controllers based on:
        # Macey, Jon. (n.d.). PyNGLDemos/ObjViewer [Source code]
        # Available from: https://github.com/NCCA/PyNGLDemos/tree/main/ObjViewer
        position = event.position()
        if event.button() == Qt.LeftButton:
            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()
            self.rotate = True
        elif event.button() == Qt.RightButton:
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.translate = True

    def mouseReleaseEvent(self, event) -> None:
        # Controllers based on:
        # Macey, Jon. (n.d.). PyNGLDemos/ObjViewer [Source code]
        # Available from: https://github.com/NCCA/PyNGLDemos/tree/main/ObjViewer
        # Stop rotating when the left button is released
        if event.button() == Qt.LeftButton:
            self.rotate = False
        # Stop translating when the right button is released
        elif event.button() == Qt.RightButton:
            self.translate = False

    def wheelEvent(self, event) -> None:
        # based on ObjViewer PyNGLDemos example
        num_pixels = event.angleDelta()
        # Zoom in or out by adjusting the Z position of the model
        if num_pixels.x() > 0:
            self.model_position.z += self.ZOOM
        elif num_pixels.x() < 0:
            self.model_position.z -= self.ZOOM
        self.update()
