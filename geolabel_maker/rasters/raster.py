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
from itertools import product
from pathlib import Path
import rasterio
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
import gdal2tiles

# Geolabel Maker
from .sentinelhub import SentinelHubAPI


# Global variables
ZOOM2RES = {
    0: 156_412,
    1: 78_206,
    2: 39_103,
    3: 19_551,
    4: 9_776,
    5: 4_888,
    6: 2_444,
    7: 1_222,
    8: 610.984,
    9: 305.492,
    10: 152.746,
    11: 76.373,
    12: 38.187,
    13: 19.093,
    14: 9.547,
    15: 4.773,
    16: 2.387,
    17: 1.193,
    18: 0.596,
    19: 0.298,
    20: 0.149
}


__all__ = [
    "to_raster",
    "Raster",
    "RasterCollection"
]


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
    if isinstance(element, (str, Path)):
        return Raster.open(str(element), *args, **kwargs)
    elif isinstance(element, rasterio.io.DatasetReader):
        return Raster(element, *args, **kwargs)
    elif isinstance(element, Raster):
        return element
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Raster`.")


class Raster:
    r"""Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    """

    def __init__(self, data, filename=None):
        if not isinstance(data, (rasterio.io.DatasetReader, rasterio.io.DatasetWriter)):
            raise TypeError(f"Unknown type for the raster data.",
                            f"Got {type(data)} but expected `rasterio.io.DatasetReader`.",
                            f"Try opening the raster data with `Raster.open('path/to/raster.tif')` class method.")
        self.data = data
        self.filename = filename

    @classmethod
    def open(cls, filename):
        r"""Load the ``Raster`` from an image file. 
        The supported extensions are the one supported by `GDAL <https://gdal.org/drivers/raster/index.html>`__.

        Args:
            filename (str): The path to the image file.

        Returns:
            Category

        Examples:
            >>> from geolabel_maker.rasters import Raster
            >>> raster = Raster.open("images/tile.tif")
        """
        data = rasterio.open(filename)
        return Raster(data, filename=str(filename))

    @classmethod
    def download(cls, username, password, bbox, **kwargs):
        r"""Download a collection of rasters from a bounding box.
        This method relies on `SentinelHub` API.

        .. note::
            Depending on the bounding box, multiple rasters can be returned.

        Args:
            username (str): SciHub username.
            password (str): SciHub pasword.
            bbox (tuple): A bounding box in the format :math:`(lat_{min}, lon_{min}, lat_{max}, lon_{max})`.
            kwargs (dict): Remaining arguments from ``SentinelHubAPI.download()`` method.

        Returns:
            RasterCollection
        """
        api = SentinelHubAPI(username, password)
        files = api.download(bbox, **kwargs)
        return RasterCollection(files)

    @classmethod
    def from_array(cls, array, width=None, height=None, count=None, dtype=None, **profile):
        r"""Create a ``Raster`` from a numpy array. 
        This method requires a profile (see `rasterio documentation <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__).

        .. note::
            The created raster will be stored in the memory cache.

        Args:
            array (numpy.ndarray): A 3 dimensional array, of shape :math:`(C, X, Y)`.
            profile (dict): Additional arguments required.

        Returns:
            Raster  
        """
        if len(array.shape) == 2:
            width = width or array.shape[0]
            height = height or array.shape[1]
            count = count or 0
        elif len(array.shape) == 3:
            width = width or array.shape[0]
            height = height or array.shape[1]
            count = count or array.shape[2]
        dtype = dtype or str(array.dtype)
        memfile = MemoryFile()
        data = memfile.open(width=width, height=height, count=count, dtype=dtype, **profile)
        data.write(array)
        filename = data.name
        return Raster(data, filename)

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        r"""Load a raster image from a `PostgreSQL` database."""
        raise NotImplementedError

    def save(self, filename, window=None, **profile):
        """Save the raster to the disk.

        Args:
            filename (str): Name of the file to be saved.
        """
        with rasterio.open(filename, "w", **profile) as dst:
            dst.write(self.data.read(window=window))

    def numpy(self):
        """Convert the raster image to a numpy array, of shape :math:`(C, X, Y)`

        Returns:
            numpy.ndarray

        Examples:
            >>> raster = Raster.open("tile.tif")
            >>> array = raster.to_numpy()
        """
        return self.data.read()

    # TODO: rescale on X and Y with different values (?)
    def rescale(self, factor):
        """Rescale the geo-referenced image. The result is the rescaled data and 
        the associated transformation.

        Args:
            factor (float): Rescale factor.

        Returns:
            numpy.ndarray, rasterio.Transform

        Examples:
            >>> raster = Raster.open("tile.tif")
            >>> raster.data.shape
                (3, 256, 256)
            >>> out_data, out_transform = raster.rescale(factor=2)
            >>> out_data.shape
                (3, 512, 512)
        """
        out_count = self.data.count
        out_height = int(self.data.height * factor)
        out_width = int(self.data.width * factor)
        out_shape = (out_count, out_height, out_width)
        out_data = self.data.read(out_shape=out_shape, resampling=Resampling.bilinear)
        out_transform = self.data.transform * self.data.transform.scale(
            (self.data.width / self.data.shape[-1]),
            (self.data.height / self.data.shape[-2])
        )
        out_profile = self.data.profile.copy()
        out_profile.update({
            "count": out_count,
            "width": out_width,
            "height": out_height,
            "transform": out_transform
        })
        return self.from_array(out_data, **out_profile)

    def zoom(self, zoom):
        x_res, y_res = self.data.res
        factor = x_res / ZOOM2RES[zoom]
        return self.rescale(factor)

    def generate_tiles(self, out_dir="tiles", **kwargs):
        r"""Create tiles from a raster file (using GDAL)

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        Args:
            out_dir (str, optional): Path to the directory where the tiles will be saved.

        Examples:
            >>> raster = Raster.open("raster.tif")
            >>> raster.generate_tiles(out_dir="tiles")
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        # Generate tiles with `gdal2tiles`
        file_raster = self.data.name
        gdal2tiles.generate_tiles(file_raster, out_dir, **kwargs)

    def generate_mosaic(self, width=256, height=256, zoom=None, out_dir="mosaic"):
        """Generate a mosaic from the raster. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        Args:
            width (int, optional): The width of the window. Defaults to ``256``.
            height (int, optional): The height of the window. Defaults to ``256``.
            out_dir (str, optional): Path to the directory where the windows are saved. Defaults to ``"mosaic"``.

        Examples:
            >>> raster = Raster.open("raster.tif")
            >>> raster.generate_mosaic(width=256, height=256, out_dir="mosaic")
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_raster = self.data
        if zoom is not None:
            out_raster = self.zoom(zoom).data
        num_cols = out_raster.meta["width"]
        num_rows = out_raster.meta["height"]
        offsets = product(range(0, num_cols, width), range(0, num_rows, height))
        main_window = rasterio.windows.Window(col_off=0, row_off=0, width=num_cols, height=num_rows)
        for col_off, row_off in offsets:
            window = rasterio.windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(main_window)
            out_transform = rasterio.windows.transform(window, out_raster.transform)
            out_profile = {
                "driver": "GTiff",
                "height": window.height,
                "width": window.width,
                "transform": out_transform,
                "crs": out_raster.profile.get("crs", None),
                "count": 3,
                "photometric": "RGB",
                "dtype": out_raster.profile.get("dtype", None)
            }
            out_path = Path(out_dir) / f"{Path(self.filename).stem}-tile_{window.col_off}x{window.row_off}.tif"
            with rasterio.open(out_path, "w", **out_profile) as dst:
                dst.write(out_raster.read(window=window))
        return out_dir

    def __repr__(self):
        return f"Raster(name='{self.data.name}', bbox={tuple(self.data.bounds)}, crs={self.data.crs})"


class RasterCollection:
    r"""
    Defines a collection of ``Raster``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Raster``.

    * :attr:`items` (list): List of rasters.

    """

    def __init__(self, *rasters):
        if not isinstance(rasters, (list, tuple, RasterCollection)):
            rasters = [rasters]
        elif isinstance(rasters, (list, tuple)) and len(rasters) == 1:
            rasters = rasters[0]
        if not rasters:
            rasters = []
        self.items = [to_raster(raster) for raster in rasters]

    def append(self, raster):
        r"""Add a ``Raster`` to the collection.

        Args:
            raster (Raster): The raster to add.

        Examples:
            >>> collection = RasterCollection()
            >>> raster = Raster.open("tile.tif")
            >>> collection.append(raster)
            >>> collection
                RasterCollection(
                  (0): Raster(filename='tile.tif')
                )
        """
        raster = to_raster(raster)
        self.items.append(raster)

    def extend(self, rasters):
        r"""Add multiple ``Raster`` to the collection.

        Args:
            rasters (list): List of raster to add.

        Examples:
            >>> collection = RasterCollection()
            >>> rasters = [Raster.open("tile1.tif"), Raster.open("tile2.tif")]
            >>> collection.extend(rasters)
            >>> collection
                RasterCollection(
                  (0): Raster(filename='tile1.tif')
                  (1): Raster(filename='tile2.tif')
                )
        """
        rasters = [to_raster(raster) for raster in rasters]
        self.items.extend(rasters)

    def __setitem__(self, index, raster):
        raster = to_raster(raster)
        self.items[index] = raster

    def __getitem__(self, index):
        return self.items[index]

    def __iter__(self):
        yield from self.items

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        rep = f"{self.__class__.__name__}("
        for i, raster in enumerate(self):
            rep += f"\n  ({i}): {raster}"
        rep += "\n)"
        return rep
