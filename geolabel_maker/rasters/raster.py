# Encoding: UTF-8
# File: raster.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
This module handles georeferenced raster image (usually ``.tif`` image).

.. code-block:: python

    from geolabel_maker.rasters import Raster
    
    raster = Raster.open("tile.tif")

"""


# Basic imports
from pathlib import Path
import rasterio

# Geolabel Maker
from geolabel_maker.data import Data


def to_raster(element, *args, **kwargs):
    r"""Convert an object to a ``Raster``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``rasterio.DatasetReader`` etc...

    Returns:
        Raster

    Examples:
        >>> raster = to_raster("tile.tif")
        >>> raster = to_raster(Path("tile.tif"))
        >>> raster = to_raster(rasterio.open("tile.tif"))
    """
    if isinstance(element, str):
        return Raster.open(element, *args, **kwargs)
    elif isinstance(element, Path):
        return Raster.open(str(element), *args, **kwargs)
    elif isinstance(element, rasterio.io.DatasetReader):
        return Raster(element, *args, **kwargs)
    elif isinstance(element, Raster):
        return element
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Raster`.")


class Raster(Data):
    """Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    """

    def __init__(self, data):
        if not isinstance(data, rasterio.io.DatasetReader):
            raise TypeError(f"Unknown type for the raster data.",
                            f"Got {type(data)} but expected `rasterio.io.DatasetReader`.",
                            f"Try opening the raster data with `Raster.open('path/to/raster.tif')` class method.")
        super().__init__()
        self.data = data

    @classmethod
    def open(cls, filename):
        data = rasterio.open(filename)
        return Raster(data)

    @classmethod
    def download(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_psql(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_array(cls, array, *args, **kwargs):
        raise NotImplementedError

    @property
    def filename(self):
        return self.data.name

    def save(self, outname):
        # To fasten the process and reduces memory usage,
        # we write the image by sub-windows (usually 256x256 windows)
        array = self.data.read()
        with rasterio.open(outname, 'w', **self.data.profile) as dst:
            for ji, window in self.data.block_windows(1):
                array_window = array[:, window.row_off:window.row_off + window.height, window.col_off:window.col_off + window.width]
                dst.write(array_window.astype("uint8"), window=window)

    def numpy(self):
        return self.data.read()

    def to_gdal(self):
        raise NotImplementedError

    def generate_tiles(self, zoom_min=12, zoom_max=12):
        raise NotImplementedError

    def show(self):
        raise NotImplementedError

    def inner_repr(self):
        return f"filename='{Path(self.filename).name}', bbox={tuple(self.data.bounds)}, crs={self.data.crs}"
