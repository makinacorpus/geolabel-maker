# Encoding: UTF-8
# File: __init__.py
# Creation: Monday December 28th 2020
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2020, Makina Corpus


# Basic imports
from shapely import speedups

# Geolabel Maker
from .dataset import Dataset


DISABLE_SPEEDUPS = False

if DISABLE_SPEEDUPS:
    speedups.disable()
else:
    speedups.enable()
