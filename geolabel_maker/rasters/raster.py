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
import json
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
import gdal2tiles
from pyproj.crs import CRS
from shapely.geometry import box
import geopandas as gpd
import matplotlib.pyplot as plt

# Geolabel Maker
from .sentinelhub import SentinelHubAPI
from .mapbox import MapBoxAPI
from .functions import generate_vrt, generate_tiles
from .utils import color_mask, merge_masks
from geolabel_maker.data import GeoData, GeoCollection, BoundingBox
from geolabel_maker.logger import logger


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


def _check_rasterio(element):
    r"""Check if the element is a ``rasterio.DatasetReader`` or ``rasterio.DatasetWriter``.

    Args:
        element (any): Element to check. 

    Raises:
        ValueError: If the element is not a ``DatasetReader`` or ``DatasetWriter``.

    Returns:
        bool: ``True`` if the element is in the correct type.

    Examples:
        >>> _check_rasterio("tile.tif")
            ValueError("Element of class 'str' is not a 'rasterio.DatasetReader'.")
        >>> _check_rasterio(Path("tile.tif"))
            ValueError("Element of class 'Path' is not a 'rasterio.DatasetReader'.")
        >>> _check_rasterio(rasterio.open("tile.tif"))
            True
    """
    if not isinstance(element, (rasterio.io.DatasetReader, rasterio.io.DatasetWriter)):
        ValueError(f"Element of class '{type(element).__name__}' is not a 'DatasetReader' or 'DatasetWriter'.")
    return True


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
        >>> _check_raster(Raster.open("raster.tif"))
            True
    """
    if not isinstance(element, Raster):
        raise ValueError(f"Element of class '{type(element).__name__}' is not a 'Raster'.")
    return True


class RasterBase(GeoData):
    pass


class Raster(GeoData):
    r"""Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    * :attr:`filename` (str): Name of the raster image.

    """

    def __init__(self, data, filename=None):
        _check_rasterio(data)
        if (filename and data) and Path(filename) != Path(data.name):
            raise ValueError(f"The provided filename does not correspond to the input data.")
        super().__init__(data, filename=filename)

    @property
    def crs(self):
        return CRS(self.data.crs)

    @property
    def bounds(self):
        return BoundingBox(*self.data.bounds)

    @classmethod
    def open(cls, filename):
        r"""Load the ``Raster`` from an image file. 
        The supported extensions are the one supported by `GDAL <https://gdal.org/drivers/raster/index.html>`__.

        Args:
            filename (str): The path to the image file.

        Returns:
            Category

        Examples:
            >>> raster = Raster.open("images/tile.tif")
        """
        with rasterio.open(filename) as data:
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
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            kwargs (dict): Remaining arguments from ``SentinelHubAPI.download()`` method.

        Returns:
            RasterCollection
        """
        api = SentinelHubAPI(username, password)
        files = api.download(bbox, **kwargs)
        return RasterCollection(files)

    @classmethod
    def from_array(cls, array, filename=None, **profile):
        r"""Create a ``Raster`` from a numpy array. 
        This method requires a profile (see `rasterio documentation <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__).

        .. note::
            The created raster will be stored in the memory cache.

        Args:
            array (numpy.ndarray): A 3 dimensional array, of shape :math:`(C, X, Y)`.
            profile (dict): Additional arguments required by `GDAL`.

        Returns:
            Raster
        """
        assert len(array.shape) >= 2, f"The provided array is not a matrix. Got a shape of {array.shape}."
        out_profile = {"driver": "GTiff", **profile}
        out_profile.update({
            "count": array.shape[-3] if len(array.shape) > 2 else 1,
            "height": array.shape[-2],
            "width": array.shape[-1],
            "dtype": str(array.dtype)
        })

        memfile = MemoryFile()
        out_data = memfile.open(**out_profile)
        out_data.write(array)
        return Raster(out_data, filename=filename)

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        r"""Load a raster image from a `PostgreSQL` database."""
        raise NotImplementedError

    def to_rasterio(self, **profile):
        """Convert the inner data in an **opened** rasterio dataset.

        Returns:
            rasterio.DatasetBase
        """
        out_profile = self.data.meta.copy()
        out_profile.update(**profile)
        if self.data.closed and isinstance(self.data, rasterio.DatasetReader):
            return rasterio.open(self.data.name, **out_profile)
        return self.data

    def save(self, out_file, window=None, **profile):
        r"""Save the raster to the disk.

        Args:
            out_file (str): Name of the file to be saved.
            window (rasterio.Window, optional): Output window. Defaults to ``None``.
            profile (dict): Profile parameters from ``rasterio``.

        Examples:
            >>> raster = Raster.open("tile.tif")
            >>> raster.save("tile2.tif")
        """
        out_profile = self.data.meta.copy()
        out_profile.update({**profile})
        with rasterio.open(str(out_file), "w", **out_profile) as dst:
            raster_data = self.to_rasterio()
            dst.write(raster_data.read(window=window))

    def rescale(self, factor, resampling="bilinear"):
        r"""Rescale the geo-referenced image. The result is the rescaled data and 
        the associated transformation.

        .. warning::
            This operation create a ``Raster`` in memory.

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
            >>> out_raster = raster.rescale(factor=2)
            >>> out_raster.data.shape
                (3, 512, 512)
        """
        raster_data = self.to_rasterio()
        out_count = raster_data.count
        out_height = int(raster_data.height * factor)
        out_width = int(raster_data.width * factor)
        out_shape = (out_count, out_height, out_width)
        out_data = raster_data.read(out_shape=out_shape, resampling=getattr(Resampling, resampling))
        out_transform = raster_data.transform * raster_data.transform.scale(
            (raster_data.width / out_data.shape[-1]),
            (raster_data.height / out_data.shape[-2])
        )
        out_profile = raster_data.profile.copy()
        out_profile.update({
            "count": out_count,
            "width": out_width,
            "height": out_height,
            "transform": out_transform
        })
        return self.from_array(out_data, **out_profile)

    def zoom(self, zoom, **kwargs):
        r"""Rescale the raster on a `zoom` level. 
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
        zoom = int(zoom)
        x_res, y_res = self.data.res
        x_factor = x_res / ZOOM2RES[zoom]
        y_factor = y_res / ZOOM2RES[zoom]
        factor = min(x_factor, y_factor)
        return self.rescale(factor, **kwargs)

    def to_crs(self, crs, **profile):
        r"""Project the raster from its initial `CRS` to another one.

        .. note::
            This method will create an in-memory raster.

        Args:
            crs (str, pyproj.crs.CRS): The destination `CRS`.

        Returns:
            Raster
        """
        raster_data = self.to_rasterio()
        transform, width, height = calculate_default_transform(
            raster_data.crs, crs, raster_data.width, raster_data.height, *raster_data.bounds
        )
        out_profile = raster_data.profile.copy()
        out_profile.update({
            "crs": crs,
            "transform": transform,
            "width": width,
            "height": height,
            **profile
        })

        memfile = MemoryFile()
        out_data = memfile.open(**out_profile)

        for i in range(1, raster_data.count + 1):
            reproject(
                source=rasterio.band(raster_data, i),
                destination=rasterio.band(out_data, i),
                src_transform=raster_data.transform,
                src_crs=raster_data.crs,
                dst_transform=transform,
                dst_crs=crs
            )

        return Raster(out_data)

    def crop(self, bbox):
        r"""Crop a raster from a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the raster extent.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            Raster
        """
        # Open the dataset if its closed
        raster_data = self.to_rasterio()
        
        # Format the bounding box in a format understood by rasterio
        df_bounds = gpd.GeoDataFrame({"geometry": box(*bbox)}, index=[0], crs=raster_data.crs)
        shape = json.loads(df_bounds.to_json())["features"][0]["geometry"]
        
        # Crop the raster
        out_array, out_transform = rasterio.mask.mask(raster_data, shapes=[shape], crop=True)
        out_profile = raster_data.profile.copy()
        out_profile.update({
            "height": out_array.shape[1],
            "width": out_array.shape[2],
            "transform": out_transform
        })

        return self.from_array(out_array, **out_profile)

    def mask(self, categories):
        """Mask the raster from a set of geometries.

        Args:
            categories (CategoryCollection): A list of categories, with distinct colors.

        Returns:
            Raster
        """
        masks = []
        out_transform = None
        bbox = self.bounds
        for category in categories:
            # Match the category to the raster extends
            category = category.to_crs(self.data.crs)
            category_cropped = category.crop(bbox)
            # If the category contains vectors in the cropped area
            if not category_cropped.data.empty:
                # Create a raster from the geometries
                mask, out_transform = rasterio.mask.mask(
                    self.to_rasterio(),
                    list(category_cropped.data.geometry),
                    crop=False
                )
                # Convert from (C, H, W) to (H, W, C)
                mask = mask.transpose(1, 2, 0)
                mask = color_mask(mask, category.color)
                masks.append(mask)

        # Merge masks into one image
        out_mask = merge_masks(masks)
        out_array = out_mask.transpose(2, 0, 1)
    
        out_profile = self.data.meta.copy()
        out_profile.update({
            "driver": "GTiff",
            "height": out_array.shape[1],  # numpy.array.shape[1] or PIL.Image.size[1],
            "width": out_array.shape[2],   # numpy.array.shape[2] or PIL.Image.size[0],
            "count": 3,
            "transform": out_transform,
            "photometric": "RGB",
        })

        return self.from_array(out_array, **out_profile)

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
        gdal2tiles.generate_tiles(self.filename, out_dir, **kwargs)

    def generate_mosaic(self, zoom=None, width=256, height=256, is_full=True, out_dir="mosaic"):
        r"""Generate a mosaic from the raster. 
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
            # Generate mosaics only for full sub image of shape (height, width)
            if is_full and (window.height != height or window.width != width):
                continue
            out_transform = rasterio.windows.transform(window, out_raster.data.transform)
            out_profile = out_raster.data.  meta.copy()
            out_profile.update({
                "driver": "GTiff",
                "height": window.height,
                "width": window.width,
                "transform": out_transform,
                "count": 3,
                "photometric": "RGB",
            })
            out_path = Path(out_dir) / f"{Path(self.filename).stem}-tile_{window.col_off}x{window.row_off}.tif"
            out_raster.save(out_path, window=window, **out_profile)
        return out_dir

    def plot(self, axes=None, figsize=None, **kwargs):
        r"""Plot a raster.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show the raster. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        raster_data = self.to_rasterio()
        array = raster_data.read().transpose(1, 2, 0)
        axes.imshow(array, **kwargs)
        return axes

    def inner_repr(self):
        return f"bounds={tuple(self.data.bounds)}"


class RasterCollection(GeoCollection):
    r"""
    Defines a collection of ``Raster``.
    This class behaves similarly as a ``list``, excepts it is made only of ``Raster``.

    """

    def __init__(self, *rasters):
        super().__init__(*rasters)

    @classmethod
    def open(cls, *filenames, **kwargs):
        rasters = []
        for filename in filenames:
            rasters.append(Raster.open(filename, **kwargs))
        return RasterCollection(*rasters)

    def save(self, out_dir):
        raise NotImplementedError

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

    def crop(self, bbox):
        """Crop all rasters from a bounding box.

        .. seealso::
            See ``Raster.crop()`` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.                

        Returns:
            RasterCollection
        """
        cropped = RasterCollection()
        for raster in self:
            try:
                cropped.append(raster.crop(bbox))
            except Exception as error:
                logger.error(f"Could not crop raster '{raster.filename}': {error}")
        return cropped

    #! It is not possible to create VRT from in memory Rasters.
    # TODO: Provide an alternative.
    def generate_vrt(self, out_file):
        """Builds a virtual raster from a list of rasters.

        Args:
            out_file (str): Name of the output virtual raster.

        Returns:
            str: Path to the VRT file.

        Examples:
            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_vrt("tiles.vrt")
        """
        raster_files = []
        for raster in self._items:
            if not raster.filename:
                raise ValueError("Could not access the raster from the disk. "
                                 "This error may be raised if the raster was loaded from a temporary file. "
                                 "You should save the rasters first before creating a virtual raster (use `.save()` method).")
            raster_files.append(str(raster.filename))
        out_file = generate_vrt(raster_files, str(out_file))
        return out_file

    def generate_mosaic(self, **kwargs):
        """Generate a mosaic from the rasters. 
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
            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_mosaic(width=256, height=256, out_dir="mosaic")
        """
        for raster in tqdm(self._items, desc="Generating Mosaics", leave=True, position=0):
            raster.generate_mosaic(**kwargs)

    def generate_tiles(self, out_dir="tiles", **kwargs):
        r"""Create tiles from rasters (using GDAL).

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        Args:
            out_dir (str, optional): Path to the directory where the tiles will be saved.

        Examples:
            >>> raster = Raster.open("raster.tif")
            >>> raster.generate_tiles(out_dir="tiles")
        """
        # Create a virtual raster of all the files
        rasters_vrt = self.generate_vrt(".raster-collection.vrt")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        generate_tiles(rasters_vrt, out_dir, **kwargs)
        # Remove the virtual raster
        Path(rasters_vrt).unlink()
