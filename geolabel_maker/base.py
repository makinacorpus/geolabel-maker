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
import rasterio.crs
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
    """Wraps ``pyproj.crs.CRS`` to add custom methods."""

    def __init__(self, projparams, **kwargs):
        # If initialized from a rasterio.crs.CRS, convert it to pyproj.crs.CRS
        if isinstance(projparams, rasterio.crs.CRS):   
            srs = osr.SpatialReference()
            srs.SetFromUserInput(projparams.to_wkt())
            epsg = srs.GetAttrValue("AUTHORITY", 1)
            projparams = int(epsg)
        super().__init__(projparams=projparams, **kwargs)

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
        """Open the data from a file."""
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def save(self, out_file):
        """Save the data to the disk."""
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def to_crs(self, crs, **kwargs):
        """Project the geo data in another system."""
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def crop(self, bbox, **kwargs):
        """Crop the data from a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the raster extent.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    def plot_bounds(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the geographic extent of the data.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
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
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
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

    * :attr:`crs` (CRS): CRS projection of all elements. 
        If the elements are in different CRS, it will show a warning.

    * :attr:`bounds` (BoundingBox): The geographic extent of all data.

    """

    def __init__(self, *items):
        super().__init__()
        self._items = []
        if not items:
            items = []
        elif isinstance(items, GeoData):
            items = [items]
        elif isinstance(items, (list, tuple)) and len(items) == 1:
            item = items[0]
            if not item:
                items = []
            elif isinstance(item, (list, tuple, GeoCollection)):
                items = item
        self.extend(items)

    @property
    def crs(self):
        crs = None
        for value in self._items:
            if crs is None:
                crs = CRS(value.crs)
            elif value.crs and crs and CRS(value.crs) != crs:
                error_msg = f"The CRS values of the {self.__class__.__name__} are different: " \
                            f"got EPSG:{CRS(value.crs).to_epsg()} != EPSG:{crs.to_epsg()}."
                warnings.warn(error_msg, RuntimeWarning)
                logger.warning(error_msg)
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
        """Project all values of the collection to `CRS`.

        Args:
            crs (CRS): Destination `CRS`.

        Returns:
            GeoCollection: The collection with projected data.

        Examples:
            Load a ``RasterCollection`` or ``CategoryCollection`` as ``collection``.
            Then, you can convert all its elements into another ``CRS`` with:

            >>> collection.to_crs("EPSG:4326")
        """
        collection = self.__class__()
        for value in tqdm(self._items, desc="Projection", leave=True, position=0):
            if not value.crs or CRS(value.crs) != CRS(crs):
                value = value.to_crs(crs, **kwargs)
            collection.append(value)
        return collection

    def crop(self, bbox, **kwargs):
        """Crop all values from a bounding box.

        Args:
            bbox (BoundingBox): The geographic extent used to crop all data.

        Returns:
            GeoCollection: The collection with cropped data.

        Examples:
            Load a ``RasterCollection`` or ``CategoryCollection`` as ``collection``.
            Then, you can crop all its elements into a smaller sub set with:

            >>> bbox = (1843045.92, 5173595.36, 1843056.48, 5173605.92)
            >>> collection.crop(bbox)
        """
        collection = self.__class__()
        for value in tqdm(self._items, desc="Cropping", leave=True, position=0):
            try:
                value = value.crop(bbox, **kwargs)
            except Exception:
                continue
            finally:
                collection.append(value)
        return collection

    def plot_bounds(self, axes=None, figsize=None, label=None, **kwargs):
        """Plot the geographic extent of the collection.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.

        Examples:
            Load a ``RasterCollection`` or ``CategoryCollection`` as ``collection``.
            Then, you can plot its geographic extent:

            >>> collection.plot_bounds()
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
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.

        Examples:
            Load a ``RasterCollection`` or ``CategoryCollection`` as ``collection``.
            Then, you can plot its content:

            >>> collection.plot()
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
