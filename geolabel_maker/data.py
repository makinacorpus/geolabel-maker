# Encoding: UTF-8
# File: data.py
# Creation: Friday February 5th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from abc import ABC


class Data(ABC):
    r"""
    Abstract class used to wraps rasters, categories and other data related elements.

    * :attr:`data` (any): The data to be stored.

    * :attr:`filename` (str): Path to the file.

    """

    def __init__(self, data, filename=None):
        self.data = data
        self.filename = str(filename) if filename else None

    @classmethod
    def open(cls, filename, *args, **kwargs):
        raise NotImplementedError

    def save(self, filename):
        raise NotImplementedError

    def inner_repr(self):
        """Inner representation of the object."""
        return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"


class DataCollection(ABC):

    def __init__(self, *items):
        self._items = []
        if isinstance(items, Data):
            items = [items]
        elif isinstance(items, (list, tuple)) and len(items) == 1:
            items = items[0]
        elif not items:
            items = []
        self.extend(items)

    def append(self, value):
        raise NotImplementedError

    def insert(self, index, value):
        raise NotImplementedError

    def extend(self, values):
        for value in values:
            self.append(value)

    def count(self, value):
        return self._items.count(value)

    def index(self, value):
        return self._items.index(value)

    def pop(self, index):
        return self._items.pop(index)

    def remove(self, value):
        self._items.remove(value)

    def clear(self):
        self._items.clear()

    def copy(self):
        return self.__class__(self._items.copy())

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
