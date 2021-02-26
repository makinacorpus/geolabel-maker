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
from .functional import extract_categories


def extract_paths(element, pattern="*.*"):
    paths = []
    if isinstance(element, (str, Path)):
        if Path(element).is_dir():
            paths = list(Path(element).rglob(pattern))
        elif Path(element).is_file():
            paths = [Path(element)]
    elif isinstance(element, (Raster, Category)):
        paths = [Path(element.filename)]
    elif isinstance(element, (RasterCollection, CategoryCollection)):
        paths = [Path(elem.filename) for elem in element]
    elif isinstance(element, (tuple, list, GeneratorType)):
        for elem in element:
            path = extract_paths(elem, pattern=pattern)
            paths.extend(path)
    else:
        raise ValueError(f"Unrecognized type {type(element).__name__}")
    return paths


def find_paths(files=None, in_dir=None, pattern="*"):
    assert files or in_dir, "Files or an input directory must be provided."
    
    # First, retrieve paths from a directory
    paths = []
    if in_dir and Path(in_dir).is_dir():
        paths = list(Path(in_dir).rglob(pattern))
    
    # Then from a list or collection
    elif files:
        if isinstance(files, (Raster, Category)):
            paths = [Path(files.filename)]
        elif isinstance(files, (RasterCollection, CategoryCollection)):
            paths = [Path(data.filename) for data in files]
        elif isinstance(files, (tuple, list, GeneratorType)):
            paths = files
        else:
            raise ValueError(f"Unrecognized type {type(files).__name__}")
    paths.sort()
    return paths


def find_colors(categories=None, colors=None):
    assert categories or colors, "Categories or colors must be provided."
    
    if colors:
        categories = CategoryCollection()
        for name, color in colors.items():
            categories.append(Category(None, name, color=color))
        return categories
    return categories
