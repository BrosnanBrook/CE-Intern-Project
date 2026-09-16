import sys
import numpy
import vtk
from pathlib import Path
from vtkmodules.util import numpy_support
vtk_to_numpy = numpy_support.vtk_to_numpy

from PySide6 import QtCore, QtWidgets, QtGui

class MainWindow(QtWidgets.QMainWindow):
    def __init__(
            self):
        super().__init__()
        self.setWindowTitle("Volume Viewer")
        self.resize(700, 500)
        self.setMinimumSize(400, 300)

        self.volume_data = VolumeData()
        self.viewer = SliceViewerWidget(self.volume_data)

        
        self.viewer.setStyleSheet("""
            QDockWidget {
                background-color: #e6e9ef;
                border: 1px solid blue;
                color: #e6e9ef;
            }

            QLabel {
                color: ##707f9c;
            }

            QPushButton {
                padding: 6px 10px;
                border: 1px solid #474a4d;
                border-radius: 4px;
                background-color: #3a424f;
            }

            QPushButton:hover {
                background-color: #4a5565;
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
        

class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(
            self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


    def wheelEvent(
            self, event) -> None:
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def panEvent(
            self, event) -> None:
        if event.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)

class GraphicsImage(QtWidgets.QGraphicsPixmapItem):
    def __init__(self):
        super().__init__()
        self.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
        self.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
        self.setZValue(1)
        self.setOpacity(1.0)
        self.setVisible(True)
        self.setToolTip("Orthographic Slice")


class SliceViewerWidget(QtWidgets.QDockWidget):
    slice_ready = QtCore.Signal(QtGui.QImage, str)

    def __init__(
            self, volume_data):
        super().__init__()
        self.current_qimage = None
        self.current_slice = None
        self.volume_data = volume_data
        self.current_axis = "Axial"

        self.slice_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slice_slider.valueChanged.connect(self.update_slice)

        self.axis_combo = QtWidgets.QComboBox()
        self.axis_combo.addItems(["Axial", "Coronal", "Sagittal"])
        self.axis_combo.currentTextChanged.connect(self.set_axis)

        self.button_raw = QtWidgets.QPushButton("Import Volume (raw)")
        self.button_vtk = QtWidgets.QPushButton("Import Volume (vtk)")
        self.button_rng = QtWidgets.QPushButton("Generate Random Volume")
        self.voxel_size_x = QtWidgets.QDoubleSpinBox()
        self.voxel_size_y = QtWidgets.QDoubleSpinBox()
        self.voxel_size_z = QtWidgets.QDoubleSpinBox()
        for box in [self.voxel_size_x, self.voxel_size_y, self.voxel_size_z]:
            box.setRange(0.00001, 5.0)
            box.setDecimals(5)
            box.setSingleStep(0.00001)
            box.setValue(1.0)

        self.text = QtWidgets.QLabel("Orthogonal View",
                                     alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        self.text_voxel_size = QtWidgets.QLabel(
            "Voxel Size: X, Y, Z",
            alignment=QtCore.Qt.AlignmentFlag.AlignBottom
        )

        self.widget = QtWidgets.QWidget()
        self.setWidget(self.widget)
        self.layout = QtWidgets.QVBoxLayout(self.widget)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button_raw)
        self.layout.addWidget(self.button_vtk)
        self.layout.addWidget(self.button_rng)
        self.layout.addWidget(self.axis_combo)
        self.layout.addWidget(self.slice_slider)
        self.layout.addWidget(self.text_voxel_size)
        for box in [self.voxel_size_x, self.voxel_size_y, self.voxel_size_z]:
            self.layout.addWidget(box)


        self.button_raw.clicked.connect(self.import_volume_raw)
        self.button_vtk.clicked.connect(self.import_volume_vtk)
        self.button_rng.clicked.connect(self.generate_random_volume)
        self.voxel_size_x.valueChanged.connect(self.set_voxel_size)
        self.voxel_size_y.valueChanged.connect(self.set_voxel_size)
        self.voxel_size_z.valueChanged.connect(self.set_voxel_size)


    def import_volume_raw(
            self) -> None:
        print("RAW handler reached")
        print("Importing .raw volume...")
        dialog_parent = self.window()
        dialog_parent.raise_()
        dialog_parent.activateWindow()

        file_dialog = QtWidgets.QFileDialog(
            None,
            "Open RAW Volume",
            "",
            "RAW Files (*.raw)",
        )
        file_dialog.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        file_dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        if file_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            print("No file selected.")
            return

        selected_files = file_dialog.selectedFiles()
        file_path = selected_files[0] if selected_files else ""
        if not file_path:
            print("No file selected.")
            return

        size_x, ok = self.get_dimension("Size X:")
        if not ok:
            return
        size_y, ok = self.get_dimension("Size Y:")
        if not ok:
            return
        size_z, ok = self.get_dimension("Size Z:")
        if not ok:
            return
            
        temp_dtype, ok = QtWidgets.QInputDialog.getItem(
            None,
            "RAW Data Type",
            "Select dtype:",
            ["uint8", "uint16", "float32"],
            0,
            False,
        )
        if not ok:
            print("RAW import cancelled.")
            return
        try:   
            loaded = self.volume_data.load_raw(
                file_path,
                shape=(size_x, size_y, size_z),
                dtype=temp_dtype,
            )
        except (OSError, ValueError) as exc:
            print(f"Failed to load RAW volume: {exc}")
            return
        if not loaded:
            return
        print("RAW dtype:", self.volume_data.array.dtype)
        print("RAW shape:", self.volume_data.array.shape)
        print("RAW min/max:", self.volume_data.array.min(), self.volume_data.array.max())
        print("RAW nonzero:", numpy.count_nonzero(self.volume_data.array))
        print("RAW volume imported successfully.")
        self.set_axis(self.axis_combo.currentText())

    @staticmethod
    def get_dimension(label):
        dialog = QtWidgets.QInputDialog()
        dialog.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        dialog.setWindowTitle("RAW Dimensions")
        dialog.setLabelText(label)
        dialog.setInputMode(QtWidgets.QInputDialog.InputMode.IntInput)
        dialog.setIntValue(256)
        dialog.setIntRange(1, 100000)
        dialog.setIntStep(1)
        dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        result = dialog.exec()
        return dialog.intValue(), result == QtWidgets.QDialog.DialogCode.Accepted
                            
    def import_volume_vtk(
            self) -> bool:
        print("Importing .vti volume...")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window(), 
            "Open VTI Volume",
            "", 
            "VTI Files (*.vti)"
        )
        if not file_path:
            print("No file selected.")
            return False
        try:
            self.volume_data.load_vti(file_path)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Failed to load VTI: {exc}")
            return False
        print("VTI volume imported successfully.")
        self.set_axis(self.axis_combo.currentText())
        return True
        
    def set_axis(
            self, axis) -> None:
        print(f"Axis changed to: {axis}")
        self.current_axis = axis

        if self.volume_data.array is None:
            return
                
        max_slice = VolumeData.get_max_slice_for_axis(self.volume_data.array, axis)
        self.slice_slider.setRange(0, max_slice)

        middle_index = max_slice // 2
        self.slice_slider.setValue(middle_index)
        self.update_slice(middle_index)

    def update_slice(
            self, index) -> None:
        print(f"Slice changed to: {index}")
        self.current_slice = index

        if self.volume_data.array is None:
            print("No volume data available.")
            return

        slice_2d = VolumeData.get_slice(self.volume_data.array, self.current_axis, index)

        image = VolumeData.normalize_to_uint8(slice_2d)
        image = numpy.ascontiguousarray(image)

        self.current_qimage = self.numpy_to_qimage(image)
        self.slice_ready.emit(self.current_qimage, self.current_axis)
        
        # At this point, slice_2d contains the 2D slice of the volume data
        print(f"Extracted 2D slice shape: {slice_2d.shape}")
        print(
            "minimum:", slice_2d.min(),
            "maximum:", slice_2d.max(),
            "center value:", slice_2d[slice_2d.shape[0] // 2, slice_2d.shape[1] // 2]
        )

    def numpy_to_qimage(
            self, image) -> QtGui.QImage:
        height, width = image.shape
        bytes_per_line = image.strides[0]

        q_image = QtGui.QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QtGui.QImage.Format.Format_Grayscale8,
        ).copy()

        return q_image

    def generate_random_volume(
            self) -> None:
        self.volume_data._sx = 128
        self.volume_data._sy = 128
        self.volume_data._sz = 128
        self.volume_data._dtype = numpy.float32
        shape = (self.volume_data._sz, self.volume_data._sy, self.volume_data._sx)
        self.volume_data.array = numpy.random.rand(*shape).astype(self.volume_data._dtype)

        self.set_axis(self.axis_combo.currentText())

    def set_voxel_size(
            self) -> None:
        new_size = (
            self.voxel_size_x.value(),
            self.voxel_size_y.value(),
            self.voxel_size_z.value()
        )
        
        self.volume_data.spacing = new_size
        if self.current_qimage is not None:
            self.slice_ready.emit(self.current_qimage, self.current_axis)


class VolumeData:
    def __init__(
            self):
        self.array = None
    # RAW data has no metadata, so unit spacing is the neutral default.
        self.spacing = (1.0, 1.0, 1.0)
        self.origin = None
        self.dimensions = None
        self.format = None

    # Two separate loading functions, one for .raw files and one for .vti files (VTK)
    # Initially I was storing x,y,z for raw files as class member variables, but I don't store
    # this in the class itself so I pass the shape as an argument to the load_raw function.
    # This is to keep the data logic separate from the UI.
    def load_raw(
            self, file_path, shape, dtype) -> bool:
        path = file_path.strip()
        if not path:
            print("Enter a file path.")
            return False
        p = Path(path)
        if not p.exists():
            print(f"File does not exist: {p}")
            return False

        if len(shape) != 3 or any(size <= 0 for size in shape):
            raise ValueError(f"RAW shape must contain three positive sizes: {shape}")

        dtype = numpy.dtype(dtype)
        print(f"Loading RAW file: {p}, shape: {shape}, dtype: {dtype}")

        expected_bytes = numpy.prod(shape) * dtype.itemsize
        if p.stat().st_size != expected_bytes:
            raise ValueError(
                f"File size does not match dimensions and dtype: "
                f"{p.stat().st_size} != {expected_bytes}"
            )
        try:
            self.array = numpy.memmap(
                str(p),
                dtype=dtype,
                mode="r",
                shape=(shape[2], shape[1], shape[0]),
            )
        except Exception as exc:
            print(f"Failed to load volume: {exc}")
            return False
        
        return True
        
    def load_vti(
            self, file_path) -> None:
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(file_path)
        reader.Update()
    
        image_data = reader.GetOutput()
        
        self.dimensions = image_data.GetDimensions()
        self.spacing = image_data.GetSpacing()
        self.origin = image_data.GetOrigin()
        
        point_data = image_data.GetPointData()
        vtk_scalars = point_data.GetScalars()
        
        if vtk_scalars is None:
            raise ValueError("VTI file does not contain voxel data.")
        
        flat_array = vtk_to_numpy(vtk_scalars)
        
        self._sx = self.dimensions[0]
        self._sy = self.dimensions[1]
        self._sz = self.dimensions[2]
        
        if flat_array.size != self._sx * self._sy * self._sz:
            raise ValueError("VTI file dimensions do not match the expected size.")
        self.array = flat_array.reshape((self._sz, self._sy, self._sx))
        self.spacing = (1.0, 1.0, 1.0)
    
    @staticmethod
    def get_slice(
            volume, axis, index):
        if axis == "Axial":
            return volume[index, :, :]
        if axis == "Coronal":
            return volume[:, index, :]
        if axis == "Sagittal":
            return volume[:, :, index]
        raise ValueError(f"Unknown axis: {axis}")

    @staticmethod
    def get_max_slice_for_axis(
            volume, axis):
        depth = volume.shape[0] 
        height = volume.shape[1]
        width = volume.shape[2]

        if axis == "Axial":
            return depth - 1
        if axis == "Coronal":
            return height - 1
        if axis == "Sagittal":
            return width - 1
        
        raise ValueError(f"Unknown axis: {axis}")

    @staticmethod
    def get_middle_slice_for_axis(
            volume, axis):
        max_index = VolumeData.get_max_slice_for_axis(volume, axis)
        return max_index // 2

    def normalize_to_uint8(
            slice_2d):
        min_val = slice_2d.min()
        max_val = slice_2d.max()

        if max_val == min_val:
            return numpy.absolute(numpy.zeros_like(slice_2d, dtype=numpy.uint8))

        normalized = numpy.clip((slice_2d - min_val) / (max_val - min_val),
                                0,
                                1,
        )     
        image_8bit = normalized * 255

        return image_8bit.astype(numpy.uint8)

    def change_voxel_size(
            self, new_voxel_size):
        self.spacing = new_voxel_size
    

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())