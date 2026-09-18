import numpy
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui

from volume_data import VolumeData

class SliceViewerWidget(QtWidgets.QDockWidget):
    slice_ready = QtCore.Signal(QtGui.QImage, str)

    def __init__(self, volume_data):
        super().__init__()
        self.current_qimage = None
        self.current_slice = None
        self.volume_data = volume_data
        self.current_axis = "Axial"
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.widget = QtWidgets.QWidget()
        self.setWidget(self.widget)
        self.layout = QtWidgets.QVBoxLayout(self.widget)

        self.slice_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slice_slider.valueChanged.connect(self.update_slice)
        self.slice_slider.valueChanged.connect(self.update_slice_label)

        self.axis_combo = QtWidgets.QComboBox()
        self.axis_combo.addItems(["Axial", "Coronal", "Sagittal"])
        self.axis_combo.currentTextChanged.connect(self.set_axis)

        self.button_raw = QtWidgets.QPushButton("Import Volume (raw)")
        self.button_vtk = QtWidgets.QPushButton("Import Volume (vtk)")
        self.button_rng = QtWidgets.QPushButton("Generate Mock Volume")
        self.voxel_size_x = QtWidgets.QDoubleSpinBox()
        self.voxel_size_y = QtWidgets.QDoubleSpinBox()
        self.voxel_size_z = QtWidgets.QDoubleSpinBox()
        for box in [self.voxel_size_x, self.voxel_size_y, self.voxel_size_z]:
            box.setRange(0.00001, 5.0)
            box.setDecimals(5)
            box.setSingleStep(0.00001)
            box.setValue(1.0)

        self.text_voxel_dimensions = []

        for axis in ["X", "Y", "Z"]:
            label = QtWidgets.QLabel(
                f"Axis: {axis}",
                alignment=QtCore.Qt.AlignmentFlag.AlignTop
            )
            self.text_voxel_dimensions.append(label)

        self.text_slider = QtWidgets.QLabel(
            "0",
            alignment=QtCore.Qt.AlignmentFlag.AlignTop
        )

        self.import_group = QtWidgets.QGroupBox("Import/Generate Volume")
        self.import_layout = QtWidgets.QVBoxLayout(self.import_group)
        self.import_layout.addWidget(self.button_raw)
        self.import_layout.addWidget(self.button_vtk)
        self.import_layout.addWidget(self.button_rng)

        self.axis_group = QtWidgets.QGroupBox("Axis")
        self.axis_layout = QtWidgets.QVBoxLayout(self.axis_group)
        self.axis_layout.addWidget(self.axis_combo)

        self.slider_group = QtWidgets.QGroupBox("Slice")
        self.slider_layout = QtWidgets.QVBoxLayout(self.slider_group)
        self.slider_layout.addWidget(self.text_slider)
        self.slider_layout.addWidget(self.slice_slider)

        self.voxel_group = QtWidgets.QGroupBox("Voxel Size")
        self.voxel_layout = QtWidgets.QVBoxLayout(self.voxel_group)

        voxel_boxes = [self.voxel_size_x, self.voxel_size_y, self.voxel_size_z]
        for label, box in zip(self.text_voxel_dimensions, voxel_boxes):
            self.voxel_layout.addWidget(label)
            self.voxel_layout.addWidget(box)

        self.layout.addWidget(self.import_group)
        self.layout.addWidget(self.axis_group)
        self.layout.addWidget(self.slider_group)
        self.layout.addWidget(self.voxel_group)
        self.layout.addStretch(1)

        self.button_raw.clicked.connect(self.import_volume_raw)
        self.button_vtk.clicked.connect(self.import_volume_vtk)
        self.button_rng.clicked.connect(self.generate_mock_volume)
        self.voxel_size_x.valueChanged.connect(self.set_voxel_size)
        self.voxel_size_y.valueChanged.connect(self.set_voxel_size)
        self.voxel_size_z.valueChanged.connect(self.set_voxel_size)

    def update_slice_label(self, value):
        self.text_slider.setText(f"{value}")

    def import_volume_raw(self) -> None:
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
                            
    def import_volume_vtk(self) -> bool:
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
        
    def set_axis(self, axis) -> None:
        print(f"Axis changed to: {axis}")
        self.current_axis = axis

        if self.volume_data.array is None:
            return
                
        max_slice = VolumeData.get_max_slice_for_axis(self.volume_data.array, axis)
        self.slice_slider.setRange(0, max_slice)

        middle_index = max_slice // 2
        self.slice_slider.setValue(middle_index)
        self.update_slice(middle_index)

    def update_slice(self, index) -> None:
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

    def numpy_to_qimage(self, image) -> QtGui.QImage:
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

    def generate_mock_volume(self) -> None:
        self.volume_data._sx = 100
        self.volume_data._sy = 100
        self.volume_data._sz = 100
        self.volume_data._dtype = numpy.float32
        shape = (self.volume_data._sz, self.volume_data._sy, self.volume_data._sx)
        self.volume_data.array = numpy.zeros(shape, dtype=self.volume_data._dtype)
        self.volume_data.array[25:75, 25:75, 25:75] = 1

        self.set_axis(self.axis_combo.currentText())

    def set_voxel_size(self) -> None:
        new_size = (
            self.voxel_size_x.value(),
            self.voxel_size_y.value(),
            self.voxel_size_z.value()
        )
        
        self.volume_data.spacing = new_size
        if self.current_qimage is not None:
            self.slice_ready.emit(self.current_qimage, self.current_axis)