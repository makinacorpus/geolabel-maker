# Encoding: UTF-8
# File: base.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


r"""
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
    Defines a bounding box as :math:`(\text{left}, \text{bottom}, \text{right}, \text{top})`.

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


def to_crs(element):
    r"""Converts an element to a Coordinate Reference System (CRS).

    Args:
        element (Any): An object describing a coordinate reference system.

    Returns:
        CRS: The associated CRS.
    """
    if isinstance(element, rasterio.crs.CRS):
        return CRS.from_rasterio(element)
    elif isinstance(element, CRS):
        return element
    return CRS(element)


class CRS(pyproj.crs.CRS):
    r"""
    Defines a Coordinate Reference System (CRS) from :mod:`pyproj` implementation.
    This class is mainly used to homogenize CRS representations from :mod:`rasterio` and :mod:`geopandas`.

    .. seealso::
        See :class:`pyproj.crs.CRS` on `readthedocs <https://pyproj4.github.io/pyproj/dev/api/crs/crs.html>`__
        for further details.

    """

    def __init__(self, projparams, **kwargs):
        super().__init__(projparams=projparams, **kwargs)

    @classmethod
    def from_rasterio(cls, crs):
        r"""Creates a crs from a ``rasterio.crs.CRS`` objetc.

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

    def __eq__(self, crs):
        crs = to_crs(crs)
        if crs.to_epsg() == self.to_epsg():
            return True
        return False

    def __repr__(self):
        return super().__repr__()


class GeoBase(ABC):
    r"""
    Abstract architecture used to wrap geographic data.

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
        r"""Opens the data from a file.

        Args:
            filename (str): Name of the file to load.
            kwargs (dict): Remaining options.

        Returns:
            GeoBase: The loaded geo data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def save(self, out_file):
        r"""Saves the data to the disk.

        Args:
            out_file (str): Name of the output file.

        Returns:
            str: Path to the output file.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def to_crs(self, crs, **kwargs):
        r"""Projects the geo data from its coordinate reference system (CRS) to another one.

        Args:
            crs (CRS): Destination CRS.
            kwargs (dict): Remaining options.

        Returns:
            GeoBase: The projected data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    @abstractmethod
    def crop(self, bbox, **kwargs):
        r"""Crops the data in a bounding box.

        .. note::
            The bounding box coordinates should be in the same system as the raster extent.

        Args:
            bbox (tuple): Bounding box used to crop the rasters,
                in the format :math:`(X_{min}, Y_{min}, X_{max}, Y_{max})`.

        Returns:
            GeoBase: The cropped geo data.
        """
        raise NotImplementedError(f"This method is currently not supported.")

    def plot_bounds(self, ax=None, figsize=None, **kwargs):
        r"""Plots the geographic extent of the data using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)

        x, y = box(*self.bounds).exterior.xy
        ax.plot(x, y, **kwargs)

        plt.title(f"Bounds of the {self.__class__.__name__}")
        return ax

    def plot(self, ax=None, figsize=None, **kwargs):
        r"""Plots the data using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        return self.plot_bounds(ax=ax, figsize=figsize, **kwargs)

    def inner_repr(self):
        r"""Inner representation of the data."""
        return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"


