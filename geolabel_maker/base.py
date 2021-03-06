# Encoding: UTF-8
# File: base.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


"""
This module defines abstract skeleton for geometries, rasters and datasets.

"""


# Basic imports
from tqdm import tqdm
from abc import ABC, abstractmethod
import warnings
from pathlib import Path
import numpy as np
from shapely.geometry import box
import matplotlib.pyplot as plt
import pyproj.crs
import rasterio
import osgeo.osr as osr

# Geolabel Maker
from geolabel_maker.logger import logger


class BoundingBox:
    r"""
    Defines a bounding box as :math`(left, bottom, right, top)`.

    * :attr:`left` (float): The left coordinate of the bounding box.

    * :attr:`bottom` (float): The bottom coordinate of the bounding box.

    * :attr:`right` (float): The right coordinate of the bounding box.

    * :attr:`top` (float): The top coordinate of the bounding box.

    """

    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

    def __iter__(self):
        yield from [self.left, self.bottom, self.right, self.top]

    def __len__(self):
        return 4

    def __repr__(self):
        return f"BoundingBox(left={self.left}, bottom={self.bottom}, right={self.right}, top={self.top})"


class CRS(pyproj.crs.CRS):
    r"""
    Defines a Coordinate Reference System (CRS) from ``pyproj`` implementation.
    This class is mainly used to homogenize CRS representations from ``rasterio`` and ``geopandas``.

    .. seealso::
        Visit the source implementation on `readthedocs <https://pyproj4.github.io/pyproj/dev/api/crs/crs.html>`__.

    """

    def __init__(self, projparams, **kwargs):
        # If initialized from a rasterio.crs.CRS, convert it to pyproj.crs.CRS
        super().__init__(projparams=projparams, **kwargs)

    @classmethod
    def from_rasterio(cls, crs):
        r"""Create a crs from a ``rasterio.crs.CRS`` objetc.

        Args:
            crs (rasterio.crs.CRS): Rasterio crs.

        Returns:
            CRS: CRS in the ``pyproj`` format.

        Examples:
            Get a ``rasterio`` CRS objet:

            >>> import rasterio
            >>> raster = rasterio.open("tile.tif")
            >>> raster_crs
                CRS.from_wkt('LOCAL_CS["RGF93 / CC46",UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","3946"]]')

            Then, convert it to a ``CRS`` object with the above method:

            >>> crs = CRS.from_rasterio(raster_crs)
        """
        # In case the dataset reader is provided
        if isinstance(crs, rasterio.DatasetReader):
            crs = crs.crs

        # Extract the EPSG. This method ensure that the CRS is correctly converted
        # on all operating systems (Linux, Windows etc.)
        srs = osr.SpatialReference()
        srs.SetFromUserInput(crs.to_wkt())
        epsg = srs.GetAttrValue("AUTHORITY", 1)
        return CRS.from_epsg(epsg)

    def __repr__(self):
        return super().__repr__()


