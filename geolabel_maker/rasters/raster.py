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
from tqdm import tqdm
from itertools import product
from pathlib import Path
import rasterio
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
import gdal2tiles

# Geolabel Maker
from .sentinelhub import SentinelHubAPI
from geolabel_maker.data import Data, DataCollection


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
    "Raster",
    "RasterCollection"
]


def to_rasterio(element, **kwargs):
    r"""Convert an object to a ``Raster``.

    Args:
        element (any): Element to convert. 
            It can be a ``str``, ``Path``, ``rasterio.DatasetReader`` etc...

    Returns:
        Raster

    Examples:
        >>> raster = to_rasterio("tile.tif")
        >>> raster = to_rasterio(Path("tile.tif"))
        >>> raster = to_rasterio(rasterio.open("tile.tif"))
    """
    if isinstance(element, (str, Path)):
        return rasterio.open(str(element), **kwargs)
    elif isinstance(element, (rasterio.io.DatasetReader, rasterio.io.DatasetWriter)):
        return element
    elif isinstance(element, Raster):
        return element.data
    raise ValueError(f"Unknown element: Cannot convert {type(element)} to `Raster`.")


def _check_raster(element):
    r"""Check if an object is a ``Raster``.

    Args:
        element (any): Element to verify. 

    Raises:
        ValueError: If the element is not a ``Raster``.

    Returns:
        bool: ``True`` if the element is a ``Raster``.

    Examples:
        >>> _check_raster("raster.tif")
            ValueError("Element of class 'str' is not a 'Raster'.")
        >>>  _check_raster(Raster.open("raster.tif"))
    """
    if not isinstance(element, Raster):
        raise ValueError(f"Element of class '{type(element).__name__}' is not a 'Raster'.")
    return True


class Raster(Data):
    r"""Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    """

    def __init__(self, data, filename=None):
        data = to_rasterio(data)
        super().__init__(data, filename=filename)

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
    def from_array(cls, array, **profile):
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
        assert len(array.shape) >= 2, f"The provided array is not a matrix. Got a shape of {array.shape}."
        out_profile = profile or {}
        out_profile.update({
            "count": array.shape[-3] if len(array.shape) > 2 else 1,
            "width": array.shape[-2],
            "height": array.shape[-1],
            "dtype": str(array.dtype)
        })
        memfile = MemoryFile()
        data = memfile.open(**out_profile)
        data.write(array)
        return Raster(data)

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        r"""Load a raster image from a `PostgreSQL` database."""
        raise NotImplementedError

    def save(self, out_file, window=None, **profile):
        """Save the raster to the disk.

        Args:
            out_file (str): Name of the file to be saved.
        """
        with rasterio.open(str(out_file), "w", **profile) as dst:
            dst.write(self.data.read(window=window))

    def rescale(self, factor, resampling="bilinear"):
        """Rescale the geo-referenced image. The result is the rescaled data and 
        the associated transformation.

        .. warning::
            This operation will return a ``Raster`` with no filename.

        Args:
            factor (float): Rescale factor.
            resampling (str, optional): Resempling method.  
                Options available are from ``rasterio.enums.Resampling``. Default to ``"bilinear"``.

        Returns:
            Raster

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
        out_data = self.data.read(out_shape=out_shape, resampling=getattr(Resampling, resampling))
        out_transform = self.data.transform * self.data.transform.scale(
            (self.data.width / out_data.shape[-1]),
            (self.data.height / out_data.shape[-2])
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
        """Rescale the raster on a `zoom` level. 
        The levels used are from `Open Street Map <https://wiki.openstreetmap.org/wiki/Zoom_levels>`__.

        .. seealso::
            This operation is a variant of ``geolabel_maker.rasters.Raster.rescale`` method.

        .. warning::
            This operation will return a ``Raster`` with no filename.

        Args:
            zoom (int): The zoom level.

        Returns:
            Raster

        Examples:
            >>> raster = Raster.open("tile.tif")
            >>> raster = raster.zoom(18)
            >>> raster.filename
                None
        """
        x_res, y_res = self.data.res
        x_factor = x_res / ZOOM2RES[zoom]
        y_factor = y_res / ZOOM2RES[zoom]
        factor = min(x_factor, y_factor)
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
        gdal2tiles.generate_tiles(self.filename, out_dir, **kwargs)

    def generate_mosaic(self, zoom=None, width=256, height=256, out_dir="mosaic"):
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
        out_raster = self.zoom(zoom) if zoom else self
        num_cols = out_raster.data.meta["width"]
        num_rows = out_raster.data.meta["height"]
        offsets = product(range(0, num_cols, width), range(0, num_rows, height))
        main_window = rasterio.windows.Window(col_off=0, row_off=0, width=num_cols, height=num_rows)
        for col_off, row_off in offsets:
            window = rasterio.windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(main_window)
            out_transform = rasterio.windows.transform(window, out_raster.data.transform)
            out_profile = {
                "driver": "GTiff",
                "height": window.height,
                "width": window.width,
                "transform": out_transform,
                "crs": out_raster.data.profile.get("crs", None),
                "count": 3,
                "photometric": "RGB",
                "dtype": out_raster.data.profile.get("dtype", None)
            }
            out_path = Path(out_dir) / f"{Path(self.filename).stem}-tile_{window.col_off}x{window.row_off}.tif"
            out_raster.save(out_path, window=window, **out_profile)
        return out_dir

    def inner_repr(self):
        return f"name='{self.filename or 'None'}', bbox={tuple(self.data.bounds)}, crs={self.data.crs}"


class RasterCollection(DataCollection):
    r"""
    Defines a collection of ``Raster``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Raster``.

    * :attr:`items` (list): List of rasters.

    """

    def __init__(self, *rasters):
        super().__init__(*rasters)

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
        _check_raster(raster)
        self._items.append(raster)

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
        self._items.extend(rasters)

    def insert(self, index, raster):
        """Insert a ``Raster`` at a specific index.

        Args:
            index (int): Index.
            raster (Raster): Raster to insert.
        """
        _check_raster(raster)
        self._items[index] = raster
