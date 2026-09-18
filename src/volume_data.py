import numpy
import vtk
from pathlib import Path
from vtkmodules.util import numpy_support
vtk_to_numpy = numpy_support.vtk_to_numpy

class VolumeData:
    def __init__(self):
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
        
        self._sx = self.dimensions[0]
        self._sy = self.dimensions[1]
        self._sz = self.dimensions[2]
        
        if flat_array.size != self._sx * self._sy * self._sz:
            raise ValueError("VTI file dimensions do not match the expected size.")
        self.array = flat_array.reshape((self._sz, self._sy, self._sx))
        self.spacing = (1.0, 1.0, 1.0)
    
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

    @staticmethod
    def get_middle_slice_for_axis(volume, axis):
        max_index = VolumeData.get_max_slice_for_axis(volume, axis)
        return max_index // 2


    @staticmethod
    def normalize_to_uint8(slice_2d):
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

    def change_voxel_size(self, new_voxel_size):
        self.spacing = new_voxel_size