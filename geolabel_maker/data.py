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
        self.filename = filename

    @classmethod
    def open(cls, filename, *args, **kwargs):
        raise NotImplementedError

    def inner_repr(self):
        """Inner representation of the object."""
        return ""
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"
