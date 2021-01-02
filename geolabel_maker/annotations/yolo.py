# Encoding: UTF-8
# File: yolo.py
# Creation: Friday January 1st 2021
# Supervisor: Daphné Lercier (dlercier)
# Author: Arthur Dujardin (arthurdjn)
# ------
# Copyright (c) 2021, Makina Corpus


# Geolabel Maker
from .annotation import Annotation


class YOLO(Annotation):

    def __init__(self, data):
        super().__init__(data)

    @classmethod
    def from_dataset(cls, dataset, *args, **kwargs):
        raise NotImplementedError
