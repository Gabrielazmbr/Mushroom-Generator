#!/usr/bin/env -S uv run --script
import sys
import traceback

import OpenGL.GL as gl
from ncca.ngl import Vec3, logger
from ncca.ngl.widgets import RGBColourWidget
from PySide6.QtCore import QFile
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from mushroomgen.core.build import Build
from mushroomgen.core.species import FLY_AGARIC
from mushroomgen.render.openGl import OpenGLScene
from mushroomgen.render.viewer import (
    plot,
    plot_lines,
    plot_mesh,
    visualize_pyvista,
)


class Loader(QUiLoader):
    def createWidget(self, class_name, parent=None, name=""):
        if class_name == "RGBColourWidget":
            return RGBColourWidget(parent)
        return super().createWidget(class_name, parent, name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.species = FLY_AGARIC
        self.load_ui("QtMainWidget.ui")
        self.resize(1024, 720)
        self.scene = OpenGLScene()
        self.centralWidget().layout().addWidget(self.scene, 0, 0, 2, 1)
        self._set_menu_widgets()
        self._set_color_widgets()
        self._connect_signals_and_slots()

    def _set_color_widgets(self):
        self.cap_inner_color.set_colour(self.species.cap_inner_color)
        self.cap_outer_color.set_colour(self.species.cap_outer_color)
        self.stem_color.set_colour(self.species.stem_color)
        self.gills_color.set_colour(self.species.gills_color)
        self.scales_color.set_colour(self.species.scales_color)

    def _set_menu_widgets(self):
        self.cap_curve_type.addItems(["Round Cap", "Cone Cap"])
        self.cap_curve_type.setCurrentIndex(0)
        self.stem_curve_type.addItems(["Stem Ring", "Stem Bulb"])
        self.stem_curve_type.setCurrentIndex(0)

    def _connect_signals_and_slots(self):
        self.exportobj.clicked.connect(self.scene.export_obj)
        # Cap
        self.cap_height.valueChanged.connect(self.scene.update_cap_height)
        self.cap_radius.valueChanged.connect(self.scene.update_cap_radius)
        self.cap_noise.valueChanged.connect(self.scene.update_cap_noise)
        self.cap_rows.valueChanged.connect(self.scene.update_cap_rows)
        self.cap_columns.valueChanged.connect(self.scene.update_cap_columns)
        self.cap_inner_color.colourChanged.connect(self.scene.update_cap_inner_color)
        self.cap_outer_color.colourChanged.connect(self.scene.update_cap_outer_color)
        self.cap_curve_type.currentTextChanged.connect(self.scene.update_cap_curve_type)
        # Stem
        self.stem_height.valueChanged.connect(self.scene.update_stem_height)
        self.stem_radius.valueChanged.connect(self.scene.update_stem_radius)
        self.stem_noise.valueChanged.connect(self.scene.update_stem_noise)
        self.stem_curve_type.currentTextChanged.connect(
            self.scene.update_stem_curve_type
        )
        self.stem_rows.valueChanged.connect(self.scene.update_stem_rows)
        self.stem_columns.valueChanged.connect(self.scene.update_stem_columns)
        self.stem_color.colourChanged.connect(self.scene.update_stem_color)
        # Gills
        self.gills_amount.valueChanged.connect(self.scene.update_gills_amount)
        self.gills_width.valueChanged.connect(self.scene.update_gills_width)
        self.gills_noise.valueChanged.connect(self.scene.update_gills_noise)
        self.gills_seed.valueChanged.connect(self.scene.update_gills_seed)
        self.gills_color.colourChanged.connect(self.scene.update_gills_color)
        # Gills
        self.scales_amount.valueChanged.connect(self.scene.update_scales_amount)
        self.scales_radius.valueChanged.connect(self.scene.update_scales_radius)
        self.scales_radius_jitter.valueChanged.connect(
            self.scene.update_scales_radius_jitter
        )
        self.scales_noise.valueChanged.connect(self.scene.update_scales_noise)
        self.scales_seed.valueChanged.connect(self.scene.update_scales_seed)
        self.scales_color.colourChanged.connect(self.scene.update_scales_color)
        self.scales_rows.valueChanged.connect(self.scene.update_scales_rows)
        self.scales_columns.valueChanged.connect(self.scene.update_scales_columns)

        slider_label_map = {
            # Cap
            self.cap_height: (self.cap_height_num, 1),
            self.cap_radius: (self.cap_radius_num, 1),
            self.cap_noise: (self.cap_noise_num, 10),
            self.cap_rows: (self.cap_rows_num, 1),
            self.cap_columns: (self.cap_columns_num, 1),
            # Stem
            self.stem_height: (self.stem_height_num, 1),
            self.stem_radius: (self.stem_radius_num, 10),
            self.stem_noise: (self.stem_noise_num, 10),
            self.stem_rows: (self.stem_rows_num, 1),
            self.stem_columns: (self.stem_columns_num, 1),
            # Gills
            self.gills_amount: (self.gills_amount_num, 1),
            self.gills_width: (self.gills_width_num, 10),
            self.gills_noise: (self.gills_noise_num, 10),
            self.gills_seed: (self.gills_seed_num, 1),
            # Scales
            self.scales_amount: (self.scales_amount_num, 1),
            self.scales_radius: (self.scales_radius_num, 10),
            self.scales_radius_jitter: (self.scales_radius_jitter_num, 10),
            self.scales_noise: (self.scales_noise_num, 1),
            self.scales_seed: (self.scales_seed_num, 1),
            self.scales_rows: (self.scales_rows_num, 1),
            self.scales_columns: (self.scales_columns_num, 1),
        }

        # Connect sliders with labels
        for slider, (label, scale) in slider_label_map.items():
            slider.valueChanged.connect(
                lambda v, lbl=label, s=scale: lbl.setText(f"{v / s:.1f}")
            )
            label.setText(f"{slider.value() / scale:.1f}")

    def load_ui(self, ui_file_name: str) -> None:
        """
        Load a .ui file.
        """
        try:
            loader = Loader()
            ui_file = QFile(ui_file_name)
            ui_file.open(QFile.OpenModeFlag.ReadOnly)
            loaded_ui = loader.load(ui_file, self)
            self.setCentralWidget(loaded_ui)
            for child in loaded_ui.findChildren(QWidget):
                name = child.objectName()
                if name:
                    setattr(self, name, child)
            ui_file.close()
        except Exception:
            print(f"There was an issue loading the Qt UI file {ui_file_name}")
            raise


def main():
    app = QApplication(sys.argv)
    format = QSurfaceFormat()
    format.setMajorVersion(4)
    format.setMinorVersion(1)
    format.setProfile(QSurfaceFormat.CoreProfile)
    format.setDepthBufferSize(24)
    format.setSamples(4)
    QSurfaceFormat.setDefaultFormat(format)
    print(f"{format.profile()} OpenGL {format.majorVersion()} {format.minorVersion()}")

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