class GeoData(GeoBase):
    r"""
    Abstract architecture used to wrap rasters, categories and other single geo data objects.

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
    r"""
    Abstract architecture used to wrap a collection of data.

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
        r"""Gets the coordinate reference system (CRS).
        Raises a warning if the elements are in different CRS.
        """
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
        r"""Gets the total geographic extent of the collection."""
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
        r"""Opens a collection from multiple file paths.

        Args:
            filenames (list): List of file paths.

        Returns:
            GeoCollection: The loaded collection.
        """
        collection = []
        for filename in tqdm(filenames, desc="Opening", leave=True, position=0):
            if not Path(filename).is_file():
                raise ValueError(f"{filename} is not a a file.")

            collection.append(cls.__inner_class__.open(filename, **kwargs))
        return cls(*collection)

    @classmethod
    def from_dir(cls, in_dir, pattern="*", **kwargs):
        """Opens a collection from a directory.

        Args:
            in_dir (str): Path to the directory containing the data to be loaded.
            pattern (str, optional): Regular expression used to filter data. Defaults to ``"*"``.
    
        Returns:
            GeoCollection: The loaded collection.
        """
        if not in_dir:
            return cls()

        if not Path(in_dir).is_dir():
            raise ValueError(f"'{in_dir}' is not a directory.")

        filenames = sorted(list(Path(in_dir).rglob(pattern=pattern)))
        return cls.open(*filenames, **kwargs)

    def _check_data(self, data):
        if not isinstance(data, self.__inner_class__):
            raise ValueError(f"Invalid data '{type(data).__name__}' encountered for collection '{self.__class__.__name__}'.")

    def append(self, data):
        r"""Adds a new data to the collection.

        Args:
            data (GeoData): The data to add.
        """
        self._check_data(data)
        self._items.append(data)

    def insert(self, index, data):
        r"""Inserts a data at a specific index.

        Args:
            index (int): index of the list.
            data (GeoData): Data to insert.
        """
        self._check_data(data)
        self._items.insert(index, data)

    def extend(self, collection):
        r"""Adds a list of data to the collection.

        Args:
            collection (list): List of data.
        """
        for data in collection:
            self.append(data)

    def count(self, data):
        r"""Counts the occurrence of a specific data in the collection.

        Args:
            data (GeoData): The data to count.

        Returns:
            int: The occurrence of data.
        """
        return self._items.count(data)

    def index(self, data):
        r"""Gets the index of a data.

        Args:
            data (GeoData): The data to retrieve its index.

        Returns:
            int: The index of data.
        """
        return self._items.index(data)

    def pop(self, index):
        r"""Pops and remove a data by its index.

        Args:
            index (int): Index of the data to pop.

        Returns:
            Data: The removed data.
        """
        return self._items.pop(index)

    def remove(self, data):
        r"""Removes a data from the collection.

        Args:
            data (GeoData): The data to remove.
        """
        self._items.remove(data)

    def clear(self):
        r"""Clears the collection."""
        self._items.clear()

    def copy(self):
        r"""Creates a copy of the collection.

        Returns:
            GeoCollection: A copy of the collection.
        """
        return self.__class__(self._items.copy())

    def to_crs(self, crs, **kwargs):
        r"""Projects all data from the collection to another coordinate reference system (CRS).

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
                out_collection.append(data)
            except Exception as error:
                logger.debug(f"Could not change CRS '{data.filename}': {error}")
                continue

        return out_collection

    def crop(self, *args, **kwargs):
        r"""Crops all data from the collection in a bounding box.

        Args:
            bbox (BoundingBox): The geographic extent used to crop all data.

        Returns:
            GeoCollection: The collection with cropped data.
        """
        out_collection = self.__class__()
        for data in tqdm(self._items, desc="Cropping", leave=True, position=0):
            try:
                out_data = data.crop(*args, **kwargs)
                out_collection.append(out_data)
            except Exception as error:
                logger.debug(f"Could not crop '{data.filename}': {error}")
                continue

        return out_collection

    def plot_bounds(self, ax=None, figsize=None, **kwargs):
        r"""Plots the geographic extent of the collection using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Remaining arguments from :func`matplotlib.pyplot.plot`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        if not ax or figsize:
            _, ax = plt.subplots(figsize=figsize)

        for i, data in enumerate(self):
            kwargs["label"] = Path(data.filename).stem if data.filename else f"{data.__class__.__name__.lower()} {i}"
            ax = data.plot_bounds(ax=ax, **kwargs)

        ax.legend(loc=1, frameon=True)
        plt.title(f"Bounds of the {self.__class__.__name__}")
        return ax

    def plot(self, ax=None, figsize=None, **kwargs):
        r"""Plots the collection using :mod:`matplotlib.pyplot`.

        Args:
            ax (matplotlib.AxesSubplot, optional): Axes of the figure. Defaults to ``None``.
            figsize (tuple, optional): Size of the figure. Defaults to ``None``.
            kwargs (dict): Remaining arguments from :func`matplotlib.pyplot.plot`.

        Returns:
            matplotlib.AxesSubplot: Axes of the figure.
        """
        return self.plot_bounds(ax=ax, figsize=figsize, **kwargs)

    def __getitem__(self, index):
        out_item = self._items[index]
        # In case multiple items are returned, wrap them in a collection
        if isinstance(out_item, list):
            return self.__class__(out_item)
        return out_item

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
