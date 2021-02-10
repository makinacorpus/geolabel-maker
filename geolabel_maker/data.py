# Encoding: UTF-8
# File: data.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


"""
This module defines abstract skeleton.
Therefore the child classes ``Raster`` and ``Category`` share a common architecture.

"""


# Basic imports
from abc import ABC
import numpy as np
from shapely.geometry import box
import matplotlib.pyplot as plt


class BoundingBox:

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


class Data(ABC):
    r"""
    Abstract class used to wraps rasters, categories and other data related elements.

    * :attr:`data` (any): The data to be stored.

    * :attr:`filename` (str): Path to the file.

    """

    def __init__(self, data, filename=None):
        self.data = data
        self._filename = str(filename) if filename else None

    @property
    def filename(self):
        return self._filename

    @classmethod
    def open(cls, filename, *args, **kwargs):
        """Open the data from a file.

        Args:
            filename (str): Path to the file.

        Returns:
            Data
        """
        raise NotImplementedError

    def save(self, out_file):
        """Save the data to the disk.

        Args:
            out_file (str): name of the saved file.
        """
        raise NotImplementedError

    def get_bounds(self):
        """Get the total bounds of the data."""
        raise NotImplementedError

    def inner_repr(self):
        """Inner representation of the data."""
        return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"


class DataCollection(ABC):
    """An abstract class used to store a list of ``Data``.

    """

    def __init__(self, *items):
        self._items = []
        if isinstance(items, Data):
            items = [items]
        elif isinstance(items, (list, tuple)) and len(items) == 1:
            items = items[0]
        if not items:
            items = []
        self.extend(items)

    def append(self, value):
        """Add a new value to the collection.

        Args:
            value (Data): The data to add.
        """
        raise NotImplementedError

    def insert(self, index, value):
        """Insert a value at a specific index.

        Args:
            index (int): index of the list.
            value (Data): Data to insert.
        """
        raise NotImplementedError

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
        """
        return self._items.count(value)

    def index(self, value):
        """Get the index of a value.

        Args:
            value (Data): The data to retrieve its index.
        """
        return self._items.index(value)

    def pop(self, index):
        """Pop and remove a data by its index.

        Args:
            index (int): Index of the data to pop.

        Returns:
            Data: Removed data.
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
            DataCollection
        """
        return self.__class__(self._items.copy())

    def get_bounds(self):
        """Get the total bounds of the collection."""
        # If the collection is empty
        if len(self) == 0:
            return None
        
        bounds_array = []
        for value in self:
            bounds_array.append(np.array([*value.get_bounds()]))
        bounds_array = np.stack(bounds_array)
        left = np.min(bounds_array[:, 0])
        bottom = np.min(bounds_array[:, 1])
        right = np.max(bounds_array[:, 2])
        top = np.max(bounds_array[:, 3])
        return BoundingBox(left, bottom, right, top)

    def show_bounds(self, axes=None, figsize=None, label=None, **kwargs):
        """Show the geographic extent of the collection.

        Args:
            axes (matplotlib.AxesSubplot, optional): Axes used to show. Defaults to ``None``.
            figsize (tuple, optional): Size of the graph. Defaults to ``None``.
            label (str, optional): Legend for the collection. Defaults to ``None``.
            kwargs (dict): Other arguments from `matplotlib`.

        Returns:
            matplotlib.AxesSubplot
        """
        values_xy = [box(*value.get_bounds()).exterior.xy for value in self]
        if not axes:
            _, axes = plt.subplots(figsize=figsize)
        for i, (x, y) in enumerate(values_xy) :
            axes.plot(x, y, **kwargs, label=label or f"index {i}")
            if label: label = "_no_legend_"
        plt.title(f"Bounds of the {self.__class__.__name__}")
        plt.legend(loc=1, frameon=True)
        return axes

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
