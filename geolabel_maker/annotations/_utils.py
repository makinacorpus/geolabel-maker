# Encoding: UTF-8
# File: utils.py
# Creation: Sunday February 7th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from tqdm import tqdm
from pathlib import Path
from types import GeneratorType
from PIL import Image
import numpy as np


# Geolabel Maker
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.vectors import Category, CategoryCollection


def get_paths(files=None, in_dir=None, pattern="*"):
    paths = []

    # Get paths from a list or collection
    if files:
        if isinstance(files, (Raster, Category)):
            paths = [Path(files.filename)]
        elif isinstance(files, (RasterCollection, CategoryCollection)):
            paths = [Path(data.filename) for data in files]
        elif isinstance(files, (tuple, list, GeneratorType)):
            paths = list(files)
        else:
            raise ValueError(f"Could not retrieve paths for element of type '{type(files).__name__}'.")

    # Get paths from a directory
    elif in_dir and Path(in_dir).is_dir():
        paths = sorted(list(Path(in_dir).rglob(pattern)))

    return paths


def get_categories(categories=None, dir_categories=None, colors=None, pattern="*"):
    collection = CategoryCollection()

    # Get categories from provided colors
    if colors:
        if not isinstance(colors, dict):
            raise ValueError(f"The provided argument 'colors' must be a dict containing categories' names and colors. " \
                             f"Got {type(colors).__name__}.")

        for name, color in colors.items():
            collection.append(Category(None, name, color=color))
        return collection

    # Get categories from a list
    elif categories:
        if not isinstance(categories, (tuple, list, CategoryCollection, GeneratorType)):
            raise ValueError(f"The provided argument 'categories' must be a list of categories (or a collection). " \
                             f"Got {type(categories).__name__}.")

        for category in categories:
            if isinstance(category, Category):
                collection.append(category)
            else:
                collection.append(Category.open(category))
        return collection

    # Get categories from a directory
    elif dir_categories:
        if not isinstance(dir_categories, (str, Path)):
            raise ValueError(f"The provided argument 'dir_categories' must be a string or path. " \
                             f"Got {type(dir_categories).__name__}.")

        collection = CategoryCollection.from_dir(dir_categories, pattern=pattern)
    return collection
