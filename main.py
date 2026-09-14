import vtk
from pathlib import Path
from vtkmodules.util import numpy_support
vtk_to_numpy = numpy_support.vtk_to_numpy
import numpy

from PySide6 import QtCore, QtWidgets, QtGui
import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volume Viewer")
        self.resize(700, 500)
        self.setMinimumSize(400, 300)

        self.volume_data = VolumeData()
        self.viewer = SliceViewerWidget(self.volume_data)
        self.setCentralWidget(self.viewer)

        

class SliceViewerWidget(QtWidgets.QWidget):
    def __init__(self, volume_data):
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
        self.text = QtWidgets.QLabel("Orthogonal View",
                                     alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
        #self.original_pixmap = QtGui.QPixmap.fromImage(qimage)

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(1, 1)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.image_label, stretch=1)
        self.layout.addWidget(self.button_raw)
        self.layout.addWidget(self.button_vtk)
        self.layout.addWidget(self.axis_combo)
        self.layout.addWidget(self.slice_slider)

        self.button_raw.clicked.connect(self.import_volume_raw)
        self.button_vtk.clicked.connect(self.import_volume_vtk)

    def import_volume_raw(self):
        print("Importing .raw volume...")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open RAW Volume", "", "RAW Files (*.raw)")
        if not file_path:
            print("No file selected.")
            return
        sx, ok = QtWidgets.QInputDialog.getInt(self, "RAW Dimensions", "Size X:", 256, 1)
        if not ok:
            return
        sy, ok = QtWidgets.QInputDialog.getInt(self, "RAW Dimensions", "Size Y:", 256, 1)
        if not ok:
            return
        sz, ok = QtWidgets.QInputDialog.getInt(self, "RAW Dimensions", "Size Z:", 256, 1)
        if not ok:
            return

        dtype, ok = QtWidgets.QInputDialog.getItem(
            self,
            "RAW Data Type",
            "Select dtype:",
            ["uint8", "uint16", "float32"],
            0,
            False,
        )
        if not ok:
            return
        self.volume_data.load_raw(file_path)
        self.set_axis(self.axis_combo.currentText())
                
    def import_volume_vtk(self):
        print("Importing .vti volume...")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open VTI Volume",
                                                             "", "VTI Files (*.vti)")
        if not file_path:
            print("No file selected.")
            return

        self.volume_data.load_vti(file_path)
        self.set_axis(self.axis_combo.currentText())
        
    def set_axis(self, axis):
        print(f"Axis changed to: {axis}")
        self.current_axis = axis

        if self.volume_data.array is None:
            return
                
        max_slice = VolumeData.get_max_slice_for_axis(self.volume_data.array, axis)
        self.slice_slider.setRange(0, max_slice)

        middle_index = max_slice // 2
        self.slice_slider.setValue(middle_index)
        self.update_slice(middle_index)

    def update_slice(self, index):
        print(f"Slice changed to: {index}")
        self.current_slice = index

        if self.volume_data.array is None:
            print("No volume data available.")
            return

        slice_2d = VolumeData.get_slice(self.volume_data.array, self.current_axis, index)

        image = VolumeData.normalize_to_uint8(slice_2d)
        image = numpy.ascontiguousarray(image)

        height, width = image.shape
        bytes_per_line = image.strides[0]

        q_image = QtGui.QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QtGui.QImage.Format.Format_Grayscale8,
        ).copy()

        self.current_qimage = q_image
        self.refresh_pixmap()
        
        # At this point, slice_2d contains the 2D slice of the volume data
        print(f"Extracted 2D slice shape: {slice_2d.shape}")

    def refresh_pixmap(self):
        if self.current_qimage is None:
            return

        pixmap = QtGui.QPixmap.fromImage(self.current_qimage)
        scaled = pixmap.scaled(
            self.image_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_pixmap()
        

class VolumeData:
    def __init__(self):
        self.array = None
        self.spacing = None
        self.origin = None
        self.dimensions = None
        self.format = None
        self._sx = None
        self._sy = None
        self._sz = None
        self._status = None

    # Two separate loading functions, one for .raw files and one for .vti files (VTK)
    def load_raw(self, file_path) -> None:
        path = file_path.strip()
        if not path:
            self._status.showMessage("Enter a file path.")
            return
        p = Path(path)
        if not p.exists():
            self._status.showMessage(f"File does not exist: {p}")
            return
        shape = (self._sx.value(), self._sy.value(), self._sz.value())
        dtype = numpy.dtype(self._dtype.currentText())
        try:
            self.array = numpy.memmap(str(p), dtype=dtype, mode="r", shape=shape)
        except Exception as exc:
            self._status.showMessage(f"Failed to load volume: {exc}")
            return


    def load_vti(self, file_path) -> None:
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

        x_size = self.dimensions[0]
        y_size = self.dimensions[1]
        z_size = self.dimensions[2]

        self.array = flat_array.reshape((z_size, y_size, x_size))

        return self.array

    @staticmethod
    def get_slice(volume, axis, index):
        if axis == "Axial":
            return volume[index, :, :]
        if axis == "Coronal":
            return volume[:, index, :]
        if axis == "Sagittal":
            return volume[:, :, index]
        raise ValueError(f"Unknown axis: {axis}")

    @staticmethod
    def get_max_slice_for_axis(volume, axis):
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


    def get_middle_slice_for_axis(volume, axis):
        max_index = VolumeData.get_max_slice_for_axis(volume, axis)
        return max_index // 2
    

    def normalize_to_uint8(slice_2d):
        min_val = slice_2d.min()
        max_val = slice_2d.max()

        if max_val == min_val:
            return numpy.absolute(numpy.zeros_like(slice_2d, dtype=numpy.uint8))

        normalized = (slice_2d - min_val) / (max_val - min_val)
        image_8bit = normalized * 255

        return image_8bit.astype(numpy.uint8)
    

    def normalize_to_uint16(slice_2d):
        min_val = slice_2d.min()
        max_val = slice_2d.max()
    
        if max_val == min_val:
            return numpy.zeros_like(slice_2d, dtype=numpy.int16)
    
        normalized = (slice_2d - min_val) / (max_val - min_val)
        image_16bit = normalized * 32767
    
        return image_16bit.astype(numpy.int16)
    

    def normalize_to_float32(slice_2d):
        min_val = slice_2d.min()
        max_val = slice_2d.max()

        if max_val == min_val:
            return numpy.zeros_like(slice_2d, dtype=numpy.float32)

        image_32bit = (slice_2d - min_val) / (max_val - min_val)

        return image_32bit.astype(numpy.float32)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())