class GeoBase(ABC):
    """Abstract architecture for all geographic elements.

    * :attr:`crs` (CRS): The projection of the data.

    * :attr:`bounds` (BoundingBox): The geographic extent of the data.

    """

    def __init__(self):
        super().__init__()

    @property
    def crs(self):
        raise AttributeError(f"This attribute is currently not supported.")

    @property
    def bounds(self):
        raise AttributeError(f"This attribute is currently not supported.")

    @classmethod
    @abstractmethod
    def open(cls, filename, **kwargs):
        """Open the data from a file.

        Args:
            filename (str): Name of the file to load.
            kwargs (dict): Remaining options.

        Returns:
            GeoBase: The loaded geo data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def save(self, out_file):
        """Save the data to the disk.

        Args:
            out_file (str): Name of the output file.

        Returns:
            str: Path to the output file.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def to_crs(self, crs, **kwargs):
        """Project the geo data in another system.

        Args:
            crs (CRS): The destination coordinate  reference system.
            kwargs (dict): Remaining options.

        Returns:
            GeoBase: The projected data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def crop(self, bbox, **kwargs):
        """Crop the data from a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the raster extent.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            GeoBase: The cropped geo data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    def plot_bounds(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the geographic extent of the data.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        x, y = box(*self.bounds).exterior.xy
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        axes.plot(x, y, label=label, **kwargs)
        if label:
            axes.legend(loc=1, frameon=True)
        plt.title(f"Bounds of the {self.__class__.__name__}")
        return axes

    def plot(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the the data.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        return self.plot_bounds(axes=axes, figsize=figsize, label=label, **kwargs)

    def inner_repr(self):
        """Inner representation of the data."""
        return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"


class GeoData(GeoBase):
    r"""
    Abstract class used to wrap rasters, categories and other geo data elements.

    * :attr:`crs` (CRS): CRS projection of the element.

    * :attr:`bounds` (BoundingBox): The geographic extent of the data.

    * :attr:`data` (any): The data to be stored.

    * :attr:`filename` (str): Path to the file.

    """

    def __init__(self, data, filename=None):
        super().__init__()
        self.data = data
        self._filename = str(Path(filename)) if filename else None

    @property
    def filename(self):
        return self._filename

    def __repr__(self):
        rep = f"{self.__class__.__name__}("
        # Add the filename, if exists
        if self.filename:
            rep += f"filename='{self.filename}', "
        rep += f"{self.inner_repr()}"
        # Add the CRS, if exists
        if self.crs:
            rep += f", crs=EPSG:{self.crs.to_epsg()}"
        rep += ")"
        return rep


class GeoCollection(GeoBase):
    """An abstract class used to store a collection of ``Data``.

    * :attr:`crs` (CRS): CRS projection of all elements. If the elements are in different CRS, it will show a warning.

    * :attr:`bounds` (BoundingBox): The geographic extent of all data.

    """

    __inner_class__ = GeoData

    def __init__(self, *items):
        super().__init__()
        self._items = []
        if not items:
            items = []
        elif isinstance(items, self.__inner_class__):
            items = [items]
        elif isinstance(items, (list, tuple)) and len(items) == 1:
            item = items[0]
            if not item:
                items = []
            elif isinstance(item, (list, tuple, self.__class__)):
                items = item
        self.extend(items)

    @property
    def crs(self):
        crs = None
        for value in self._items:
            if crs is None:
                crs = CRS(value.crs)
            # If the CRS are differents, raise a warning and return
            elif value.crs and crs and CRS(value.crs) != crs:
                error_msg = f"The CRS values of the {self.__class__.__name__} are different: " \
                            f"got EPSG:{CRS(value.crs).to_epsg()} != EPSG:{crs.to_epsg()}."
                warnings.warn(error_msg, RuntimeWarning)
                logger.warning(error_msg)
                return crs
        return crs

    @property
    def bounds(self):
        """Get the total geographic extent of the collection."""
        # If the collection is empty
        if len(self) == 0:
            return None

        bounds_array = []
        for value in self:
            bounds_array.append(np.array([*value.bounds]))
        bounds_array = np.stack(bounds_array)
        left = np.min(bounds_array[:, 0])
        bottom = np.min(bounds_array[:, 1])
        right = np.max(bounds_array[:, 2])
        top = np.max(bounds_array[:, 3])
        return BoundingBox(left, bottom, right, top)

    @classmethod
    def open(cls, *filenames, **kwargs):
        collection = []
        for filename in tqdm(filenames, desc="Opening", leave=True, position=0):
            if not Path(filename).is_file():
                raise ValueError(f"{filename} is not a a file.")

            collection.append(cls.__inner_class__.open(filename, **kwargs))
        return cls(*collection)

    @classmethod
    def from_dir(cls, in_dir, pattern="*", **kwargs):
        if not Path(in_dir).is_dir():
            raise ValueError(f"{in_dir} is not a directory.")

        filenames = list(Path(in_dir).rglob(pattern=pattern))
        return cls.open(*filenames, **kwargs)

    @abstractmethod
    def append(self, value):
        """Add a new value to the collection.

        Args:
            value (Data): The data to add.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def insert(self, index, value):
        """Insert a value at a specific index.

        Args:
            index (int): index of the list.
            value (Data): Data to insert.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def extend(self, values):
        """Add a list of data to the collection.

        Args:
            values (list): List of data.
        """
        for value in values:
            self.append(value)

    def count(self, value):
        """Count the occurrence of a specific value in the collection.

        Args:
            value (Data): The data to count.

        Returns:
            int: The occurrence of ``value``.
        """
        return self._items.count(value)

    def index(self, value):
        """Get the index of a value.

        Args:
            value (Data): The data to retrieve its index.

        Returns:
            int: The index of ``value``.
        """
        return self._items.index(value)

    def pop(self, index):
        """Pop and remove a data by its index.

        Args:
            index (int): Index of the data to pop.

        Returns:
            Data: The removed data.
        """
        return self._items.pop(index)

    def remove(self, value):
        """Remove a data by its value.

        Args:
            value (Data): The data to remove.
        """
        self._items.remove(value)

    def clear(self):
        """Empty the collection."""
        self._items.clear()

    def copy(self):
        """Create a copy of the collection.

        Returns:
            GeoCollection: A copy of the collection.
        """
        return self.__class__(self._items.copy())

    def to_crs(self, crs, **kwargs):
        """Change the CRS of the collection's items.

        Args:
            crs (CRS): Destination CRS.

        Returns:
            GeoCollection: The collection with projected data.
        """
        out_collection = self.__class__()
        for data in tqdm(self._items, desc="Projection", leave=True, position=0):
            try:
                if not data.crs or CRS(data.crs) != CRS(crs):
                    data = data.to_crs(crs, **kwargs)
            except Exception as error:
                logger.error(f"Could not change CRS '{data.filename}': {error}")
                continue
            finally:
                out_collection.append(data)
        return out_collection

    def crop(self, *args, **kwargs):
        """Crop all values from a bounding box.

        Args:
            bbox (BoundingBox): The geographic extent used to crop all data.

        Returns:
            GeoCollection: The collection with cropped data.
        """
        out_collection = self.__class__()
        for data in tqdm(self._items, desc="Cropping", leave=True, position=0):
            try:
                out_data = data.crop(*args, **kwargs)
            except Exception as error:
                logger.error(f"Could not rescale raster '{data.filename}': {error}")
                continue
            finally:
                out_collection.append(out_data)
        return out_collection

    def plot_bounds(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the geographic extent of the collection.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        if not axes or figsize:
            _, axes = plt.subplots(figsize=figsize)
        for i, value in enumerate(self):
            label_ = label or f"{value.__class__.__name__.lower()} {i}"
            axes = value.plot_bounds(axes=axes, label=label_, **kwargs)
            if label:
                label = "_no_legend_"
        axes.legend(loc=1, frameon=True)
        plt.title(f"Bounds of the {self.__class__.__name__}")
        return axes

    def plot(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the the data.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        return self.plot_bounds(axes=axes, figsize=figsize, label=label, **kwargs)

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self.insert(index, value)

    def __iter__(self):
        yield from self._items

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        rep = f"{self.__class__.__name__}("
        for i, value in enumerate(self):
            rep += f"\n  ({i}): {value}"
        rep += "\n)"
        return rep
