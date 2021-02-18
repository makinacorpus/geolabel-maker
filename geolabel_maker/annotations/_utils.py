# Encoding: UTF-8
# File: utils.py
# Creation: Sunday February 7th 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
from types import GeneratorType


# Geolabel Maker
from geolabel_maker.rasters import Raster, RasterCollection
from geolabel_maker.vectors import Category, CategoryCollection


def extract_paths(element, pattern="*.*"):
    paths = []
    if isinstance(element, (str, Path)):
        if Path(element).is_dir():
            paths = list(Path(element).rglob(pattern))
        elif Path(element).is_file():
            paths =  [Path(element)]
    elif isinstance(element, (Raster, Category)):
        paths =  [Path(element.filename)]
    elif isinstance(element, (RasterCollection, CategoryCollection)):
        paths =  [Path(elem.filename) for elem in element]
    elif isinstance(element, (tuple, list, GeneratorType)):
        for elem in element:
            path = extract_paths(elem, pattern=pattern)
            paths.extend(path)
    else:
        raise ValueError(f"Unrecognized type {type(element).__name__}")
    return paths
