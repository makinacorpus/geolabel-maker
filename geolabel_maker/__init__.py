# Encoding: UTF-8
# File: __init__.py
# Creation: Monday December 28th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from shapely import speedups
import os
from PIL import Image

# Geolabel Maker
from .dataset import Dataset


# Global variables
HERE = os.path.abspath(os.path.dirname(__file__))
Image.MAX_IMAGE_PIXELS = 156_250_000


__version__ = open(os.path.join(HERE, "VERSION.md")).read().strip()
__all__ = (
    "__version__",
    "Dataset"
)
