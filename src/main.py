import sys
import math
from pathlib import Path
from vtkmodules.util import numpy_support
vtk_to_numpy = numpy_support.vtk_to_numpy

from PySide6 import QtCore, QtWidgets, QtGui
from slice_viewer import SliceViewerWidget
from volume_data import VolumeData
from qt_graphics import GraphicsView, GraphicsImage

ICON_PATH = Path(__file__).resolve().parent / "images" / "VolumeIcon.png"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(
            self):
        super().__init__()
        self.setWindowTitle("VolSlicer")
        self.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))
        self.resize(700, 500)
        self.setMinimumSize(700, 500)

        self.volume_data = VolumeData()
        self.viewer = SliceViewerWidget(self.volume_data)
        self.viewer.setTitleBarWidget(QtWidgets.QWidget())
        self._default_dock_width = 140
        self._base_window_width = None
        self._base_window_height = None
        
        self.viewer.setStyleSheet("""
            QDockWidget QPushButton {
                background-color: #747b85;
                border: 1px solid #8d949d;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px 5px;
            }

            QDockWidget QPushButton:hover {
                background-color: #858d97;
            }

            QDockWidget QPushButton:pressed {
                background-color: #646b75;
            }

            QDockWidget QComboBox {
                background-color: #747b85;
                border: 1px solid #8d949d;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px 5px;
            }

            QDockWidget QComboBox:hover {
                background-color: #858d97;
            }

            QDockWidget QComboBox QAbstractItemView {
                color: #ffffff;
            }
            
            QDockWidget QComboBox:pressed {
                background-color: #646b75;
            }

        """)

        self.scene = QtWidgets.QGraphicsScene(self)
        

        self.image = GraphicsImage()
        self.scene.addItem(self.image)
        self.image.setPos(400, 80)
        self.viewer.slice_ready.connect(self.display_slice)

        self.scene.setSceneRect(0, 0, 1100, 700)

        view = GraphicsView(self.scene)
        view.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        view.setBackgroundBrush(QtGui.QColor("#1e2530"))
        view.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        view.centerOn(self.image)
        self.viewer.adjustSize()
        self.setCentralWidget(view)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.viewer)
        QtCore.QTimer.singleShot(0, self._record_base_sizes)


    def _record_base_sizes(self) -> None:
        self.resizeDocks(
            [self.viewer], 
            [self._default_dock_width], 
            QtCore.Qt.Orientation.Horizontal
        )
        self._base_window_width = self.width()
        self._base_window_height = self.height()


    @QtCore.Slot(QtGui.QImage, str)
    def display_slice(self, image, axis):
        self.image.setPixmap(QtGui.QPixmap.fromImage(image))

        spacing_x, spacing_y, spacing_z = self.volume_data.spacing
        if axis == "Axial":
            plane_spacing_x, plane_spacing_y = spacing_x, spacing_y
        elif axis == "Coronal":
            plane_spacing_x, plane_spacing_y = spacing_x, spacing_z
        else:
            plane_spacing_x, plane_spacing_y = spacing_y, spacing_z

        scale = 2.0 / max(plane_spacing_x, plane_spacing_y)
        transform = QtGui.QTransform.fromScale(
            plane_spacing_x * scale,
            plane_spacing_y * scale,
        )
        self.image.setTransform(transform)
        

        bounds = self.image.sceneBoundingRect().adjusted(-40, -40, 40, 40)
        self.scene.setSceneRect(self.scene.itemsBoundingRect().united(bounds))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()

    sys.exit(app.exec())