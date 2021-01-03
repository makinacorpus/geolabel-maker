# Encoding: UTF-8
# File: data.py
# Creation: Tuesday December 29th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


r"""
Defines an abstract architecture for all subsets of data i.e. ``Annotation``, ``Raster``, ``Category``.

.. note::
    This module will be extended to support `MLFlow <https://mlflow.org/>`__ workflow.
"""

# Basic imports
from abc import ABC


class Data(ABC):
    r"""
    A ``Data`` object is an abstract skeleton used to wrap ``Raster``, ``Category`` and ``Annotation``.
    This class is also used to defines the pipeline and tools 
    used to process ML models with `MLFlow <https://mlflow.org/>`__ workflow.

    """

    def __init__(self):
        super().__init__()

    @classmethod
    def open(cls, filename):
        raise NotImplementedError

    def save(self, outname):
        raise NotImplementedError

    def inner_repr(self):
        return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.inner_repr()})"
