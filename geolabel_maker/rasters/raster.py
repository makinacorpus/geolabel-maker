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

    # Basic imports
    import rasterio
    from geolabel_maker.rasters import Raster
    
    # 1. Open a raster
    raster = Raster.open("tile.tif")
    
    # 1.1. Open a raster with rasterio
    with rasterio.open("tile.tif") as raster_data:
        raster = Raster(raster_data)
    
    # 2. Change its coordinate reference system (CRS)
    out_raster = raster.to_crs("EPSG:4326")
    
    # 3. Crop the raster
    out_raster = raster.crop((43, 2, 44, 3))
    
    # 4. Generate mosaics
    raster.generate_mosaics()
    
    # 5.  Generate tiles
    raster.generate_tiles()
"""


# Basic imports
from abc import abstractmethod
from tqdm import tqdm
import warnings
from itertools import product
from pathlib import Path
import json
import rasterio
import rasterio.mask
import rasterio.plot
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
import gdal2tiles
from shapely.geometry import box
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Geolabel Maker
from .functions import generate_vrt, generate_tiles
from .utils import color_mask, merge_masks
from geolabel_maker.base import GeoBase, GeoData, GeoCollection, BoundingBox, CRS
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
    r"""Checks if the element is a :class:`rasterio.DatasetReader` or :class:`rasterio.DatasetWriter`.

    Args:
        element (any): Element to check. 

    Examples:
        >>> _check_rasterio("tile.tif")
            ValueError("Element of class 'str' is not a 'rasterio.DatasetReader'.")
    """
    if not isinstance(element, (rasterio.io.DatasetReader, rasterio.io.DatasetWriter)):
        ValueError(f"Element of class '{type(element).__name__}' is not a 'DatasetReader' or 'DatasetWriter'.")


class RasterBase(GeoBase):
    r"""
    Abstract architecture used to wrap all raster elements.

    """

    @abstractmethod
    def rescale(self, factor, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def zoom(self, zoom, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def mask(self, categories, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def generate_tiles(self, out_dir="tiles", **kwargs):
        raise NotImplementedError

    @abstractmethod
    def generate_mosaics(self, zoom=None, width=256, height=256, 
                         col_off=0, row_off=0,
                         is_full=True, out_dir="mosaics", **kwargs):
        raise NotImplementedError


class Raster(GeoData, RasterBase):
    r"""
    A raster is a georeferenced image. This class encapsulates :mod:`rasterio.DatasetReader` object,
    and defines custom processing methods to work with a :class:`~geolabel_maker.Dataset`.

    * :attr:`data` (rasterio.io.DatasetReader): The raster data corresponding to a georeferenced image.

    * :attr:`filename` (str): Name of the raster image.

    * :attr:`crs` (CRS): Coordinate reference system.
    
    * :attr:`bounds` (BoundingBox): Bounding box of the geographic extent.

    """

    def __init__(self, data, filename=None):
        _check_rasterio(data)
        GeoData.__init__(self, data, filename=filename)

    @property
    def crs(self):
        return CRS.from_rasterio(self.data.crs)

    @property
    def bounds(self):
        return BoundingBox(*self.data.bounds)

    @classmethod
    def open(cls, filename):
        r"""Load the ``Raster`` from an image file. 
        The supported extensions are the one supported by `GDAL <https://gdal.org/drivers/raster/index.html>`__.
        This method relies on :func:`rasterio.open` function.

        Args:
            filename (str): The path to the image file.

        Returns:
            Raster: The loaded raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, load it with:

            >>> raster = Raster.open("tile.tif")

            Check if the raster is successfully loaded:

            >>> raster
                Raster(filename='tile.tif')
        """
        with rasterio.open(filename) as data:
            return Raster(data, filename=str(filename))

    @classmethod
    def from_array(cls, array, **profile):
        r"""Creates a ``Raster`` from a numpy array. 
        This method requires a profile (see `rasterio documentation <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__).

        .. note::
            The created raster will be stored in the cache memory.

        Args:
            array (numpy.array): A 3 dimensional array, of shape :math:`(C, Height, Width)`.
            profile (dict): Profile parameters from `rasterio profiles <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__.

        Returns:
            Raster

        Examples:
            To create an in-memory raster, you can first create an array (i.e. the rasters' pixels)
            and then defines its CRS and transformation.

            >>> import numpy as np
            >>> from rasterio.coords import CRS
            >>> from rasterio.transform import Affine
            >>> raster_array = np.zeros((3, 256, 256))
            >>> crs = CRS.from_epsg(3946)
            >>> transform = Affine(0.08, 0.0, 1843040.96, 0.0, -0.08, 5173610.88)

            Once you defined your parameters, create a raster with:

            >>> raster = Raster.from_array(array, crs=crs, transform=transform)
            >>> raster
                Raster(bounds=(1843040.96, 5173590.399999999, 1843061.44, 5173610.88), crs=EPSG:3946)

            Notice that the created raster does not have a ``filename``: it means the raster is
            stored in the memory.
        """
        assert len(array.shape) >= 2, f"The provided array is not a matrix. Got a shape of {array.shape}."

        out_profile = {"driver": "GTiff", **profile}
        out_profile.update({
            "count": array.shape[-3] if len(array.shape) > 2 else 1,
            "height": array.shape[-2],
            "width": array.shape[-1],
            "dtype": str(array.dtype)
        })
        with MemoryFile() as memfile:
            out_data = memfile.open(**out_profile)
            out_data.write(array)

        return Raster(out_data)

    @classmethod
    def from_postgis(cls, *args, **kwargs):
        r"""Loads a raster image from a `PostgreSQL` database."""
        raise NotImplementedError

    def rasterio(self, **profile):
        """Converts the inner data in an **opened** rasterio dataset.

        Args:
            profile (dict): Profile parameters from `rasterio profiles <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__.

        Returns:
            rasterio.DatasetBase

        Examples:
            If ``tile.tif`` is a raster available from the disk, open it with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.data
                <closed DatasetReader name='tile.tif' mode='r'>

            Notice that the dataset reader is closed. That means the data itself is not loaded,
            and can not be loaded. 
            To load it, simply use the ``rasterio`` method to open the dataset:

            >>> raster_data = raster.rasterio()
            >>> raster_data
                <open DatasetReader name='tile.tif' mode='r'>

            You can now extract data with ``rasterio`` API.
        """
        out_profile = self.data.meta.copy()
        out_profile.update(**profile)
        if self.data.closed and isinstance(self.data, rasterio.DatasetReader):
            return rasterio.open(self.data.name, **out_profile)
        return self.data

    def save(self, out_file, window=None, **profile):
        r"""Saves the raster to the disk.

        Args:
            out_file (str): Name of the file to be saved.
            window (rasterio.Window, optional): Output window. Defaults to ``None``.
            profile (dict): Profile parameters from `rasterio profiles <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__.

        Returns:
            str: Path to the saved raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can save it to another location with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.save("tile2.tif")

            Note that this method also works for in-memory rasters.
        """
        out_profile = self.data.meta.copy()
        out_profile.update({**profile})

        with rasterio.open(str(out_file), "w", **out_profile) as dst:
            raster_data = self.rasterio()
            dst.write(raster_data.read(window=window))

        return str(out_file)

    def overwrite(self, raster, **profile):
        r"""Overwrites the current raster with the a new one. 

        .. note::
            This operation will not modify the values in place,
            but will overwrite the raster saved on the disk.

        Args:
            raster (Raster): Raster to save.
            profile (dict): Profile parameters from `rasterio profiles <https://rasterio.readthedocs.io/en/latest/topics/profiles.html>`__.

        Raises:
            RuntimeError: If the current raster does not have a filename or was generated from a ``rasterio.io.DatasetWriter``,
                this error will be raised as it is impossible to overwrite on the disk a raster loaded only in-memory.

        Returns:
            Raster: The saved raster.
        """
        if self.filename is None or isinstance(self.data, rasterio.io.DatasetWriter):
            raise RuntimeError(f"Could not overwrite a raster that does not have a filename or "
                               "was generated from a DatasetWriter.")

        raster.save(self.filename, **profile)
        return Raster.open(self.filename)

    def to_crs(self, crs, overwrite=False):
        r"""Projects the raster from its initial coordinate reference system (CRS) to another one.

        .. note::
            By default, this method will create an in-memory raster.
            To automatically save it, use ``overwrite`` argument.

        Args:
            crs (str, pyproj.crs.CRS): The destination CRS.
            overwrite (bool, optional): If ``True``, overwrites the initial raster saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Raster: The projected raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can project it in a different CRS with:

            >>> raster = Raster.open("tile.tif")
            >>> crs = "EPSG:4326"
            >>> out_raster = raster.to_crs(crs)
            
            The output raster is loaded in-memory:

            >>> out_raster.filename
                None
            
            To automatically replace the ``tile.tif`` with the output raster,
            use the ``overwrite`` argument:
            
            >>> out_raster = raster.to_crs(crs, overwrite=True)
            >>> out_raster.filename
                'tile.tif'
        """
        raster_data = self.rasterio()
        transform, width, height = calculate_default_transform(
            raster_data.crs, crs, raster_data.width, raster_data.height, *raster_data.bounds
        )
        out_meta = raster_data.meta.copy()
        out_meta.update({
            "crs": crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        memfile = MemoryFile()
        out_data = memfile.open(**out_meta)

        for i in range(1, raster_data.count + 1):
            reproject(
                source=rasterio.band(raster_data, i),
                destination=rasterio.band(out_data, i),
                src_transform=raster_data.transform,
                src_crs=raster_data.crs,
                dst_transform=transform,
                dst_crs=crs
            )

        raster = Raster(out_data)

        # Write to the disk if overwrite
        if overwrite:
            out_profile = raster_data.profile.copy()
            out_profile.update(**out_meta)
            raster_data.close()
            return self.overwrite(raster, **out_profile)

        return raster

    def crop(self, bbox, overwrite=False):
        r"""Crops a raster in box extent.

        .. note::
            By default, this method will create an in-memory raster.
            To automatically save it, use ``overwrite`` argument.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the raster.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial raster saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.
            
        Returns:
            Raster: The cropped raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, crop it with:

            >>> raster = Raster.open("tile.tif")
            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> out_raster = raster.crop(bbox)
            
            The output raster is loaded in-memory:

            >>> out_raster.filename
                None
            
            To automatically replace the ``tile.tif`` with the output raster,
            use the ``overwrite`` argument:
            
            >>> out_raster = raster.crop(bbox, overwrite=True)
            >>> out_raster.filename
                'tile.tif'
        """
        # Open the dataset if its closed
        raster_data = self.rasterio()

        # Format the bounding box in a format understood by rasterio
        df_bounds = gpd.GeoDataFrame({"geometry": box(*bbox)}, index=[0], crs=raster_data.crs)
        shape = json.loads(df_bounds.to_json())["features"][0]["geometry"]

        # Crop the raster
        out_array, out_transform = rasterio.mask.mask(raster_data, shapes=[shape], crop=True)
        out_meta = raster_data.meta.copy()
        out_meta.update({
            "height": out_array.shape[1],
            "width": out_array.shape[2],
            "transform": out_transform
        })
        raster = self.from_array(out_array, **out_meta)
        
        # Write to the disk if overwrite
        if overwrite:
            out_profile = raster_data.profile.copy()
            out_profile.update(**out_meta)
            raster_data.close()
            return self.overwrite(raster, **out_profile)

        return raster

    def rescale(self, factor, resampling="bilinear", overwrite=False):
        r"""Rescales the geo-referenced image.

        .. note::
            By default, this method will create an in-memory raster.
            To automatically save it, use ``overwrite`` argument.

        Args:
            factor (float): Rescale factor.
            resampling (str, optional): Resempling method.  
                Options available are from ``rasterio.enums.Resampling``. Defaults to ``"bilinear"``.
            overwrite (bool, optional): If ``True``, overwrites the initial raster saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.
                
        Returns:
            Raster: The rescaled raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can rescale it by a given factor with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.data.shape
                (3, 256, 256)
            >>> out_raster = raster.rescale(factor)
            >>> out_raster.data.shape
                (3, 512, 512)
            
            The output raster is loaded in-memory:

            >>> out_raster.filename
                None
            
            To automatically replace the ``tile.tif`` with the output raster,
            use the ``overwrite`` argument:
            
            >>> out_raster = raster.rescale(factor, overwrite=True)
            >>> out_raster.filename
                'tile.tif'
        """
        raster_data = self.rasterio()
        out_count = raster_data.count
        out_height = int(raster_data.height * factor)
        out_width = int(raster_data.width * factor)
        out_shape = (out_count, out_height, out_width)
        out_data = raster_data.read(out_shape=out_shape, resampling=getattr(Resampling, resampling))
        out_transform = raster_data.transform * raster_data.transform.scale(
            (raster_data.width / out_data.shape[-1]),
            (raster_data.height / out_data.shape[-2])
        )
        out_meta = raster_data.meta.copy()
        out_meta.update({
            "count": out_count,
            "width": out_width,
            "height": out_height,
            "transform": out_transform
        })
        raster = self.from_array(out_data, **out_meta)

        # Write to the disk if overwrite
        if overwrite:
            out_profile = raster_data.profile.copy()
            out_profile.update(**out_meta)
            raster_data.close()
            return self.overwrite(raster, **out_profile)

        return raster

    def zoom(self, zoom, overwrite=False, **kwargs):
        r"""Zooms the raster on a `zoom` level. 
        The levels used are from `Open Street Map <https://wiki.openstreetmap.org/wiki/Zoom_levels>`__.

        .. note::
            By default, this method will create an in-memory raster.
            To automatically save it, use ``overwrite`` argument.

        Args:
            zoom (int): The zoom level.
            overwrite (bool, optional): If ``True``, overwrites the initial raster saved on disk with the output. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.
            kwargs (dict): Remaining arguments from :func:`~geolabel_maker.rasters.raster.Raster.rescale` method.

        Returns:
            Raster: The zoomed raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can change its "zoom" level with:

            >>> raster = Raster.open("tile.tif")
            >>> zoom_level = 18
            >>> out_raster = raster.zoom(zoom_level)

            The output raster is loaded in-memory:

            >>> out_raster.filename
                None
                
            To automatically replace the ``tile.tif`` with the output raster,
            use the ``overwrite`` argument:
            
            >>> out_raster = raster.zoom(zoom_level, overwrite=True)
            >>> out_raster.filename
                'tile.tif'
        """
        zoom = int(zoom)
        x_res, y_res = self.data.res
        x_factor = x_res / ZOOM2RES[zoom]
        y_factor = y_res / ZOOM2RES[zoom]
        factor = min(x_factor, y_factor)
        return self.rescale(factor, overwrite=overwrite, **kwargs)

    def mask(self, categories):
        """Masks the raster from a set of geometries.

        .. note::
            This method creates an in-memory raster.

        Args:
            categories (CategoryCollection): A list of categories, with distinct colors.

        Returns:
            Raster: The label corresponding to the rasterized categories.

        Examples:
            If ``tile.tif`` is a raster and ``buildings.json``, ``vegetation.json`` are geometries
            available from the disk, generate masks (or labels) with:

            >>> raster = Raster.open("tile.tif")
            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> out_raster = raster.mask(categories)
        """
        masks = []
        out_transform = None
        bbox = self.bounds
        with self.rasterio() as raster_data:
            for category in categories:
                # Match the category to the raster extends
                if category.crs != self.crs:
                    category = category.to_crs(self.crs)
                    error_msg = f"The provided category '{category.name}' has a different CRS than the raster. " \
                                f"Please project all your elements in the same CRS for better performance."
                    warnings.warn(error_msg, RuntimeWarning)
                    logger.warning(error_msg)

                category_cropped = category.crop(bbox)
                # If the category contains vectors in the cropped area
                if not category_cropped.data.empty:
                    # Create a raster from the geometries
                    mask, out_transform = rasterio.mask.mask(
                        raster_data,
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
        r"""Creates tiles from a raster file (using GDAL).

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        Args:
            out_dir (str, optional): Path to the directory where the tiles will be saved.

        Returns:
            str: Path to the output directory.

        Examples:
            If ``tile.tif`` is a raster available from the disk, generate tiles with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.generate_tiles(out_dir="tiles")
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        gdal2tiles.generate_tiles(self.filename, out_dir, **kwargs)
        return str(out_dir)

    def generate_mosaics(self, zoom=None, width=256, height=256, 
                         col_off=0, row_off=0,
                         is_full=True, out_dir="mosaics", **kwargs):
        r"""Generates a mosaic from the raster. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        Args:
            width (int, optional): The width of the window. Defaults to ``256``.
            height (int, optional): The height of the window. Defaults to ``256``.
            col_off (int, optional): Column offset for the mosaics.
            row_off (int, optional): Row offset for the mosaics.
            is_full (bool, optional): If ``True``, will only generate mosaics with dimension :math:`(width, height)`.
                Defaults to ``True``.
            out_dir (str, optional): Path to the directory where the windows are saved. Defaults to ``"mosaics"``.

        Returns:
            str: Path to the output directory.

        Examples:
            If ``tile.tif`` is a raster available from the disk, generate mosaics with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.generate_mosaics(width=256, height=256, out_dir="mosaic")
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_raster = self.zoom(zoom, **kwargs) if zoom else self
        num_cols = out_raster.data.meta["width"]
        num_rows = out_raster.data.meta["height"]
        offsets = product(range(col_off, num_cols, width), range(row_off, num_rows, height))
        main_window = rasterio.windows.Window(col_off=col_off, row_off=row_off, width=num_cols, height=num_rows)
        for col_off, row_off in offsets:
            window = rasterio.windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(main_window)
            # Generate mosaics only for full sub image of shape (height, width)
            if is_full and (window.height != height or window.width != width):
                continue
            out_transform = rasterio.windows.transform(window, out_raster.data.transform)
            out_profile = {
                "driver": "GTiff",
                "height": window.height,
                "width": window.width,
                "transform": out_transform,
                "count": 3
            }
            out_path = Path(out_dir) / f"{Path(self.filename).stem}-tile_{window.row_off}x{window.col_off}.tif"
            out_raster.save(out_path, window=window, **out_profile)
        # Close the raster and free the memory
        if zoom: 
            out_raster.data.close()
        return str(out_dir)

    def plot(self, ax=None, figsize=None, **kwargs):
        r"""Plots a raster using :func:`rasterio.plot.show` function.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure the raster. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from :func:`rasterio.plot.show` function.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)
        
        raster_data = self.rasterio()
        ax = rasterio.plot.show(raster_data, ax=ax, **kwargs)
        return ax

    def inner_repr(self):
        return f"bounds={tuple(self.data.bounds)}"


class RasterCollection(GeoCollection, RasterBase):
    r"""
    A raster collection is an ordered set of rasters.
    This class behaves similarly as a list, excepts it is made only of :class:`~geolabel_maker.rasters.raster.Raster`.

    * :attr:`crs` (CRS): Coordinate reference system.
    
    * :attr:`bounds` (BoundingBox): Bounding box of the geographic extent.

    """

    __inner_class__ = Raster

    def __init__(self, *rasters):
        GeoCollection.__init__(self, *rasters)

    @classmethod
    def open(cls, *filenames, **kwargs):
        r"""Opens multiple rasters.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.open` method for further details.

        Args:
            filenames (list): List of filenames.
            kwargs (dict): Optional arguments that will be used to open each raster.

        Returns:
            RasterCollection: The loaded collection of rasters.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, then:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")

            Check if the rasters are successfully loaded:

            >>> rasters
                RasterCollection(
                  (0): Raster(filename='tile1.tif')
                  (1): Raster(filename='tile2.tif')
                )
        """
        return super().open(*filenames, **kwargs)

    def save(self, out_dir, in_place=True):
        """Saves all the rasters in a given directory.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.save` method for further details.

        Args:
            out_dir (str): Path to the output directory.
            in_place (bool): If ``True``, it will update the items of the collection
                with the saved element. This is useful if an object at index :math:`i` is in-memory:
                the new item at :math:`i` will then link to the saved element.

        Returns:
            RasterCollection: Collection of rasters loaded in memory.
        """
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        for i, raster in enumerate(self._items):
            out_file = raster.filename or Path(out_dir) / f"raster_{i}.tif"
            raster.save(out_file)
            # Update the collection if needed
            if in_place:
                self._items[i] = Raster.open(Path(out_dir) / out_file)
        return str(out_dir)

    def to_crs(self, *args, **kwargs):
        r"""Projects the rasters from their initial coordinate reference system (CRS) to another one.

        .. note::
            By default, this method will create in-memory rasters.
            To automatically save them, use ``overwrite`` argument.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.to_crs` method for further details.

        Args:
            crs (str, CRS): The destination CRS.
            overwrite (bool, optional): If ``True``, overwrites the initial rasters saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.

        Returns:
            Raster: The projected raster.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            you can project them in a different CRS with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> crs = "EPSG:4326"
            >>> out_rasters = raster.to_crs(crs)
            
            To automatically replace the ``tile1.tif`` and ``tile2.tif`` with the output rasters,
            use the ``overwrite`` argument:
            
            >>> out_rasters = rasters.to_crs(crs, overwrite=True)
        """
        return super().to_crs(*args, **kwargs)

    def crop(self, *args, **kwargs):
        r"""Crops all rasters in box extent.

        .. note::
            By default, this method will create in-memory rasters.
            To automatically save them, use ``overwrite`` argument.

        .. note::
            The bounding box coordinates should be in the same 
            coordinate reference system (CRS) as the raster collection.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.crop` method for further details.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
            overwrite (bool, optional): If ``True``, overwrites the initial rasters saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.
            
        Returns:
            RasterCollection: The cropped rasters.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            crop them with:
            
            >>> raster = Raster.open("tile.tif")
            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> out_raster = raster.crop(bbox)
            
            To automatically replace the ``tile1.tif`` and ``tile2.tif`` with the output rasters,
            use the ``overwrite`` argument:
            
            >>> out_rasters = rasters.crop(bbox, overwrite=True)
        """
        return super().crop(*args, **kwargs)

    def rescale(self, *args, **kwargs):
        r"""Rescales all rasters in respect of a scale factor.

        .. note::
            By default, this method will create in-memory rasters.
            To automatically save them, use ``overwrite`` argument.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.rescale` method for further details.

        Args:
            factor (float): Rescale factor.
            resampling (str, optional): Resempling method.  
                Options available are from :class:`rasterio.enums.Resampling`. Defaults to ``"bilinear"``.
            overwrite (bool, optional): If ``True``, overwrites the initial rasters saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.                  

        Returns:
            RasterCollection: The rescaled rasters.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            rescale them by two with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> factor = 2
            >>> out_rasters = rasters.rescale(factor)
            
            To automatically replace the ``tile1.tif`` and ``tile2.tif`` with the output rasters,
            use the ``overwrite`` argument:
            
            >>> out_rasters = rasters.rescale(factor, overwrite=True)
        """
        out_rasters = RasterCollection()
        for raster in tqdm(self._items, desc="Rescaling", leave=True, position=0):
            try:
                out_rasters.append(raster.rescale(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not rescale raster '{raster.filename}': {error}")
        return out_rasters

    def zoom(self, *args, **kwargs):
        r"""Zooms the rasters on a `zoom` level. 
        The levels used are from `Open Street Map <https://wiki.openstreetmap.org/wiki/Zoom_levels>`__.

        .. note::
            By default, this method will create in-memory rasters.
            To automatically save them, use ``overwrite`` argument.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.zoom` method for further details.

        Args:
            zoom (int): The zoom level.
            overwrite (bool, optional): If ``True``, overwrites the initial raster saved on disk with the outputs. 
                If ``False``, the output data will not be written on disk. Defaults to ``False``.
            kwargs (dict): Remaining arguments from :func:`~geolabel_maker.rasters.raster.Raster.rescale` method.                  

        Returns:
            RasterCollection: The zoomed rasters.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then to "zoom" at a specific level use:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> zoom_level = 2
            >>> out_rasters = rasters.zoom(zoom_level)
            
            To automatically replace the ``tile1.tif`` and ``tile2.tif`` with the output rasters,
            use the ``overwrite`` argument:
            
            >>> out_rasters = rasters.zoom(zoom_level, overwrite=True)
        """
        out_rasters = RasterCollection()
        for raster in tqdm(self._items, desc=f"Zooming", leave=True, position=0):
            try:
                out_rasters.append(raster.zoom(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not zoom raster '{raster.filename}': {error}")
        return out_rasters

    def mask(self, *args, **kwargs):
        r"""Masks the raster from a set of geometries.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.mask` method for further details.

        Args:
            categories (CategoryCollection): A list of categories, with distinct colors.

        Returns:
            RasterCollection: The masked collections.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters
            and ``buildings.json`` and ``vegetation.json`` are geometries available from the disk,
            you can generate masks (or labels) with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> out_rasters = rasters.mask(categories)
        """
        out_rasters = RasterCollection()
        for raster in tqdm(self._items, desc="Generating Masks", leave=True, position=0):
            try:
                out_rasters.append(raster.mask(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not mask raster '{raster.filename}': {error}")
        return out_rasters

    #! It is not possible to create VRT from in memory rasters.
    def generate_vrt(self, out_file):
        r"""Builds a virtual raster from the rasters.

        Args:
            out_file (str): Name of the output virtual raster.

        Returns:
            str: Path to the VRT file.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then create a virtual raster with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_vrt("tiles.vrt")
        """
        raster_files = []
        for raster in tqdm(self._items, desc="Generating VRT", leave=True, position=0):
            if not isinstance(raster.data, rasterio.DatasetReader):
                raise ValueError(f"Could not access the raster {raster.data.name} from the disk. "
                                 "This error may be raised if the raster was loaded from a temporary file. "
                                 "You should save the rasters first before creating a virtual raster (use `.save()` method).")
            raster_files.append(str(raster.filename))
        out_file = generate_vrt(raster_files, str(out_file))
        return out_file

    def generate_mosaics(self, **kwargs):
        r"""Generates a mosaic from the rasters. 
        A mosaic is a division of the main raster into 'windows'.
        This method does not create slippy tiles.

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.generate_mosaics` method for further details.

        Args:
            width (int, optional): The width of the window. Defaults to ``256``.
            height (int, optional): The height of the window. Defaults to ``256``.
            col_off (int, optional): Column offset for the mosaics.
            row_off (int, optional): Row offset for the mosaics.
            is_full (bool, optional): If ``True``, will only generate mosaics with dimension :math:`(width, height)`.
                Defaults to ``True``.
            out_dir (str, optional): Path to the directory where the windows are saved. Defaults to ``"mosaics"``.

        Returns:
            str: Path to the output directory

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then generate a mosaic of sub-images of shape :math:`(256, 256)` with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_mosaics(width=256, height=256, out_dir="mosaics")
        """
        out_dir = None
        for raster in tqdm(self._items, desc="Generating Mosaics", leave=True, position=0):
            out_dir = raster.generate_mosaics(**kwargs)
        return str(out_dir)

    def generate_tiles(self, out_dir="tiles", **kwargs):
        r"""Create tiles from rasters (using GDAL).

        .. note::
            If the output directory ``out_dir`` does not exist,
            it will be created.

        .. seealso::
            See :func:`~geolabel_maker.rasters.raster.Raster.generate_tiles` method for further details.

        Args:
            kwargs (dict): Optional arguments.

        Returns:
            str: Path to the output directory

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then generate tiles of shape :math:`(256, 256)` with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_tiles(out_dir="tiles")
        """
        # Create a virtual raster of all the files
        rasters_vrt = self.generate_vrt(".raster-collection.vrt")
        out_dir = generate_tiles(rasters_vrt, out_dir=out_dir, **kwargs)
        # Remove the virtual raster
        Path(rasters_vrt).unlink()
        return str(out_dir)

    def plot(self, ax=None, figsize=None, **kwargs):
        r"""Plots the collection using :func:`rasterio.plot.show` function.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: The axes of the figure.
        """
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)
        
        handles = []
        for i, raster in enumerate(self._items):
            ax = raster.plot(ax=ax, **kwargs)
            label = Path(raster.filename).name if raster.filename else f"raster {i}"
            handles.append(mpatches.Patch(facecolor="none", label=label))
        
        # Need to plot empty graph to avoid rasterio issues
        ax.plot([], [])
    
        ax.legend(loc=1, handles=handles, frameon=True)
        plt.title(f"{self.__class__.__name__}")
        return ax
