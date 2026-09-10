import sys
import random
import vtk
from zipfile import Path
import numpy

from PySide6 import QtCore, QtWidgets, QtGui

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec())

class VolumeData:
    def __init__(self):
        self.array = None
        self.spacing = None
        self.origin = None
        self.dimensions = None
        self._sx = None
        self._sy = None
        self._sz = None

    def load_raw(self) -> None:
        path = self._path_edit.text().strip()
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
        reader = vtk.vtkXMLImageDataReader
        reader.SetFileName(file_path)
        reader.Update()

        image_data = reader.getOutput()

        self.dimensions = image_data.GetDimensions()
        self.spacing = image_data.GetSpacing()
        self.origin = image_data.GetOrigin()