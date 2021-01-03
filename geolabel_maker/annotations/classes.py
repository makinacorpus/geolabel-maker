# Encoding: UTF-8
# File: classes.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Basic imports
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np

# Geolabel Maker
from .annotation import Annotation


class Classes(Annotation):

    def __init__(self, data):
        super().__init__(data)

    @classmethod
    def from_dataset(cls, dataset, *args, **kwargs):
        # TODO: for each image, get the geometries per categories.
        # TODO: The associated category is the biggest area.
        raise NotImplementedError