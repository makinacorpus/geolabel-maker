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
    
    # Crop the raster
    out_raster = raster.crop((43, 2, 44, 3))
    
    # Change its CRS
    out_raster = raster.to_crs("EPSG:4326")
    
    # Generate mosaics
    raster.generate_mosaics()
    
    # Generate tiles
    raster.generate_tiles()
"""


# Basic imports
from abc import abstractmethod
from tqdm import tqdm
from itertools import product
from pathlib import Path
import json
import rasterio
import rasterio.mask
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
import gdal2tiles
from shapely.geometry import box
import geopandas as gpd
import matplotlib.pyplot as plt

# Geolabel Maker
from geolabel_maker.downloads import SentinelHubAPI, MapBoxAPI
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


class RasterBase(GeoBase):
    r"""
    Defines a shared structure for ``Raster`` and ``RasterCollection``.

    """

    @abstractmethod
    def rescale(self, factor):
        raise NotImplementedError

    @abstractmethod
    def zoom(self, zoom):
        raise NotImplementedError

    @abstractmethod
    def mask(self, categories):
        raise NotImplementedError

    @abstractmethod
    def generate_tiles(self, out_dir="tiles", **kwargs):
        raise NotImplementedError

    @abstractmethod
    def generate_mosaics(self, zoom=None, width=256, height=256, is_full=True, out_dir="mosaic"):
        raise NotImplementedError


class Raster(GeoData, RasterBase):
    r"""
    Defines a georeferenced image. This class encapsulates ``rasterio`` dataset,
    and defines custom auto-download and processing methods, to work with `geolabel_maker`.

    * :attr:`data` (rasterio.io.DatasetReader): The ``rasterio`` data corresponding to a georeferenced image.

    * :attr:`filename` (str): Name of the raster image.

    """

    def __init__(self, data, filename=None):
        _check_rasterio(data)
        if (filename and data) and Path(filename) != Path(data.name):
            raise ValueError(f"The provided filename does not correspond to the input data.")
        GeoData.__init__(self, data, filename=filename)

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

    # TODO: remove this method. The user should download data from tje API directly.
    @classmethod
    def download(cls, platform, bbox, **kwargs):
        r"""Download a collection of rasters from a bounding box.
        This method relies on `SentinelHub` API.

        .. note::
            Depending on the bounding box, multiple rasters can be returned.

        Args:
            platform (str): Name of the platform to retrieve satellite imagery.
            bbox (tuple): A bounding box in the format :math:`(lon_{min}, lat_{min}, lon_{max}, lat_{max})`.
            kwargs (dict): Remaining arguments used to connect to the API.

        Returns:
            RasterCollection: The downloaded rasters.
        """
        # Download Sentinel images
        if platform.lower() == "sentinelhub":
            username = kwargs.pop("username", None)
            password = kwargs.pop("password", None)
            api = SentinelHubAPI(username, password)
            files = api.download(bbox, **kwargs)
            return RasterCollection.open(*files)
        # Download MapBox images
        elif platform.lower() == "mapbox":
            access_token = kwargs.pop("access_token", None)
            api = MapBoxAPI(access_token)
            files = api.download(bbox, **kwargs)
            return RasterCollection.open(*files)

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

        Examples:
            If ``tile.tif`` is a raster available from the disk, open it with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.data
                <closed DatasetReader name='tile.tif' mode='r'>

            Notice that the dataset reader is closed. That means the data itself is not loaded,
            and can not be loaded. 
            To load it, simply use the ``to_rasterio`` method to open the dataset:

            >>> raster_data = raster.to_rasterio()
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
        r"""Save the raster to the disk.

        Args:
            out_file (str): Name of the file to be saved.
            window (rasterio.Window, optional): Output window. Defaults to ``None``.
            profile (dict): Profile parameters from ``rasterio``.

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
            raster_data = self.to_rasterio()
            dst.write(raster_data.read(window=window))
        return str(out_file)

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
            Raster: The rescaled raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can rescale it by a given factor with:

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
            Raster: The zoomed raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can change its "zoom" level with:

            >>> raster = Raster.open("tile.tif")
            >>> out_raster = raster.zoom(18)
            
            The zoomed raster is loaded in-memory:
            
            >>> out_raster.filename
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
            Raster: The projected raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, 
            you can project it in a different CRS with:

            >>> raster = Raster.open("tile.tif")
            >>> crs = "EPSG:4326"
            >>> out_raster = raster.to_crs(crs)
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
            Raster: The cropped raster.

        Examples:
            If ``tile.tif`` is a raster available from the disk, crop it with:

            >>> raster = Raster.open("tile.tif")
            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> out_raster = raster.crop(bbox)
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

    def generate_mosaics(self, zoom=None, width=256, height=256, is_full=True, out_dir="mosaic"):
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

        Returns:
            str: Path to the output directory.

        Examples:
            If ``tile.tif`` is a raster available from the disk, generate mosaics with:

            >>> raster = Raster.open("tile.tif")
            >>> raster.generate_mosaics(width=256, height=256, out_dir="mosaic")
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
        return str(out_dir)

    def plot(self, axes=None, figsize=None, **kwargs):
        r"""Plot a raster.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure the raster. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        raster_data = self.to_rasterio()
        array = raster_data.read().transpose(1, 2, 0)
        axes.imshow(array, **kwargs)
        return axes

    def inner_repr(self):
        return f"bounds={tuple(self.data.bounds)}"


class RasterCollection(GeoCollection, RasterBase):
    r"""
    Defines a collection of raster.
    This class behaves similarly as a ``list``, excepts it is made only of ``Raster``.

    """

    def __init__(self, *rasters):
        GeoCollection.__init__(self, *rasters)

    @classmethod
    def open(cls, *filenames, **kwargs):
        r"""Open multiple rasters.

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
        rasters = []
        for filename in filenames:
            rasters.append(Raster.open(filename, **kwargs))
        return RasterCollection(*rasters)

    def save(self, out_dir):
        raise NotImplementedError

    def append(self, raster):
        r"""Add a raster to the collection.

        Args:
            raster (Raster): The raster to add.

        Examples:
            If ``tile.tif`` is a raster available from the disk, then:

            >>> rasters = RasterCollection()
            >>> raster = Raster.open("tile.tif")
            >>> rasters.append(raster)
            
            Check if the raster is successfully added:
            
            >>> rasters
                RasterCollection(
                  (0): Raster(filename='tile.tif')
                )
        """
        _check_raster(raster)
        self._items.append(raster)

    def extend(self, rasters):
        r"""Add multiple raster to the collection.

        Args:
            rasters (list): List of raster to add.

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, then:

            >>> rasters = RasterCollection()
            >>> rasters_list = [Raster.open("tile1.tif"), Raster.open("tile2.tif")]
            >>> rasters.extend(rasters_list)
            
            Check if the rasters are successfully added:
            
            >>> rasters
                RasterCollection(
                  (0): Raster(filename='tile1.tif')
                  (1): Raster(filename='tile2.tif')
                )
        """
        self._items.extend(rasters)

    def insert(self, index, raster):
        """Insert a raster at a specific index.

        Args:
            index (int): Index.
            raster (Raster): Raster to insert.
        """
        _check_raster(raster)
        self._items[index] = raster

    def crop(self, *args, **kwargs):
        """Crop all rasters from a bounding box.

        .. seealso::
            See ``Raster.crop()`` method for further details.

        Args:
            args (list): List of mandatory arguments from ``Raster.crop()`` method.                
            kwargs (dict): Dictionary of optional arguments from ``Raster.crop()`` method.                

        Returns:
            RasterCollection

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then to crop both of them use:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> out_rasters = rasters.crop(bbox)
        """
        out_rasters = RasterCollection()
        for raster in self._items:
            try:
                out_rasters.append(raster.crop(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not crop raster '{raster.filename}': {error}")
        return out_rasters

    def rescale(self, *args, **kwargs):
        """Rescale all rasters in respect of a scale factor.

        .. seealso::
            See ``Raster.rescale()`` method for further details.

        Args:
            args (list): List of mandatory arguments from ``Raster.crop()`` method.                
            kwargs (dict): Dictionary of optional arguments from ``Raster.crop()`` method.                    

        Returns:
            RasterCollection

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then to increase by two their resolution use:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> factor = 2
            >>> out_rasters = rasters.rescale(factor)
        """
        out_rasters = RasterCollection()
        for raster in self._items:
            try:
                out_rasters.append(raster.rescale(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not rescale raster '{raster.filename}': {error}")
        return out_rasters

    def zoom(self, *args, **kwargs):
        """Zoom all rasters in respect of a scale factor.

        .. seealso::
            See ``Raster.zoom()`` method for further details.

        Args:
            args (list): List of mandatory arguments from ``Raster.zoom()`` method.                
            kwargs (dict): Dictionary of optional arguments from ``Raster.zoom()`` method.                    

        Returns:
            RasterCollection

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then to "zoom" at a specific level use:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> zoom_level = 2
            >>> out_rasters = rasters.zoom(zoom_level)
        """
        out_rasters = RasterCollection()
        for raster in self._items:
            try:
                out_rasters.append(raster.zoom(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not zoom raster '{raster.filename}': {error}")
        return out_rasters

    def mask(self, *args, **kwargs):
        """Mask all rasters in respect of a scale factor.

        .. seealso::
            See ``Raster.mask()`` method for further details.

        Args:
            args (list): List of mandatory arguments from ``Raster.mask()`` method.                
            kwargs (dict): Dictionary of optional arguments from ``Raster.mask()`` method.                    

        Returns:
            RasterCollection

        Examples:
            If ``tile1.tif`` and ``tile2.tif`` are rasters
            and ``buildings.json`` and ``vegetation.json`` are geometries available from the disk,
            you can generate masks (or labels) with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> categories = CategoryCollection.open("buildings.json", "vegetation.json")
            >>> out_rasters = rasters.mask(categories)
        """
        out_rasters = RasterCollection()
        for raster in self._items:
            try:
                out_rasters.append(raster.mask(*args, **kwargs))
            except Exception as error:
                logger.error(f"Could not mask raster '{raster.filename}': {error}")
        return out_rasters

    #! It is not possible to create VRT from in memory rasters.
    def generate_vrt(self, out_file):
        """Builds a virtual raster from a list of rasters.

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
        for raster in self._items:
            if not isinstance(raster.data, rasterio.DatasetReader):
                raise ValueError(f"Could not access the raster {raster.data.name} from the disk. "
                                 "This error may be raised if the raster was loaded from a temporary file. "
                                 "You should save the rasters first before creating a virtual raster (use `.save()` method).")
            raster_files.append(str(raster.filename))
        out_file = generate_vrt(raster_files, str(out_file))
        return out_file

    def generate_mosaics(self, **kwargs):
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
            If ``tile1.tif`` and ``tile2.tif`` are rasters available from the disk, 
            then generate a mosaic of sub-images of shape :math:`(256, 256)` with:

            >>> rasters = RasterCollection.open("tile1.tif", "tile2.tif")
            >>> rasters.generate_mosaics(width=256, height=256, out_dir="mosaic")
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

        Args:
            kwargs (dict): Optional arguments.

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
